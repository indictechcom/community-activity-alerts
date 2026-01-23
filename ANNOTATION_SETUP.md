# Quick Setup Guide for Annotation System

## Prerequisites

- MySQL database running
- Flask backend configured
- Vue.js frontend set up
- OAuth authentication working

## Step-by-Step Setup

### 1. Database Setup (5 minutes)

Execute the schema file to create all necessary tables:

```bash
# From the project root
mysql -u your_username -p community_alerts < backend/annotations_schema.sql
```

Or connect to MySQL and run:

```sql
SOURCE backend/annotations_schema.sql;
```

Verify tables were created:

```sql
SHOW TABLES LIKE '%annotation%';
```

You should see:
- `annotation_audit_log`
- `annotation_reports`
- `annotation_reviewers`
- `annotation_reviews`
- `peak_annotations`

### 2. Add Initial Reviewers (2 minutes)

Add yourself and other tool maintainers as reviewers:

```sql
INSERT INTO annotation_reviewers (username, region, added_by, notes)
VALUES 
  ('YourWikimediaUsername', 'Global', 'system', 'Tool maintainer'),
  ('Reviewer1', 'South Asia', 'YourWikimediaUsername', 'Regional volunteer'),
  ('Reviewer2', 'ESEAP', 'YourWikimediaUsername', 'Regional volunteer');
```

**Important**: Use exact Wikimedia usernames (case-sensitive).

### 3. Backend Integration (Already Done)

The annotation routes are already integrated in `backend/app.py`:

```python
from annotation_routes import create_annotation_blueprint
annotation_bp = create_annotation_blueprint(mwo_auth)
app.register_blueprint(annotation_bp, url_prefix='/api/annotations')
```

### 4. Frontend Integration

#### Update View Components

In your view files (e.g., `EditCounts.vue`, `EditorCounts.vue`), pass the `project` prop to PeaksTable:

```vue
<PeaksTable 
  :peaks="peaks" 
  :project="currentProject"  <!-- Add this prop -->
/>
```

#### Add Router Configuration

In `frontend/src/router/index.js`, add the reviewer dashboard route:

```javascript
import ReviewerDashboard from '@/views/ReviewerDashboard.vue'

const routes = [
  // ... existing routes
  {
    path: '/reviewer',
    name: 'ReviewerDashboard',
    component: ReviewerDashboard,
    meta: { requiresAuth: true }  // Optional: add auth guard
  }
]
```

#### Add Navigation Link (Optional)

In your navbar component, add a link for reviewers:

```vue
<router-link 
  v-if="isReviewer" 
  to="/reviewer"
  class="nav-link"
>
  Reviewer Dashboard
</router-link>
```

### 5. Install Dependencies (if needed)

The annotation system uses existing dependencies. If you encounter issues, verify:

```bash
# Backend
pip install requests  # Already in requirements.txt

# Frontend
npm install axios  # Should already be installed
```

### 6. Test the System

#### Test as Regular User

1. Navigate to a page with peaks
2. Click "Add annotation" on any peak
3. Fill in description and link
4. Submit
5. Verify you see "Annotation submitted for review"

#### Test as Reviewer

1. Add yourself to reviewers table (see step 2)
2. Navigate to `/reviewer`
3. You should see the reviewer dashboard
4. Review the pending annotation you just submitted

### 7. Verify Everything Works

Run these SQL queries to check:

```sql
-- Check if annotation was created
SELECT * FROM peak_annotations ORDER BY submitted_at DESC LIMIT 5;

-- Check if action was logged
SELECT * FROM annotation_audit_log ORDER BY created_at DESC LIMIT 5;

-- Check active reviewers
SELECT username, region FROM annotation_reviewers WHERE is_active = TRUE;
```

## Common Issues and Solutions

### Issue: "Authentication required" error

**Solution**: Ensure user is logged in via OAuth. Check session in browser dev tools.

### Issue: "Insufficient edit count" error

**Solution**: 
- User needs ≥1000 global edits
- Check user's global edit count at: `https://meta.wikimedia.org/wiki/Special:CentralAuth/USERNAME`

### Issue: Annotations not appearing on peaks

**Solution**:
- Annotations must be approved first
- Check `peak_annotations` table for status
- Verify `is_visible = TRUE` and `status = 'approved'`

### Issue: "Reviewer privileges required" error

**Solution**:
- Add user to `annotation_reviewers` table
- Ensure `is_active = TRUE`
- Username must match exactly (case-sensitive)

### Issue: Can't access reviewer dashboard

**Solution**:
- Verify route is added to router
- Check user is in reviewers table
- Ensure user is logged in

## Configuration Options

### Adjust Word Limit

In `AnnotationModal.vue` and review modals, change the word limit:

```javascript
// Current: 50 words max
if (wordCount.value > 50) {
  // Change 50 to your desired limit
}
```

### Adjust Edit Count Requirement

In `backend/annotation_routes.py`:

```python
# Current: 1000 edits required
if edit_count < 1000:
    # Change 1000 to your desired threshold
```

### Customize Email Notifications

In `backend/annotation_utils.py`, implement the `send_reviewer_notification()` function to actually send emails via MediaWiki API.

## Regional Reviewer Setup

For different regions, add reviewers with appropriate region tags:

```sql
INSERT INTO annotation_reviewers (username, region, added_by, notes)
VALUES 
  ('SAReviewer', 'South Asia', 'admin', 'Hindi, Bengali, Tamil speaker'),
  ('ESEAPReviewer', 'ESEAP', 'admin', 'Indonesian, Tagalog speaker'),
  ('LATAMReviewer', 'LATAM', 'admin', 'Spanish, Portuguese speaker'),
  ('CEEReviewer', 'CEE', 'admin', 'Russian, Polish speaker');
```

## Monitoring

### Daily Checks

```sql
-- Pending items count
SELECT 
  (SELECT COUNT(*) FROM peak_annotations WHERE status = 'pending') as pending_annotations,
  (SELECT COUNT(*) FROM annotation_reports WHERE status = 'pending') as pending_reports;
```

### Weekly Review

```sql
-- Activity summary
SELECT 
  DATE(created_at) as date,
  action_type,
  COUNT(*) as count
FROM annotation_audit_log
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(created_at), action_type
ORDER BY date DESC;
```

## Next Steps

1. ✅ Database tables created
2. ✅ Reviewers added
3. ✅ Backend integrated
4. ✅ Frontend components created
5. ⏳ Test with real users
6. ⏳ Monitor for spam/abuse
7. ⏳ Implement email notifications (optional)
8. ⏳ Add more reviewers as needed

## Support

For detailed documentation, see `ANNOTATION_SYSTEM.md`.

For issues:
- Check browser console for errors
- Review backend logs
- Check database for data consistency
- Verify OAuth authentication is working
