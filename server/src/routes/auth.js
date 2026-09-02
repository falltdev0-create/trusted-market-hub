import { Router } from "express";
import bcrypt from "bcryptjs";
import { db, uid } from "../db.js";
import { signToken, publicUser, requireAuth } from "../auth.js";

export const router = Router();

router.post("/register", (req, res) => {
  const { full_name, email, phone, password, national_id, city, role } = req.body || {};
  if (!full_name || !email || !password)
    return res.status(422).json({ detail: "الاسم والبريد وكلمة المرور مطلوبة" });

  const exists = db.prepare("SELECT id FROM users WHERE email = ?").get(String(email).toLowerCase());
  if (exists) return res.status(409).json({ detail: "البريد الإلكتروني مسجّل مسبقاً" });

  const id = uid();
  db.prepare(
    `INSERT INTO users (id, full_name, email, phone, national_id, password_hash, role, city)
     VALUES (?,?,?,?,?,?,?,?)`,
  ).run(
    id,
    full_name,
    String(email).toLowerCase(),
    phone || null,
    national_id || null,
    bcrypt.hashSync(String(password), 10),
    role || "both",
    city || null,
  );
  const user = db.prepare("SELECT * FROM users WHERE id = ?").get(id);
  db.prepare("INSERT INTO notifications (id, user_id, title, body, type) VALUES (?,?,?,?,?)").run(
    uid(),
    id,
    "مرحباً بك في معاملاتي",
    "أكمل التحقق من هويتك لتتمكن من نشر إعلاناتك.",
    "info",
  );
  res.status(201).json({ access_token: signToken(user), token_type: "bearer", user: publicUser(user) });
});

router.post("/login", (req, res) => {
  const email = (req.body?.email || req.body?.username || "").toLowerCase();
  const password = req.body?.password;
  if (!email || !password) return res.status(422).json({ detail: "البريد وكلمة المرور مطلوبة" });

  const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email);
  if (!user || !bcrypt.compareSync(String(password), user.password_hash))
    return res.status(401).json({ detail: "بيانات الدخول غير صحيحة" });
  if (user.is_banned) return res.status(403).json({ detail: "تم حظر هذا الحساب" });

  res.json({ access_token: signToken(user), token_type: "bearer", user: publicUser(user) });
});

router.get("/me", requireAuth, (req, res) => res.json(publicUser(req.user)));
