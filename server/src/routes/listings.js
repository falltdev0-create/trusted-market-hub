import { Router } from "express";
import { db, uid, json } from "../db.js";
import { requireAuth, isAdmin } from "../auth.js";
import { ai, computeTier } from "../ai.js";

export const router = Router();

function hydrate(row) {
  if (!row) return null;
  const images = db
    .prepare("SELECT url FROM listing_images WHERE listing_id = ? ORDER BY sort_order")
    .all(row.id)
    .map((r) => r.url);
  return {
    ...row,
    images,
    details: json(row.details, {}),
    condition_report: json(row.condition_report, null),
    docs_report: json(row.docs_report, null),
  };
}

function getOwned(id, user) {
  const row = db.prepare("SELECT * FROM listings WHERE id = ?").get(id);
  if (!row) return { error: [404, "الإعلان غير موجود — ابدأ إعلاناً جديداً"] };
  if (row.owner_id !== user.id && !isAdmin(user)) return { error: [403, "لا تملك صلاحية هذا الإعلان"] };
  return { row };
}

/** GET /listings/ — قائمة الإعلانات المنشورة مع الفلاتر */
router.get("/", (req, res) => {
  const { city, category, kind, listing_type, price_tier, q, condition_grade } = req.query;
  const min = req.query.min_price, max = req.query.max_price;
  const where = ["status = 'published'"];
  const params = {};
  const add = (cond, key, val) => {
    if (val !== undefined && val !== "" && val !== null) {
      where.push(cond);
      params[key] = val;
    }
  };
  add("city = :city", "city", city);
  add("category = :category", "category", category);
  add("kind = :kind", "kind", kind);
  add("listing_type = :listing_type", "listing_type", listing_type);
  add("price_tier = :price_tier", "price_tier", price_tier);
  add("condition_grade = :condition_grade", "condition_grade", condition_grade);
  add("price >= :min", "min", min ? Number(min) : undefined);
  add("price <= :max", "max", max ? Number(max) : undefined);
  if (q) {
    where.push("(title LIKE :q OR description LIKE :q OR brand LIKE :q OR model LIKE :q)");
    params.q = `%${q}%`;
  }
  const page = Math.max(1, Number(req.query.page || 1));
  const limit = Math.min(60, Number(req.query.limit || 24));
  const rows = db
    .prepare(
      `SELECT * FROM listings WHERE ${where.join(" AND ")} ORDER BY created_at DESC LIMIT ${limit} OFFSET ${(page - 1) * limit}`,
    )
    .all(params);
  const total = db.prepare(`SELECT COUNT(*) c FROM listings WHERE ${where.join(" AND ")}`).get(params).c;
  res.json({ items: rows.map(hydrate), total, page, limit });
});

/** GET /listings/mine */
router.get("/mine", requireAuth, (req, res) => {
  const rows = db.prepare("SELECT * FROM listings WHERE owner_id = ? ORDER BY created_at DESC").all(req.user.id);
  res.json({ items: rows.map(hydrate), total: rows.length });
});

/** POST /listings/ — إنشاء مسودة */
router.post("/", requireAuth, (req, res) => {
  const { kind, category, listing_type } = req.body || {};
  const id = uid();
  db.prepare(
    "INSERT INTO listings (id, owner_id, kind, category, listing_type, status) VALUES (?,?,?,?,?,'draft')",
  ).run(id, req.user.id, kind || category || null, category || kind || null, listing_type || null);
  res.status(201).json(hydrate(db.prepare("SELECT * FROM listings WHERE id = ?").get(id)));
});

/** GET /listings/:id */
router.get("/:id", (req, res) => {
  const row = db.prepare("SELECT * FROM listings WHERE id = ?").get(req.params.id);
  if (!row) return res.status(404).json({ detail: "الإعلان غير موجود" });
  db.prepare("UPDATE listings SET views = views + 1 WHERE id = ?").run(row.id);
  res.json(hydrate({ ...row, views: row.views + 1 }));
});

