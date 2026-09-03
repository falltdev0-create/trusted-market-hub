import { Router } from "express";
import bcrypt from "bcryptjs";
import { db, uid, json } from "../db.js";
import { requireAdmin, publicUser, audit, adminLevel } from "../auth.js";

export const router = Router();

const notify = (userId, title, body, type = "info", link = null) =>
  db.prepare("INSERT INTO notifications (id, user_id, title, body, type, link) VALUES (?,?,?,?,?,?)").run(
    uid(), userId, title, body, type, link,
  );

const hydrateListing = (row) => ({
  ...row,
  details: json(row.details, {}),
  condition_report: json(row.condition_report, null),
  docs_report: json(row.docs_report, null),
  images: db
    .prepare("SELECT url FROM listing_images WHERE listing_id = ? ORDER BY sort_order")
    .all(row.id)
    .map((r) => r.url),
  documents: db.prepare("SELECT * FROM listing_documents WHERE listing_id = ?").all(row.id),
  owner: publicUser(db.prepare("SELECT * FROM users WHERE id = ?").get(row.owner_id)),
});

/** إحصائيات لوحة التحكم */
router.get("/dashboard-stats", requireAdmin("reviewer"), (_req, res) => {
  const one = (sql, ...p) => db.prepare(sql).get(...p).c;
  res.json({
    pending_listings: one("SELECT COUNT(*) c FROM listings WHERE status = 'pending_review'"),
    published_listings: one("SELECT COUNT(*) c FROM listings WHERE status = 'published'"),
    rejected_listings: one("SELECT COUNT(*) c FROM listings WHERE status = 'rejected'"),
    draft_listings: one("SELECT COUNT(*) c FROM listings WHERE status = 'draft'"),
    total_users: one("SELECT COUNT(*) c FROM users"),
    banned_users: one("SELECT COUNT(*) c FROM users WHERE is_banned = 1"),
    pending_kyc: one("SELECT COUNT(*) c FROM kyc_submissions WHERE status = 'pending'"),
    conversations: one("SELECT COUNT(*) c FROM conversations"),
    messages: one("SELECT COUNT(*) c FROM messages"),
    recent_activity: db
      .prepare("SELECT * FROM admin_audit_logs ORDER BY created_at DESC LIMIT 10")
      .all()
      .map((r) => ({ ...r, meta: json(r.meta, {}) })),
  });
});

/* ------------------------- الإعلانات ------------------------- */
router.get("/listings", requireAdmin("reviewer"), (req, res) => {
  const status = req.query.status;
  const page = Math.max(1, Number(req.query.page || 1));
  const limit = Math.min(50, Number(req.query.limit || 20));
  const where = status ? "WHERE status = @status" : "";
  const rows = db
    .prepare(`SELECT * FROM listings ${where} ORDER BY created_at DESC LIMIT ${limit} OFFSET ${(page - 1) * limit}`)
    .all(status ? { status } : {});
  const total = db.prepare(`SELECT COUNT(*) c FROM listings ${where}`).get(status ? { status } : {}).c;
  res.json({ items: rows.map(hydrateListing), total, page, limit });
});

router.get("/pending-listings", requireAdmin("reviewer"), (req, res) => {
  const page = Math.max(1, Number(req.query.page || 1));
  const limit = 20;
  const rows = db
    .prepare(
      `SELECT * FROM listings WHERE status = 'pending_review' ORDER BY created_at ASC LIMIT ${limit} OFFSET ${(page - 1) * limit}`,
    )
    .all();
  const total = db.prepare("SELECT COUNT(*) c FROM listings WHERE status = 'pending_review'").get().c;
  res.json({ items: rows.map(hydrateListing), total, page, limit });
});

router.get("/listings/:id", requireAdmin("reviewer"), (req, res) => {
  const row = db.prepare("SELECT * FROM listings WHERE id = ?").get(req.params.id);
  if (!row) return res.status(404).json({ detail: "الإعلان غير موجود" });
  res.json(hydrateListing(row));
});

router.post("/approve-listing", requireAdmin("moderator"), (req, res) => {
  const id = req.body?.listing_id || req.body?.id;
  const row = db.prepare("SELECT * FROM listings WHERE id = ?").get(id);
  if (!row) return res.status(404).json({ detail: "الإعلان غير موجود" });
  db.prepare("UPDATE listings SET status = 'published', reject_reason = NULL, updated_at = datetime('now') WHERE id = ?").run(id);
  notify(row.owner_id, "تم نشر إعلانك", "تمت الموافقة على إعلانك وهو الآن متاح للمشترين.", "listing", `/listing/${id}`);
  audit(req.user.id, "approve_listing", "listing", id, {});
  res.json({ id, status: "published" });
});

