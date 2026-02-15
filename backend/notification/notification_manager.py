import logging
from datetime import datetime, timedelta
from config import get_db_connection
from notification.mediawiki_email_service import MediaWikiEmailService

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.email_service = MediaWikiEmailService()
    
    def get_subscribed_users_for_peak(self, project, peak_type):
        """Get users watching this project either directly or via language watch"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Extract language code from project (e.g., 'en' from 'en.wikipedia.org')
            language_code = project.split('.')[0] if '.' in project else None
            
            # Get users watching this specific project
            cursor.execute("""
                SELECT DISTINCT username
                FROM user_project_watchlist
                WHERE project = %s 
                AND is_active = TRUE
                AND (notification_type = %s OR notification_type = 'both')
            """, (project, peak_type))
            
            users = set(row[0] for row in cursor.fetchall())
            
            # Get users watching this language (if language code exists)
            if language_code:
                cursor.execute("""
                    SELECT DISTINCT username
                    FROM user_language_watchlist
                    WHERE language_code = %s 
                    AND is_active = TRUE
                    AND (notification_type = %s OR notification_type = 'both')
                """, (language_code, peak_type))
                
                language_users = set(row[0] for row in cursor.fetchall())
                users.update(language_users)
            
            return list(users)
            
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
    
    def check_if_already_notified(self, project, peak_timestamp, peak_type):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM notification_logs
                WHERE project = %s 
                AND peak_timestamp = %s 
                AND peak_type = %s
                AND notification_status = 'sent'
            """, (project, peak_timestamp, peak_type))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking notification status: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def send_notifications_for_peak(self, peak):
        project = peak['project']
        peak_type = peak['peak_type']
        
        if self.check_if_already_notified(project, peak['timestamp'], peak_type):
            logger.info(f"Peak already notified: {project} at {peak['timestamp']}")
            return {"sent": 0, "failed": 0, "skipped": True}
        
        subscribed_users = self.get_subscribed_users_for_peak(project, peak_type)
        
        if not subscribed_users:
            logger.info(f"No subscribed users for {project} ({peak_type} peaks)")
            return {"sent": 0, "failed": 0, "skipped": False}
        
        logger.info(f"Sending notifications to {len(subscribed_users)} users for {project}")
        
        sent_count = 0
        failed_count = 0
        
        for username in subscribed_users:
            try:
                result = self.email_service.send_peak_notification(
                    username=username,
                    project=project,
                    peak_data={
                        'peak_type': peak_type,
                        'timestamp': peak['timestamp'].strftime('%Y-%m-%d') if hasattr(peak['timestamp'], 'strftime') else str(peak['timestamp']),
                        'value': peak['value'],
                        'percentage_difference': peak['percentage_difference']
                    }
                )
                
                if result.get('success'):
                    self.log_notification(
                        username, project, peak_type, peak['timestamp'], 'sent'
                    )
                    sent_count += 1
                else:
                    error_msg = result.get('error', 'Unknown error')
                    self.log_notification(
                        username, project, peak_type, peak['timestamp'], 'failed', error_msg
                    )
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending notification to {username}: {e}")
                self.log_notification(
                    username, project, peak_type, peak['timestamp'], 'failed', str(e)
                )
                failed_count += 1
        
        return {"sent": sent_count, "failed": failed_count, "skipped": False}
    
    def get_new_peaks_from_alerts(self, days_back=31):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
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
        
        logger.info(f"Processing {len(peaks)} peaks")
        
        # Group peaks by user
        user_peaks = {}
        for peak in peaks:
            # Skip if already notified
            if self.check_if_already_notified(peak['project'], peak['timestamp'], peak['peak_type']):
                logger.info(f"Peak already notified: {peak['project']} at {peak['timestamp']}")
                continue
            
            # Get subscribed users for this peak
            subscribed_users = self.get_subscribed_users_for_peak(peak['project'], peak['peak_type'])
            
            for username in subscribed_users:
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
                "total_skipped": len(peaks)
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
                            username, peak['project'], peak['peak_type'], 
                            peak['timestamp'], 'sent'
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
            "total_skipped": 0
        }
