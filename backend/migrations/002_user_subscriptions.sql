-- Watchlist System for Peak Notifications
-- This works with existing community_alerts and editor_alerts tables

-- Project Watchlist - users watching specific projects
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

-- Language Watchlist - users watching all projects from a language
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

-- Notification Logs to track delivery and prevent duplicates
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