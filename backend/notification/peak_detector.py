import pandas as pd
import logging
from datetime import datetime, timedelta
from config import get_db_connection

logger = logging.getLogger(__name__)

class PeakDetector:
    def __init__(self, threshold_percentage=0.30):
        self.threshold_percentage = threshold_percentage
    
    def find_peaks_rolling_3_years(self, df, value_column='edits'):
        df = df.sort_values("timestamp").reset_index(drop=True)
        peaks = []

        for i in range(len(df)):
            t_i = df.at[i, "timestamp"]
            value_i = df.at[i, value_column]

            window = df[
                (df["timestamp"] >= t_i - pd.DateOffset(years=3)) & (df["timestamp"] <= t_i)
            ]
            if window.empty:
                continue

            rolling_mean = window[value_column].mean()
            threshold = rolling_mean * (1 + self.threshold_percentage)
            pct_diff = ((value_i - rolling_mean) / rolling_mean) * 100

            if value_i >= threshold:
                peaks.append({
                    "timestamp": t_i,
                    "value": value_i,
                    "rolling_mean": rolling_mean,
                    "threshold": threshold,
                    "percentage_difference": pct_diff,
                })

        return peaks
    
    def detect_new_peaks_for_project(self, project, peak_type='edit'):
        conn = get_db_connection()
        
        try:
            if peak_type == 'edit':
                table = 'edit_counts'
                value_column = 'edit_count'
            else:
                table = 'editor_counts'
                value_column = 'editor_count'
            
            query = f"""
                SELECT timestamp, {value_column} as value
                FROM {table}
                WHERE project = %s
                ORDER BY timestamp ASC
            """
            
            df = pd.read_sql(query, conn, params=(project,))
            
            if df.empty:
                return []
            
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.rename(columns={'value': 'edits'})
            
            peaks = self.find_peaks_rolling_3_years(df, value_column='edits')
            
            cursor = conn.cursor()
            new_peaks = []
            
            for peak in peaks:
                cursor.execute("""
                    SELECT id FROM detected_peaks
                    WHERE project = %s AND timestamp = %s AND peak_type = %s
                """, (project, peak['timestamp'], peak_type))
                
                if not cursor.fetchone():
                    new_peaks.append({
                        'project': project,
                        'timestamp': peak['timestamp'],
                        'peak_type': peak_type,
                        'value': int(peak['value']),
                        'rolling_mean': float(peak['rolling_mean']),
                        'threshold': float(peak['threshold']),
                        'percentage_difference': float(peak['percentage_difference'])
                    })
            
            cursor.close()
            return new_peaks
            
        except Exception as e:
            logger.error(f"Error detecting peaks for project {project}: {e}")
            return []
        finally:
            conn.close()
    
    def detect_all_new_peaks(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT DISTINCT project FROM edit_counts")
            projects = [row[0] for row in cursor.fetchall()]
            
            all_edit_peaks = []
            all_editor_peaks = []
            
            for project in projects:
                logger.info(f"Detecting peaks for project: {project}")
                
                edit_peaks = self.detect_new_peaks_for_project(project, 'edit')
                editor_peaks = self.detect_new_peaks_for_project(project, 'editor')
                
                all_edit_peaks.extend(edit_peaks)
                all_editor_peaks.extend(editor_peaks)
            
            logger.info(f"Detected {len(all_edit_peaks)} new edit peaks and {len(all_editor_peaks)} new editor peaks")
            
            return {
                'edit_peaks': all_edit_peaks,
                'editor_peaks': all_editor_peaks
            }
            
        except Exception as e:
            logger.error(f"Error detecting all peaks: {e}")
            return {'edit_peaks': [], 'editor_peaks': []}
        finally:
            cursor.close()
            conn.close()
    
    def store_detected_peaks(self, peaks):
        if not peaks:
            return 0
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            stored_count = 0
            for peak in peaks:
                cursor.execute("""
                    INSERT INTO detected_peaks 
                    (project, timestamp, peak_type, value, rolling_mean, threshold, 
                     percentage_difference, notification_sent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
                    ON DUPLICATE KEY UPDATE
                        value = VALUES(value),
                        rolling_mean = VALUES(rolling_mean),
                        threshold = VALUES(threshold),
                        percentage_difference = VALUES(percentage_difference)
                """, (
                    peak['project'],
                    peak['timestamp'],
                    peak['peak_type'],
                    peak['value'],
                    peak['rolling_mean'],
                    peak['threshold'],
                    peak['percentage_difference']
                ))
                stored_count += 1
            
            conn.commit()
            logger.info(f"Stored {stored_count} peaks in database")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing peaks: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def get_peaks_pending_notification(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, project, timestamp, peak_type, value, 
                       rolling_mean, threshold, percentage_difference
                FROM detected_peaks
                WHERE notification_sent = FALSE
                ORDER BY detected_at DESC
            """)
            
            peaks = []
            for row in cursor.fetchall():
                peaks.append({
                    'id': row[0],
                    'project': row[1],
                    'timestamp': row[2],
                    'peak_type': row[3],
                    'value': row[4],
                    'rolling_mean': row[5],
                    'threshold': row[6],
                    'percentage_difference': row[7]
                })
            
            return peaks
            
        except Exception as e:
            logger.error(f"Error fetching pending peaks: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def mark_peak_as_notified(self, peak_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE detected_peaks
                SET notification_sent = TRUE
                WHERE id = %s
            """, (peak_id,))
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error marking peak {peak_id} as notified: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
