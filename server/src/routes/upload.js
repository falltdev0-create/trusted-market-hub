import { Router } from "express";
import { db, uid, json } from "../db.js";
import { requireAuth, isAdmin } from "../auth.js";
import { upload, bucket, publicUrl } from "../upload.js";
import { ai } from "../ai.js";

export const router = Router();

function owned(id, user) {
  const row = db.prepare("SELECT * FROM listings WHERE id = ?").get(id);
  if (!row) return { error: [404, "الإعلان غير موجود"] };
  if (row.owner_id !== user.id && !isAdmin(user)) return { error: [403, "لا تملك صلاحية هذا الإعلان"] };
  return { row };
}

/** رفع صور الإعلان + بدء تحليل الحالة بالخلفية */
router.post(
  "/listing/:id/images",
  requireAuth,
  bucket("listings"),
  upload.array("files", 12),
  async (req, res) => {
    const { row, error } = owned(req.params.id, req.user);
    if (error) return res.status(error[0]).json({ detail: error[1] });

    const files = req.files || [];
    if (!files.length) return res.status(422).json({ detail: "أرفق صورة واحدة على الأقل" });

    const start = db.prepare("SELECT COALESCE(MAX(sort_order),-1) m FROM listing_images WHERE listing_id = ?").get(row.id).m;
    files.forEach((f, i) => {
      db.prepare("INSERT INTO listing_images (id, listing_id, url, sort_order) VALUES (?,?,?,?)").run(
        uid(), row.id, publicUrl(f.path), start + 1 + i,
      );
    });
    db.prepare("UPDATE listings SET condition_status = 'processing', updated_at = datetime('now') WHERE id = ?").run(row.id);
    res.status(201).json({ uploaded: files.length, condition_status: "processing" });

    // معالجة غير متزامنة بنموذج خفيف
    const paths = files.map((f) => f.path);
    ai.assessCondition(paths, row.kind || row.category || "house")
      .then((r) => {
        if (r?.ok) {
          db.prepare(
            `UPDATE listings SET condition_status = 'done', condition_grade = ?, condition_score = ?,
             condition_report = ?, updated_at = datetime('now') WHERE id = ?`,
          ).run(r.grade || null, r.score ?? null, JSON.stringify(r), row.id);
        } else {
          db.prepare("UPDATE listings SET condition_status = 'failed', condition_report = ? WHERE id = ?").run(
            JSON.stringify(r || {}), row.id,
          );
        }
      })
      .catch(() => db.prepare("UPDATE listings SET condition_status = 'failed' WHERE id = ?").run(row.id));
  },
);

/** استعلام دوري عن نتيجة التقييم */
router.get("/listing/:id/condition-result", requireAuth, (req, res) => {
  const { row, error } = owned(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  const report = json(row.condition_report, null);
  const done = row.condition_status === "done";
  res.json({
    status: row.condition_status,
    ready: done,
    progress: done ? 100 : row.condition_status === "processing" ? 60 : row.condition_status === "failed" ? 100 : 0,
    grade: row.condition_grade,
    grade_ar: report?.grade_ar ?? null,
    score: row.condition_score,
    suggested_price: row.suggested_price,
    price_tier: row.price_tier,
    report,
  });
});

/** رفع صورة شخصية */
router.post("/avatar", requireAuth, bucket("avatars"), upload.single("file"), (req, res) => {
  if (!req.file) return res.status(422).json({ detail: "أرفق صورة" });
  const url = publicUrl(req.file.path);
  db.prepare("UPDATE users SET avatar_url = ? WHERE id = ?").run(url, req.user.id);
  res.json({ url });
});
