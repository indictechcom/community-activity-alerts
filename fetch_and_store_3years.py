#!/usr/bin/env python3

import requests
import pandas as pd
import pymysql
import configparser
from datetime import datetime, timedelta
import logging
import time
from random import uniform

# --- Configure logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Toolforge DB credentials ---
cfg = configparser.ConfigParser()
cfg.read('/data/project/community-activity-alerts-system/replica.my.cnf')
user = cfg['client']['user']
password = cfg['client']['password']

# --- Fetch project list from SiteMatrix ---
sitematrix_url = "https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json"
response = requests.get(sitematrix_url)
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

# --- Date range for last 3 years ---
today = datetime.utcnow().date().replace(day=1)
end_date = today - timedelta(days=1)
start_date = end_date.replace(year=end_date.year - 3, day=1)

start = start_date.strftime("%Y%m%d")
end = end_date.strftime("%Y%m%d")

logging.info(f"Fetching data from {start} to {end} (3 years)")

# --- Connect to Toolforge DB ---
DB_NAME = 's56391__community_alerts'
DB_TABLE = 'edit_counts'

conn = pymysql.connect(
    host='tools.db.svc.wikimedia.cloud',
    user=user,
    password=password,
    database=DB_NAME,
    charset='utf8mb4',
    autocommit=True
)

cursor = conn.cursor()

# --- Ensure table exists ---
create_table_sql = f'''
CREATE TABLE IF NOT EXISTS {DB_TABLE} (
    timestamp DATETIME,
    edit_count INT,
    project VARCHAR(255),
    PRIMARY KEY (timestamp, project)
)
'''
cursor.execute(create_table_sql)

# --- API config ---
base_url = "https://wikimedia.org/api/rest_v1/metrics/edits/aggregate"
editor_type = "all-editor-types"
page_type = "content"
granularity = "monthly"

# --- Loop through projects ---
for project in sorted(projects):
    logging.info(f"Fetching edits for {project} from {start} to {end}")

    url = f"{base_url}/{project}/{editor_type}/{page_type}/{granularity}/{start}/{end}"
    response = requests.get(url)
    if response.status_code != 200:
        logging.warning(f"API Error for {project}: {response.status_code} - {response.text}")
        time.sleep(uniform(1, 3))  # Sleep before next request
        continue

    try:
        data = response.json()
        edit_counts = data["items"][0]["results"]
        if not edit_counts:
            logging.info(f"No data returned for {project}")
            continue
    except Exception as e:
        logging.error(f"Parsing error for {project}: {e}")
        continue

    df = pd.DataFrame(edit_counts)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['project'] = project
    df.rename(columns={'edits': 'edit_count'}, inplace=True)

    for _, row in df.iterrows():
        try:
            insert_sql = f"""
            INSERT INTO {DB_TABLE} (timestamp, edit_count, project)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE edit_count = VALUES(edit_count)
            """
            cursor.execute(
                insert_sql,
                (row['timestamp'].to_pydatetime(), int(row['edit_count']), row['project'])
            )
        except Exception as e:
            logging.error(f"DB insert failed for {project}: {e}")
            continue

logging.info("All 3-year data saved successfully to the edit_counts table.")

# --- Cleanup ---
cursor.close()
conn.close()