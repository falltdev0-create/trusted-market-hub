import { Router } from "express";
import { db } from "../db.js";
import { publicUser, requireAuth } from "../auth.js";

export const router = Router();

router.get("/me", requireAuth, (req, res) => {
  const uidv = req.user.id;
  const listings = db.prepare("SELECT COUNT(*) c FROM listings WHERE owner_id = ?").get(uidv).c;
  const conversations = db
    .prepare("SELECT COUNT(*) c FROM conversations WHERE buyer_id = ? OR seller_id = ?")
    .get(uidv, uidv).c;
  const views = db.prepare("SELECT COALESCE(SUM(views),0) v FROM listings WHERE owner_id = ?").get(uidv).v;
  const notifications = db
    .prepare("SELECT COUNT(*) c FROM notifications WHERE user_id = ? AND is_read = 0")
    .get(uidv).c;

  res.json({ ...publicUser(req.user), stats: { listings, conversations, views, notifications } });
});

router.patch("/me", requireAuth, (req, res) => {
  const { full_name, phone, city, avatar_url } = req.body || {};
  db.prepare(
    `UPDATE users SET full_name = COALESCE(?, full_name), phone = COALESCE(?, phone),
     city = COALESCE(?, city), avatar_url = COALESCE(?, avatar_url), updated_at = datetime('now')
     WHERE id = ?`,
  ).run(full_name ?? null, phone ?? null, city ?? null, avatar_url ?? null, req.user.id);
  res.json(publicUser(db.prepare("SELECT * FROM users WHERE id = ?").get(req.user.id)));
});
