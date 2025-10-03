from flask import Flask, render_template, request, jsonify, redirect, session
from datetime import datetime
from flask_cors import CORS
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html
import calendar
from flask_mwoauth import MWOAuth
import os

from dotenv import load_dotenv
from utils import getHeader
from config import get_db_connection

app = Flask(__name__)
CORS(app, 
     supports_credentials=True,
     origins=["http://localhost:5173"],  # Specify your frontend origin
     allow_headers=["Content-Type"],
     expose_headers=["Content-Type"])

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")

# Add these session configuration settings
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # or 'None' if cross-site
app.config['SESSION_COOKIE_SECURE'] = True  # Set to True if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_DOMAIN'] = None  # Let Flask handle this


mwo_auth = MWOAuth(
    base_url=os.getenv("MWO_BASE_URL"),
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    user_agent="CommunityActivityAlerts/1.0 (http://localhost:5000)"
)

app.register_blueprint(mwo_auth.bp)


from auth.routes import create_auth_blueprint
auth_bp = create_auth_blueprint(mwo_auth)
app.register_blueprint(auth_bp, url_prefix='/auth')


@app.route("/")
def index():
    return redirect("http://localhost:5173/")

@app.after_request
def after_request(response):
    print(f"Session contents: {session}")
    return response




# --- Get communities list from SiteMatrix API ---
@app.route("/api/communities")
def get_all_communities():
    url = "https://commons.wikimedia.org/w/api.php?action=sitematrix&smtype=language&format=json"

    response = requests.get(url, headers=getHeader())
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

    return jsonify(languages)


# --- Peak detection function ---
def find_peaks_rolling_3_years(df, threshold_percentage=0.30):
    df = df.sort_values("timestamp").reset_index(drop=True)
    peaks = []

    for i in range(len(df)):
        t_i = df.at[i, "timestamp"]
        edits_i = df.at[i, "edits"]

        window = df[
            (df["timestamp"] >= t_i - pd.DateOffset(years=3)) & (df["timestamp"] <= t_i)
        ]
        if window.empty:
            continue

        rolling_mean = window["edits"].mean()
        threshold = rolling_mean * (1 + threshold_percentage)
        pct_diff = ((edits_i - rolling_mean) / rolling_mean) * 100

        if edits_i >= threshold:
            peaks.append(
                {
                    "timestamp": t_i,
                    "edits": edits_i,
                    "rolling_mean": rolling_mean,
                    "threshold": threshold,
                    "percentage_difference": pct_diff,
                }
            )

    return peaks


# --- Format peaks for display ---
def log_peaks(peaks):
    peaks_list = []
    for peak in peaks:
        peaks_list.append(
            {
                "timestamp": peak["timestamp"].strftime("%Y-%m-%d"),
                "edits": int(peak["edits"]),
                "rolling_mean": round(float(peak["rolling_mean"]), 2),
                "threshold": round(float(peak["threshold"]), 2),
                "percentage_difference": round(float(peak["percentage_difference"]), 2),
            }
        )
    return peaks_list




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
    if mwo_auth.get_current_user(True):
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
    else:
        return jsonify({"error": "please login first"})


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

# app.py

@app.route("/api/activity-data")
def get_activity_data():
    language = request.args.get("language")
    project_group = request.args.get("project_group")
    datestart = request.args.get("datestart")
    dateend = request.args.get("dateend")
    filter_edits = request.args.get("filter_edits") == "true"
    filter_users = request.args.get("filter_users") == "true"

    if not (language and project_group and datestart and dateend):
        print("Missing parameters", language, project_group, datestart, dateend)
        return jsonify({"error": "Missing required parameters"}), 400

    project = project_group
    start = datetime.strptime(datestart, "%b %Y")
    end = datetime.strptime(dateend, "%b %Y")
    
    
    start = start.replace(day=1, hour=0, minute=0, second=0)
    last_day = calendar.monthrange(end.year, end.month)[1]
    end = end.replace(day=last_day, hour=23, minute=59, second=59)


    try:
        # 3. Fetch and process data from DB (same logic as before)
        conn = get_db_connection()
        query = """
            SELECT timestamp, edit_count AS edits
            FROM edit_counts
            WHERE project = %s AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """
        df = pd.read_sql(query, conn, params=(project, start, end))
        conn.close()

        if df.empty:
            return jsonify({"peaks": [], "chartData": {}})
        

        df["timestamp"] = pd.to_datetime(df["timestamp"])
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
            except:
                peak_labels[peak["timestamp"]] = ""

        conn.close()

         # 4. Format data for JSON response
        chart_timestamps = df["timestamp"].dt.strftime('%b %Y').tolist()
        chart_edits = df["edits"].tolist()

        # CORRECTED LINE: Format peak timestamps to match the chart's x-axis format.
        peak_timestamps = [datetime.strptime(p['timestamp'], '%Y-%m-%d').strftime('%b %Y') for p in peaks]
        peak_values = [p['edits'] for p in peaks]
        
        response_data = {
            "peaks": peaks, # This still contains the full timestamp for the table
            "chartData": {
                "lineTrace": {
                    "x": chart_timestamps,
                    "y": chart_edits,
                    "type": 'scatter', 'mode': 'lines+markers', 'name': 'Edits'
                },
                "peaksTrace": {
                    "x": peak_timestamps, # Now correctly formatted for the chart
                    "y": peak_values,
                    "mode": 'markers+text', 'name': 'Peaks',
                    "text": [peak_labels.get(p['timestamp'], "") for p in peaks]
                }
            }
        }
        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
