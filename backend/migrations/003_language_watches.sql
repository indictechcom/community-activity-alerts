-- Language Watch System
-- Allows users to watch all projects from a specific language

CREATE TABLE IF NOT EXISTS user_language_watches (
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
);

-- Rename existing tables from subscription to watch terminology
-- Note: This is a non-destructive rename that maintains data
RENAME TABLE user_subscriptions TO user_watches;

-- Add a comment to clarify the distinction
ALTER TABLE user_watches COMMENT = 'Individual project watches - users watching specific projects';
ALTER TABLE user_language_watches COMMENT = 'Language watches - users watching all projects from a language';
