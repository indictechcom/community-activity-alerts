#!/usr/bin/env python3

import polars as pl
import pymysql
import configparser
import logging
from datetime import timedelta

# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

#--- DB config ---
cfg = configparser.ConfigParser()
cfg.read("/data/project/community-activity-alerts-system/replica.my.cnf")
user = cfg["client"]["user"]
password = cfg["client"]["password"]

DB_NAME = "s56391__community_alerts"
SOURCE_TABLE = "edit_counts"
ALERTS_TABLE = "community_alerts"

# Uncomment for local testing:
# DB_USER = "wikim"
# DB_PASSWORD = "wikimedia"
# DB_NAME = "community_alerts"


def find_peaks_rolling_3_years_polars(df, threshold_percentage=0.30):
    """
    Polars implementation that matches the original pandas logic exactly.
    For each timestamp, calculates rolling mean of past 3 years of data.
    """
    df = df.sort("timestamp")
    peaks_list = []

    # Convert to list of dicts for easier processing
    data = df.to_dicts()

    for i, row in enumerate(data):
        t_i = row["timestamp"]
        edits_i = row["edit_count"]

        # Create 3-year lookback window (same as pandas version)
        three_years_ago = t_i - timedelta(
            days=3 * 365.25
        )  # More precise than DateOffset

        # Filter data for the window (from 3 years ago up to current timestamp)
        window_data = [
            r
            for r in data[: i + 1]  # Only look at current and past data
            if three_years_ago <= r["timestamp"] <= t_i
        ]

        if not window_data:
            continue

        # Calculate rolling mean for this window
        edit_counts = [r["edit_count"] for r in window_data]
        rolling_mean = sum(edit_counts) / len(edit_counts)
        threshold = rolling_mean * (1 + threshold_percentage)
        pct_diff = ((edits_i - rolling_mean) / rolling_mean) * 100

        if edits_i >= threshold:
            peaks_list.append(
                {
                    "timestamp": t_i,
                    "edit_count": edits_i,
                    "rolling_mean": rolling_mean,
                    "threshold": threshold,
                    "percentage_difference": pct_diff,
                }
            )

    return peaks_list


def find_peaks_rolling_3_years_polars_optimized(df, threshold_percentage=0.30):
    """
    More efficient Polars implementation using rolling operations.
    This approximates the 3-year window using rolling_mean with a time-based window.
    """
    df = df.sort("timestamp")

    # Use Polars' time-based rolling window (3 years = ~1095 days)
    df_with_rolling = df.with_columns(
        [
            pl.col("edit_count")
            .rolling_mean_by("timestamp", window_size="3y")
            .alias("rolling_mean")
        ]
    )

    # Calculate threshold and percentage difference
    df_with_metrics = df_with_rolling.with_columns(
        [
            (pl.col("rolling_mean") * (1 + threshold_percentage)).alias("threshold"),
            (
                (pl.col("edit_count") - pl.col("rolling_mean"))
                / pl.col("rolling_mean")
                * 100
            ).alias("percentage_difference"),
        ]
    )

    # Filter for peaks
    peaks_df = df_with_metrics.filter(
        (pl.col("edit_count") >= pl.col("threshold"))
        & (pl.col("rolling_mean").is_not_null())
    )

    return peaks_df.to_dicts() if not peaks_df.is_empty() else []


def main():
    conn = None
    try:
        # Connect to DB
        conn = pymysql.connect(
            host="tools.db.svc.wikimedia.cloud",
            user=user,
            password=password,
            database=DB_NAME,
            charset="utf8mb4",
            autocommit=True,
        )

        # Uncomment for local testing:
        # conn = pymysql.connect(
        #     host="localhost",
        #     user=DB_USER,
        #     password=DB_PASSWORD,
        #     database=DB_NAME,
        #     charset="utf8mb4",
        #     autocommit=True,
        # )

        # Ensure alerts table exists
        with conn.cursor() as cursor:
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {ALERTS_TABLE} (
                project VARCHAR(255),
                timestamp DATETIME,
                edit_count INT,
                rolling_mean FLOAT,
                threshold FLOAT,
                percentage_difference FLOAT,
                PRIMARY KEY (project, timestamp)
            )
            """)

        # Read data using traditional method (more reliable than read_database_uri)
        query = f"SELECT project, timestamp, edit_count FROM {SOURCE_TABLE}"

        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        if not results:
            logging.info("Source table is empty. Nothing to process.")
            return

        # Convert to Polars DataFrame
        df = pl.DataFrame(
            results, schema=["project", "timestamp", "edit_count"], orient="row"
        )

        # Ensure timestamp is datetime and timezone-aware
        df = df.with_columns(pl.col("timestamp").dt.replace_time_zone("UTC"))

        # Process each project
        for project_name, group_df in df.group_by("project", maintain_order=True):
            logging.info(f"Analyzing peaks for: {project_name}")

            # Use the optimized version (closer to original behavior)
            peaks = find_peaks_rolling_3_years_polars_optimized(
                group_df, threshold_percentage=0.30
            )

            # Alternative: use exact replica of pandas logic
            # peaks = find_peaks_rolling_3_years_polars(group_df, threshold_percentage=0.30)

            if not peaks:
                logging.info(f"No peaks found for {project_name}")
                continue

            # Insert detected peaks into DB
            with conn.cursor() as cursor:
                for peak in peaks:
                    try:
                        cursor.execute(
                            f"""
                            INSERT INTO {ALERTS_TABLE}
                            (project, timestamp, edit_count, rolling_mean, threshold, percentage_difference)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                edit_count=VALUES(edit_count),
                                rolling_mean=VALUES(rolling_mean),
                                threshold=VALUES(threshold),
                                percentage_difference=VALUES(percentage_difference)
                        """,
                            (
                                project_name,
                                peak["timestamp"],
                                int(peak["edit_count"]),
                                float(peak["rolling_mean"]),
                                float(peak["threshold"]),
                                float(peak["percentage_difference"]),
                            ),
                        )
                    except Exception as e:
                        logging.error(
                            f"DB insert failed for {project_name} on {peak['timestamp']}: {e}"
                        )

    except Exception as e:
        logging.error(f"An error occurred during main processing: {e}")
    finally:
        if conn and conn.open:
            conn.close()
            logging.info("Database connection closed.")

    logging.info("Peak detection completed for all projects.")


if __name__ == "__main__":
    main()