router.post("/reject-listing", requireAdmin("moderator"), (req, res) => {
  const id = req.body?.listing_id || req.body?.id;
  const reason = req.body?.reason || "لم يستوفِ الإعلان شروط النشر";
  const row = db.prepare("SELECT * FROM listings WHERE id = ?").get(id);
  if (!row) return res.status(404).json({ detail: "الإعلان غير موجود" });
  db.prepare("UPDATE listings SET status = 'rejected', reject_reason = ?, updated_at = datetime('now') WHERE id = ?").run(reason, id);
  notify(row.owner_id, "تم رفض إعلانك", reason, "listing", `/my-listings`);
  audit(req.user.id, "reject_listing", "listing", id, { reason });
  res.json({ id, status: "rejected", reason });
});

router.delete("/listings/:id", requireAdmin("admin"), (req, res) => {
  db.prepare("DELETE FROM listings WHERE id = ?").run(req.params.id);
  audit(req.user.id, "delete_listing", "listing", req.params.id, {});
  res.json({ deleted: req.params.id });
});

/* ------------------------- المستخدمون ------------------------- */
router.get("/users", requireAdmin("moderator"), (req, res) => {
  const q = req.query.q ? `%${req.query.q}%` : null;
  const rows = q
    ? db.prepare("SELECT * FROM users WHERE full_name LIKE ? OR email LIKE ? ORDER BY created_at DESC LIMIT 200").all(q, q)
    : db.prepare("SELECT * FROM users ORDER BY created_at DESC LIMIT 200").all();
  res.json({ items: rows.map(publicUser), total: rows.length });
});

router.patch("/users/:id", requireAdmin("admin"), (req, res) => {
  const target = db.prepare("SELECT * FROM users WHERE id = ?").get(req.params.id);
  if (!target) return res.status(404).json({ detail: "المستخدم غير موجود" });
  if (adminLevel(target) >= adminLevel(req.user) && target.id !== req.user.id)
    return res.status(403).json({ detail: "لا يمكنك تعديل حساب بصلاحيات مساوية أو أعلى" });

  const { role, admin_role, is_banned, is_active, kyc_status, trust_score } = req.body || {};
  if ((role === "super_admin" || admin_role === "super_admin") && req.user.role !== "super_admin")
    return res.status(403).json({ detail: "منح صلاحية السوبر أدمن يتطلب سوبر أدمن" });

  db.prepare(
    `UPDATE users SET role = COALESCE(?, role), admin_role = COALESCE(?, admin_role),
       is_banned = COALESCE(?, is_banned), is_active = COALESCE(?, is_active),
       kyc_status = COALESCE(?, kyc_status), trust_score = COALESCE(?, trust_score),
       updated_at = datetime('now') WHERE id = ?`,
  ).run(
    role ?? null, admin_role ?? null,
    is_banned === undefined ? null : is_banned ? 1 : 0,
    is_active === undefined ? null : is_active ? 1 : 0,
    kyc_status ?? null, trust_score ?? null, target.id,
  );
  audit(req.user.id, "update_user", "user", target.id, req.body || {});
  res.json(publicUser(db.prepare("SELECT * FROM users WHERE id = ?").get(target.id)));
});

router.post("/users/:id/ban", requireAdmin("admin"), (req, res) => {
  const banned = req.body?.banned === undefined ? 1 : req.body.banned ? 1 : 0;
  db.prepare("UPDATE users SET is_banned = ? WHERE id = ?").run(banned, req.params.id);
  audit(req.user.id, banned ? "ban_user" : "unban_user", "user", req.params.id, {});
  res.json({ id: req.params.id, is_banned: !!banned });
});

router.delete("/users/:id", requireAdmin("super_admin"), (req, res) => {
  db.prepare("DELETE FROM users WHERE id = ?").run(req.params.id);
  audit(req.user.id, "delete_user", "user", req.params.id, {});
  res.json({ deleted: req.params.id });
});

/* ------------------------- المشرفون ------------------------- */
router.get("/admins", requireAdmin("admin"), (_req, res) => {
  const rows = db
    .prepare("SELECT * FROM users WHERE admin_role IS NOT NULL OR role IN ('admin','super_admin') ORDER BY created_at")
    .all();
  res.json({ items: rows.map(publicUser) });
});

