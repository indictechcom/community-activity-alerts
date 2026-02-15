#!/bin/bash

# Navigate to project root (assuming standard Toolforge structure)
# Adjust this path to where your code lives, e.g., $HOME/www/python/src
cd $HOME/www/python/src 

# Set Python Path so backend modules are found
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "--- Starting Monthly Run: $(date) ---"

# 1. Fetch Edits (Last Month)
$HOME/www/python/venv/bin/python3 cron/fetch_and_store_cron.py --mode monthly

# 2. Fetch Editors (Last Month)
$HOME/www/python/venv/bin/python3 cron/fetch_and_store_editors_cron.py --mode monthly

# 3. Compute Community Peaks (Full Recalculation)
$HOME/www/python/venv/bin/python3 backend/alerts/community_alerts.py

# 4. Compute Editor Peaks (Full Recalculation)
$HOME/www/python/venv/bin/python3 backend/alerts/editor_alerts.py

# 5. Monthly Peak Detection and Notification
$HOME/www/python/venv/bin/python3 cron/monthly_peak_detection.py >> cron/notification.log 2>&1

echo "--- Finished Monthly Run: $(date) ---"