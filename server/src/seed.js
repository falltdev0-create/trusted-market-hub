/**
 * بيانات أولية — معاملاتي
 * node src/seed.js
 */
import bcrypt from "bcryptjs";
import { db, uid } from "./db.js";

const hash = (p) => bcrypt.hashSync(p, 10);

const upsertUser = (u) => {
  const existing = db.prepare("SELECT * FROM users WHERE email = ?").get(u.email);
  if (existing) {
    db.prepare(
      `UPDATE users SET full_name=?, password_hash=?, role=?, admin_role=?, kyc_status=?, trust_score=?, city=?, phone=?
       WHERE id=?`,
    ).run(u.full_name, hash(u.password), u.role, u.admin_role ?? null, u.kyc_status, u.trust_score, u.city, u.phone, existing.id);
    return existing.id;
  }
  const id = uid();
  db.prepare(
    `INSERT INTO users (id, full_name, email, phone, password_hash, role, admin_role, kyc_status, trust_score, city)
     VALUES (?,?,?,?,?,?,?,?,?,?)`,
  ).run(id, u.full_name, u.email, u.phone, hash(u.password), u.role, u.admin_role ?? null, u.kyc_status, u.trust_score, u.city);
  return id;
};

const superId = upsertUser({
  full_name: "المدير العام",
  email: "superadmin@moamalati.sd",
  phone: "0912000000",
  password: "Admin@123",
  role: "super_admin",
  admin_role: "super_admin",
  kyc_status: "verified",
  trust_score: 100,
  city: "الخرطوم",
});

upsertUser({
  full_name: "مشرف المحتوى",
  email: "admin@moamalati.sd",
  phone: "0912000001",
  password: "Admin@123",
  role: "admin",
  admin_role: "moderator",
  kyc_status: "verified",
  trust_score: 95,
  city: "الخرطوم",
});

const sellerId = upsertUser({
  full_name: "عثمان محمد",
  email: "seller@moamalati.sd",
  phone: "0912000002",
  password: "User@123",
  role: "both",
  kyc_status: "verified",
  trust_score: 88,
  city: "أم درمان",
});

const buyerId = upsertUser({
  full_name: "سارة إبراهيم",
  email: "buyer@moamalati.sd",
  phone: "0912000003",
  password: "User@123",
  role: "buyer",
  kyc_status: "pending",
  trust_score: 60,
  city: "بحري",
});

// طلب توثيق قيد المراجعة
if (!db.prepare("SELECT 1 FROM kyc_submissions WHERE user_id = ?").get(buyerId)) {
  db.prepare(
    `INSERT INTO kyc_submissions (id, user_id, full_name, national_id, status, ai_score, ai_report)
     VALUES (?,?,?,?,'pending',?,?)`,
  ).run(uid(), buyerId, "سارة إبراهيم", "199203456789", 72.5, JSON.stringify({ engine: "seed", checks: [] }));
}

const LISTINGS = [
  {
    kind: "house", category: "house", listing_type: "sale", title: "فيلا حديثة في الرياض — الخرطوم",
    description: "فيلا دورين بتشطيب فاخر، حديقة أمامية ومواقف سيارات.",
    city: "الخرطوم", district: "الرياض", price: 950000000, suggested_price: 900000000,
    area: 400, rooms: 6, bathrooms: 4, condition_score: 91, status: "published",
  },
  {
    kind: "house", category: "apartment", listing_type: "rent", title: "شقة مفروشة للإيجار — بحري",
    description: "شقة غرفتين مفروشة بالكامل، قريبة من الخدمات.",
    city: "بحري", district: "شمبات", price: 1200000, suggested_price: 1500000,
    area: 120, rooms: 2, bathrooms: 1, condition_score: 78, status: "published",
  },
  {
    kind: "car", category: "car", listing_type: "sale", title: "تويوتا كورولا 2018",
    description: "سيارة بحالة ممتازة، فحص كامل، ماشية 90 ألف كم.",
    city: "أم درمان", price: 22000000, suggested_price: 19000000,
    year: 2018, mileage: 90000, brand: "Toyota", model: "Corolla",
    condition_score: 84, status: "published",
  },
  {
    kind: "house", category: "land", listing_type: "sale", title: "قطعة أرض سكنية — الأزهري",
    description: "أرض 300م² مربعة، أوراق سليمة وجاهزة للبناء.",
    city: "الخرطوم", district: "الأزهري", price: 180000000, suggested_price: 175000000,
    area: 300, condition_score: 70, status: "pending_review",
  },
  {
    kind: "car", category: "car", listing_type: "sale", title: "هيونداي إلنترا 2020",
    description: "استخدام شخصي، بدون حوادث.",
    city: "الخرطوم", price: 34000000, suggested_price: 33000000,
    year: 2020, mileage: 55000, brand: "Hyundai", model: "Elantra",
    condition_score: 88, status: "pending_review",
  },
];

