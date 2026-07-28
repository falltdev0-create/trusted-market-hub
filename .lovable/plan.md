# خطة إكمال منصة معاملاتي

المشروع كبير ومتشعب، سأنفذه على 5 محاور متوازية. أرجو الموافقة قبل البدء لأن التغييرات واسعة على الـ backend وقاعدة البيانات والواجهة.

## 1) قاعدة البيانات — ملف SQL شامل
إعادة كتابة `backend/maskan_mysql.sql` ليشمل كل الجداول المستخدمة فعلياً في الكود + جداول المشرفين الهرمية:

**جداول المستخدمين والتحقق**
- `users` (id, full_name, email, phone, password_hash, kyc_status, created_at, updated_at)
- `kyc_submissions` (id, user_id, id_front_url, id_back_url, selfie_url, status, reviewed_by, reviewed_at, rejection_reason)

**جداول الإعلانات**
- `listings` (id, seller_id, category, listing_type, title, description, details_json, condition_grade, condition_score, price, price_tier ENUM('cheap','medium','expensive'), status, views_count, created_at, published_at)
- `listing_images` (id, listing_id, url, order_index, ai_analyzed)
- `listing_documents` (id, listing_id, type, url, verification_status, match_score)
- `condition_reports` (id, listing_id, grade, score, report_json, model_version, created_at)
- `price_estimates` (id, listing_id, suggested_min, suggested_max, market_avg, tier, model_version)

**جداول المحادثات**
- `conversations` (id, listing_id, buyer_id, seller_id, last_message_at)
- `messages` (id, conversation_id, sender_id, content, filtered_content, is_flagged, created_at)

**جداول الإشعارات**
- `notifications` (id, user_id, type, title, body, link, is_read, created_at)

**جداول المشرفين الهرمية (جديد)**
- `admin_roles` ENUM('super_admin','admin','moderator','reviewer')
- `admins` (id, user_id, role, created_by, permissions_json, is_active, created_at)
- `admin_actions_log` (id, admin_id, action_type, target_type, target_id, details_json, created_at)
- `admin_permissions` (role, permission_key) — للتحكم الدقيق

**جداول عامة**
- `categories`, `system_settings`, `reports` (بلاغات المستخدمين)
- بيانات seed: super_admin افتراضي + التصنيفات

## 2) Backend — إكمال الربط
- توحيد `app/services/ai_service.py` مع النماذج في `ai_models/` (ConditionPredictor / DocumentMatcher / PricingPredictor) بدل نداءات HuggingFace pipeline المباشرة المكسورة (`vision2seq-lm` غير صالح).
- إصلاح `upload.py` ليخزّن `condition_reports` ويُرجع نتيجة polling صحيحة.
- إضافة endpoint `/listings/{id}/price-estimate` يُرجع نطاق (min/max/tier) بدون فرض سعر.
- إعادة كتابة `admin.py` بالكامل مع:
  - `/admin/dashboard-stats` (users, listings, pending, revenue)
  - `/admin/users` + `/admin/users/{id}/kyc-review`
  - `/admin/listings/pending` + approve/reject
  - `/admin/admins` (super_admin فقط: إنشاء/تعديل صلاحيات)
  - `/admin/actions-log`
  - `/admin/reports` (بلاغات)
  - middleware للتحقق من الدور الهرمي
- إصلاح `verification.py` و `kyc.py` لحفظ حقيقي في DB.
- ربط `notifications` بأحداث النظام (approve/reject/new message).

## 3) نماذج الذكاء الاصطناعي — HuggingFace
- `ai_models/condition_model/predictor.py`: استخدام `microsoft/resnet-50` مع mapping ذكي لدرجات الحالة.
- `ai_models/document_model/predictor.py`: `microsoft/trocr-large-handwritten` لاستخراج نص + مقارنة fuzzy.
- `ai_models/pricing_model/predictor.py`: نموذج تصنيف tier (cheap/medium/expensive) بناء على category+condition+details بدل رقم قاطع. يُرجع range + tier.
- تنزيل تلقائي عند أول استخدام + caching.
- ملف `requirements.txt` محدّث.

## 4) تصنيف السعر (تغيير جوهري)
- إزالة `PRICE_CAPS` من الإعدادات كقيد إجباري.
- Backend يحفظ `price` (من البائع بحرية) + `price_tier` محسوب من AI.
- في الواجهة:
  - `sell.set-price` → إدخال حر بدون max، مع عرض النطاق المقترح إرشادياً + التصنيف المتوقع.
  - `ListingCard` و `marketplace` و `listing.$id` → عرض شارة ملونة (رخيص أخضر / متوسط أزرق / غالي أحمر) بجانب السعر.
  - فلتر جديد في `marketplace` حسب التصنيف السعري.

## 5) واجهة المستخدم — إصلاحات وإكمال
- لوحة مشرف جديدة `/admin` بتبويبات هرمية (نظرة عامة، مستخدمين، إعلانات، KYC، مشرفون، سجل الإجراءات، بلاغات، إعدادات).
- صفحة `/admin/admins` (super_admin فقط) لإدارة المشرفين وصلاحياتهم.
- إصلاح جميع الأزرار المعطلة + حالات loading/empty/error موحّدة.
- شارة `PriceTierBadge` جديدة.
- تأكد من عمل كل مسار fetch مع fallback ذكي.

## ملفات ستُنشأ/تُعدَّل (تقريباً 25 ملف)
```text
backend/maskan_mysql.sql                    (إعادة كتابة كاملة)
backend/app/models/models.py                (إضافة جداول admin + price_tier)
backend/app/api/routes/admin.py             (إعادة كتابة)
backend/app/api/routes/upload.py            (polling + condition_reports)
backend/app/api/routes/listings.py          (price-estimate endpoint)
backend/app/api/routes/kyc.py               (حفظ حقيقي)
backend/app/api/routes/verification.py
backend/app/api/routes/notifications.py     (أحداث تلقائية)
backend/app/services/ai_service.py          (توحيد مع ai_models/)
backend/app/core/security.py                (admin role guards)
backend/create_admin.py                     (super_admin seeder)
ai_models/condition_model/predictor.py
ai_models/document_model/predictor.py
ai_models/pricing_model/predictor.py        (tier classifier)
ai_models/requirements.txt
src/lib/api.ts                              (adminApi + priceApi)
src/components/PriceTierBadge.tsx           (جديد)
src/components/ListingCard.tsx              (شارة tier)
src/routes/marketplace.tsx                  (فلتر tier)
src/routes/listing.$id.tsx                  (شارة tier)
src/routes/sell.set-price.tsx               (بدون سقف)
src/routes/admin.tsx                        (تبويبات هرمية)
src/routes/admin.admins.tsx                 (جديد)
src/routes/admin.users.tsx                  (جديد)
src/routes/admin.logs.tsx                   (جديد)
```

## ملاحظات مهمة
- الـ backend يعمل على جهازك (`localhost:8000`) — لن أستطيع تشغيله لاختباره من المعاينة، لكن الكود سيكون متكاملاً وقابلاً للتشغيل مباشرة عندك.
- ستحتاج بعد التطبيق:
  1. `mysql < backend/maskan_mysql.sql`
  2. `pip install -r ai_models/requirements.txt`
  3. `python backend/create_admin.py` لإنشاء أول super_admin
  4. أول تشغيل سيحمّل نماذج HuggingFace (~500MB)

هل أبدأ التنفيذ؟ أم تريد تعديل نطاق معين أولاً (مثلاً تأجيل النماذج، أو تبسيط لوحة المشرفين)؟
