# Notification System for Detected Peaks

This document describes the opt-in notification system that alerts subscribed users when activity peaks are detected in their projects of interest.

## Overview

The notification system allows users to subscribe to specific Wikimedia projects and receive email notifications when significant activity spikes are detected. This implements the solution proposed in [Issue #35](https://github.com/indictechcom/community-activity-alerts/issues/35).

## Architecture

### Components

1. **User Subscriptions** (`user_subscriptions` table)
   - Stores user preferences for which projects they want to monitor
   - Supports filtering by notification type: `edit`, `editor`, or `both`

2. **Notification Logs** (`notification_logs` table)
   - Tracks all notification attempts (sent, failed, pending)
   - Prevents duplicate notifications for the same peak

3. **Notification Manager** (`backend/notification/notification_manager.py`)
   - Fetches new peaks from existing `community_alerts` and `editor_alerts` tables
   - Matches peaks with subscribed users
   - Sends notifications via MediaWiki API

4. **MediaWiki Email Service** (`backend/notification/mediawiki_email_service.py`)
   - Handles authentication with MediaWiki API
   - Sends emails using the `API:Emailuser` endpoint

5. **Monthly Cron Job** (`cron/monthly_peak_detection.py`)
   - Runs monthly to process and notify about detected peaks
   - Checks peaks from the last 31 days

## Database Schema

### user_subscriptions
```sql
- id: INT (Primary Key)
- username: VARCHAR(255) - Wikimedia username
- project: VARCHAR(255) - Project URL (e.g., 'hi.wikibooks.org')
- notification_type: ENUM('edit', 'editor', 'both')
- is_active: BOOLEAN
- created_at: DATETIME
- updated_at: DATETIME
```

### notification_logs
```sql
- id: INT (Primary Key)
- username: VARCHAR(255)
- project: VARCHAR(255)
- peak_type: ENUM('edit', 'editor')
- peak_timestamp: DATETIME
- notification_sent_at: DATETIME
- notification_status: ENUM('sent', 'failed', 'pending')
- error_message: TEXT (nullable)
```

## API Endpoints

All endpoints require authentication via MediaWiki OAuth.

### Subscribe to Project
```
POST /api/subscriptions/subscribe
Body: {
  "project": "hi.wikibooks.org",
  "notification_type": "both"  // 'edit', 'editor', or 'both'
}
```

### Unsubscribe from Project
```
POST /api/subscriptions/unsubscribe
Body: {
  "project": "hi.wikibooks.org"
}
```

### Get User's Subscriptions
```
GET /api/subscriptions/my-subscriptions
Response: {
  "success": true,
  "subscriptions": [
    {
      "project": "hi.wikibooks.org",
      "notification_type": "both",
      "is_active": true,
      "created_at": "2026-02-01T12:00:00",
      "updated_at": "2026-02-01T12:00:00"
    }
  ]
}
```

### Check Subscription Status
```
GET /api/subscriptions/check-subscription?project=hi.wikibooks.org
Response: {
  "subscribed": true,
  "notification_type": "both"
}
```

### Update Notification Type
```
PUT /api/subscriptions/update-notification-type
Body: {
  "project": "hi.wikibooks.org",
  "notification_type": "edit"
}
```

## Setup Instructions

### 1. Database Migration

Run the migration to create the necessary tables:

```bash
cd backend
python migrate.py
```

This will apply `migrations/002_user_subscriptions.sql`.

### 2. Configure Bot Credentials

Add the following to your `.env` file:

```env
# Bot credentials for email notifications (MediaWiki API)
BOT_USERNAME=YourBotUsername@YourBotName
BOT_PASSWORD=your_bot_password_here
```

**Note:** You need to create a bot account on Meta-Wiki and obtain bot credentials via [Special:BotPasswords](https://meta.wikimedia.org/wiki/Special:BotPasswords).

Required bot permissions:
- `High-volume editing`
- `Send email to other users`

### 3. Set Up Cron Job

Add the monthly notification job to your crontab:

```bash
# Run on the 1st of every month at 2:00 AM
0 2 1 * * cd /path/to/community-activity-alerts && python3 cron/monthly_peak_detection.py
```

Or for Toolforge:

```bash
toolforge jobs create monthly-notifications \
  --command "python3 /data/project/community-activity-alerts/cron/monthly_peak_detection.py" \
  --schedule "0 2 1 * *" \
  --image tf-python39
```

## How It Works

### Workflow

1. **Peak Detection** (Existing)
   - `backend/alerts/community_alerts.py` detects edit count peaks
   - `backend/alerts/editor_alerts.py` detects editor count peaks
   - Peaks are stored in `community_alerts` and `editor_alerts` tables

2. **User Subscription**
   - Users log in via MediaWiki OAuth
   - Users subscribe to projects via the frontend UI
   - Subscriptions are stored in `user_subscriptions` table

3. **Monthly Notification Job**
   - Cron job runs monthly
   - Fetches peaks from the last 31 days
   - For each peak:
     - Checks if already notified (via `notification_logs`)
     - Finds subscribed users for that project
     - Sends email notifications via MediaWiki API
     - Logs notification status

4. **Email Notification**
   - Uses MediaWiki `API:Emailuser` endpoint
   - Sends formatted email with peak details
   - Includes link to dashboard for more information

### Email Template

```
Subject: Community Activity Alert: Peak detected in {project}

Hello {username},

A significant activity peak has been detected in the {project} project 
that you are subscribed to:

Peak Type: Edit/Editor
Date: 2026-01-15
Value: 1500
Percentage Increase: 45.2%

This represents a notable increase in community activity. You may want 
to investigate this spike and consider adding an annotation to help 
document what caused this increase.

Visit the Community Activity Alerts dashboard to view more details and 
add annotations:
https://community-activity-alerts.toolforge.org/

To manage your notification preferences, visit your subscription 
settings in the dashboard.

---
This is an automated notification from the Community Activity Alerts tool.
```

## Testing

### Manual Testing

1. Subscribe to a project with known peaks:
```bash
curl -X POST http://localhost:5000/api/subscriptions/subscribe \
  -H "Content-Type: application/json" \
  -d '{"project": "hi.wikibooks.org", "notification_type": "both"}' \
  --cookie "session=your_session_cookie"
```

2. Run the notification job manually:
```bash
cd cron
python3 monthly_peak_detection.py
```

3. Check logs:
```bash
tail -f cron/notification.log
```

### Verify Database

```sql
-- Check subscriptions
SELECT * FROM user_subscriptions;

-- Check notification logs
SELECT * FROM notification_logs ORDER BY notification_sent_at DESC LIMIT 10;

-- Check recent peaks
SELECT * FROM community_alerts WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 31 DAY);
SELECT * FROM editor_alerts WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 31 DAY);
```

## Troubleshooting

### No Notifications Sent

1. **Check bot credentials**: Verify `BOT_USERNAME` and `BOT_PASSWORD` in `.env`
2. **Check bot permissions**: Ensure bot has email permissions on Meta-Wiki
3. **Check subscriptions**: Verify users are subscribed to projects with peaks
4. **Check logs**: Review `cron/notification.log` for errors

### Duplicate Notifications

The system prevents duplicates by checking `notification_logs` before sending. If you receive duplicates:

1. Check the `idx_peak_lookup` index exists on `notification_logs`
2. Verify the `check_if_already_notified()` method is working

### Authentication Errors

If MediaWiki API authentication fails:

1. Verify bot password is correct and not expired
2. Check bot account is not blocked
3. Ensure bot has necessary permissions
4. Review MediaWiki API error messages in logs

## Future Enhancements

- [ ] Add frontend UI for subscription management
- [ ] Support for email digest (weekly/monthly summaries)
- [ ] Notification preferences (threshold customization)
- [ ] Support for User Talk page notifications (alternative to email)
- [ ] Integration with MassMessage for Village Pump posts
- [ ] Notification history view in dashboard

## Related Files

- `backend/subscription/routes.py` - Subscription API endpoints
- `backend/notification/mediawiki_email_service.py` - Email service
- `backend/notification/notification_manager.py` - Notification logic
- `backend/migrations/002_user_subscriptions.sql` - Database schema
- `cron/monthly_peak_detection.py` - Monthly notification job
- `backend/sample.env` - Environment configuration template
