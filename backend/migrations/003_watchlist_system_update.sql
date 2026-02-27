-- Migration 003: Update Watchlist System
-- Migrates user_subscriptions to the new split watchlist tables (project + language).

-- 1. Create Project Watchlist - users watching specific projects
CREATE TABLE IF NOT EXISTS user_project_watchlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    project VARCHAR(255) NOT NULL,
    notification_type ENUM('edit', 'editor', 'both') NOT NULL DEFAULT 'both',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_project (username, project),
    INDEX idx_username (username),
    INDEX idx_project (project),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Project watchlist - users watching specific projects';

-- 2. Create Language Watchlist - users watching all projects from a language
CREATE TABLE IF NOT EXISTS user_language_watchlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    notification_type ENUM('edit', 'editor', 'both') NOT NULL DEFAULT 'both',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_language (username, language_code),
    INDEX idx_username (username),
    INDEX idx_language_code (language_code),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Language watchlist - users watching all projects from a language';

-- 3. Migrate existing data from user_subscriptions to user_project_watchlist (if table exists)
INSERT IGNORE INTO user_project_watchlist (username, project, notification_type, is_active, created_at, updated_at)
SELECT username, project, notification_type, is_active, created_at, updated_at
FROM user_subscriptions
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'user_subscriptions');

-- 4. Drop the old subscriptions table after migration
DROP TABLE IF EXISTS user_subscriptions;

-- 5. Ensure Notification Logs exists (Will be ignored safely if 002 already created it)
CREATE TABLE IF NOT EXISTS notification_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    project VARCHAR(255) NOT NULL,
    peak_type ENUM('edit', 'editor') NOT NULL,
    peak_timestamp DATETIME NOT NULL,
    notification_sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notification_status ENUM('sent', 'failed', 'pending') NOT NULL DEFAULT 'pending',
    error_message TEXT DEFAULT NULL,
    UNIQUE KEY unique_notification_event (username, project, peak_timestamp, peak_type),
    INDEX idx_username (username),
    INDEX idx_project (project),
    INDEX idx_notification_status (notification_status),
    INDEX idx_notification_lookup (project, peak_timestamp, peak_type, username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;