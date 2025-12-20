#!/usr/bin/env python3

import requests
import pandas as pd
import pymysql
import configparser
from datetime import datetime, timedelta
import logging
import time
from random import uniform
from backend.utils import getHeader
from backend.config import get_db_connection, get_db_credentials, API_CONFIG

# --- Configure logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Fetch project list from SiteMatrix ---
sitematrix_url = "https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json"
response = requests.get(sitematrix_url, headers=getHeader())
data = response.json()

projects = set()
sitematrix = data.get("sitematrix", {})

for key, val in sitematrix.items():
    if key in ("count", "specials"):
        continue
    if isinstance(val, dict):
        sites = val.get("site", [])
        for site in sites:
            if site.get("closed"):
                continue
            site_url = site.get("url")
            if site_url:
                cleaned_url = site_url.replace("https://", "")
                projects.add(cleaned_url)

# --- Date range for last 36 months ---
today = datetime.utcnow().date()
end_date = today.replace(day=1)  # First day of current month
start_date = (end_date - timedelta(days=1080)).replace(day=1)  # Approximately 36 months ago

start = start_date.strftime("%Y%m%d")
end = end_date.strftime("%Y%m%d")

# --- Connect to DB ---
credentials = get_db_credentials()
DB_TABLE = 'editor_counts'

conn = get_db_connection()
cursor = conn.cursor()

# --- Ensure editor counts table exists ---
create_table_sql = f'''
CREATE TABLE IF NOT EXISTS {DB_TABLE} (
    timestamp DATETIME,
    editor_count INT,
    project VARCHAR(255),
    PRIMARY KEY (timestamp, project)
)
'''
cursor.execute(create_table_sql)

# --- API config for editors ---
base_url = "https://wikimedia.org/api/rest_v1/metrics/editors/aggregate"
editor_type = "all-editor-types"
page_type = "content"
activity_level = "1..4-edits"  # Editors with 1-4 edits, or use "5..24-edits", "25..99-edits", "100..-edits"
granularity = "monthly"

# --- Loop through projects ---
for project in sorted(projects):
    logging.info(f"Fetching editor counts for {project} from {start} to {end}")

    url = f"{base_url}/{project}/{editor_type}/{page_type}/{activity_level}/{granularity}/{start}/{end}"
    response = requests.get(url, headers=getHeader())
    if response.status_code != 200:
        logging.warning(f"API Error for {project}: {response.status_code} - {response.text}")
        time.sleep(uniform(1, 3))
        continue

    try:
        data = response.json()
        editor_counts = data["items"][0]["results"]
        if not editor_counts:
            logging.info(f"No editor data returned for {project}")
            continue
    except Exception as e:
        logging.error(f"Parsing error for {project}: {e}")
        continue

    df = pd.DataFrame(editor_counts)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['project'] = project
    df.rename(columns={'editors': 'editor_count'}, inplace=True)

    for _, row in df.iterrows():
        try:
            insert_sql = f"""
            INSERT INTO {DB_TABLE} (timestamp, editor_count, project)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE editor_count = VALUES(editor_count)
            """
            cursor.execute(
                insert_sql,
                (row['timestamp'].to_pydatetime(), int(row['editor_count']), row['project'])
            )
        except Exception as e:
            logging.error(f"DB insert failed for {project}: {e}")
            continue

logging.info("All editor data saved successfully.")

# --- Cleanup ---
cursor.close()
conn.close()