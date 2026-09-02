-- معاملاتي — SQLite schema (full)

CREATE TABLE IF NOT EXISTS users (
  id              TEXT PRIMARY KEY,
  full_name       TEXT NOT NULL,
  email           TEXT NOT NULL UNIQUE,
  phone           TEXT,
  national_id     TEXT,
  password_hash   TEXT NOT NULL,
  role            TEXT NOT NULL DEFAULT 'both',        -- buyer|seller|both|admin|super_admin
  admin_role      TEXT,                                -- reviewer|moderator|admin|super_admin
  kyc_status      TEXT NOT NULL DEFAULT 'unverified',  -- unverified|pending|verified|rejected
  trust_score     INTEGER NOT NULL DEFAULT 50,
  avatar_url      TEXT,
  city            TEXT,
  is_active       INTEGER NOT NULL DEFAULT 1,
  is_banned       INTEGER NOT NULL DEFAULT 0,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS kyc_submissions (
  id            TEXT PRIMARY KEY,
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  full_name     TEXT,
  national_id   TEXT,
  id_front_url  TEXT,
  id_back_url   TEXT,
  selfie_url    TEXT,
  status        TEXT NOT NULL DEFAULT 'pending',
  ai_score      REAL,
  ai_report     TEXT,
  reviewer_id   TEXT,
  reject_reason TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  reviewed_at   TEXT
);

CREATE TABLE IF NOT EXISTS listings (
  id                TEXT PRIMARY KEY,
  owner_id          TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind              TEXT,                    -- house|car
  category          TEXT,
  listing_type      TEXT,                    -- sale|rent
  title             TEXT,
  description       TEXT,
  city              TEXT,
  district          TEXT,
  price             REAL,
  suggested_price   REAL,
  price_tier        TEXT,                    -- cheap|medium|expensive
  currency          TEXT NOT NULL DEFAULT 'SDG',
  area              REAL,
  rooms             INTEGER,
  bathrooms         INTEGER,
  year              INTEGER,
  mileage           INTEGER,
  brand             TEXT,
  model             TEXT,
  details           TEXT,                    -- JSON
  condition_grade   TEXT,
  condition_score   REAL,
  condition_report  TEXT,                    -- JSON
  condition_status  TEXT NOT NULL DEFAULT 'idle', -- idle|processing|done|failed
  docs_status       TEXT NOT NULL DEFAULT 'idle',
  docs_match_score  REAL,
  docs_report       TEXT,
  status            TEXT NOT NULL DEFAULT 'draft', -- draft|pending_review|published|rejected|sold|archived
  reject_reason     TEXT,
  views             INTEGER NOT NULL DEFAULT 0,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS listing_images (
  id         TEXT PRIMARY KEY,
  listing_id TEXT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  url        TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS listing_documents (
  id         TEXT PRIMARY KEY,
  listing_id TEXT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  doc_type   TEXT NOT NULL,   -- id_doc|ownership_doc
  url        TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conversations (
  id          TEXT PRIMARY KEY,
  listing_id  TEXT REFERENCES listings(id) ON DELETE SET NULL,
  buyer_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  seller_id   TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
  id              TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  sender_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body            TEXT NOT NULL,
  filtered        INTEGER NOT NULL DEFAULT 0,
  read_at         TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title      TEXT NOT NULL,
  body       TEXT,
  type       TEXT NOT NULL DEFAULT 'info',
  link       TEXT,
  is_read    INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS admin_audit_logs (
  id          TEXT PRIMARY KEY,
  admin_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  action      TEXT NOT NULL,
  target_type TEXT,
  target_id   TEXT,
  meta        TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS site_settings (
  key        TEXT PRIMARY KEY,
  value      TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rag_documents (
  id          TEXT PRIMARY KEY,
  source      TEXT NOT NULL,
  source_id   TEXT,
  title       TEXT,
  chunk_index INTEGER NOT NULL DEFAULT 0,
  content     TEXT NOT NULL,
  embedding   TEXT NOT NULL,
  metadata    TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
CREATE INDEX IF NOT EXISTS idx_listings_owner  ON listings(owner_id);
CREATE INDEX IF NOT EXISTS idx_messages_conv   ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_notif_user      ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_rag_source      ON rag_documents(source);
