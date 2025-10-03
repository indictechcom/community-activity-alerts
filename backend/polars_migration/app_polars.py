import logging
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import requests
import polars as pl
import pymysql
import configparser
import plotly.graph_objects as go
from plotly.io import to_html
import calendar

app = Flask(__name__)


# --- DB connection setup ---
def get_db_connection():
    cfg = configparser.ConfigParser()
    cfg.read("/data/project/community-activity-alerts-system/replica.my.cnf")
    user = cfg["client"]["user"]
    password = cfg["client"]["password"]

    conn = pymysql.connect(
        host="tools.db.svc.wikimedia.cloud",
        user=user,
        password=password,
        database="s56391__community_alerts",
        charset="utf8mb4",
    )
    return conn


# --- Get communities list from SiteMatrix API ---
def get_all_communities():
    url = "https://commons.wikimedia.org/w/api.php?action=sitematrix&smtype=language&format=json"
    headers = {
        "User-Agent": "Community Activity Alerts (https://github.com/indictechcom/community-activity-alerts)",
        "tool": "Community Activity Alerts",
        "url": "https://github.com/indictechcom/community-activity-alerts",
        "email": "tools.community-activity-alerts-system@toolforge.org",
    }

    response = requests.get(url, headers=headers)
    data = response.json()
    sitematrix = data["sitematrix"]

    languages = {}
    for key, value in sitematrix.items():
        if key.isdigit() and "localname" in value:
            communities = [
                {"sitename": site["code"], "url": site["url"]}
                for site in value.get("site", [])
            ]
            languages[value["localname"]] = communities

    return languages


# --- Peak detection function (Polars version) ---
def find_peaks_rolling_3_years_polars_optimized(df, threshold_percentage=0.30):
    """
    Polars implementation using rolling operations.
    This approximates the 3-year window using rolling_mean with a time-based window.
    """
    df = df.sort("timestamp")

    # Use Polars' time-based rolling window (3 years = ~1095 days)
    df_with_rolling = df.with_columns(
        [
            pl.col("edits")
            .rolling_mean_by("timestamp", window_size="3y")
            .alias("rolling_mean")
        ]
    )

    # Calculate threshold and percentage difference
    df_with_metrics = df_with_rolling.with_columns(
        [
            (pl.col("rolling_mean") * (1 + threshold_percentage)).alias("threshold"),
            (
                (pl.col("edits") - pl.col("rolling_mean"))
                / pl.col("rolling_mean")
                * 100
            ).alias("percentage_difference"),
        ]
    )

    # Filter for peaks
    peaks_df = df_with_metrics.filter(
        (pl.col("edits") >= pl.col("threshold"))
        & (pl.col("rolling_mean").is_not_null())
    )

    return peaks_df.to_dicts() if not peaks_df.is_empty() else []


def find_peaks_rolling_3_years_polars_exact(df, threshold_percentage=0.30):
    """
    Exact replica of the original pandas logic using Polars.
    For each timestamp, calculates rolling mean of past 3 years of data.
    """
    df = df.sort("timestamp")
    peaks_list = []

    # Convert to list of dicts for easier processing
    data = df.to_dicts()

    for i, row in enumerate(data):
        t_i = row["timestamp"]
        edits_i = row["edits"]

        # Create 3-year lookback window (same as pandas version)
        three_years_ago = t_i - timedelta(days=3 * 365.25)

        # Filter data for the window (from 3 years ago up to current timestamp)
        window_data = [
            r
            for r in data[: i + 1]  # Only look at current and past data
            if three_years_ago <= r["timestamp"] <= t_i
        ]

        if not window_data:
            continue

        # Calculate rolling mean for this window
        edit_counts = [r["edits"] for r in window_data]
        rolling_mean = sum(edit_counts) / len(edit_counts)
        threshold = rolling_mean * (1 + threshold_percentage)
        pct_diff = ((edits_i - rolling_mean) / rolling_mean) * 100

        if edits_i >= threshold:
            peaks_list.append(
                {
                    "timestamp": t_i,
                    "edits": edits_i,
                    "rolling_mean": rolling_mean,
                    "threshold": threshold,
                    "percentage_difference": pct_diff,
                }
            )

    return peaks_list


# --- Peak detection function (main interface) ---
def find_peaks_rolling_3_years(df, threshold_percentage=0.30):
    """
    Main peak detection function that works with Polars DataFrames.
    Maintains compatibility with the original pandas interface.
    """
    # Convert pandas DataFrame to Polars if needed
    if hasattr(df, "to_pandas"):  # It's already a Polars DataFrame
        polars_df = df
    else:  # It's a pandas DataFrame, convert it
        polars_df = pl.from_pandas(df)

    # Ensure timestamp column is datetime
    if polars_df.schema["timestamp"] != pl.Datetime:
        polars_df = polars_df.with_columns(pl.col("timestamp").str.to_datetime())

    # Use the optimized version for better performance
    return find_peaks_rolling_3_years_polars_optimized(polars_df, threshold_percentage)


# --- Format peaks for display ---
def log_peaks(peaks):
    """
    Format peaks for display in the web interface.
    """
    peaks_list = []
    for peak in peaks:
        # Handle both datetime objects and strings
        if isinstance(peak["timestamp"], str):
            timestamp_str = peak["timestamp"]
        else:
            timestamp_str = peak["timestamp"].strftime("%Y-%m-%d")

        peaks_list.append(
            {
                "timestamp": timestamp_str,
                "edits": int(peak["edits"]),
                "rolling_mean": round(float(peak["rolling_mean"]), 2),
                "threshold": round(float(peak["threshold"]), 2),
                "percentage_difference": round(float(peak["percentage_difference"]), 2),
            }
        )
    return peaks_list


