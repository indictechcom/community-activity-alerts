# Annotation System Documentation

## Overview

The annotation system allows users to add contextual information to detected peak activity points (spikes in edit counts or editor counts). This system includes a review workflow to prevent spam and ensure quality.

## Features

### For Regular Users
- **Add Annotations**: Provide context for detected peaks with a description (max 50 words) and optional link
- **View Annotations**: See approved annotations on peak activity points
- **Report Annotations**: Flag inappropriate or inaccurate annotations for review

### For Reviewers
- **Review Submissions**: Approve, edit, or reject annotation submissions
- **Manage Reports**: Review and take action on reported annotations
- **Dashboard**: Centralized view of all pending items

## Architecture

### Database Schema

The system uses 5 main tables:

1. **peak_annotations**: Stores all annotation submissions
2. **annotation_reviews**: Tracks reviewer actions on annotations
3. **annotation_reports**: Stores user reports on approved annotations
4. **annotation_audit_log**: Comprehensive logging of all actions
5. **annotation_reviewers**: Allowlist of authorized reviewers

### Backend Components

- **`annotation_utils.py`**: Utility functions for edit count validation, reviewer checks, and notifications
- **`annotation_routes.py`**: Flask blueprint with all API endpoints
- **`annotations_schema.sql`**: Database schema definition

### Frontend Components

- **`AnnotationModal.vue`**: Modal for submitting new annotations
- **`ReportModal.vue`**: Modal for reporting existing annotations
- **`ReviewAnnotationModal.vue`**: Modal for reviewing annotation submissions
- **`ReviewReportModal.vue`**: Modal for reviewing reports
- **`ReviewerDashboard.vue`**: Dashboard view for reviewers
- **`PeaksTable.vue`**: Updated to display and manage annotations

## Setup Instructions

### 1. Database Setup

Run the schema creation script:

```bash
mysql -u your_user -p community_alerts < backend/annotations_schema.sql
```

Or manually execute the SQL in `backend/annotations_schema.sql`.

### 2. Add Reviewers

Add authorized reviewers to the allowlist:

```sql
INSERT INTO annotation_reviewers (username, region, added_by, notes)
VALUES 
  ('YourUsername', 'South Asia', 'system', 'Tool maintainer'),
  ('Reviewer1', 'ESEAP', 'YourUsername', 'Regional volunteer'),
  ('Reviewer2', 'LATAM', 'YourUsername', 'Regional volunteer');
```

### 3. Backend Configuration

The annotation routes are automatically integrated into the Flask app. No additional configuration needed.

### 4. Frontend Integration

Update your view components to pass the `project` prop to `PeaksTable`:

```vue
<PeaksTable :peaks="peaks" :project="selectedProject" />
```

Add the reviewer dashboard route to your router:

```javascript
import ReviewerDashboard from '@/views/ReviewerDashboard.vue'

{
  path: '/reviewer',
  name: 'ReviewerDashboard',
  component: ReviewerDashboard
}
```

## User Workflows

### Submitting an Annotation

1. User views a peak in the activity chart
2. Clicks "Add annotation" button on the peak
3. Fills in description (max 50 words) and optional link
4. System validates:
   - User is logged in
   - User has ≥1000 global edits
   - Description meets requirements
5. Annotation is submitted for review
6. Reviewers are notified via email

### Reviewing an Annotation

1. Reviewer accesses the dashboard at `/reviewer`
2. Views pending annotations in the "Pending Annotations" tab
3. Reviews the annotation content and context
4. Takes one of three actions:
   - **Approve**: Annotation is published as-is
   - **Edit & Approve**: Modify description/link before publishing
   - **Reject**: Annotation is not published
5. Action is logged and submitter is notified (future enhancement)

### Reporting an Annotation

1. User sees a problematic annotation on a peak
2. Clicks "Report" button
3. Provides reason for the report
4. Report is submitted to reviewers
5. Reviewers are notified

### Reviewing a Report

1. Reviewer accesses the "Pending Reports" tab
2. Reviews the report reason and current annotation
3. Takes one of three actions:
   - **Dismiss Report**: No action needed, report is unfounded
   - **Edit Annotation**: Modify the annotation to address concerns
   - **Remove Annotation**: Hide the annotation from view
4. Action is logged

## API Endpoints

### Public Endpoints

- `GET /api/annotations/get` - Get approved annotation for a peak
  - Params: `project`, `timestamp`, `peak_type`

### Authenticated Endpoints

- `POST /api/annotations/submit` - Submit new annotation
- `POST /api/annotations/report` - Report an annotation

### Reviewer Endpoints

- `GET /api/annotations/pending` - Get pending annotations
- `POST /api/annotations/review` - Review an annotation
- `GET /api/annotations/reports/pending` - Get pending reports
- `POST /api/annotations/reports/review` - Review a report
- `GET /api/annotations/stats` - Get review statistics

## Spam Prevention

