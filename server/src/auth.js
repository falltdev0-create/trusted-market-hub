import jwt from "jsonwebtoken";
import { config } from "./config.js";
import { db } from "./db.js";

export const ADMIN_LEVEL = { reviewer: 1, moderator: 2, admin: 3, super_admin: 4 };

export function signToken(user) {
  return jwt.sign({ sub: user.id, email: user.email, role: user.role }, config.jwtSecret, {
    expiresIn: config.jwtExpiresIn,
  });
}

export function publicUser(u) {
  if (!u) return null;
  return {
    id: u.id,
    full_name: u.full_name,
    email: u.email,
    phone: u.phone,
    city: u.city,
    role: u.role,
    admin_role: u.admin_role,
    kyc_status: u.kyc_status,
    trust_score: u.trust_score,
    avatar_url: u.avatar_url,
    is_active: !!u.is_active,
    is_banned: !!u.is_banned,
    created_at: u.created_at,
  };
}

export function optionalAuth(req, _res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;
  if (token) {
    try {
      const payload = jwt.verify(token, config.jwtSecret);
      const user = db.prepare("SELECT * FROM users WHERE id = ?").get(payload.sub);
      if (user && !user.is_banned) req.user = user;
    } catch {
      /* ignore invalid token */
    }
  }
  next();
}

export function requireAuth(req, res, next) {
  if (!req.user) return res.status(401).json({ detail: "غير مصرح — سجّل الدخول أولاً" });
  next();
}

export function isAdmin(user) {
  return user?.role === "admin" || user?.role === "super_admin" || !!user?.admin_role;
}

export function adminLevel(user) {
  if (!user) return 0;
  if (user.role === "super_admin") return ADMIN_LEVEL.super_admin;
  return ADMIN_LEVEL[user.admin_role] || (user.role === "admin" ? ADMIN_LEVEL.admin : 0);
}

export function requireAdmin(minRole = "reviewer") {
  const min = ADMIN_LEVEL[minRole] || 1;
  return (req, res, next) => {
    if (!req.user) return res.status(401).json({ detail: "غير مصرح — سجّل الدخول أولاً" });
    if (adminLevel(req.user) < min)
      return res.status(403).json({ detail: "هذه العملية تتطلب صلاحيات أعلى" });
    next();
  };
}

export function audit(adminId, action, targetType, targetId, meta) {
  db.prepare(
    "INSERT INTO admin_audit_logs (id, admin_id, action, target_type, target_id, meta) VALUES (?,?,?,?,?,?)",
  ).run(crypto.randomUUID(), adminId, action, targetType || null, targetId || null, JSON.stringify(meta || {}));
}
