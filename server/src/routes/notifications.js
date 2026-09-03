import { Router } from "express";
import { db } from "../db.js";
import { requireAuth } from "../auth.js";

export const router = Router();

router.get("/", requireAuth, (req, res) => {
  const items = db
    .prepare("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 100")
    .all(req.user.id)
    .map((n) => ({ ...n, is_read: !!n.is_read }));
  res.json({ items, total: items.length });
});

router.get("/unread-count", requireAuth, (req, res) => {
  const count = db
    .prepare("SELECT COUNT(*) c FROM notifications WHERE user_id = ? AND is_read = 0")
    .get(req.user.id).c;
  res.json({ count, unread: count });
});

router.post("/:id/read", requireAuth, (req, res) => {
  db.prepare("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?").run(req.params.id, req.user.id);
  res.json({ ok: true });
});

router.post("/read-all", requireAuth, (req, res) => {
  db.prepare("UPDATE notifications SET is_read = 1 WHERE user_id = ?").run(req.user.id);
  res.json({ ok: true });
});

router.delete("/:id", requireAuth, (req, res) => {
  db.prepare("DELETE FROM notifications WHERE id = ? AND user_id = ?").run(req.params.id, req.user.id);
  res.json({ deleted: req.params.id });
});
