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

router.post(
  "/:id/upload-documents",
  requireAuth,
  bucket("documents"),
  upload.fields([
    { name: "id_doc", maxCount: 1 },
    { name: "ownership_doc", maxCount: 1 },
    { name: "files", maxCount: 4 },
  ]),
  async (req, res) => {
    const { row, error } = owned(req.params.id, req.user);
    if (error) return res.status(error[0]).json({ detail: error[1] });

    const f = req.files || {};
    const list = f.files || [];
    const idDoc = f.id_doc?.[0] || list[0];
    const ownDoc = f.ownership_doc?.[0] || list[1] || idDoc;
    if (!idDoc) return res.status(422).json({ detail: "أرفق وثيقة الهوية ووثيقة الملكية" });

    for (const [type, file] of [["id_doc", idDoc], ["ownership_doc", ownDoc]]) {
      db.prepare("INSERT INTO listing_documents (id, listing_id, doc_type, url) VALUES (?,?,?,?)").run(
        uid(), row.id, type, publicUrl(file.path),
      );
    }
    db.prepare("UPDATE listings SET docs_status = 'processing' WHERE id = ?").run(row.id);

    const result = await ai.matchDocuments(idDoc.path, ownDoc.path, row.kind || row.category || "house");
    const ok = !!result?.ok;
    db.prepare(
      "UPDATE listings SET docs_status = ?, docs_match_score = ?, docs_report = ?, updated_at = datetime('now') WHERE id = ?",
    ).run(ok ? "done" : "failed", result?.match_score ?? null, JSON.stringify(result || {}), row.id);

    res.status(201).json({
      status: ok ? "done" : "failed",
      match_score: result?.match_score ?? null,
      passed: result?.passed ?? null,
      issues: result?.issues ?? [],
      report: result,
    });
  },
);

router.get("/:id/status", requireAuth, (req, res) => {
  const { row, error } = owned(req.params.id, req.user);
  if (error) return res.status(error[0]).json({ detail: error[1] });
  res.json({
    docs_status: row.docs_status,
    match_score: row.docs_match_score,
    report: json(row.docs_report, null),
    condition_status: row.condition_status,
  });
});
