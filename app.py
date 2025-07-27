from flask import Flask, render_template, request, jsonify, redirect
from datetime import datetime
import requests
import pandas as pd
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


# --- Peak detection function ---
def find_peaks_rolling_3_years(df, threshold_percentage=0.30, metric_column="edits"):
    df = df.sort_values("timestamp").reset_index(drop=True)
    peaks = []

    for i in range(len(df)):
        t_i = df.at[i, "timestamp"]
        metric_value_i = df.at[i, metric_column]

        window = df[
            (df["timestamp"] >= t_i - pd.DateOffset(years=3)) & (df["timestamp"] <= t_i)
        ]
        if window.empty:
            continue

        rolling_mean = window[metric_column].mean()
        threshold = rolling_mean * (1 + threshold_percentage)
        pct_diff = ((metric_value_i - rolling_mean) / rolling_mean) * 100

        if metric_value_i >= threshold:
            peaks.append(
                {
                    "timestamp": t_i,
                    metric_column: metric_value_i,
                    "rolling_mean": rolling_mean,
                    "threshold": threshold,
                    "percentage_difference": pct_diff,
                }
            )

    return peaks


# --- Format peaks for display ---
def log_peaks(peaks, metric_type="edits"):
    peaks_list = []
    for peak in peaks:
        peaks_list.append(
            {
                "timestamp": peak["timestamp"].strftime("%Y-%m-%d"),
                metric_type: int(peak[metric_type]),
                "rolling_mean": round(float(peak["rolling_mean"]), 2),
                "threshold": round(float(peak["threshold"]), 2),
                "percentage_difference": round(float(peak["percentage_difference"]), 2),
            }
        )
    return peaks_list


# --- Helper function for dashboard logic ---
def get_dashboard_data(metric_type, language, project_group, datestart, dateend):
    """
    Generic function to get dashboard data for either edits or editors
    """
    if not (language and project_group and datestart and dateend):
        return None, None, None, "Missing parameters"

    project = project_group.split(":/")[1][1:]  # e.g. "en.wikipedia.org"
    start = datetime.strptime(datestart, "%b %Y")
    end = datetime.strptime(dateend, "%b %Y")
    # Set start to first day, end to last day of month
    start = start.replace(day=1, hour=0, minute=0, second=0)
    last_day = calendar.monthrange(end.year, end.month)[1]
    end = end.replace(day=last_day, hour=23, minute=59, second=59)

    try:
        conn = get_db_connection()
        
        if metric_type == "edits":
            table_name = "edit_counts"
            count_column = "edit_count"
            metric_label = "Edits"
            color = "blue"
        else:  # editors
            table_name = "editor_counts"
            count_column = "editor_count"
            metric_label = "Editors"
            color = "green"
        
        query = f"""
            SELECT timestamp, {count_column} AS count_value
            FROM {table_name}
            WHERE project = %s
              AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """
        df = pd.read_sql(query, conn, params=(project, start, end))
        conn.close()

        if df.empty:
            return [], None, None, "No data available."

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.rename(columns={'count_value': metric_type}, inplace=True)
        
        peaks_raw = find_peaks_rolling_3_years(df, threshold_percentage=0.30, metric_column=metric_type)
        peaks = log_peaks(peaks_raw, metric_type)

        # --- Generate plot ---
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df[metric_type],
                mode="lines+markers",
                name=metric_label,
                line=dict(color=color),
            )
        )

        peak_timestamps = [peak["timestamp"] for peak in peaks]
        peak_values = [peak[metric_type] for peak in peaks]
        
        # --- Fetch labels for peaks ---
        conn = get_db_connection()
        cursor = conn.cursor()
        peak_labels = {}
        alerts_table = 'community_alerts' if metric_type == 'edits' else 'editor_alerts'
        
        for peak in peaks:
            try:
                cursor.execute(f"SELECT label FROM {alerts_table} WHERE project = %s AND timestamp = %s", 
                             (project, peak['timestamp']))
                result = cursor.fetchone()
                peak_labels[peak['timestamp']] = result[0] if result and result[0] else ''
            except:
                peak_labels[peak['timestamp']] = ''
        conn.close()

        peak_labels_list = [peak_labels.get(peak['timestamp'], '') for peak in peaks]
        
        fig.add_trace(
            go.Scatter(
                x=peak_timestamps,
                y=peak_values,
                mode="markers+text",
                name="Peaks Above Threshold",
                marker=dict(color="red", size=10, symbol="circle"),
                text=peak_labels_list,
                textposition="top center",
                customdata=[{'project': project, 'timestamp': peak['timestamp']} for peak in peaks],
                hovertemplate=f"<b>Peak</b><br>Date: %{{x}}<br>{metric_label}: %{{y}}<br><extra></extra>"
            )
        )

        fig.update_layout(
            title=f"{metric_label} count over time with peaks (30% over 3-year rolling mean)",
            xaxis_title="Timestamp",
            yaxis_title=f"Count ({metric_label})",
            showlegend=True,
            # Increase chart size
            height=600,
            width=None,  # Auto width to fill container
            # Move legend to bottom
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,
                xanchor="center",
                x=0.5
            ),
            # Add margins for better spacing
            margin=dict(l=60, r=60, t=80, b=100),
            # Improve font sizes for readability
            font=dict(size=12),
            title_font=dict(size=16),
            # Better grid and background
            plot_bgcolor='white',
            paper_bgcolor='white',
            # Combined xaxis configuration
            xaxis=dict(
                tickformat="%Y-%m-%d", 
                tickangle=45,
                gridcolor='lightgray',
                gridwidth=1,
                showgrid=True
            ),
            yaxis=dict(
                gridcolor='lightgray',
                gridwidth=1,
                showgrid=True
            )
        )

        # Enable click events and configure chart
        config = {
            'displayModeBar': True, 
            'displaylogo': False,
            'responsive': True,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{metric_type}_chart',
                'height': 600,
                'width': 1200,
                'scale': 1
            }
        }
        chart_html = to_html(fig, full_html=False, include_plotlyjs="cdn", config=config)

        return peaks, chart_html, None, None

    except Exception as e:
        return [], None, None, f"Database error: {str(e)}"


