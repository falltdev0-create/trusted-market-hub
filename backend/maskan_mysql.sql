-- =============================================================================
-- معاملاتي (Mo'amalati) — Complete MySQL Schema
-- =============================================================================
-- Usage:
--   mysql -u root -p < backend/maskan_mysql.sql
-- =============================================================================

DROP DATABASE IF EXISTS maskandaba;
CREATE DATABASE maskandaba CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE maskandaba;

SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================================
-- USERS & AUTH
-- =============================================================================
CREATE TABLE users (
    id              CHAR(36) PRIMARY KEY,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(191) NOT NULL UNIQUE,
    phone           VARCHAR(32)  NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(500) NULL,
    kyc_status      ENUM('unverified','pending','verified','rejected') NOT NULL DEFAULT 'unverified',
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    last_login_at   DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_kyc   (kyc_status)
) ENGINE=InnoDB;

CREATE TABLE kyc_submissions (
    id                CHAR(36) PRIMARY KEY,
    user_id           CHAR(36) NOT NULL,
    id_front_url      VARCHAR(500) NOT NULL,
    id_back_url       VARCHAR(500) NULL,
    selfie_url        VARCHAR(500) NULL,
    national_id       VARCHAR(64)  NULL,
    status            ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    match_score       DECIMAL(5,4) NULL,
    ai_report_json    JSON NULL,
    reviewed_by       CHAR(36) NULL,
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
    user_id         CHAR(36) NOT NULL UNIQUE,
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
-- LISTINGS
-- =============================================================================
CREATE TABLE listings (
    id                  CHAR(36) PRIMARY KEY,
    seller_id           CHAR(36) NOT NULL,
    category            VARCHAR(64)  NOT NULL,
    listing_type        ENUM('sale','rent') NOT NULL DEFAULT 'sale',
    title               VARCHAR(200) NULL,
    description         TEXT NULL,
    details             JSON NULL,
    location_city       VARCHAR(120) NULL,
    location_area       VARCHAR(120) NULL,
    condition_grade     ENUM('excellent','good','fair','poor') NULL,
    condition_score     DECIMAL(5,2) NULL,
    price               BIGINT NULL,
    price_tier          ENUM('cheap','medium','expensive') NULL,
    suggested_min       BIGINT NULL,
    suggested_max       BIGINT NULL,
    status              ENUM('draft','pending_images','pending_docs','pending_details','pending_price','pending_review','approved','rejected','sold','archived') NOT NULL DEFAULT 'draft',
    rejection_reason    TEXT NULL,
    views_count         INT NOT NULL DEFAULT 0,
    contacts_count      INT NOT NULL DEFAULT 0,
    is_featured         TINYINT(1) NOT NULL DEFAULT 0,
    approved_by         CHAR(36) NULL,
    approved_at         DATETIME NULL,
    published_at        DATETIME NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id)   REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_listings_status   (status),
    INDEX idx_listings_category (category),
    INDEX idx_listings_tier     (price_tier),
    INDEX idx_listings_seller   (seller_id),
    INDEX idx_listings_created  (created_at)
) ENGINE=InnoDB;

CREATE TABLE listing_images (
    id              CHAR(36) PRIMARY KEY,
    listing_id      CHAR(36) NOT NULL,
    url             VARCHAR(500) NOT NULL,
    thumbnail_url   VARCHAR(500) NULL,
    order_index     INT NOT NULL DEFAULT 0,
    ai_analyzed     TINYINT(1) NOT NULL DEFAULT 0,
    ai_score        DECIMAL(5,4) NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX idx_img_listing (listing_id)
) ENGINE=InnoDB;

CREATE TABLE listing_documents (
    id                    CHAR(36) PRIMARY KEY,
    listing_id            CHAR(36) NOT NULL,
    doc_type              ENUM('ownership','id','contract','other') NOT NULL DEFAULT 'ownership',
    url                   VARCHAR(500) NOT NULL,
    extracted_text        TEXT NULL,
    verification_status   ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    match_score           DECIMAL(5,4) NULL,
    ai_report_json        JSON NULL,
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX idx_doc_listing (listing_id)
) ENGINE=InnoDB;

CREATE TABLE condition_reports (
    id              CHAR(36) PRIMARY KEY,
    listing_id      CHAR(36) NOT NULL,
    grade           ENUM('excellent','good','fair','poor') NOT NULL,
    score           DECIMAL(5,2) NOT NULL,
    report          JSON NOT NULL,
    model_version   VARCHAR(64) NULL,
    processing_ms   INT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX idx_cond_listing (listing_id)
) ENGINE=InnoDB;

CREATE TABLE price_estimates (
    id              CHAR(36) PRIMARY KEY,
    listing_id      CHAR(36) NOT NULL,
    suggested_min   BIGINT NOT NULL,
    suggested_max   BIGINT NOT NULL,
    market_avg      BIGINT NULL,
    tier            ENUM('cheap','medium','expensive') NOT NULL,
    confidence      DECIMAL(5,4) NULL,
    model_version   VARCHAR(64) NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX idx_price_listing (listing_id)
) ENGINE=InnoDB;

-- =============================================================================
-- CHAT / MESSAGES
-- =============================================================================
CREATE TABLE conversations (
    id                CHAR(36) PRIMARY KEY,
    listing_id        CHAR(36) NOT NULL,
    buyer_id          CHAR(36) NOT NULL,
    seller_id         CHAR(36) NOT NULL,
    last_message_at   DATETIME NULL,
    buyer_unread      INT NOT NULL DEFAULT 0,
    seller_unread     INT NOT NULL DEFAULT 0,
    is_closed         TINYINT(1) NOT NULL DEFAULT 0,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id)   REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (seller_id)  REFERENCES users(id)    ON DELETE CASCADE,
    UNIQUE KEY uq_conv (listing_id, buyer_id, seller_id),
    INDEX idx_conv_buyer  (buyer_id),
    INDEX idx_conv_seller (seller_id)
) ENGINE=InnoDB;

