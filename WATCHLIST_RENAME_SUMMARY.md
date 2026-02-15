# Watchlist Feature Rename Summary

## Overview
Successfully renamed the feature from "Watches" to "Watchlist" throughout the entire codebase for better clarity and consistency with Wikimedia conventions.

## Changes Made

### 1. Database Migration (`004_rename_to_watchlist.sql`)
**New Tables:**
- `user_watches` → `user_project_watchlist`
- `user_language_watches` → `user_language_watchlist`

**Migration Command:**
```bash
docker exec -it backend python migrate.py
```

### 2. Backend Routes (`backend/subscription/routes.py`)

**API Endpoint Changes:**

| Old Endpoint | New Endpoint | Description |
|-------------|-------------|-------------|
| `/api/watches/watch` | `/api/watchlist/add-project` | Add project to watchlist |
| `/api/watches/unwatch` | `/api/watchlist/remove-project` | Remove project from watchlist |
| `/api/watches/my-watches` | `/api/watchlist/project-watchlist` | Get user's project watchlist |
| `/api/watches/check-watch` | `/api/watchlist/check-project` | Check if project is in watchlist |
| `/api/watches/watch-language` | `/api/watchlist/add-language` | Add language to watchlist |
| `/api/watches/unwatch-language` | `/api/watchlist/remove-language` | Remove language from watchlist |
| `/api/watches/my-language-watches` | `/api/watchlist/language-watchlist` | Get user's language watchlist |

**Blueprint Registration:**
- Changed from `/api/watches` to `/api/watchlist` in `backend/app.py`

### 3. Notification Manager (`backend/notification/notification_manager.py`)
**Table References Updated:**
- `user_watches` → `user_project_watchlist`
- `user_language_watches` → `user_language_watchlist`

### 4. Frontend UI (`frontend/src/views/Subscriptions.vue`)

**Page Title:**
- "Watch Projects & Languages" → "Project & Language Watchlist"

**Section Headers:**
- "Watch a Project" → "Add Project to Watchlist"
- "Watch a Language" → "Add Language to Watchlist"
- "Your Project Watches" → "Your Project Watchlist"
- "Your Language Watches" → "Your Language Watchlist"

**Button Labels:**
- "Watch Project" → "Add to Watchlist"
- "Watch Language" → "Add to Watchlist"
- "Unwatch" → "Remove"

**Variable Names:**
- `watches` → `projectWatchlist`
- `languageWatches` → `languageWatchlist`
- `unwatching` → `removingProject`
- `unwatchingLanguage` → `removingLanguage`
- `fetchWatches()` → `fetchWatchlist()`

### 5. Router (`frontend/src/router/index.js`)
**Route Changes:**
- Path: `/watches` → `/watchlist`
- Name: `Watches` → `Watchlist`

### 6. Navbar (`frontend/src/components/Navbar.vue`)
**Navigation Link:**
- "Watches" → "Watchlist"
- Path: `/watches` → `/watchlist`

## Terminology Consistency

### Before:
- "Watch a project"
- "Watching projects"
- "Unwatch"
- "My watches"

### After:
- "Add to watchlist"
- "Project watchlist" / "Language watchlist"
- "Remove from watchlist"
- "Your watchlist"

## Deployment Steps

### 1. Run Database Migration
```bash
docker exec -it backend python migrate.py
```

Expected output:
```
INFO - Applying migration: 004_rename_to_watchlist.sql...
INFO - Successfully applied 004_rename_to_watchlist.sql
```

### 2. Restart Backend
```bash
docker-compose restart backend
```

### 3. Clear Frontend Cache (if needed)
```bash
cd frontend
npm run build
```

### 4. Verify Changes

**Check Database Tables:**
```bash
docker exec -it db mysql -u root -p community_alerts -e "SHOW TABLES LIKE '%watchlist%';"
```

Expected tables:
- `user_project_watchlist`
- `user_language_watchlist`

**Test API Endpoints:**
```bash
# Get project watchlist
curl http://localhost:5000/api/watchlist/project-watchlist

# Get language watchlist
curl http://localhost:5000/api/watchlist/language-watchlist
```

**Test Frontend:**
- Navigate to `/watchlist` (not `/watches`)
- Verify all UI text uses "watchlist" terminology
- Test adding/removing projects and languages

## User-Facing Changes

### Navigation
- Menu item changed from "Watches" to "Watchlist"
- URL changed from `/watches` to `/watchlist`

### Page Content
- Clearer terminology: "Add to Watchlist" instead of "Watch"
- Separate sections for "Project Watchlist" and "Language Watchlist"
- "Remove" button instead of "Unwatch"

### Messages
- "Successfully added [project] to watchlist"
- "Successfully removed [project] from watchlist"
- "Successfully added [language] to language watchlist"
- "Successfully removed [language] from language watchlist"

## Benefits of This Change

1. **Clarity:** "Watchlist" is more descriptive than "Watches"
2. **Consistency:** Aligns with Wikimedia's existing "Watchlist" feature
3. **User-Friendly:** More intuitive for new users
4. **Professional:** Better terminology for a production feature

## Backward Compatibility

⚠️ **Breaking Changes:**
- Old API endpoints (`/api/watches/*`) will no longer work
- Old frontend route (`/watches`) will return 404
- Database tables have been renamed

**Migration Notes:**
- All existing data is preserved during table rename
- No data loss occurs
- Users will need to use new URLs

## Testing Checklist

- [x] Database migration runs successfully
- [x] Backend starts without errors
- [x] Frontend compiles without errors
- [ ] Can add project to watchlist
- [ ] Can remove project from watchlist
- [ ] Can add language to watchlist
- [ ] Can remove language from watchlist
- [ ] Notifications still work correctly
- [ ] All UI text uses "watchlist" terminology
- [ ] Navigation links work correctly

## Support

If you encounter issues:

1. **Database errors:** Ensure migration ran successfully
2. **API errors:** Check backend logs: `docker logs backend`
3. **Frontend errors:** Check browser console
4. **404 errors:** Clear browser cache and use `/watchlist` URL

## Related Files

- `backend/migrations/004_rename_to_watchlist.sql`
- `backend/subscription/routes.py`
- `backend/notification/notification_manager.py`
- `backend/app.py`
- `frontend/src/views/Subscriptions.vue`
- `frontend/src/router/index.js`
- `frontend/src/components/Navbar.vue`
