import { Router } from "express";
import { db, uid } from "../db.js";
import { requireAuth } from "../auth.js";
import { upload, bucket, publicUrl } from "../upload.js";
import { ai } from "../ai.js";

export const router = Router();

const setStatus = (userId, status) =>
  db.prepare("UPDATE users SET kyc_status = ?, updated_at = datetime('now') WHERE id = ?").run(status, userId);

router.post("/start", requireAuth, (req, res) => {
  setStatus(req.user.id, "pending");
  db.prepare("INSERT INTO kyc_submissions (id, user_id, full_name, status) VALUES (?,?,?,?)").run(
    uid(),
    req.user.id,
    req.user.full_name,
    "pending",
  );
  res.json({ status: "pending" });
});

router.post(
  "/submit",
  requireAuth,
  bucket("kyc"),
  upload.fields([
    { name: "id_front", maxCount: 1 },
    { name: "id_back", maxCount: 1 },
    { name: "selfie", maxCount: 1 },
    { name: "document", maxCount: 1 },
  ]),
  async (req, res) => {
    const f = req.files || {};
    const pick = (k) => (f[k]?.[0] ? f[k][0] : null);
    const front = pick("id_front") || pick("document");
    const back = pick("id_back");
    const selfie = pick("selfie");

    const id = uid();
    db.prepare(
      `INSERT INTO kyc_submissions (id, user_id, full_name, national_id, id_front_url, id_back_url, selfie_url, status)
       VALUES (?,?,?,?,?,?,?, 'pending')`,
    ).run(
      id,
      req.user.id,
      req.body?.full_name || req.user.full_name,
      req.body?.national_id || null,
      front ? publicUrl(front.path) : null,
      back ? publicUrl(back.path) : null,
      selfie ? publicUrl(selfie.path) : null,
    );
    setStatus(req.user.id, "pending");

    // تحليل خفيف عبر نموذج الوثائق (لا يمنع الاستجابة عند فشله)
    if (front) {
      const result = await ai.matchDocuments(front.path, (back || front).path, "identity");
      if (result?.ok) {
        db.prepare("UPDATE kyc_submissions SET ai_score = ?, ai_report = ? WHERE id = ?").run(
          result.match_score ?? null,
          JSON.stringify(result),
          id,
        );
      }
    }

    db.prepare("INSERT INTO notifications (id, user_id, title, body, type) VALUES (?,?,?,?,?)").run(
      uid(),
      req.user.id,
      "تم استلام طلب التحقق",
      "سيقوم فريق المراجعة بالرد خلال وقت قصير.",
      "kyc",
    );
    res.status(201).json({ id, status: "pending" });
  },
);

router.get("/status", requireAuth, (req, res) => {
  const sub = db
    .prepare("SELECT * FROM kyc_submissions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1")
    .get(req.user.id);
  res.json({ kyc_status: req.user.kyc_status, submission: sub || null });
});
