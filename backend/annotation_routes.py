from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from config import get_db_connection
from annotation_utils import (
    get_user_edit_count,
    is_reviewer,
    log_annotation_action,
    get_pending_annotations_count,
    get_pending_reports_count,
    send_reviewer_notification,
    get_annotation_for_peak
)

logger = logging.getLogger(__name__)

def create_annotation_blueprint(mwo_auth):
    annotation_bp = Blueprint('annotations', __name__)

    # --- Submit Annotation ---
    @annotation_bp.route('/submit', methods=['POST'])
    def submit_annotation():
        """
        Submit a new annotation for a peak.
        Requires: authenticated user with >= 1000 global edits
        """
        current_user = mwo_auth.get_current_user(True)
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        username = current_user[0]
        data = request.json
        
        # Validate required fields
        required_fields = ['project', 'timestamp', 'peak_type', 'description']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        project = data['project']
        timestamp = data['timestamp']
        peak_type = data['peak_type']
        description = data['description'].strip()
        relevant_link = data.get('relevant_link', '').strip() or None
        
        # Validate description length (50 words max)
        word_count = len(description.split())
        if word_count > 50:
            return jsonify({"error": f"Description exceeds 50 words (current: {word_count})"}), 400
        
        if len(description) < 10:
            return jsonify({"error": "Description too short (minimum 10 characters)"}), 400
        
        # Validate peak_type
        if peak_type not in ['edit', 'editor']:
            return jsonify({"error": "Invalid peak_type"}), 400
        
        # Check user's global edit count
        edit_count = get_user_edit_count(username)
        if edit_count is None:
            return jsonify({"error": "Unable to verify edit count"}), 500
        
        if edit_count < 1000:
            return jsonify({
                "error": f"Insufficient edit count. Required: 1000, Current: {edit_count}"
            }), 403
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if user already has a pending annotation for this peak
            cursor.execute(
                """
                SELECT id FROM peak_annotations 
                WHERE project = %s AND timestamp = %s AND peak_type = %s 
                AND submitted_by = %s AND status = 'pending'
                """,
                (project, timestamp, peak_type, username)
            )
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                return jsonify({"error": "You already have a pending annotation for this peak"}), 409
            
            # Insert annotation
            cursor.execute(
                """
                INSERT INTO peak_annotations 
                (project, timestamp, peak_type, description, relevant_link, submitted_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (project, timestamp, peak_type, description, relevant_link, username)
            )
            annotation_id = cursor.lastrowid
            conn.commit()
            
            # Log the action
            log_annotation_action(
                annotation_id, 
                'submit', 
                username,
                f"Submitted annotation for {project} at {timestamp}",
                request.remote_addr,
                request.headers.get('User-Agent')
            )
            
            # Send notification to reviewers
            send_reviewer_notification(
                "New Annotation Submitted",
                f"User {username} submitted an annotation for {project} ({peak_type}) at {timestamp}.\n\nDescription: {description}"
            )
            
            conn.close()
            
            return jsonify({
                "success": True,
                "annotation_id": annotation_id,
                "message": "Annotation submitted for review"
            }), 201
            
        except Exception as e:
            logger.error(f"Error submitting annotation: {e}")
            return jsonify({"error": "Failed to submit annotation"}), 500

    # --- Get Annotations for Peak ---
    @annotation_bp.route('/get', methods=['GET'])
    def get_peak_annotation():
        """
        Get approved annotation for a specific peak.
        Public endpoint - no authentication required.
        """
        project = request.args.get('project')
        timestamp = request.args.get('timestamp')
        peak_type = request.args.get('peak_type', 'edit')
        
        if not (project and timestamp):
            return jsonify({"error": "Missing required parameters"}), 400
        
        annotation = get_annotation_for_peak(project, timestamp, peak_type)
        
        if annotation:
            return jsonify(annotation), 200
        else:
            return jsonify({"annotation": None}), 200

    # --- Get Pending Annotations (Reviewers Only) ---
    @annotation_bp.route('/pending', methods=['GET'])
    def get_pending_annotations():
        """
        Get all pending annotations for review.
        Requires: reviewer privileges
        """
        current_user = mwo_auth.get_current_user(True)
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        username = current_user[0]
        
        if not is_reviewer(username):
            return jsonify({"error": "Reviewer privileges required"}), 403
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT id, project, timestamp, peak_type, description, relevant_link, 
                       submitted_by, submitted_at
                FROM peak_annotations
                WHERE status = 'pending'
                ORDER BY submitted_at ASC
                """
            )
            results = cursor.fetchall()
            conn.close()
            
            annotations = []
            for row in results:
                annotations.append({
                    "id": row[0],
                    "project": row[1],
                    "timestamp": row[2].isoformat() if row[2] else None,
                    "peak_type": row[3],
                    "description": row[4],
                    "relevant_link": row[5],
                    "submitted_by": row[6],
                    "submitted_at": row[7].isoformat() if row[7] else None
                })
            
            return jsonify({"annotations": annotations}), 200
            
        except Exception as e:
            logger.error(f"Error fetching pending annotations: {e}")
            return jsonify({"error": "Failed to fetch annotations"}), 500

    # --- Review Annotation (Approve/Reject/Edit) ---
    @annotation_bp.route('/review', methods=['POST'])
    def review_annotation():
        """
        Review an annotation (approve, reject, or edit).
        Requires: reviewer privileges
        """
        current_user = mwo_auth.get_current_user(True)
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        username = current_user[0]
        
        if not is_reviewer(username):
            return jsonify({"error": "Reviewer privileges required"}), 403
        
        data = request.json
        annotation_id = data.get('annotation_id')
        action = data.get('action')  # 'approve', 'reject', 'edit'
        
        if not (annotation_id and action):
            return jsonify({"error": "Missing required fields"}), 400
        
        if action not in ['approve', 'reject', 'edit']:
            return jsonify({"error": "Invalid action"}), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get current annotation
            cursor.execute(
                """
                SELECT description, relevant_link, submitted_by, status
                FROM peak_annotations WHERE id = %s
                """,
                (annotation_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return jsonify({"error": "Annotation not found"}), 404
            
            original_description, original_link, submitted_by, current_status = result
            
            if current_status != 'pending':
                conn.close()
                return jsonify({"error": "Annotation already reviewed"}), 409
            
            if action == 'approve':
                # Approve annotation
                cursor.execute(
                    """
                    UPDATE peak_annotations
                    SET status = 'approved', is_visible = TRUE, 
                        reviewed_by = %s, reviewed_at = %s
                    WHERE id = %s
                    """,
                    (username, datetime.now(), annotation_id)
                )
                
                # Log review
                cursor.execute(
                    """
                    INSERT INTO annotation_reviews
                    (annotation_id, reviewer_username, action, review_notes)
                    VALUES (%s, %s, 'approve', %s)
                    """,
                    (annotation_id, username, data.get('notes'))
                )
                
                log_annotation_action(
                    annotation_id, 'review_approve', username,
                    f"Approved annotation by {submitted_by}",
                    request.remote_addr, request.headers.get('User-Agent')
                )
                
                message = "Annotation approved"
                
            elif action == 'reject':
                # Reject annotation
                cursor.execute(
                    """
                    UPDATE peak_annotations
                    SET status = 'rejected', reviewed_by = %s, reviewed_at = %s
                    WHERE id = %s
                    """,
                    (username, datetime.now(), annotation_id)
                )
                
                cursor.execute(
                    """
                    INSERT INTO annotation_reviews
                    (annotation_id, reviewer_username, action, review_notes)
                    VALUES (%s, %s, 'reject', %s)
                    """,
                    (annotation_id, username, data.get('notes'))
                )
                
                log_annotation_action(
                    annotation_id, 'review_reject', username,
                    f"Rejected annotation by {submitted_by}",
                    request.remote_addr, request.headers.get('User-Agent')
                )
                
                message = "Annotation rejected"
                
            elif action == 'edit':
                # Edit and approve annotation
                edited_description = data.get('edited_description', '').strip()
                edited_link = data.get('edited_link', '').strip() or None
                
                if not edited_description:
                    conn.close()
                    return jsonify({"error": "Edited description required"}), 400
                
                # Validate edited description length
                word_count = len(edited_description.split())
                if word_count > 50:
                    conn.close()
                    return jsonify({"error": f"Description exceeds 50 words (current: {word_count})"}), 400
                
                cursor.execute(
                    """
                    UPDATE peak_annotations
                    SET description = %s, relevant_link = %s, 
                        status = 'approved', is_visible = TRUE,
                        reviewed_by = %s, reviewed_at = %s
                    WHERE id = %s
                    """,
                    (edited_description, edited_link, username, datetime.now(), annotation_id)
                )
                
                cursor.execute(
                    """
                    INSERT INTO annotation_reviews
                    (annotation_id, reviewer_username, action, 
                     original_description, edited_description, 
                     original_link, edited_link, review_notes)
                    VALUES (%s, %s, 'edit', %s, %s, %s, %s, %s)
                    """,
                    (annotation_id, username, original_description, edited_description,
                     original_link, edited_link, data.get('notes'))
                )
                
                log_annotation_action(
                    annotation_id, 'review_edit', username,
                    f"Edited and approved annotation by {submitted_by}",
                    request.remote_addr, request.headers.get('User-Agent')
                )
                
                message = "Annotation edited and approved"
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "message": message}), 200
            
        except Exception as e:
            logger.error(f"Error reviewing annotation: {e}")
            return jsonify({"error": "Failed to review annotation"}), 500

    # --- Report Annotation ---
    @annotation_bp.route('/report', methods=['POST'])
    def report_annotation():
        """
        Report an approved annotation.
        Requires: authenticated user
        """
        current_user = mwo_auth.get_current_user(True)
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        username = current_user[0]
        data = request.json
        
        annotation_id = data.get('annotation_id')
        report_reason = data.get('report_reason', '').strip()
        
        if not (annotation_id and report_reason):
            return jsonify({"error": "Missing required fields"}), 400
        
        if len(report_reason) < 10:
            return jsonify({"error": "Report reason too short"}), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verify annotation exists and is approved
            cursor.execute(
                "SELECT status FROM peak_annotations WHERE id = %s",
                (annotation_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return jsonify({"error": "Annotation not found"}), 404
            
            if result[0] != 'approved':
                conn.close()
                return jsonify({"error": "Can only report approved annotations"}), 400
            
            # Check if user already reported this annotation
            cursor.execute(
                """
                SELECT id FROM annotation_reports 
                WHERE annotation_id = %s AND reported_by = %s AND status = 'pending'
                """,
                (annotation_id, username)
            )
            if cursor.fetchone():
                conn.close()
                return jsonify({"error": "You already reported this annotation"}), 409
            
            # Insert report
            cursor.execute(
                """
                INSERT INTO annotation_reports
                (annotation_id, reported_by, report_reason)
                VALUES (%s, %s, %s)
                """,
                (annotation_id, username, report_reason)
            )
            report_id = cursor.lastrowid
            conn.commit()
            
            # Log the action
            log_annotation_action(
                annotation_id, 'report', username,
                f"Reported annotation: {report_reason}",
                request.remote_addr, request.headers.get('User-Agent')
            )
            
            # Notify reviewers
            send_reviewer_notification(
                "Annotation Reported",
                f"User {username} reported annotation #{annotation_id}.\n\nReason: {report_reason}"
            )
            
            conn.close()
            
            return jsonify({
                "success": True,
                "report_id": report_id,
                "message": "Report submitted for review"
            }), 201
            
        except Exception as e:
            logger.error(f"Error reporting annotation: {e}")
            return jsonify({"error": "Failed to submit report"}), 500

    # --- Get Pending Reports (Reviewers Only) ---
    @annotation_bp.route('/reports/pending', methods=['GET'])
    def get_pending_reports():
        """
        Get all pending reports for review.
        Requires: reviewer privileges
        """
        current_user = mwo_auth.get_current_user(True)
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        username = current_user[0]
        
        if not is_reviewer(username):
            return jsonify({"error": "Reviewer privileges required"}), 403
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT r.id, r.annotation_id, r.reported_by, r.report_reason, r.reported_at,
                       a.project, a.timestamp, a.peak_type, a.description, a.relevant_link
                FROM annotation_reports r
                JOIN peak_annotations a ON r.annotation_id = a.id
                WHERE r.status = 'pending'
                ORDER BY r.reported_at ASC
                """
            )
            results = cursor.fetchall()
            conn.close()
            
            reports = []
            for row in results:
                reports.append({
                    "report_id": row[0],
                    "annotation_id": row[1],
                    "reported_by": row[2],
                    "report_reason": row[3],
                    "reported_at": row[4].isoformat() if row[4] else None,
                    "annotation": {
                        "project": row[5],
                        "timestamp": row[6].isoformat() if row[6] else None,
                        "peak_type": row[7],
                        "description": row[8],
                        "relevant_link": row[9]
                    }
                })
            
            return jsonify({"reports": reports}), 200
            
        except Exception as e:
            logger.error(f"Error fetching pending reports: {e}")
            return jsonify({"error": "Failed to fetch reports"}), 500

    # --- Review Report ---
    @annotation_bp.route('/reports/review', methods=['POST'])
    def review_report():
        """
        Review a report and take action.
        Requires: reviewer privileges
        """
        current_user = mwo_auth.get_current_user(True)
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        username = current_user[0]
        
        if not is_reviewer(username):
            return jsonify({"error": "Reviewer privileges required"}), 403
        
        data = request.json
        report_id = data.get('report_id')
        action = data.get('action')  # 'dismiss', 'edit', 'remove'
        
        if not (report_id and action):
            return jsonify({"error": "Missing required fields"}), 400
        
        if action not in ['dismiss', 'edit', 'remove']:
            return jsonify({"error": "Invalid action"}), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get report details
            cursor.execute(
                """
                SELECT annotation_id, status FROM annotation_reports WHERE id = %s
                """,
                (report_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return jsonify({"error": "Report not found"}), 404
            
            annotation_id, report_status = result
            
            if report_status != 'pending':
                conn.close()
                return jsonify({"error": "Report already reviewed"}), 409
            
            if action == 'dismiss':
                # Dismiss report, no action on annotation
                cursor.execute(
                    """
                    UPDATE annotation_reports
                    SET status = 'reviewed', reviewed_by = %s, 
                        reviewed_at = %s, action_taken = 'no_action'
                    WHERE id = %s
                    """,
                    (username, datetime.now(), report_id)
                )
                message = "Report dismissed"
                
            elif action == 'edit':
                # Edit annotation
                edited_description = data.get('edited_description', '').strip()
                edited_link = data.get('edited_link', '').strip() or None
                
                if not edited_description:
                    conn.close()
                    return jsonify({"error": "Edited description required"}), 400
                
                cursor.execute(
                    """
                    UPDATE peak_annotations
                    SET description = %s, relevant_link = %s
                    WHERE id = %s
                    """,
                    (edited_description, edited_link, annotation_id)
                )
                
                cursor.execute(
                    """
                    UPDATE annotation_reports
                    SET status = 'reviewed', reviewed_by = %s, 
                        reviewed_at = %s, action_taken = 'edited'
                    WHERE id = %s
                    """,
                    (username, datetime.now(), report_id)
                )
                
                log_annotation_action(
                    annotation_id, 'report_action', username,
                    f"Edited annotation based on report #{report_id}",
                    request.remote_addr, request.headers.get('User-Agent')
                )
                
                message = "Annotation edited"
                
            elif action == 'remove':
                # Remove annotation (set invisible)
                cursor.execute(
                    """
                    UPDATE peak_annotations
                    SET is_visible = FALSE
                    WHERE id = %s
                    """,
                    (annotation_id,)
                )
                
                cursor.execute(
                    """
                    UPDATE annotation_reports
                    SET status = 'reviewed', reviewed_by = %s, 
                        reviewed_at = %s, action_taken = 'removed'
                    WHERE id = %s
                    """,
                    (username, datetime.now(), report_id)
                )
                
                log_annotation_action(
                    annotation_id, 'report_action', username,
                    f"Removed annotation based on report #{report_id}",
                    request.remote_addr, request.headers.get('User-Agent')
                )
                
                message = "Annotation removed"
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "message": message}), 200
            
        except Exception as e:
            logger.error(f"Error reviewing report: {e}")
            return jsonify({"error": "Failed to review report"}), 500

    # --- Get Review Stats (Reviewers Only) ---
    @annotation_bp.route('/stats', methods=['GET'])
    def get_review_stats():
        """
        Get statistics for reviewer dashboard.
        Requires: reviewer privileges
        """
        current_user = mwo_auth.get_current_user(True)
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        username = current_user[0]
        
        if not is_reviewer(username):
            return jsonify({"error": "Reviewer privileges required"}), 403
        
        try:
            pending_annotations = get_pending_annotations_count()
            pending_reports = get_pending_reports_count()
            
            return jsonify({
                "pending_annotations": pending_annotations,
                "pending_reports": pending_reports,
                "total_pending": pending_annotations + pending_reports
            }), 200
            
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return jsonify({"error": "Failed to fetch stats"}), 500

    return annotation_bp