# --- Main route (landing page) ---
@app.route("/")
def index():
    return render_template("landing.html")


# --- Edits Dashboard ---
@app.route("/edits")
def edits_dashboard():
    language = request.args.get("language")
    project_group = request.args.get("project_group")
    datestart = request.args.get("datestart")
    dateend = request.args.get("dateend")
    filter_edits = request.args.get("filter_edits") == "true"
    filter_users = request.args.get("filter_users") == "true"

    if not (language and project_group and datestart and dateend):
        return render_template("index.html", 
                             languages=get_all_communities(), 
                             metric_type="edits",
                             page_title="Edit Counts Dashboard")

    data, chart, _, error = get_dashboard_data("edits", language, project_group, datestart, dateend)
    
    if error:
        return render_template("index.html", 
                             languages=get_all_communities(), 
                             metric_type="edits",
                             page_title="Edit Counts Dashboard",
                             error=error)

    return render_template("index.html", 
                         languages=get_all_communities(), 
                         data=data, 
                         chart=chart,
                         metric_type="edits",
                         page_title="Edit Counts Dashboard")


# --- Editors Dashboard ---
@app.route("/editors")
def editors_dashboard():
    language = request.args.get("language")
    project_group = request.args.get("project_group")
    datestart = request.args.get("datestart")
    dateend = request.args.get("dateend")
    filter_edits = request.args.get("filter_edits") == "true"
    filter_users = request.args.get("filter_users") == "true"

    if not (language and project_group and datestart and dateend):
        return render_template("index.html", 
                             languages=get_all_communities(), 
                             metric_type="editors",
                             page_title="Editor Counts Dashboard")

    data, chart, _, error = get_dashboard_data("editors", language, project_group, datestart, dateend)
    
    if error:
        return render_template("index.html", 
                             languages=get_all_communities(), 
                             metric_type="editors",
                             page_title="Editor Counts Dashboard",
                             error=error)

    return render_template("index.html", 
                         languages=get_all_communities(), 
                         data=data, 
                         chart=chart,
                         metric_type="editors",
                         page_title="Editor Counts Dashboard")


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
@app.route('/api/update_peak_label', methods=['POST'])
def update_peak_label():
    data = request.json
    project = data['project']
    timestamp = data['timestamp']
    label = data['label']
    metric_type = data.get('metric_type', 'edits')  # Default to edits for backward compatibility
    
    table_name = 'community_alerts' if metric_type == 'edits' else 'editor_alerts'
    
    print(f"DEBUG: Updating label for project={project}, timestamp={timestamp}, label={label}, table={table_name}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"""
            UPDATE {table_name} 
            SET label = %s 
            WHERE project = %s AND timestamp = %s
        """, (label, project, timestamp))
        
        if cursor.rowcount == 0:
            print(f"DEBUG: No rows updated. Checking if record exists...")
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE project = %s AND timestamp = %s", 
                          (project, timestamp))
            count = cursor.fetchone()[0]
            print(f"DEBUG: Found {count} matching records")
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"DEBUG: Error updating label: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()


# --- API endpoint to get peak label ---
@app.route('/api/get_peak_label', methods=['GET'])
def get_peak_label():
    project = request.args.get('project')
    timestamp = request.args.get('timestamp')
    metric_type = request.args.get('metric_type', 'edits')  # Default to edits for backward compatibility
    
    table_name = 'community_alerts' if metric_type == 'edits' else 'editor_alerts'
    
    print(f"DEBUG: Getting label for project={project}, timestamp={timestamp}, table={table_name}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT label FROM {table_name} WHERE project = %s AND timestamp = %s", 
                      (project, timestamp))
        result = cursor.fetchone()
        label = result[0] if result else ''
        print(f"DEBUG: Found label: {label}")
        return jsonify({'label': label})
    except Exception as e:
        print(f"DEBUG: Error getting label: {e}")
        return jsonify({'error': str(e)})
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=False)
