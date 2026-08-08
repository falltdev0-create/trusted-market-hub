-- =============================================================================
-- معاملاتي (Mo'amalati) — Complete MySQL Schema (aligned with SQLAlchemy models)
-- =============================================================================
-- Usage (Windows / XAMPP / MySQL 8+):
--   mysql -u root -p < backend/maskan_mysql.sql
-- =============================================================================

DROP DATABASE IF EXISTS maskandaba;
CREATE DATABASE maskandaba CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE maskandaba;

SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================================
-- USERS
-- =============================================================================
CREATE TABLE users (
    id                    VARCHAR(36) PRIMARY KEY,
    email                 VARCHAR(255) NOT NULL UNIQUE,
    phone                 VARCHAR(20)  NOT NULL UNIQUE,
    password_hash         VARCHAR(255) NOT NULL,
    full_name             VARCHAR(255) NOT NULL,
    national_id           VARCHAR(50)  NULL UNIQUE,
    role                  ENUM('buyer','seller','both','admin','super_admin') NOT NULL DEFAULT 'both',
    is_verified           TINYINT(1) NOT NULL DEFAULT 0,
    is_active             TINYINT(1) NOT NULL DEFAULT 1,
    avatar_url            VARCHAR(500) NULL,
    kyc_status            ENUM('unverified','pending','verified','rejected') NOT NULL DEFAULT 'unverified',
    selfie_url            VARCHAR(500) NULL,
    kyc_doc_url           VARCHAR(500) NULL,
    disclaimer_signed     TINYINT(1) NOT NULL DEFAULT 0,
    disclaimer_signed_at  DATETIME NULL,
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_kyc   (kyc_status)
) ENGINE=InnoDB;

-- =============================================================================
-- KYC SUBMISSIONS
-- =============================================================================
CREATE TABLE kyc_submissions (
    id                CHAR(36) PRIMARY KEY,
    user_id           VARCHAR(36) NOT NULL,
    id_front_url      VARCHAR(500) NOT NULL,
    id_back_url       VARCHAR(500) NULL,
    selfie_url        VARCHAR(500) NULL,
    national_id       VARCHAR(64)  NULL,
    status            ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    match_score       DECIMAL(5,4) NULL,
    ai_report_json    JSON NULL,
    reviewed_by       VARCHAR(36) NULL,
    reviewed_at       DATETIME NULL,
    rejection_reason  TEXT NULL,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_kyc_status (status),
    INDEX idx_kyc_user   (user_id)
) ENGINE=InnoDB;

-- =============================================================================
-- ADMIN HIERARCHY
-- =============================================================================
CREATE TABLE admins (
    id              CHAR(36) PRIMARY KEY,
    user_id         VARCHAR(36) NOT NULL UNIQUE,
    role            ENUM('super_admin','admin','moderator','reviewer') NOT NULL DEFAULT 'reviewer',
    permissions     JSON NULL,
    created_by      CHAR(36) NULL,
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)    REFERENCES users(id)  ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_admin_role (role)
) ENGINE=InnoDB;

CREATE TABLE admin_permissions (
    role            ENUM('super_admin','admin','moderator','reviewer') NOT NULL,
    permission_key  VARCHAR(64) NOT NULL,
    PRIMARY KEY (role, permission_key)
) ENGINE=InnoDB;

