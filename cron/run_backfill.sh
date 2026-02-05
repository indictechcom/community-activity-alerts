#!/bin/bash

cd $HOME/www/python/src 
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "--- Starting BACKFILL Run: $(date) ---"

# 1. Fetch Edits (Backfill 24 months)
python3 cron/fetch_and_store_cron.py --mode backfill

# 2. Fetch Editors (Backfill 36 months)
python3 cron/fetch_and_store_editors_cron.py --mode backfill

# 3. Compute Community Peaks
python3 backend/alerts/community_alerts.py

# 4. Compute Editor Peaks
python3 backend/alerts/editor_alerts.py

echo "--- Finished Backfill Run: $(date) ---"