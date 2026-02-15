-- User Subscription System for Peak Notifications
-- This works with existing community_alerts and editor_alerts tables

CREATE TABLE IF NOT EXISTS user_subscriptions (
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
);

CREATE TABLE IF NOT EXISTS notification_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    project VARCHAR(255) NOT NULL,
    peak_type ENUM('edit', 'editor') NOT NULL,
    peak_timestamp DATETIME NOT NULL,
    notification_sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notification_status ENUM('sent', 'failed', 'pending') NOT NULL DEFAULT 'pending',
    error_message TEXT DEFAULT NULL,
    INDEX idx_username (username),
    INDEX idx_project (project),
    INDEX idx_notification_sent_at (notification_sent_at),
    INDEX idx_notification_status (notification_status),
    INDEX idx_peak_lookup (project, peak_timestamp, peak_type)
);
