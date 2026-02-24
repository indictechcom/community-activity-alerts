from flask import Blueprint, request, jsonify
from config import get_db_connection
import logging
from subscription.sitematrix_validator import (
    is_valid_project,
    is_valid_language,
    normalize_project,
    normalize_language_code
)

logger = logging.getLogger(__name__)

def create_subscription_blueprint(mwo_auth):
    watchlist_bp = Blueprint('watchlist', __name__)

    @watchlist_bp.route('/add-project', methods=['POST'])
    def add_project_to_watchlist():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400
        project = data.get('project')
        notification_type = data.get('notification_type', 'both')

        if not project:
            return jsonify({"error": "Project is required"}), 400

        if notification_type not in ['edit', 'editor', 'both']:
            return jsonify({"error": "Invalid notification type"}), 400

        normalized_project = normalize_project(project)
        if not is_valid_project(normalized_project):
            return jsonify({
                "error": f"Invalid project: '{project}' is not a valid Wikimedia project. Please enter a valid project URL (e.g., en.wikipedia.org, hi.wikibooks.org)"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO user_project_watchlist (username, project, notification_type, is_active)
                VALUES (%s, %s, %s, TRUE)
                ON DUPLICATE KEY UPDATE 
                    notification_type = VALUES(notification_type),
                    is_active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
            """, (user, normalized_project, notification_type))
            
            conn.commit()
            return jsonify({
                "success": True,
                "message": "Successfully added project to watchlist"
            }), 200

        except Exception as e:
            logger.error(f"Error adding project {project} to watchlist for user {user}: {e}")
            conn.rollback()
            return jsonify({"error": "Failed to add project to watchlist"}), 500
        finally:
            cursor.close()
            conn.close()

    @watchlist_bp.route('/remove-project', methods=['POST'])
    def remove_project_from_watchlist():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400
        project = data.get('project')

        if not project:
            return jsonify({"error": "Project is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE user_project_watchlist 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE username = %s AND project = %s
            """, (user, project))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Project not found in watchlist"}), 404
            
            return jsonify({
                "success": True,
                "message": "Successfully removed project from watchlist"
            }), 200

        except Exception as e:
            logger.error(f"Error removing project {project} from watchlist for user {user}: {e}")
            conn.rollback()
            return jsonify({"error": "Failed to remove project from watchlist"}), 500
        finally:
            cursor.close()
            conn.close()

    @watchlist_bp.route('/project-watchlist', methods=['GET'])
    def get_project_watchlist():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT project, notification_type, is_active, created_at, updated_at
                FROM user_project_watchlist
                WHERE username = %s
                ORDER BY created_at DESC
            """, (user,))
            
            watchlist = []
            for row in cursor.fetchall():
                watchlist.append({
                    "project": row[0],
                    "notification_type": row[1],
                    "is_active": bool(row[2]),
                    "created_at": row[3].isoformat() if row[3] else None,
                    "updated_at": row[4].isoformat() if row[4] else None
                })
            
            return jsonify({
                "success": True,
                "watchlist": watchlist
            }), 200

        except Exception as e:
            logger.error(f"Error fetching project watchlist for user {user}: {e}")
            return jsonify({"error": "Failed to fetch project watchlist"}), 500
        finally:
            cursor.close()
            conn.close()

    @watchlist_bp.route('/check-project', methods=['GET'])
    def check_project_in_watchlist():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        project = request.args.get('project')
        if not project:
            return jsonify({"error": "Project parameter is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT notification_type, is_active
                FROM user_project_watchlist
                WHERE username = %s AND project = %s
            """, (user, project))
            
            result = cursor.fetchone()
            
            if result:
                return jsonify({
                    "in_watchlist": bool(result[1]),
                    "notification_type": result[0]
                }), 200
            else:
                return jsonify({
                    "in_watchlist": False,
                    "notification_type": None
                }), 200

        except Exception as e:
            logger.error(f"Error checking project in watchlist for user {user} and project {project}: {e}")
            return jsonify({"error": "Failed to check project in watchlist"}), 500
        finally:
            cursor.close()
            conn.close()

    @watchlist_bp.route('/update-notification-type', methods=['PUT'])
    def update_notification_type():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400
        project = data.get('project')
        notification_type = data.get('notification_type')

        if not project or not notification_type:
            return jsonify({"error": "Project and notification_type are required"}), 400

        if notification_type not in ['edit', 'editor', 'both']:
            return jsonify({"error": "Invalid notification type"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE user_project_watchlist 
                SET notification_type = %s, updated_at = CURRENT_TIMESTAMP
                WHERE username = %s AND project = %s AND is_active = TRUE
            """, (notification_type, user, project))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Project not found in active watchlist"}), 404
            
            return jsonify({
                "success": True,
                "message": "Notification type updated successfully"
            }), 200

        except Exception as e:
            logger.error(f"Error updating notification type for user {user} and project {project}: {e}")
            conn.rollback()
            return jsonify({"error": "Failed to update notification type"}), 500
        finally:
            cursor.close()
            conn.close()

    # Language watchlist endpoints
    @watchlist_bp.route('/add-language', methods=['POST'])
    def add_language_to_watchlist():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        data = request.json
        language_code = data.get('language_code')
        notification_type = data.get('notification_type', 'both')

        if not language_code:
            return jsonify({"error": "Language code is required"}), 400

        if notification_type not in ['edit', 'editor', 'both']:
            return jsonify({"error": "Invalid notification type"}), 400

        normalized_language = normalize_language_code(language_code)
        if not is_valid_language(normalized_language):
            return jsonify({
                "error": f"Invalid language code: '{language_code}' is not a valid Wikimedia language. Please enter a valid language code (e.g., en, hi, fr)"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO user_language_watchlist (username, language_code, notification_type, is_active)
                VALUES (%s, %s, %s, TRUE)
                ON DUPLICATE KEY UPDATE 
                    notification_type = VALUES(notification_type),
                    is_active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
            """, (user, normalized_language, notification_type))
            
            conn.commit()
            return jsonify({
                "success": True,
                "message": f"Successfully added {language_code} to language watchlist"
            }), 200

        except Exception as e:
            logger.error(f"Error adding language {language_code} to watchlist for user {user}: {e}")
            conn.rollback()
            return jsonify({"error": "Failed to add language to watchlist"}), 500
        finally:
            cursor.close()
            conn.close()

    @watchlist_bp.route('/remove-language', methods=['POST'])
    def remove_language_from_watchlist():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        data = request.json
        language_code = data.get('language_code')

        if not language_code:
            return jsonify({"error": "Language code is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE user_language_watchlist 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE username = %s AND language_code = %s
            """, (user, language_code))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Language not found in watchlist"}), 404
            
            return jsonify({
                "success": True,
                "message": f"Successfully removed {language_code} from language watchlist"
            }), 200

        except Exception as e:
            logger.error(f"Error removing language {language_code} from watchlist for user {user}: {e}")
            conn.rollback()
            return jsonify({"error": "Failed to remove language from watchlist"}), 500
        finally:
            cursor.close()
            conn.close()

    @watchlist_bp.route('/language-watchlist', methods=['GET'])
    def get_language_watchlist():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT language_code, notification_type, is_active, created_at, updated_at
                FROM user_language_watchlist
                WHERE username = %s
                ORDER BY created_at DESC
            """, (user,))
            
            language_watchlist = []
            for row in cursor.fetchall():
                language_watchlist.append({
                    "language_code": row[0],
                    "notification_type": row[1],
                    "is_active": bool(row[2]),
                    "created_at": row[3].isoformat() if row[3] else None,
                    "updated_at": row[4].isoformat() if row[4] else None
                })
            
            return jsonify({
                "success": True,
                "language_watchlist": language_watchlist
            }), 200

        except Exception as e:
            logger.error(f"Error fetching language watchlist for user {user}: {e}")
            return jsonify({"error": "Failed to fetch language watchlist"}), 500
        finally:
            cursor.close()
            conn.close()

    return watchlist_bp