CREATE TABLE admin_actions_log (
    id              CHAR(36) PRIMARY KEY,
    admin_id        CHAR(36) NOT NULL,
    action_type     VARCHAR(64)  NOT NULL,
    target_type     VARCHAR(32)  NULL,
    target_id       CHAR(36)     NULL,
    details         JSON NULL,
    ip_address      VARCHAR(45)  NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE,
    INDEX idx_log_admin (admin_id),
    INDEX idx_log_type  (action_type),
    INDEX idx_log_date  (created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- CATEGORIES
-- =============================================================================
CREATE TABLE categories (
    id              CHAR(36) PRIMARY KEY,
    slug            VARCHAR(64)  NOT NULL UNIQUE,
    name_ar         VARCHAR(120) NOT NULL,
    name_en         VARCHAR(120) NULL,
    icon            VARCHAR(64)  NULL,
    parent_id       CHAR(36) NULL,
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    sort_order      INT NOT NULL DEFAULT 0,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =============================================================================
-- LISTINGS  (columns match SQLAlchemy models.Listing exactly)
-- =============================================================================
CREATE TABLE listings (
    id                VARCHAR(36) PRIMARY KEY,
    seller_id         VARCHAR(36) NOT NULL,
    category          ENUM('house','car') NOT NULL,
    listing_type      ENUM('sale','rent') NOT NULL,
    title             VARCHAR(255) NOT NULL,
    description       TEXT NULL,
    status            ENUM(
        'draft','images_uploaded','condition_assessed',
        'docs_uploaded','docs_verified','price_set',
        'pending_review','published','rejected','sold'
    ) NOT NULL DEFAULT 'draft',
    city              VARCHAR(100) NULL,
    district          VARCHAR(100) NULL,
    price             DOUBLE NULL,
    price_max_limit   DOUBLE NULL,
    price_tier        ENUM('cheap','medium','expensive') NULL,
    suggested_min     DOUBLE NULL,
    suggested_max     DOUBLE NULL,
    currency          VARCHAR(10) NOT NULL DEFAULT 'SDG',
    condition_grade   ENUM('excellent','good','poor') NULL,
    condition_score   DOUBLE NULL,
    condition_report  JSON NULL,
    details           JSON NULL,
    view_count        INT NOT NULL DEFAULT 0,
    published_at      DATETIME NULL,
    rejected_reason   TEXT NULL,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX ix_listing_cat_type_status (category, listing_type, status),
    INDEX ix_listing_city_status      (city, status),
    INDEX ix_listing_tier             (price_tier),
    INDEX ix_listing_status           (status),
    INDEX ix_listing_seller           (seller_id)
) ENGINE=InnoDB;

CREATE TABLE listing_images (
    id           VARCHAR(36) PRIMARY KEY,
    listing_id   VARCHAR(36) NOT NULL,
    url          VARCHAR(500) NOT NULL,
    image_type   VARCHAR(50) NOT NULL DEFAULT 'item',
    `order`      INT NOT NULL DEFAULT 0,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX ix_img_listing (listing_id)
) ENGINE=InnoDB;

CREATE TABLE listing_documents (
    id                    CHAR(36) PRIMARY KEY,
    listing_id            VARCHAR(36) NOT NULL,
    doc_type              ENUM('ownership','id','contract','other') NOT NULL DEFAULT 'ownership',
    url                   VARCHAR(500) NOT NULL,
    extracted_text        TEXT NULL,
    verification_status   ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    match_score           DECIMAL(5,4) NULL,
    ai_report_json        JSON NULL,
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX ix_doc_listing (listing_id)
) ENGINE=InnoDB;

CREATE TABLE listing_verifications (
    id                VARCHAR(36) PRIMARY KEY,
    listing_id        VARCHAR(36) NOT NULL UNIQUE,
    owner_id_doc_url  VARCHAR(500) NULL,
    ownership_doc_url VARCHAR(500) NULL,
    match_score       DOUBLE NULL,
    match_status      ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    match_details     JSON NULL,
    rejection_reason  TEXT NULL,
    reviewed_by       VARCHAR(36) NULL,
    reviewed_at       DATETIME NULL,
    verified_at       DATETIME NULL,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE condition_reports (
    id              CHAR(36) PRIMARY KEY,
    listing_id      VARCHAR(36) NOT NULL,
    grade           ENUM('excellent','good','poor') NOT NULL,
    score           DECIMAL(5,2) NOT NULL,
    report          JSON NOT NULL,
    model_version   VARCHAR(64) NULL,
    processing_ms   INT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX ix_cond_listing (listing_id)
) ENGINE=InnoDB;

CREATE TABLE price_estimates (
    id              CHAR(36) PRIMARY KEY,
    listing_id      VARCHAR(36) NOT NULL,
    suggested_min   BIGINT NOT NULL,
    suggested_max   BIGINT NOT NULL,
    market_avg      BIGINT NULL,
    tier            ENUM('cheap','medium','expensive') NOT NULL,
    confidence      DECIMAL(5,4) NULL,
    model_version   VARCHAR(64) NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX ix_price_listing (listing_id)
) ENGINE=InnoDB;

-- =============================================================================
-- CHAT
-- =============================================================================
CREATE TABLE conversations (
    id                    VARCHAR(36) PRIMARY KEY,
    listing_id            VARCHAR(36) NOT NULL,
    buyer_id              VARCHAR(36) NOT NULL,
    seller_id             VARCHAR(36) NOT NULL,
    disclaimer_signed     TINYINT(1) NOT NULL DEFAULT 0,
    disclaimer_signed_at  DATETIME NULL,
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id)   REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (seller_id)  REFERENCES users(id)    ON DELETE CASCADE,
    UNIQUE KEY uq_conv (listing_id, buyer_id, seller_id),
    INDEX ix_conv_buyer  (buyer_id),
    INDEX ix_conv_seller (seller_id)
) ENGINE=InnoDB;

CREATE TABLE messages (
    id                VARCHAR(36) PRIMARY KEY,
    conversation_id   VARCHAR(36) NOT NULL,
    sender_id         VARCHAR(36) NOT NULL,
    content           TEXT NOT NULL,
    was_filtered      TINYINT(1) NOT NULL DEFAULT 0,
    is_read           TINYINT(1) NOT NULL DEFAULT 0,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id)       REFERENCES users(id)         ON DELETE CASCADE,
    INDEX ix_msg_conv (conversation_id, created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- NOTIFICATIONS
-- =============================================================================
CREATE TABLE notifications (
    id          VARCHAR(36) PRIMARY KEY,
    user_id     VARCHAR(36) NOT NULL,
    type        VARCHAR(50)  NOT NULL,
    title       VARCHAR(255) NOT NULL,
    body        TEXT NULL,
    is_read     TINYINT(1) NOT NULL DEFAULT 0,
    payload     JSON NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX ix_notif_user    (user_id, is_read),
    INDEX ix_notif_created (created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- REPORTS
-- =============================================================================
CREATE TABLE reports (
    id              CHAR(36) PRIMARY KEY,
    reporter_id     VARCHAR(36) NOT NULL,
    target_type     ENUM('listing','user','message') NOT NULL,
    target_id       CHAR(36) NOT NULL,
    reason          VARCHAR(120) NOT NULL,
    details         TEXT NULL,
    status          ENUM('open','reviewing','resolved','dismissed') NOT NULL DEFAULT 'open',
    resolved_by     VARCHAR(36) NULL,
    resolved_at     DATETIME NULL,
    resolution_note TEXT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX ix_reports_status (status),
    INDEX ix_reports_target (target_type, target_id)
) ENGINE=InnoDB;

-- =============================================================================
-- SYSTEM SETTINGS
-- =============================================================================
CREATE TABLE system_settings (
    setting_key   VARCHAR(120) PRIMARY KEY,
    setting_value JSON NOT NULL,
    description   TEXT NULL,
    updated_by    VARCHAR(36) NULL,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =============================================================================
-- SEED DATA
-- =============================================================================

INSERT INTO categories (id, slug, name_ar, name_en, icon, sort_order) VALUES
  (UUID(), 'house', 'عقارات', 'Real Estate', 'home', 1),
  (UUID(), 'car',   'سيارات', 'Cars',        'car',  2);

INSERT INTO admin_permissions (role, permission_key) VALUES
  ('super_admin','*'),
  ('admin','listings.review'), ('admin','listings.approve'), ('admin','listings.reject'),
  ('admin','users.view'), ('admin','users.suspend'), ('admin','kyc.review'),
  ('admin','reports.handle'), ('admin','settings.view'), ('admin','moderators.manage'),
  ('moderator','listings.review'), ('moderator','listings.approve'), ('moderator','listings.reject'),
  ('moderator','kyc.review'), ('moderator','reports.handle'), ('moderator','users.view'),
  ('reviewer','listings.review'), ('reviewer','kyc.review'), ('reviewer','users.view');

-- Default super admin
--   email:    admin@moamalati.local
--   password: Admin@12345
-- bcrypt hash (rounds=12) for "Admin@12345"
INSERT INTO users (id, full_name, email, phone, password_hash, role, is_verified, is_active, kyc_status)
VALUES (
  'a0000000-0000-0000-0000-000000000001',
  'Super Admin',
  'admin@moamalati.local',
  '000000000',
  '$2b$12$lrXwXVzguO5pUrCHReoKR.dGxRZiU2h8ABoJisGMhssKS6d1NwTMS',
  'super_admin', 1, 1, 'verified'
);
INSERT INTO admins (id, user_id, role, is_active)
VALUES (
  'ad000000-0000-0000-0000-000000000001',
  'a0000000-0000-0000-0000-000000000001',
  'super_admin', 1
);

INSERT INTO system_settings (setting_key, setting_value, description) VALUES
  ('price_tiers', JSON_OBJECT(
      'house', JSON_OBJECT('cheap', 2000000, 'medium', 5000000),
      'car',   JSON_OBJECT('cheap',  800000, 'medium', 2000000)
    ), 'Thresholds for cheap/medium/expensive tiers (SDG). >medium = expensive.'),
  ('site_name',    JSON_QUOTE('معاملاتي'),   'Public site name'),
  ('kyc_required', CAST('true' AS JSON),      'Require KYC before publishing listings'),
  ('max_images',   CAST('10' AS JSON),        'Max images per listing');

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- Optional: after running this file, you can reset/create a super_admin with:
--   python backend/create_admin.py --email admin@moamalati.local --password 'Admin@12345'
-- (the seeded bcrypt hash above is a placeholder; the script updates it).
-- =============================================================================

-- ── RAG documents (local embeddings store) ───────────────────────────────
CREATE TABLE IF NOT EXISTS rag_documents (
  id          CHAR(36)     NOT NULL PRIMARY KEY,
  source      VARCHAR(50)  NOT NULL,
  source_id   VARCHAR(64)  NULL,
  title       VARCHAR(255) NULL,
  chunk_index INT          NOT NULL DEFAULT 0,
  content     TEXT         NOT NULL,
  embedding   LONGTEXT     NOT NULL,
  metadata    JSON         NULL,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_rag_source (source, source_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
