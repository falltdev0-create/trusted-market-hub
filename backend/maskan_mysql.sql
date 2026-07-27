-- ============================================================
--  معاملاتي — قاعدة البيانات الكاملة
--  MySQL 8.x / MariaDB 10.6+  (XAMPP compatible)
--  تشمل: حساب مشرف + مدير + مستخدم عادي
--  تشغيل: mysql -u root -p < maskan_complete.sql
-- ============================================================

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;

-- ── Database ──────────────────────────────────────────────────────────────────
DROP DATABASE IF EXISTS maskan;
CREATE DATABASE maskan
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE maskan;

-- ══════════════════════════════════════════════════════════════════════════════
-- 1. users
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE users (
    id                   CHAR(36)        NOT NULL,
    email                VARCHAR(255)    NOT NULL,
    phone                VARCHAR(20)     NOT NULL,
    password_hash        VARCHAR(255)    NOT NULL,
    full_name            VARCHAR(255)    NOT NULL,
    national_id          VARCHAR(50)     DEFAULT NULL,
    role                 ENUM('buyer','seller','both','admin','manager') NOT NULL DEFAULT 'both',
    is_verified          TINYINT(1)      NOT NULL DEFAULT 0,
    is_active            TINYINT(1)      NOT NULL DEFAULT 1,
    avatar_url           VARCHAR(500)    DEFAULT NULL,
    kyc_status           ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    kyc_doc_url          VARCHAR(500)    DEFAULT NULL,
    disclaimer_signed    TINYINT(1)      NOT NULL DEFAULT 0,
    disclaimer_signed_at DATETIME        DEFAULT NULL,
    created_at           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email       (email),
    UNIQUE KEY uq_users_phone       (phone),
    UNIQUE KEY uq_users_national_id (national_id),
    KEY        ix_users_email       (email),
    KEY        ix_users_role        (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ══════════════════════════════════════════════════════════════════════════════
-- 2. listings
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE listings (
    id               CHAR(36)        NOT NULL,
    seller_id        CHAR(36)        NOT NULL,
    category         ENUM('house','car') NOT NULL,
    listing_type     ENUM('sale','rent')  NOT NULL,
    title            VARCHAR(255)    NOT NULL,
    description      TEXT            DEFAULT NULL,
    status           ENUM(
                         'draft',
                         'images_uploaded',
                         'condition_assessed',
                         'docs_uploaded',
                         'docs_verified',
                         'price_set',
                         'pending_review',
                         'published',
                         'rejected',
                         'sold'
                     ) NOT NULL DEFAULT 'draft',
    city             VARCHAR(100)    DEFAULT NULL,
    district         VARCHAR(100)    DEFAULT NULL,
    price            DOUBLE          DEFAULT NULL,
    price_max_limit  DOUBLE          DEFAULT NULL,
    currency         VARCHAR(10)     NOT NULL DEFAULT 'SDG',
    condition_grade  ENUM('excellent','good','poor') DEFAULT NULL,
    condition_score  DOUBLE          DEFAULT NULL,
    condition_report JSON            DEFAULT NULL,
    details          JSON            DEFAULT NULL,
    view_count       INT             NOT NULL DEFAULT 0,
    published_at     DATETIME        DEFAULT NULL,
    rejected_reason  TEXT            DEFAULT NULL,
    created_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY ix_listing_status           (status),
    KEY ix_listing_cat_type_status  (category, listing_type, status),
    KEY ix_listing_city_status      (city, status),
    KEY ix_listing_seller           (seller_id),

    CONSTRAINT fk_listings_seller
        FOREIGN KEY (seller_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ══════════════════════════════════════════════════════════════════════════════
-- 3. listing_images
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE listing_images (
    id         CHAR(36)     NOT NULL,
    listing_id CHAR(36)     NOT NULL,
    url        VARCHAR(500) NOT NULL,
    image_type VARCHAR(50)  NOT NULL DEFAULT 'item',
    `order`    INT          NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY ix_listing_images_listing (listing_id),

    CONSTRAINT fk_listing_images_listing
        FOREIGN KEY (listing_id) REFERENCES listings(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ══════════════════════════════════════════════════════════════════════════════
-- 4. listing_verifications
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE listing_verifications (
    id                CHAR(36)    NOT NULL,
    listing_id        CHAR(36)    NOT NULL,
    owner_id_doc_url  VARCHAR(500) DEFAULT NULL,
    ownership_doc_url VARCHAR(500) DEFAULT NULL,
    match_score       DOUBLE       DEFAULT NULL,
    match_status      ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    match_details     JSON         DEFAULT NULL,
    rejection_reason  TEXT         DEFAULT NULL,
    reviewed_by       CHAR(36)     DEFAULT NULL,
    reviewed_at       DATETIME     DEFAULT NULL,
    verified_at       DATETIME     DEFAULT NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_verif_listing (listing_id),

    CONSTRAINT fk_verif_listing
        FOREIGN KEY (listing_id) REFERENCES listings(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ══════════════════════════════════════════════════════════════════════════════
-- 5. conversations
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE conversations (
    id                   CHAR(36)   NOT NULL,
    listing_id           CHAR(36)   NOT NULL,
    buyer_id             CHAR(36)   NOT NULL,
    seller_id            CHAR(36)   NOT NULL,
    disclaimer_signed    TINYINT(1) NOT NULL DEFAULT 0,
    disclaimer_signed_at DATETIME   DEFAULT NULL,
    created_at           DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_conv_listing_buyer (listing_id, buyer_id),
    KEY ix_conv_buyer  (buyer_id),
    KEY ix_conv_seller (seller_id),

    CONSTRAINT fk_conv_listing
        FOREIGN KEY (listing_id) REFERENCES listings(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_conv_buyer
        FOREIGN KEY (buyer_id)  REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_conv_seller
        FOREIGN KEY (seller_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ══════════════════════════════════════════════════════════════════════════════
-- 6. messages
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE messages (
    id              CHAR(36)   NOT NULL,
    conversation_id CHAR(36)   NOT NULL,
    sender_id       CHAR(36)   NOT NULL,
    content         TEXT       NOT NULL,
    was_filtered    TINYINT(1) NOT NULL DEFAULT 0,
    is_read         TINYINT(1) NOT NULL DEFAULT 0,
    created_at      DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY ix_msg_conversation (conversation_id),
    KEY ix_msg_sender       (sender_id),

    CONSTRAINT fk_msg_conversation
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_msg_sender
        FOREIGN KEY (sender_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ══════════════════════════════════════════════════════════════════════════════
-- 7. notifications
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE notifications (
    id         CHAR(36)     NOT NULL,
    user_id    CHAR(36)     NOT NULL,
    type       VARCHAR(50)  NOT NULL,
    title      VARCHAR(255) NOT NULL,
    body       TEXT         DEFAULT NULL,
    is_read    TINYINT(1)   NOT NULL DEFAULT 0,
    payload    JSON         DEFAULT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY ix_notif_user    (user_id),
    KEY ix_notif_is_read (user_id, is_read),

    CONSTRAINT fk_notif_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ══════════════════════════════════════════════════════════════════════════════
-- 8. password_reset_tokens  (جديد — لدعم تغيير كلمة المرور في الإعدادات)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE password_reset_tokens (
    id         CHAR(36)     NOT NULL,
    user_id    CHAR(36)     NOT NULL,
    token      VARCHAR(255) NOT NULL,
    expires_at DATETIME     NOT NULL,
    used       TINYINT(1)   NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_reset_token (token),
    KEY ix_reset_user (user_id),

    CONSTRAINT fk_reset_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ══════════════════════════════════════════════════════════════════════════════
-- 9. Seed Data — ثلاثة حسابات: مشرف + مدير + مستخدم عادي
-- ══════════════════════════════════════════════════════════════════════════════

-- ── حساب المشرف الأعلى (Super Admin) ─────────────────────────────────────────
-- البريد:  admin@maskan.app
-- كلمة المرور: Admin@1234
INSERT INTO users (
    id, email, phone, password_hash, full_name,
    role, is_verified, is_active, kyc_status,
    disclaimer_signed, created_at, updated_at
) VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'admin@maskan.app',
    '0900000001',
    '$2b$12$amqL3uGO/OdPz67JJ7Y2SOQTqfRUHexwVShdXQlpPdFagVNOOJPZW',
    'مشرف النظام',
    'admin',
    1,
    1,
    'approved',
    1,
    NOW(),
    NOW()
);

-- ── حساب المدير (Manager) ─────────────────────────────────────────────────────
-- البريد:  manager@maskan.app
-- كلمة المرور: Manager@1234
INSERT INTO users (
    id, email, phone, password_hash, full_name,
    role, is_verified, is_active, kyc_status,
    disclaimer_signed, created_at, updated_at
) VALUES (
    'b0000000-0000-0000-0000-000000000002',
    'manager@maskan.app',
    '0900000002',
    '$2b$12$aVzmYhFfX3i551Qb2M5JUOxpxom3KWG55Oe7LQrTRbM0VI3JJm.wy',
    'مدير المنصة',
    'manager',
    1,
    1,
    'approved',
    1,
    NOW(),
    NOW()
);

-- ── حساب مستخدم عادي (تجريبي) ────────────────────────────────────────────────
-- البريد:  user@maskan.app
-- كلمة المرور: User@1234
INSERT INTO users (
    id, email, phone, password_hash, full_name,
    role, is_verified, is_active, kyc_status,
    disclaimer_signed, created_at, updated_at
) VALUES (
    'c0000000-0000-0000-0000-000000000003',
    'user@maskan.app',
    '0900000003',
    '$2b$12$jDnuCMS2fE03qhWfAKAUxuK.gl06..SHZNKS19rwe50Q.J.0KJS62',
    'أحمد محمد علي',
    'both',
    0,
    1,
    'pending',
    0,
    NOW(),
    NOW()
);

-- ── إشعار ترحيبي للمستخدم العادي ────────────────────────────────────────────
INSERT INTO notifications (
    id, user_id, type, title, body, is_read, created_at
) VALUES (
    'n0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000003',
    'info',
    'مرحباً بك في معاملاتي',
    'أكمل توثيق هويتك للبدء في نشر الإعلانات.',
    0,
    NOW()
);


SET foreign_key_checks = 1;

-- ══════════════════════════════════════════════════════════════════════════════
-- ملخص الحسابات:
--
--  المشرف:  admin@maskan.app    / Admin@1234    (role: admin)
--  المدير:  manager@maskan.app  / Manager@1234  (role: manager)
--  المستخدم: user@maskan.app    / User@1234     (role: both)
--
-- الجداول: users · listings · listing_images · listing_verifications
--          conversations · messages · notifications · password_reset_tokens
-- ══════════════════════════════════════════════════════════════════════════════