# --- Main route ---
@app.route("/")
def index():
    language = request.args.get("language")
    project_group = request.args.get("project_group")
    datestart = request.args.get("datestart")
    dateend = request.args.get("dateend")
    filter_edits = request.args.get("filter_edits") == "true"
    filter_users = request.args.get("filter_users") == "true"

    if not (language and project_group and datestart and dateend):
        return render_template("index.html", languages=get_all_communities())

    project = project_group.split(":/")[1][1:]  # e.g. "en.wikipedia.org"
    start = datetime.strptime(datestart, "%b %Y")
    end = datetime.strptime(dateend, "%b %Y")
    # Set start to first day, end to last day of month
    start = start.replace(day=1, hour=0, minute=0, second=0)
    last_day = calendar.monthrange(end.year, end.month)[1]
    end = end.replace(day=last_day, hour=23, minute=59, second=59)

    try:
        conn = get_db_connection()
        query = """
            SELECT timestamp, edit_count AS edits
            FROM edit_counts
            WHERE project = %s
              AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """

        # Fetch data using cursor for better compatibility
        with conn.cursor() as cursor:
            cursor.execute(query, (project, start, end))
            results = cursor.fetchall()

        conn.close()

        if not results:
            return render_template(
                "index.html",
                languages=get_all_communities(),
                data=[],
                chart=None,
                message="No data available.",
            )

        # Convert to Polars DataFrame
        df = pl.DataFrame(results, schema=["timestamp", "edits"], orient="row")

        # Ensure timestamp is datetime and timezone-aware
        df = df.with_columns([pl.col("timestamp").dt.replace_time_zone("UTC")])

        # Detect peaks using Polars
        peaks_raw = find_peaks_rolling_3_years(df, threshold_percentage=0.30)
        peaks = log_peaks(peaks_raw)

        # --- Fetch labels for peaks ---
        conn = get_db_connection()
        cursor = conn.cursor()
        peak_labels = {}

        for peak in peaks:
            try:
                cursor.execute(
                    "SELECT label FROM community_alerts WHERE project = %s AND timestamp = %s",
                    (project, peak["timestamp"]),
                )
                result = cursor.fetchone()
                peak_labels[peak["timestamp"]] = (
                    result[0] if result and result[0] else ""
                )
            except (pymysql.Error, KeyError, TypeError) as e:
                logging.warning(
                    f"Failed to fetch label for peak {peak['timestamp']}: {e}"
                )
                peak_labels[peak["timestamp"]] = ""

        conn.close()

        # --- Generate plot ---
        fig = go.Figure()

        # Convert Polars DataFrame to pandas for plotting compatibility
        df_pandas = df.to_pandas()

        fig.add_trace(
            go.Scatter(
                x=df_pandas["timestamp"],
                y=df_pandas["edits"],
                mode="lines+markers",
                name="Edits",
                line=dict(color="blue"),
            )
        )

        if peaks:
            peak_timestamps = [peak["timestamp"] for peak in peaks]
            peak_values = [peak["edits"] for peak in peaks]
            peak_labels_list = [
                peak_labels.get(peak["timestamp"], "") for peak in peaks
            ]

            fig.add_trace(
                go.Scatter(
                    x=peak_timestamps,
                    y=peak_values,
                    mode="markers+text",
                    name="Peaks Above Threshold",
                    marker=dict(color="red", size=10, symbol="circle"),
                    text=peak_labels_list,
                    textposition="top center",
                    customdata=[
                        {"project": project, "timestamp": peak["timestamp"]}
                        for peak in peaks
                    ],
                    hovertemplate="<b>Peak</b><br>Date: %{x}<br>Edits: %{y}<br>",
                )
            )

        fig.update_layout(
            title="Edits count over time with peaks (30% over 3-year rolling mean)",
            xaxis_title="Timestamp",
            yaxis_title="Count (Edits)",
            xaxis=dict(tickformat="%Y-%m-%d", tickangle=45),
            showlegend=True,
        )

        chart_html = to_html(fig, full_html=False, include_plotlyjs="cdn")

        return render_template(
            "index.html", languages=get_all_communities(), data=peaks, chart=chart_html
        )

    except Exception as e:
        return f"Database error: {str(e)}"


# --- Optional community name search endpoint ---
@app.route("/search")
def search():
    query = request.args.get("query", "").lower()
    communities = get_all_communities()
    filtered_communities = [
        value["name"]
        for key, value in communities.items()
        if "name" in value and query in value["name"].lower()
    ]
    return jsonify(filtered_communities)


# --- API endpoint to update peak label ---
@app.route("/api/update_peak_label", methods=["POST"])
def update_peak_label():
    data = request.json
    project = data["project"]
    timestamp = data["timestamp"]
    label = data["label"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE community_alerts 
            SET label = %s 
            WHERE project = %s AND timestamp = %s
        """,
            (label, project, timestamp),
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()


# --- API endpoint to get peak label ---
@app.route("/api/get_peak_label", methods=["GET"])
def get_peak_label():
    project = request.args.get("project")
    timestamp = request.args.get("timestamp")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT label FROM community_alerts WHERE project = %s AND timestamp = %s",
            (project, timestamp),
        )
        result = cursor.fetchone()
        label = result[0] if result else ""
        return jsonify({"label": label})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=False)