const tier = (price, suggested) => {
  const r = price / (suggested || price);
  return r <= 0.85 ? "cheap" : r >= 1.15 ? "expensive" : "medium";
};

for (const l of LISTINGS) {
  if (db.prepare("SELECT 1 FROM listings WHERE title = ?").get(l.title)) continue;
  const id = uid();
  db.prepare(
    `INSERT INTO listings (id, owner_id, kind, category, listing_type, title, description, city, district,
      price, suggested_price, price_tier, area, rooms, bathrooms, year, mileage, brand, model,
      condition_grade, condition_score, condition_status, condition_report, status, details)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'done',?,?,?)`,
  ).run(
    id, sellerId, l.kind, l.category, l.listing_type, l.title, l.description, l.city, l.district ?? null,
    l.price, l.suggested_price, tier(l.price, l.suggested_price),
    l.area ?? null, l.rooms ?? null, l.bathrooms ?? null, l.year ?? null, l.mileage ?? null,
    l.brand ?? null, l.model ?? null,
    l.condition_score >= 85 ? "excellent" : l.condition_score >= 70 ? "good" : "fair",
    l.condition_score,
    JSON.stringify({ engine: "seed", score: l.condition_score, notes: ["بيانات تجريبية"] }),
    l.status, JSON.stringify({}),
  );
  db.prepare("INSERT INTO listing_images (id, listing_id, url, sort_order) VALUES (?,?,?,0)").run(
    uid(), id, `https://picsum.photos/seed/${encodeURIComponent(l.title)}/1200/800`,
  );
}

// إشعارات
if (!db.prepare("SELECT 1 FROM notifications WHERE user_id = ?").get(sellerId)) {
  db.prepare("INSERT INTO notifications (id, user_id, title, body, type, link) VALUES (?,?,?,?,?,?)").run(
    uid(), sellerId, "مرحباً بك في معاملاتي", "أكمل توثيق حسابك لتحصل على شارة الثقة.", "info", "/dashboard",
  );
}

// إعدادات الموقع
const settings = {
  site_name: "معاملاتي",
  commission_percent: "2.5",
  allow_registration: "true",
  maintenance_mode: "false",
  contact_email: "support@moamalati.sd",
};
const st = db.prepare(
  "INSERT INTO site_settings (key, value) VALUES (?,?) ON CONFLICT(key) DO NOTHING",
);
for (const [k, v] of Object.entries(settings)) st.run(k, v);

db.prepare("INSERT INTO admin_audit_logs (id, admin_id, action, target_type, meta) VALUES (?,?,?,?,?)").run(
  uid(), superId, "seed_database", "system", JSON.stringify({ at: new Date().toISOString() }),
);

console.log("✅ تمت تهيئة قاعدة البيانات");
console.log("   سوبر أدمن : superadmin@moamalati.sd / Admin@123");
console.log("   مشرف      : admin@moamalati.sd / Admin@123");
console.log("   بائع      : seller@moamalati.sd / User@123");
console.log("   مشتري     : buyer@moamalati.sd / User@123");