CREATE TABLE messages (
    id                CHAR(36) PRIMARY KEY,
    conversation_id   CHAR(36) NOT NULL,
    sender_id         CHAR(36) NOT NULL,
    content           TEXT NOT NULL,
    filtered_content  TEXT NULL,
    is_flagged        TINYINT(1) NOT NULL DEFAULT 0,
    flag_reasons      JSON NULL,
    read_at           DATETIME NULL,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id)       REFERENCES users(id)         ON DELETE CASCADE,
    INDEX idx_msg_conv (conversation_id, created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- NOTIFICATIONS
-- =============================================================================
CREATE TABLE notifications (
    id          CHAR(36) PRIMARY KEY,
    user_id     CHAR(36) NOT NULL,
    type        VARCHAR(64)  NOT NULL,
    title       VARCHAR(200) NOT NULL,
    body        TEXT NULL,
    link        VARCHAR(500) NULL,
    is_read     TINYINT(1) NOT NULL DEFAULT 0,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notif_user   (user_id, is_read),
    INDEX idx_notif_created(created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- REPORTS (user-submitted complaints)
-- =============================================================================
CREATE TABLE reports (
    id              CHAR(36) PRIMARY KEY,
    reporter_id     CHAR(36) NOT NULL,
    target_type     ENUM('listing','user','message') NOT NULL,
    target_id       CHAR(36) NOT NULL,
    reason          VARCHAR(120) NOT NULL,
    details         TEXT NULL,
    status          ENUM('open','reviewing','resolved','dismissed') NOT NULL DEFAULT 'open',
    resolved_by     CHAR(36) NULL,
    resolved_at     DATETIME NULL,
    resolution_note TEXT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_reports_status (status),
    INDEX idx_reports_target (target_type, target_id)
) ENGINE=InnoDB;

-- =============================================================================
-- SYSTEM SETTINGS
-- =============================================================================
CREATE TABLE system_settings (
    setting_key   VARCHAR(120) PRIMARY KEY,
    setting_value JSON NOT NULL,
    description   TEXT NULL,
    updated_by    CHAR(36) NULL,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =============================================================================
-- SEED DATA
-- =============================================================================

-- Categories
INSERT INTO categories (id, slug, name_ar, name_en, icon, sort_order) VALUES
  (UUID(), 'house', 'عقارات', 'Real Estate', 'home', 1),
  (UUID(), 'car',   'سيارات', 'Cars',        'car',  2),
  (UUID(), 'other', 'أخرى',   'Other',       'box',  99);

-- Admin permission matrix
INSERT INTO admin_permissions (role, permission_key) VALUES
  ('super_admin','*'),
  ('admin','listings.review'), ('admin','listings.approve'), ('admin','listings.reject'),
  ('admin','users.view'), ('admin','users.suspend'), ('admin','kyc.review'),
  ('admin','reports.handle'), ('admin','settings.view'), ('admin','moderators.manage'),
  ('moderator','listings.review'), ('moderator','listings.approve'), ('moderator','listings.reject'),
  ('moderator','kyc.review'), ('moderator','reports.handle'), ('moderator','users.view'),
  ('reviewer','listings.review'), ('reviewer','kyc.review'), ('reviewer','users.view');

-- Default super admin (email: admin@moamalati.local  password: Admin@12345)
-- password hash generated with bcrypt (rounds=12)
INSERT INTO users (id, full_name, email, phone, password_hash, kyc_status, is_active)
VALUES (
  'a0000000-0000-0000-0000-000000000001',
  'Super Admin',
  'admin@moamalati.local',
  '000000000',
  '$2b$12$KIXQwbvS7cB/3rWL2sQ8heRhc7GrH2Y8jNTZ4W1nq9KzYQpJ3g0Iu',
  'verified',
  1
);
INSERT INTO admins (id, user_id, role, is_active)
VALUES (
  'ad000000-0000-0000-0000-000000000001',
  'a0000000-0000-0000-0000-000000000001',
  'super_admin',
  1
);

-- System settings defaults
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
  ('price_tiers', JSON_OBJECT(
      'house', JSON_OBJECT('cheap', 2000000, 'medium', 5000000),
      'car',   JSON_OBJECT('cheap',  800000, 'medium', 2000000),
      'other', JSON_OBJECT('cheap',   50000, 'medium',  250000)
    ), 'Thresholds for cheap/medium/expensive tiers (SDG). >medium = expensive.'),
  ('site_name',        JSON_QUOTE('معاملاتي'), 'Public site name'),
  ('kyc_required',     CAST('true' AS JSON),   'Require KYC before publishing listings'),
  ('max_images',       CAST('10' AS JSON),     'Max images per listing');

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- END
-- =============================================================================
