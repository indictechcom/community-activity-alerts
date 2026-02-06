import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MediaWikiEmailService:
    def __init__(self):
        self.api_url = "https://meta.wikimedia.org/w/api.php"
        self.bot_username = os.getenv("BOT_USERNAME")
        self.bot_password = os.getenv("BOT_PASSWORD")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Community Activity Alerts/1.0 (https://community-activity-alerts.toolforge.org; contact@toolforge.org)'
        })
        self.csrf_token = None
        self.session.timeout = 10  # Set a timeout for all requests to prevent hanging

        if not self.bot_username or not self.bot_password:
            logger.error("Bot credentials are not set in environment variables")
            raise ValueError("Bot credentials are required for MediaWikiEmailService")
        
    def login(self):
        try:
            params_0 = {
                "action": "query",
                "meta": "tokens",
                "type": "login",
                "format": "json"
            }
            
            response = self.session.get(url=self.api_url, params=params_0)
            data = response.json()
            login_token = data['query']['tokens']['logintoken']
            
            params_1 = {
                "action": "login",
                "lgname": self.bot_username,
                "lgpassword": self.bot_password,
                "lgtoken": login_token,
                "format": "json"
            }
            
            response = self.session.post(self.api_url, data=params_1)
            result = response.json()
            
            if result.get('login', {}).get('result') == 'Success':
                logger.info("Successfully logged in to MediaWiki API")
                return True
            else:
                logger.error(f"Login failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error during MediaWiki login: {e}")
            return False
    
    def get_csrf_token(self):
        try:
            params = {
                "action": "query",
                "meta": "tokens",
                "format": "json"
            }
            
            response = self.session.get(url=self.api_url, params=params)
            data = response.json()
            self.csrf_token = data['query']['tokens']['csrftoken']
            return self.csrf_token
            
        except Exception as e:
            logger.error(f"Error getting CSRF token: {e}")
            return None

    def send_email(self, target_username, subject, text):
            # Initial authentication and token retrieval if not present
            if not self.csrf_token:
                if not self.login():
                    return {"success": False, "error": "Failed to authenticate"}
                
                if not self.get_csrf_token():
                    return {"success": False, "error": "Failed to get CSRF token"}
            
            try:
                params = {
                    "action": "emailuser",
                    "target": target_username,
                    "subject": subject,
                    "text": text,
                    "token": self.csrf_token,
                    "format": "json"
                }
                
                # Request includes a 10-second timeout
                response = self.session.post(self.api_url, data=params, timeout=10)
                result = response.json()

                # Handle token expiration: 'badtoken' error from MediaWiki API
                if 'error' in result and result['error'].get('code') == 'badtoken':
                    logger.warning("CSRF token expired. Attempting to refresh and retry...")
                    self.csrf_token = None  # Reset local token to trigger refresh
                    return self.send_email(target_username, subject, text) # Retry once
                
                if 'emailuser' in result and result['emailuser'].get('result') == 'Success':
                    logger.info(f"Successfully sent email to {target_username}")
                    return {"success": True, "message": "Email sent successfully"}
                else:
                    error_msg = result.get('error', {}).get('info', 'Unknown error')
                    logger.error(f"Failed to send email to {target_username}: {error_msg}")
                    return {"success": False, "error": error_msg}
                    
            except Exception as e:
                logger.error(f"Error sending email to {target_username}: {e}")
                return {"success": False, "error": str(e)}

    def send_peak_notification(self, username, project, peak_data):
        peak_type = peak_data.get('peak_type', 'activity')
        timestamp = peak_data.get('timestamp', 'Unknown')
        value = peak_data.get('value', 0)
        percentage_diff = peak_data.get('percentage_difference', 0)
        
        subject = f"Community Activity Alert: Peak detected in {project}"
        
        text = f"""Hello {username},

A significant activity peak has been detected in the {project} project that you are subscribed to:

Peak Type: {peak_type.capitalize()}
Date: {timestamp}
Value: {value}
Percentage Increase: {percentage_diff:.1f}%

This represents a notable increase in community activity. You may want to investigate this spike and consider adding an annotation to help document what caused this increase.

Visit the Community Activity Alerts dashboard to view more details and add annotations:
https://community-activity-alerts.toolforge.org/

To manage your notification preferences, visit your subscription settings in the dashboard.

---
This is an automated notification from the Community Activity Alerts tool.
"""
        
        return self.send_email(username, subject, text)
    
    def send_batched_peak_notifications(self, username, peaks):
        """
        Send a single email with multiple peaks formatted as a table.
        
        Args:
            username: The username to notify
            peaks: List of peak dictionaries
            
        Returns:
            dict: Response with success status and message
        """
        if not peaks:
            return {"success": False, "error": "No peaks provided"}
        
        # Sort peaks by percentage difference (highest first)
        sorted_peaks = sorted(peaks, key=lambda x: x.get('percentage_difference', 0), reverse=True)
        
        # Count peaks by type
        edit_peaks = [p for p in sorted_peaks if p['peak_type'] == 'edit']
        editor_peaks = [p for p in sorted_peaks if p['peak_type'] == 'editor']
        
        subject = f"Community Activity Alerts: {len(sorted_peaks)} peak{'s' if len(sorted_peaks) > 1 else ''} detected"
        
        # Build wiki-style table
        text = f"""Hello {username},

{len(sorted_peaks)} significant activity peak{'s have' if len(sorted_peaks) > 1 else ' has'} been detected in projects you are subscribed to:

"""
        
        if edit_peaks:
            text += f"\n━━━ Edit Count Peaks ({len(edit_peaks)}) ━━━\n\n"
            
            for i, peak in enumerate(edit_peaks, 1):
                timestamp = peak['timestamp'].strftime('%Y-%m-%d') if hasattr(peak['timestamp'], 'strftime') else str(peak['timestamp'])
                text += f"{i}. {peak['project']}\n"
                text += f"   • Date: {timestamp}\n"
                text += f"   • Edits: {peak['value']:,}\n"
                text += f"   • Increase: +{peak['percentage_difference']:.1f}% (baseline: {peak['rolling_mean']:.0f})\n\n"
        
        if editor_peaks:
            text += f"\n━━━ Editor Count Peaks ({len(editor_peaks)}) ━━━\n\n"
            
            for i, peak in enumerate(editor_peaks, 1):
                timestamp = peak['timestamp'].strftime('%Y-%m-%d') if hasattr(peak['timestamp'], 'strftime') else str(peak['timestamp'])
                text += f"{i}. {peak['project']}\n"
                text += f"   • Date: {timestamp}\n"
                text += f"   • Editors: {peak['value']:,}\n"
                text += f"   • Increase: +{peak['percentage_difference']:.1f}% (baseline: {peak['rolling_mean']:.0f})\n\n"
        
        text += """

These represent notable increases in community activity. You may want to investigate these spikes and consider adding annotations to help document what caused these increases.

Visit the Community Activity Alerts dashboard to view more details and add annotations:
https://community-activity-alerts.toolforge.org/

To manage your notification preferences, visit your subscription settings in the dashboard.

---
This is an automated notification from the Community Activity Alerts tool.
"""
        
        return self.send_email(username, subject, text)
    
    def send_bulk_notifications(self, notifications):
        if not self.login():
            return {
                "success": False,
                "error": "Failed to authenticate",
                "sent": 0,
                "failed": len(notifications)
            }
        
        if not self.get_csrf_token():
            return {
                "success": False,
                "error": "Failed to get CSRF token",
                "sent": 0,
                "failed": len(notifications)
            }
        
        sent_count = 0
        failed_count = 0
        failed_users = []
        
        for notification in notifications:
            result = self.send_peak_notification(
                notification['username'],
                notification['project'],
                notification['peak_data']
            )
            
            if result.get('success'):
                sent_count += 1
            else:
                failed_count += 1
                failed_users.append({
                    "username": notification['username'],
                    "error": result.get('error')
                })
        
        return {
            "success": True,
            "sent": sent_count,
            "failed": failed_count,
            "failed_users": failed_users
        }
