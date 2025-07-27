#!/usr/bin/env python3

import pandas as pd
import pymysql
import configparser
import logging

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- DB config ---
DB_NAME = 'community_alerts'
SOURCE_TABLE = 'editor_counts'
ALERTS_TABLE = 'editor_alerts'

# --- Function to detect peaks ---
def find_peaks_rolling_3_years(df, threshold_percentage=0.30):
    df = df.sort_values("timestamp").reset_index(drop=True)
    peaks = []

    for i in range(len(df)):
        t_i = df.at[i, "timestamp"]
        editors_i = df.at[i, "editor_count"]

        window = df[(df["timestamp"] >= t_i - pd.DateOffset(years=3)) & (df["timestamp"] <= t_i)]
        if window.empty:
            continue

        rolling_mean = window["editor_count"].mean()
        threshold = rolling_mean * (1 + threshold_percentage)
        pct_diff = ((editors_i - rolling_mean) / rolling_mean) * 100

        if editors_i >= threshold:
            peaks.append({
                "timestamp": t_i,
                "editor_count": editors_i,
                "rolling_mean": rolling_mean,
                "threshold": threshold,
                "percentage_difference": pct_diff
            })

    return peaks

# --- Main logic ---
def main():
    # Connect to DB
    conn = pymysql.connect(
        host='localhost',
        user='wikim',
        password='wikimedia',
        database=DB_NAME,
        charset='utf8mb4',
        autocommit=True
    )

    # Ensure alerts table exists
    with conn.cursor() as cursor:
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {ALERTS_TABLE} (
            project VARCHAR(255),
            timestamp DATETIME,
            editor_count INT,
            rolling_mean FLOAT,
            threshold FLOAT,
            percentage_difference FLOAT,
            label VARCHAR(500) DEFAULT NULL,
            PRIMARY KEY (project, timestamp)
        )
        """)

    # Read full editor data
    df = pd.read_sql(f"SELECT * FROM {SOURCE_TABLE}", conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # Process each project
    for project, group in df.groupby("project"):
        logging.info(f"Analyzing editor peaks for: {project}")

        peaks = find_peaks_rolling_3_years(group)

        if not peaks:
            logging.info(f"No editor peaks found for {project}")
            continue

        # Insert detected peaks into DB
        with conn.cursor() as cursor:
            for peak in peaks:
                try:
                    cursor.execute(f"""
                        INSERT INTO {ALERTS_TABLE}
                        (project, timestamp, editor_count, rolling_mean, threshold, percentage_difference)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            editor_count=VALUES(editor_count),
                            rolling_mean=VALUES(rolling_mean),
                            threshold=VALUES(threshold),
                            percentage_difference=VALUES(percentage_difference)
                    """, (
                        project,
                        peak["timestamp"].to_pydatetime(),
                        int(peak["editor_count"]),
                        float(peak["rolling_mean"]),
                        float(peak["threshold"]),
                        float(peak["percentage_difference"])
                    ))
                except Exception as e:
                    logging.error(f"DB insert failed for {project} on {peak['timestamp']}: {e}")

    conn.close()
    logging.info("Editor peak detection completed for all projects.")

# --- Run ---
if __name__ == "__main__":
    main()