/** POST /listings/:id/update-details */
router.post("/:id/update-details", requireAuth, async (req, res) => {
  const { row, error } = getOwned(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  const d = req.body?.details ?? req.body ?? {};
  db.prepare(
    `UPDATE listings SET title = COALESCE(?, title), description = COALESCE(?, description),
       city = COALESCE(?, city), district = COALESCE(?, district), area = COALESCE(?, area),
       rooms = COALESCE(?, rooms), bathrooms = COALESCE(?, bathrooms), year = COALESCE(?, year),
       mileage = COALESCE(?, mileage), brand = COALESCE(?, brand), model = COALESCE(?, model),
       details = ?, updated_at = datetime('now') WHERE id = ?`,
  ).run(
    d.title ?? null, d.description ?? null, d.city ?? null, d.district ?? null,
    d.area ?? null, d.rooms ?? null, d.bathrooms ?? null, d.year ?? null,
    d.mileage ?? null, d.brand ?? null, d.model ?? null,
    JSON.stringify(d), row.id,
  );

  // تقدير سعر إرشادي (غير إلزامي)
  const est = await ai.estimatePrice({
    category: row.kind || row.category || "house",
    listing_type: row.listing_type || "sale",
    condition_grade: row.condition_grade || "good",
    features: { ...d, city: d.city ?? row.city },
  });
  if (est?.ok && est.suggested_price) {
    db.prepare("UPDATE listings SET suggested_price = ? WHERE id = ?").run(est.suggested_price, row.id);
  }
  res.json({ ...hydrate(db.prepare("SELECT * FROM listings WHERE id = ?").get(row.id)), price_estimate: est });
});

/** GET /listings/:id/price-suggestion */
router.get("/:id/price-suggestion", requireAuth, async (req, res) => {
  const { row, error } = getOwned(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  const est = await ai.estimatePrice({
    category: row.kind || row.category || "house",
    listing_type: row.listing_type || "sale",
    condition_grade: row.condition_grade || "good",
    features: json(row.details, {}),
  });
  res.json({ suggested_price: est?.suggested_price ?? row.suggested_price, ...est });
});

/** POST /listings/:id/set-price — بدون سقف إلزامي، فقط تصنيف */
router.post("/:id/set-price", requireAuth, async (req, res) => {
  const { row, error } = getOwned(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  const price = Number(req.body?.price);
  if (!price || price <= 0) return res.status(422).json({ detail: "أدخل سعراً صحيحاً" });

  let suggested = row.suggested_price;
  if (!suggested) {
    const est = await ai.estimatePrice({
      category: row.kind || row.category || "house",
      listing_type: row.listing_type || "sale",
      condition_grade: row.condition_grade || "good",
      features: json(row.details, {}),
    });
    suggested = est?.suggested_price ?? price;
  }
  const tier = computeTier(price, suggested);
  db.prepare(
    "UPDATE listings SET price = ?, suggested_price = ?, price_tier = ?, updated_at = datetime('now') WHERE id = ?",
  ).run(price, suggested, tier, row.id);
  res.json({ price, suggested_price: suggested, price_tier: tier });
});

/** POST /listings/:id/submit-for-review */
router.post("/:id/submit-for-review", requireAuth, (req, res) => {
  const { row, error } = getOwned(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  db.prepare("UPDATE listings SET status = 'pending_review', updated_at = datetime('now') WHERE id = ?").run(row.id);
  db.prepare("INSERT INTO notifications (id, user_id, title, body, type, link) VALUES (?,?,?,?,?,?)").run(
    uid(), row.owner_id, "تم إرسال إعلانك للمراجعة", "سيتم إشعارك فور اعتماده.", "listing", `/listing/${row.id}`,
  );
  res.json({ id: row.id, status: "pending_review" });
});

router.delete("/:id", requireAuth, (req, res) => {
  const { row, error } = getOwned(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  db.prepare("DELETE FROM listings WHERE id = ?").run(row.id);
  res.json({ deleted: row.id });
});
