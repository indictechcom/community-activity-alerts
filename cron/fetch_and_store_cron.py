#!/usr/bin/env python3

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import pymysql
import argparse
from datetime import datetime, timedelta
import logging
import time
from random import uniform
import sys
import os

# Ensure backend modules can be imported if running from root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.utils import getHeader
from backend.config import get_db_connection, get_db_credentials, API_CONFIG

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Wikimedia edit counts.")
    parser.add_argument(
        "--mode", 
        choices=["monthly", "backfill"], 
        default="monthly", 
        help="Fetch mode: 'monthly' for last month, 'backfill' for last 72 months."
    )
    return parser.parse_args()

def get_robust_session():
    """
    Creates a requests Session with automatic retries for connection errors.
    """
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def main():
    args = parse_args()
    
    # --- Date Logic ---
    # Use datetime.now(datetime.UTC) if on Python 3.11+, otherwise datetime.utcnow()
    try:
        from datetime import timezone
        today = datetime.now(timezone.utc).date()
    except ImportError:
        today = datetime.utcnow().date()
        
    end_date = today.replace(day=1)  # First day of current month
    
    if args.mode == "backfill":
        # Backfill: Last 72 months (6 years)
        # CORRECTION: 72 * 365 was 72 years. We use 6 * 365 for ~72 months.
        start_date = (end_date - timedelta(days=6*365)).replace(day=1)
        logging.info(f"Starting BACKFILL mode: {start_date} to {end_date} (Last 72 months)")
    else:
        # Monthly: Just the previous month
        last_month = end_date - timedelta(days=1)
        start_date = last_month.replace(day=1)
        logging.info(f"Starting MONTHLY mode: {start_date} to {end_date}")

    start = start_date.strftime("%Y%m%d")
    end = end_date.strftime("%Y%m%d")  

    # --- Setup Session ---
    session = get_robust_session()

    # --- Fetch project list from SiteMatrix ---
    try:
        sitematrix_url = "https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json"
        response = session.get(sitematrix_url, headers=getHeader(), timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.critical(f"Failed to fetch SiteMatrix. Aborting job. Error: {e}")
        return

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

    credentials = get_db_credentials()
    conn = get_db_connection()
    cursor = conn.cursor()

    logging.info(f"Found {len(projects)} projects to process.")
    count = 0
    total_projects = len(projects)

    # --- Loop through projects ---
    for project in sorted(projects):
        count += 1
        
        # ---Log every 50 projects ---
        if count % 50 == 0:
            logging.info(f"Progress: Processed {count}/{total_projects} projects...")
        url = f"{API_CONFIG['base_url']}/{project}/{API_CONFIG['editor_type']}/{API_CONFIG['page_type']}/{API_CONFIG['granularity']}/{start}/{end}"
        
        try:
            # Added timeout to prevent hanging indefinitely
            response = session.get(url, headers=getHeader(), timeout=20)
            
            if response.status_code != 200:
                # Silent skip for 404s (inactive projects)
                # logging.warning(f"Status {response.status_code} for {project}") # Optional debug
                continue

            data = response.json()
            items = data.get("items", [{}])
            if not items:
                continue
                
            edit_counts = items[0].get("results", [])
            if not edit_counts:
                continue

            # Process Data
            df = pd.DataFrame(edit_counts)
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df["project"] = project
            df.rename(columns={"edits": "edit_count"}, inplace=True)

            for _, row in df.iterrows():
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
            
            # Commit every project (or every N projects) to save progress
            conn.commit()

        except requests.exceptions.RequestException as e:
            # Network error: Log it but DO NOT CRASH the script
            logging.error(f"Network error for {project}: {e}")
        except Exception as e:
            # Parsing/DB error: Log it but DO NOT CRASH
            logging.error(f"Data processing error for {project}: {e}")
        
        # Polite delay to prevent connection resets
        time.sleep(uniform(0.05, 0.2))

    logging.info(f"Finished fetching edits ({args.mode}).")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()