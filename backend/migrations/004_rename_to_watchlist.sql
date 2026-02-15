-- Rename tables to use "watchlist" terminology
-- This migration renames the watch tables to watchlist for consistency

-- Rename user_watches to user_project_watchlist
RENAME TABLE user_watches TO user_project_watchlist;

-- Rename user_language_watches to user_language_watchlist
RENAME TABLE user_language_watches TO user_language_watchlist;

-- Update table comments
ALTER TABLE user_project_watchlist COMMENT = 'Project watchlist - users watching specific projects';
ALTER TABLE user_language_watchlist COMMENT = 'Language watchlist - users watching all projects from a language';
