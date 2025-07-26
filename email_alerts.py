import os
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
# import json
import pymysql
import configparser

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # --- Load config from configparser file ---
# cfg = configparser.ConfigParser()
# cfg.read('/data/project/community-activity-alerts-system/production.my.cnf')

# GMAIL_USER = cfg['gmail']['user']
# GMAIL_PASSWORD = cfg['gmail']['password']
# ALERT_FROM = cfg['gmail']['from']

# # --- Load global mailing list from JSON file ---
# MAILING_LIST_FILE = "mailing_list.json"
# if not os.path.exists(MAILING_LIST_FILE):
#     logging.error("Mailing list file not found.")
#     exit(1)
# with open(MAILING_LIST_FILE, "r") as f:
#     config = json.load(f)
# MAILING_LIST = config.get("global_mailing_list", [])

MAILING_LIST = ["fuzzphorescence@gmail.com", "farzana.shjhn@gmail.com"]

GMAIL_USER="farzana.shjhn@gmail.com"
GMAIL_PASSWORD="pxes dycc hqoy mnen"
ALERT_FROM="alerts@wiki.org"

# --- Load Toolforge DB credentials ---
user = cfg['client']['user']
password = cfg['client']['password']

DB_NAME = 's56391__community_alerts'
DB_HOST = 'tools.db.svc.wikimedia.cloud'
ALERTS_TABLE = 'community_alerts'

# --- Connect to Toolforge MySQL DB using pymysql ---
conn = pymysql.connect(
    host=DB_HOST,
    user=user,
    password=password,
    database=DB_NAME,
    charset='utf8mb4',
    autocommit=True
)

# --- Load peak alerts from DB ---
df = pd.read_sql(f"SELECT * FROM {ALERTS_TABLE}", conn)
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
logging.info(f"Loaded {len(df)} peak alerts from database.")

def dataframe_to_html_table(df):
    if df.empty:
        return "<p>No data available.</p>"
    html = "<table border='1' cellpadding='4' cellspacing='0'>"
    # Header
    html += "<tr>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr>"
    # Rows
    for _, row in df.iterrows():
        html += "<tr>" + "".join(f"<td>{row[col]}</td>" for col in df.columns) + "</tr>"
    html += "</table>"
    return html

def send_email(subject, html_body, recipients):
    msg = MIMEMultipart()
    msg['From'] = ALERT_FROM
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(ALERT_FROM, recipients, msg.as_string())
        logging.info(f"Global alert email sent to {recipients}")
    except Exception as e:
        logging.error(f"Failed to send global alert email: {e}")

def main():
    columns_to_display = ["project", "timestamp", "edit_count", "rolling_mean", "threshold", "percentage_difference"]
    html_table = dataframe_to_html_table(df[columns_to_display] if columns_to_display else df)
    subject = "[Wiki Alerts] Global Peak Edit Activity"
    send_email(subject, html_table, MAILING_LIST)

if __name__ == "__main__":
    main()