router.post("/admins", requireAdmin("super_admin"), (req, res) => {
  const { email, full_name, password, admin_role } = req.body || {};
  if (!email) return res.status(422).json({ detail: "البريد مطلوب" });
  let user = db.prepare("SELECT * FROM users WHERE email = ?").get(String(email).toLowerCase());
  if (!user) {
    if (!password) return res.status(422).json({ detail: "كلمة المرور مطلوبة لحساب جديد" });
    const id = uid();
    db.prepare(
      "INSERT INTO users (id, full_name, email, password_hash, role, admin_role, kyc_status) VALUES (?,?,?,?,?,?,'verified')",
    ).run(id, full_name || email, String(email).toLowerCase(), bcrypt.hashSync(String(password), 10), "admin", admin_role || "reviewer");
    user = db.prepare("SELECT * FROM users WHERE id = ?").get(id);
  } else {
    db.prepare("UPDATE users SET role = 'admin', admin_role = ? WHERE id = ?").run(admin_role || "reviewer", user.id);
    user = db.prepare("SELECT * FROM users WHERE id = ?").get(user.id);
  }
  audit(req.user.id, "create_admin", "user", user.id, { admin_role });
  res.status(201).json(publicUser(user));
});

/* ------------------------- طلبات التحقق ------------------------- */
router.get("/kyc-requests", requireAdmin("reviewer"), (req, res) => {
  const status = req.query.status || "pending";
  const rows = db
    .prepare("SELECT * FROM kyc_submissions WHERE status = ? ORDER BY created_at ASC LIMIT 100")
    .all(status)
    .map((s) => ({ ...s, ai_report: json(s.ai_report, null), user: publicUser(db.prepare("SELECT * FROM users WHERE id = ?").get(s.user_id)) }));
  res.json({ items: rows, total: rows.length });
});

router.post("/kyc-requests/:id/approve", requireAdmin("moderator"), (req, res) => {
  const sub = db.prepare("SELECT * FROM kyc_submissions WHERE id = ?").get(req.params.id);
  if (!sub) return res.status(404).json({ detail: "الطلب غير موجود" });
  db.prepare("UPDATE kyc_submissions SET status = 'approved', reviewer_id = ?, reviewed_at = datetime('now') WHERE id = ?").run(req.user.id, sub.id);
  db.prepare("UPDATE users SET kyc_status = 'verified', trust_score = MAX(trust_score, 85) WHERE id = ?").run(sub.user_id);
  notify(sub.user_id, "تم توثيق حسابك", "يمكنك الآن نشر الإعلانات بثقة كاملة.", "kyc", "/dashboard");
  audit(req.user.id, "approve_kyc", "kyc", sub.id, {});
  res.json({ id: sub.id, status: "approved" });
});

router.post("/kyc-requests/:id/reject", requireAdmin("moderator"), (req, res) => {
  const sub = db.prepare("SELECT * FROM kyc_submissions WHERE id = ?").get(req.params.id);
  if (!sub) return res.status(404).json({ detail: "الطلب غير موجود" });
  const reason = req.body?.reason || "الوثائق غير واضحة";
  db.prepare("UPDATE kyc_submissions SET status = 'rejected', reject_reason = ?, reviewer_id = ?, reviewed_at = datetime('now') WHERE id = ?").run(reason, req.user.id, sub.id);
  db.prepare("UPDATE users SET kyc_status = 'rejected' WHERE id = ?").run(sub.user_id);
  notify(sub.user_id, "تم رفض طلب التحقق", reason, "kyc", "/verification");
  audit(req.user.id, "reject_kyc", "kyc", sub.id, { reason });
  res.json({ id: sub.id, status: "rejected", reason });
});

/* ------------------------- السجل والإعدادات ------------------------- */
router.get("/audit-logs", requireAdmin("admin"), (_req, res) => {
  const rows = db
    .prepare(
      `SELECT l.*, u.full_name AS admin_name FROM admin_audit_logs l
       LEFT JOIN users u ON u.id = l.admin_id ORDER BY l.created_at DESC LIMIT 200`,
    )
    .all()
    .map((r) => ({ ...r, meta: json(r.meta, {}) }));
  res.json({ items: rows });
});

router.get("/settings", requireAdmin("admin"), (_req, res) => {
  const rows = db.prepare("SELECT * FROM site_settings").all();
  res.json({ items: rows, map: Object.fromEntries(rows.map((r) => [r.key, r.value])) });
});

router.put("/settings", requireAdmin("super_admin"), (req, res) => {
  const entries = Object.entries(req.body || {});
  const stmt = db.prepare(
    "INSERT INTO site_settings (key, value, updated_at) VALUES (?,?,datetime('now')) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')",
  );
  for (const [k, v] of entries) stmt.run(k, String(v));
  audit(req.user.id, "update_settings", "settings", null, req.body || {});
  res.json({ updated: entries.length });
});
