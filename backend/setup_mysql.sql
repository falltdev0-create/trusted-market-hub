-- ═══════════════════════════════════════════════════════════════════════════
-- معاملاتي — MySQL Database Setup Script
-- ═══════════════════════════════════════════════════════════════════════════

-- إنشاء قاعدة البيانات
CREATE DATABASE IF NOT EXISTS maskan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE maskan_db;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: users
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    national_id VARCHAR(50) UNIQUE,
    role ENUM('buyer', 'seller', 'both', 'admin') DEFAULT 'both',
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    avatar_url VARCHAR(500),
    kyc_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    selfie_url VARCHAR(500),
    kyc_doc_url VARCHAR(500),
    disclaimer_signed BOOLEAN DEFAULT FALSE,
    disclaimer_signed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_kyc_status (kyc_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: listings
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS listings (
    id VARCHAR(36) PRIMARY KEY,
    seller_id VARCHAR(36) NOT NULL,
    category ENUM('house', 'car') NOT NULL,
    listing_type ENUM('sale', 'rent') NOT NULL,
    title VARCHAR(255) NOT NULL,
    description LONGTEXT,
    status ENUM('draft', 'images_uploaded', 'condition_assessed', 'docs_uploaded', 
                'docs_verified', 'price_set', 'pending_review', 'published', 
                'rejected', 'sold') DEFAULT 'draft',
    city VARCHAR(100),
    district VARCHAR(100),
    price FLOAT,
    price_max_limit FLOAT,
    currency VARCHAR(10) DEFAULT 'SDG',
    condition_grade ENUM('excellent', 'good', 'poor'),
    condition_score FLOAT,
    condition_report JSON,
    details JSON,
    view_count INT DEFAULT 0,
    published_at DATETIME,
    rejected_reason LONGTEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_seller_id (seller_id),
    INDEX idx_category_type_status (category, listing_type, status),
    INDEX idx_city_status (city, status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: listing_images
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS listing_images (
    id VARCHAR(36) PRIMARY KEY,
    listing_id VARCHAR(36) NOT NULL,
    url VARCHAR(500) NOT NULL,
    image_type VARCHAR(50) DEFAULT 'item',
    `order` INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    INDEX idx_listing_id (listing_id),
    INDEX idx_order (`order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: listing_verifications
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS listing_verifications (
    id VARCHAR(36) PRIMARY KEY,
    listing_id VARCHAR(36) UNIQUE NOT NULL,
    owner_id_doc_url VARCHAR(500),
    ownership_doc_url VARCHAR(500),
    match_score FLOAT,
    match_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    match_details JSON,
    rejection_reason LONGTEXT,
    reviewed_by VARCHAR(36),
    reviewed_at DATETIME,
    verified_at DATETIME,
    
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_match_status (match_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: conversations
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(36) PRIMARY KEY,
    listing_id VARCHAR(36) NOT NULL,
    buyer_id VARCHAR(36) NOT NULL,
    seller_id VARCHAR(36) NOT NULL,
    disclaimer_signed BOOLEAN DEFAULT FALSE,
    disclaimer_signed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_listing_id (listing_id),
    INDEX idx_buyer_id (buyer_id),
    INDEX idx_seller_id (seller_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: messages
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    sender_id VARCHAR(36) NOT NULL,
    content LONGTEXT NOT NULL,
    was_filtered BOOLEAN DEFAULT FALSE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_sender_id (sender_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: notifications
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body LONGTEXT,
    is_read BOOLEAN DEFAULT FALSE,
    payload JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Sample Indexes for Performance
-- ═══════════════════════════════════════════════════════════════════════════

-- Performance queries indexes
CREATE INDEX idx_listings_seller_status ON listings(seller_id, status);
CREATE INDEX idx_listings_published ON listings(published_at) WHERE status = 'published';
CREATE INDEX idx_conversations_users ON conversations(buyer_id, seller_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- End of setup
-- ═══════════════════════════════════════════════════════════════════════════
