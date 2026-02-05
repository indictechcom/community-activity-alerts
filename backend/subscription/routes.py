from flask import Blueprint, request, jsonify
from config import get_db_connection
import logging

logger = logging.getLogger(__name__)

def create_subscription_blueprint(mwo_auth):
    subscription_bp = Blueprint('subscription', __name__)

    @subscription_bp.route('/subscribe', methods=['POST'])
    def subscribe_to_project():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        data = request.json
        project = data.get('project')
        notification_type = data.get('notification_type', 'both')

        if not project:
            return jsonify({"error": "Project is required"}), 400

        if notification_type not in ['edit', 'editor', 'both']:
            return jsonify({"error": "Invalid notification type"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO user_subscriptions (username, project, notification_type, is_active)
                VALUES (%s, %s, %s, TRUE)
                ON DUPLICATE KEY UPDATE 
                    notification_type = VALUES(notification_type),
                    is_active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
            """, (user, project, notification_type))
            
            conn.commit()
            return jsonify({
                "success": True,
                "message": "Successfully subscribed to project notifications"
            }), 200

        except Exception as e:
            logger.error(f"Error subscribing user {user} to project {project}: {e}")
            conn.rollback()
            return jsonify({"error": "Failed to subscribe to project"}), 500
        finally:
            cursor.close()
            conn.close()

    @subscription_bp.route('/unsubscribe', methods=['POST'])
    def unsubscribe_from_project():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        data = request.json
        project = data.get('project')

        if not project:
            return jsonify({"error": "Project is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE user_subscriptions 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE username = %s AND project = %s
            """, (user, project))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Subscription not found"}), 404
            
            return jsonify({
                "success": True,
                "message": "Successfully unsubscribed from project notifications"
            }), 200

        except Exception as e:
            logger.error(f"Error unsubscribing user {user} from project {project}: {e}")
            conn.rollback()
            return jsonify({"error": "Failed to unsubscribe from project"}), 500
        finally:
            cursor.close()
            conn.close()

    @subscription_bp.route('/my-subscriptions', methods=['GET'])
    def get_user_subscriptions():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT project, notification_type, is_active, created_at, updated_at
                FROM user_subscriptions
                WHERE username = %s
                ORDER BY created_at DESC
            """, (user,))
            
            subscriptions = []
            for row in cursor.fetchall():
                subscriptions.append({
                    "project": row[0],
                    "notification_type": row[1],
                    "is_active": bool(row[2]),
                    "created_at": row[3].isoformat() if row[3] else None,
                    "updated_at": row[4].isoformat() if row[4] else None
                })
            
            return jsonify({
                "success": True,
                "subscriptions": subscriptions
            }), 200

        except Exception as e:
            logger.error(f"Error fetching subscriptions for user {user}: {e}")
            return jsonify({"error": "Failed to fetch subscriptions"}), 500
        finally:
            cursor.close()
            conn.close()

    @subscription_bp.route('/check-subscription', methods=['GET'])
    def check_subscription():
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
                FROM user_subscriptions
                WHERE username = %s AND project = %s
            """, (user, project))
            
            result = cursor.fetchone()
            
            if result:
                return jsonify({
                    "subscribed": bool(result[1]),
                    "notification_type": result[0]
                }), 200
            else:
                return jsonify({
                    "subscribed": False,
                    "notification_type": None
                }), 200

        except Exception as e:
            logger.error(f"Error checking subscription for user {user} and project {project}: {e}")
            return jsonify({"error": "Failed to check subscription"}), 500
        finally:
            cursor.close()
            conn.close()

    @subscription_bp.route('/update-notification-type', methods=['PUT'])
    def update_notification_type():
        user = mwo_auth.get_current_user(True)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        data = request.json
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
                UPDATE user_subscriptions 
                SET notification_type = %s, updated_at = CURRENT_TIMESTAMP
                WHERE username = %s AND project = %s AND is_active = TRUE
            """, (notification_type, user, project))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Active subscription not found"}), 404
            
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

    return subscription_bp
