-- Annotations table: stores user-submitted annotations for peaks
CREATE TABLE IF NOT EXISTS peak_annotations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project VARCHAR(255) NOT NULL,
    timestamp DATETIME NOT NULL,
    peak_type ENUM('edit', 'editor') NOT NULL,
    description VARCHAR(500) NOT NULL,
    relevant_link VARCHAR(500) DEFAULT NULL,
    submitted_by VARCHAR(255) NOT NULL,
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    reviewed_by VARCHAR(255) DEFAULT NULL,
    reviewed_at DATETIME DEFAULT NULL,
    is_visible BOOLEAN NOT NULL DEFAULT FALSE,
    INDEX idx_project_timestamp (project, timestamp),
    INDEX idx_status (status),
    INDEX idx_submitted_by (submitted_by)
);

-- Annotation reviews table: tracks review actions
CREATE TABLE IF NOT EXISTS annotation_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    annotation_id INT NOT NULL,
    reviewer_username VARCHAR(255) NOT NULL,
    action ENUM('approve', 'reject', 'edit') NOT NULL,
    original_description VARCHAR(500) DEFAULT NULL,
    edited_description VARCHAR(500) DEFAULT NULL,
    original_link VARCHAR(500) DEFAULT NULL,
    edited_link VARCHAR(500) DEFAULT NULL,
    review_notes TEXT DEFAULT NULL,
    reviewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (annotation_id) REFERENCES peak_annotations(id) ON DELETE CASCADE,
    INDEX idx_annotation_id (annotation_id),
    INDEX idx_reviewer (reviewer_username)
);

-- Annotation reports table: tracks user reports on approved annotations
CREATE TABLE IF NOT EXISTS annotation_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    annotation_id INT NOT NULL,
    reported_by VARCHAR(255) NOT NULL,
    report_reason TEXT NOT NULL,
    reported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'reviewed', 'dismissed') NOT NULL DEFAULT 'pending',
    reviewed_by VARCHAR(255) DEFAULT NULL,
    reviewed_at DATETIME DEFAULT NULL,
    action_taken ENUM('no_action', 'edited', 'removed') DEFAULT NULL,
    FOREIGN KEY (annotation_id) REFERENCES peak_annotations(id) ON DELETE CASCADE,
    INDEX idx_annotation_id (annotation_id),
    INDEX idx_status (status),
    INDEX idx_reported_by (reported_by)
);

-- Audit log table: comprehensive logging of all annotation-related actions
CREATE TABLE IF NOT EXISTS annotation_audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    annotation_id INT DEFAULT NULL,
    action_type ENUM('submit', 'review_approve', 'review_reject', 'review_edit', 'report', 'report_action') NOT NULL,
    username VARCHAR(255) NOT NULL,
    details TEXT DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_annotation_id (annotation_id),
    INDEX idx_action_type (action_type),
    INDEX idx_username (username),
    INDEX idx_created_at (created_at)
);

-- Reviewer allowlist table: stores authorized reviewers
CREATE TABLE IF NOT EXISTS annotation_reviewers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    region VARCHAR(100) DEFAULT NULL,
    added_by VARCHAR(255) NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT DEFAULT NULL,
    INDEX idx_username (username),
    INDEX idx_is_active (is_active)
);
