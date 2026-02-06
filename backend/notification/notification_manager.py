import logging
from datetime import datetime, timedelta, timezone
from backend.config import get_db_connection
from backend.notification.mediawiki_email_service import MediaWikiEmailService

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.email_service = MediaWikiEmailService()
    
    def get_subscribed_users_for_peak(self, project, peak_type):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT username
                FROM user_subscriptions
                WHERE project = %s 
                AND is_active = TRUE
                AND (notification_type = %s OR notification_type = 'both')
            """, (project, peak_type))
            
            users = [row[0] for row in cursor.fetchall()]
            return users
            
        except Exception as e:
            logger.error(f"Error fetching subscribed users for {project}: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def log_notification(self, username, project, peak_type, peak_timestamp, status, error_message=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO notification_logs
                (username, project, peak_type, peak_timestamp, notification_status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, project, peak_type, peak_timestamp, status, error_message))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    def get_already_notified_set(self, days_back=31):
            """Fetches all successfully sent notifications in the last X days to avoid redundant DB calls"""
            conn = get_db_connection()
            cursor = conn.cursor()
            notified_set = set()
            
            try:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
                cursor.execute("""
                    SELECT project, peak_timestamp, peak_type, username
                    FROM notification_logs
                    WHERE notification_status = 'sent'
                    AND peak_timestamp >= %s
                """, (cutoff_date,))
                
                for row in cursor.fetchall():
                    # Store as a tuple key: (project, timestamp, type, username)
                    notified_set.add((row[0], row[1], row[2], row[3]))
                    
                return notified_set
            except Exception as e:
                logger.error(f"Error fetching notified set: {e}")
                return notified_set
            finally:
                cursor.close()
                conn.close()

    def get_new_peaks_from_alerts(self, days_back=31):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            cursor.execute("""
                SELECT project, timestamp, edit_count as value, 
                       rolling_mean, threshold, percentage_difference
                FROM community_alerts
                WHERE timestamp >= %s
                ORDER BY timestamp DESC
            """, (cutoff_date,))
            
            edit_peaks = []
            for row in cursor.fetchall():
                edit_peaks.append({
                    'project': row[0],
                    'timestamp': row[1],
                    'peak_type': 'edit',
                    'value': row[2],
                    'rolling_mean': row[3],
                    'threshold': row[4],
                    'percentage_difference': row[5]
                })
            
            cursor.execute("""
                SELECT project, timestamp, editor_count as value,
                       rolling_mean, threshold, percentage_difference
                FROM editor_alerts
                WHERE timestamp >= %s
                ORDER BY timestamp DESC
            """, (cutoff_date,))
            
            editor_peaks = []
            for row in cursor.fetchall():
                editor_peaks.append({
                    'project': row[0],
                    'timestamp': row[1],
                    'peak_type': 'editor',
                    'value': row[2],
                    'rolling_mean': row[3],
                    'threshold': row[4],
                    'percentage_difference': row[5]
                })
            
            logger.info(f"Found {len(edit_peaks)} edit peaks and {len(editor_peaks)} editor peaks from last {days_back} days")
            return edit_peaks + editor_peaks
            
        except Exception as e:
            logger.error(f"Error fetching peaks from alert tables: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def process_notifications(self, days_back=31):
        logger.info(f"Starting notification processing for peaks from last {days_back} days")
        
        peaks = self.get_new_peaks_from_alerts(days_back)
        
        if not peaks:
            logger.info("No peaks found to notify")
            return {
                "success": True,
                "total_peaks": 0,
                "total_sent": 0,
                "total_failed": 0,
                "total_skipped": 0
            }
        
        # Optimization: Fetch all 'sent' logs once
        already_notified = self.get_already_notified_set(days_back)
        
        logger.info(f"Processing {len(peaks)} peaks")
        
        # Group peaks by user
        user_peaks = {}
        total_skipped = 0
        for peak in peaks:
            subscribed_users = self.get_subscribed_users_for_peak(peak['project'], peak['peak_type'])
            
            # Instead of checking each notification individually, we check if the user has already been notified for this peak using the in-memory set
            for username in subscribed_users:
                # Check against the in-memory set instead of the database
                notification_key = (peak['project'], peak['timestamp'], peak['peak_type'], username)
                
                if notification_key in already_notified:
                    total_skipped += 1
                    continue
                
                if username not in user_peaks:
                    user_peaks[username] = []
                user_peaks[username].append(peak)
        
        if not user_peaks:
            logger.info("No users to notify")
            return {
                "success": True,
                "total_peaks": len(peaks),
                "total_sent": 0,
                "total_failed": 0,
                "total_skipped": total_skipped
            }
        
        # Send batched notifications to each user
        total_sent = 0
        total_failed = 0
        
        for username, user_peak_list in user_peaks.items():
            logger.info(f"Sending notification to {username} for {len(user_peak_list)} peaks")
            
            try:
                result = self.email_service.send_batched_peak_notifications(
                    username=username,
                    peaks=user_peak_list
                )
                
                if result.get('success'):
                    # Log each peak notification as sent
                    for peak in user_peak_list:
                        self.log_notification(
                            username,
                            peak['project'],
                            peak['peak_type'], 
                            peak['timestamp'],
                            'sent'
                        )
                    total_sent += 1
                    logger.info(f"Successfully sent notification to {username}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    # Log each peak notification as failed
                    for peak in user_peak_list:
                        self.log_notification(
                            username, peak['project'], peak['peak_type'],
                            peak['timestamp'], 'failed', error_msg
                        )
                    total_failed += 1
                    logger.error(f"Failed to send notification to {username}: {error_msg}")
                    
            except Exception as e:
                logger.error(f"Error sending notification to {username}: {e}")
                for peak in user_peak_list:
                    self.log_notification(
                        username, peak['project'], peak['peak_type'],
                        peak['timestamp'], 'failed', str(e)
                    )
                total_failed += 1
        
        logger.info(f"Notification processing complete. Users notified: {total_sent}, Failed: {total_failed}")
        
        return {
            "success": True,
            "total_peaks": len(peaks),
            "total_sent": total_sent,
            "total_failed": total_failed,
            "total_skipped": total_skipped
        }
