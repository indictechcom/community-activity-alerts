from flask import Flask, jsonify, request, send_from_directory
import pandas as pd
import pymysql
import configparser
import os

app = Flask(__name__, static_folder="dist")

# --- DB Config ---
cfg = configparser.ConfigParser()
cfg.read("/data/project/community-activity-alerts-system/replica.my.cnf")
user = cfg["client"]["user"]
password = cfg["client"]["password"]
DB_NAME = "s56391__community_alerts"

# --- DB Connection ---
def get_connection():
    return pymysql.connect(
        host="tools.db.svc.wikimedia.cloud",
        user=user,
        password=password,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=True
    )

# --- API to get available projects ---
@app.route("/api/projects")
def get_projects():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT project FROM community_alerts ORDER BY project", conn)
    conn.close()
    return jsonify(df["project"].tolist())

# --- API to get peaks + edits for a project ---
@app.route("/api/project/<project>")
def get_project_data(project):
    conn = get_connection()

    # Peak data
    peaks_df = pd.read_sql(
        "SELECT * FROM community_alerts WHERE project=%s ORDER BY timestamp",
        conn,
        params=[project]
    )

    # Edit history
    edits_df = pd.read_sql(
        "SELECT timestamp, edit_count FROM edit_counts WHERE project=%s ORDER BY timestamp",
        conn,
        params=[project]
    )
    conn.close()

    return jsonify({
        "peaks": peaks_df.to_dict(orient="records"),
        "edits": edits_df.to_dict(orient="records")
    })

# --- API to update a peak label ---
@app.route("/api/update_peak_label", methods=["POST"])
def update_peak_label():
    data = request.get_json()
    project = data.get("project")
    timestamp = data.get("timestamp")
    label = data.get("label")

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO peak_labels (project, timestamp, label)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE label=VALUES(label)
        """, (project, timestamp, label))
    conn.close()

    return jsonify({"status": "success"})

# --- Serve Vue Frontend ---
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_vue(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True)

