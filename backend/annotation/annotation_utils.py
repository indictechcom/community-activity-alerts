import requests
import logging
from config import get_db_connection
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user_edit_count(username):
    """
    Fetch global edit count for a Wikimedia user.
    Returns the edit count or None if user doesn't exist or API fails.
    """
    try:
        url = "https://meta.wikimedia.org/w/api.php"

        headers = {
            "User-Agent": "CommunityActivityAlerts/1.0 (CommunityActivityAlerts@example.com)" 
        }
        params = {
            "action": "query",
            "meta": "globaluserinfo",
            "guiuser": username,
            "guiprop": "editcount",
            "format": "json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "query" in data and "globaluserinfo" in data["query"]:
            user_info = data["query"]["globaluserinfo"]
            if "editcount" in user_info:
                return user_info["editcount"]
        
        return None
    except Exception as e:
        logger.error(f"Error fetching edit count for {username}: {e}")
        return None


def is_reviewer(username):
    """
    Check if a user is in the reviewer allowlist.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT is_active FROM annotation_reviewers WHERE username = %s",
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking reviewer status for {username}: {e}")
        return False


def log_annotation_action(annotation_id, action_type, username, details=None, ip_address=None, user_agent=None):
    """
    Log an annotation-related action to the audit log.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO annotation_audit_log 
            (annotation_id, action_type, username, details, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (annotation_id, action_type, username, details, ip_address, user_agent)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging annotation action: {e}")


def get_pending_annotations_count():
    """
    Get count of pending annotations awaiting review.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM peak_annotations WHERE status = 'pending'"
        )
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting pending annotations count: {e}")
        return 0


def get_pending_reports_count():
    """
    Get count of pending reports awaiting review.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM annotation_reports WHERE status = 'pending'"
        )
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting pending reports count: {e}")
        return 0


def send_reviewer_notification(subject, message_body):
    """
    Send email notification to all active reviewers using MediaWiki EmailUser API.
    This requires OAuth authentication with the emailuser right.
    
    Note: This is a placeholder implementation. In production, you would need to:
    1. Set up OAuth credentials with emailuser permission
    2. Implement proper OAuth flow
    3. Handle rate limiting and errors
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT username FROM annotation_reviewers WHERE is_active = TRUE"
        )
        reviewers = cursor.fetchall()
        conn.close()
        
        logger.info(f"Would send notification to {len(reviewers)} reviewers: {subject}")
        logger.info(f"Message: {message_body}")
        
        # TODO: Implement actual email sending via MediaWiki API
        # For now, just log the notification
        # In production, iterate through reviewers and use:
        # https://www.mediawiki.org/w/api.php?action=help&modules=emailuser
        
        return True
    except Exception as e:
        logger.error(f"Error sending reviewer notification: {e}")
        return False


def get_annotation_for_peak(project, timestamp, peak_type):
    """
    Get approved annotation for a specific peak.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, description, relevant_link, submitted_by, submitted_at
            FROM peak_annotations
            WHERE project = %s AND timestamp = %s AND peak_type = %s 
            AND status = 'approved' AND is_visible = TRUE
            ORDER BY reviewed_at DESC
            LIMIT 1
            """,
            (project, timestamp, peak_type)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "description": result[1],
                "relevant_link": result[2],
                "submitted_by": result[3],
                "submitted_at": result[4].isoformat() if result[4] else None
            }
        return None
    except Exception as e:
        logger.error(f"Error getting annotation for peak: {e}")
        return None
