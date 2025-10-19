#!/usr/bin/env python3

import requests
import pandas as pd
import pymysql
from datetime import datetime, timedelta
import logging
import time
from random import uniform
from backend.utils import getHeader
from backend.config import get_db_connection, get_db_credentials, API_CONFIG

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Fetch project list from SiteMatrix ---
sitematrix_url = "https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json"
response = requests.get(sitematrix_url,  headers=getHeader())
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

# --- Date range for last month ---
today = datetime.utcnow().date().replace(day=1)
last_month_end = today - timedelta(days=1)
last_month_start = last_month_end.replace(day=1)

start = last_month_start.strftime("%Y%m%d")
end = today.strftime("%Y%m%d")  

credentials = get_db_credentials()
conn = get_db_connection()

cursor = conn.cursor()

# --- Ensure main table exists ---
create_table_sql = f"""
CREATE TABLE IF NOT EXISTS {credentials["DB_TABLE"]} (
    timestamp DATETIME,
    edit_count INT,
    project VARCHAR(255),
    PRIMARY KEY (timestamp, project)
)
"""
cursor.execute(create_table_sql)

# --- Optional: Metadata table for fetch status ---
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS fetch_runs (
#     run_time DATETIME,
#     project VARCHAR(255),
#     status VARCHAR(20),
#     message TEXT
# )
# ''')



# --- Loop through projects ---
for project in sorted(projects):
    logging.info(f"Fetching edits for {project} from {start} to {end}")

    url = f"{API_CONFIG['base_url']}/{project}/{API_CONFIG['editor_type']}/{API_CONFIG['page_type']}/{API_CONFIG['granularity']}/{start}/{end}"
    response = requests.get(url, headers=getHeader())
    if response.status_code != 200:
            # This handles 404s for inactive wikis, which is normal
            logging.warning(f"API Info for {project}: {response.status_code} - Skipping.")
            time.sleep(uniform(0.5, 1.5))
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
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["project"] = project
    df.rename(columns={"edits": "edit_count"}, inplace=True)

    for _, row in df.iterrows():
        try:
            insert_sql = f"""
            INSERT INTO {credentials["DB_TABLE"]} (timestamp, edit_count, project)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE edit_count = VALUES(edit_count)
            """
            cursor.execute(
                insert_sql,
                (
                    row["timestamp"].to_pydatetime(),
                    int(row["edit_count"]),
                    row["project"],
                ),
            )
        except Exception as e:
            logging.error(f"DB insert failed for {project}: {e}")
            continue

logging.info("All data saved successfully.")

# --- Cleanup ---
cursor.close()
conn.close()