### Edit Count Requirement
- Users must have ≥1000 global edits to submit annotations
- Checked via MediaWiki API at submission time

### Review Workflow
- All annotations must be approved before being visible
- Reviewers can edit content before approval
- Rejected annotations are not shown

### Reporting System
- Users can report problematic annotations
- Reports trigger reviewer notification
- Reviewers can remove or edit reported content

### Audit Logging
- All actions are logged with:
  - User, timestamp, action type
  - IP address and user agent
  - Detailed action information

## Reviewer Management

### Adding Reviewers

```sql
INSERT INTO annotation_reviewers (username, region, added_by, notes)
VALUES ('NewReviewer', 'CEE', 'AdminUsername', 'Volunteer from CEE region');
```

### Removing Reviewers

```sql
UPDATE annotation_reviewers 
SET is_active = FALSE 
WHERE username = 'ReviewerToRemove';
```

### Viewing Active Reviewers

```sql
SELECT username, region, added_at 
FROM annotation_reviewers 
WHERE is_active = TRUE;
```

## Email Notifications

The system uses the MediaWiki EmailUser API to notify reviewers. Current implementation logs notifications but doesn't send actual emails.

### To Enable Email Notifications

1. Set up OAuth credentials with `emailuser` permission
2. Update `annotation_utils.py` `send_reviewer_notification()` function
3. Implement OAuth flow for sending emails
4. Consider rate limiting to avoid spam

Example implementation:

```python
def send_reviewer_notification(subject, message_body):
    # Get OAuth credentials
    # For each active reviewer:
    #   - Make API call to emailuser endpoint
    #   - Handle rate limiting
    #   - Log success/failure
```

## Monitoring and Maintenance

### Check Pending Items

```sql
-- Pending annotations
SELECT COUNT(*) FROM peak_annotations WHERE status = 'pending';

-- Pending reports
SELECT COUNT(*) FROM annotation_reports WHERE status = 'pending';
```

### View Recent Activity

```sql
SELECT action_type, COUNT(*) as count, DATE(created_at) as date
FROM annotation_audit_log
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY action_type, DATE(created_at)
ORDER BY date DESC;
```

### Clean Up Old Logs

```sql
-- Archive logs older than 1 year
DELETE FROM annotation_audit_log 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
```

## Scaling Considerations

### Current Design (Low Volume)
- Estimated 10 annotations/month
- Simple review workflow
- Regional reviewers

### If Volume Increases
1. **Automated Pre-screening**
   - Use edit filters or machine learning
   - Flag suspicious submissions

2. **Community Review**
   - Allow community voting
   - Implement reputation system

3. **Specialized Reviewers**
   - Language-specific reviewers
   - Require community membership

4. **Rate Limiting**
   - Limit submissions per user per day
   - Implement cooldown periods

## Troubleshooting

### Annotations Not Appearing

1. Check if annotation is approved:
   ```sql
   SELECT * FROM peak_annotations 
   WHERE project = 'en.wikipedia' AND timestamp = '2024-01-01'
   ```

2. Verify `is_visible = TRUE` and `status = 'approved'`

3. Check browser console for API errors

### Reviewer Can't Access Dashboard

1. Verify user is in reviewer allowlist:
   ```sql
   SELECT * FROM annotation_reviewers WHERE username = 'ReviewerName'
   ```

2. Check `is_active = TRUE`

3. Verify user is logged in with OAuth

### Edit Count Check Failing

1. Check MediaWiki API availability
2. Verify username is correct
3. Check API response in backend logs

## Future Enhancements

1. **Email Notifications**: Implement actual email sending via MediaWiki API
2. **User Notifications**: Notify submitters of review decisions
3. **Annotation History**: Track edits and changes over time
4. **Bulk Actions**: Allow reviewers to process multiple items at once
5. **Search and Filter**: Add search functionality to reviewer dashboard
6. **Analytics**: Track annotation quality and reviewer performance
7. **Multi-language Support**: Translate interface for different languages
8. **Echo Notifications**: Use MediaWiki Echo for in-wiki notifications

## Security Considerations

1. **Authentication**: All write operations require OAuth login
2. **Authorization**: Reviewer actions check allowlist
3. **Input Validation**: All inputs are sanitized and validated
4. **SQL Injection**: Using parameterized queries
5. **XSS Prevention**: Vue.js automatically escapes output
6. **Rate Limiting**: Consider implementing for high-traffic scenarios
7. **Audit Trail**: All actions are logged for accountability

## Support and Contact

For issues or questions:
- Check the audit logs for detailed error information
- Review the API response errors in browser console
- Contact tool maintainers for reviewer access
- Report bugs via the project repository











Next Steps to Deploy
Run database migration: Execute annotations_schema.sql
Add reviewers: Insert usernames into annotation_reviewers table
Update view components: Pass project prop to PeaksTable
Add router configuration: Include ReviewerDashboard route
Test the workflow: Submit → Review → Approve