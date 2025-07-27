import os
import smtplib
import pandas as pd
import pymysql
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import configparser
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load config from configparser file ---
cfg = configparser.ConfigParser()
cfg.read('/data/project/community-activity-alerts-system/replica.my.cnf')

# Gmail settings
GMAIL_USER = "farzana.shjhn@gmail.com"
GMAIL_PASSWORD = "kdbg vpvl relw uetx"
ALERT_FROM = "alerts@wiki.org"

# Mailing list
MAILING_LIST = ["fuzzphorescence@gmail.com", "farzana.shjhn@gmail.com"]

# Toolforge DB credentials
user = cfg['client']['user']
password = cfg['client']['password']
DB_NAME = 's56391__community_alerts'
DB_HOST = 'tools.db.svc.wikimedia.cloud'
ALERTS_TABLE = 'community_alerts'

# --- Connect to MySQL DB ---
conn = pymysql.connect(
    host=DB_HOST,
    user=user,
    password=password,
    database=DB_NAME,
    charset='utf8mb4',
    autocommit=True
)

# --- Utility Functions ---
def dataframe_to_html_table(df):
    if df.empty:
        return "<p>No data available.</p>"
    style = """
        <style>
            table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }
            th, td { padding: 8px 12px; border: 1px solid #ddd; text-align: center; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    """
    html = "<table>"
    html += "<tr>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr>"
    for _, row in df.iterrows():
        html += "<tr>" + "".join(f"<td>{row[col]}</td>" for col in df.columns) + "</tr>"
    html += "</table>"
    return style + html

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
        logging.info(f"Alert email sent to {recipients}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def build_email_content(df_filtered):
    intro = "<p>This is a summary of peak edit activities across projects for the last month.</p>"
    html_table = dataframe_to_html_table(df_filtered)

    top_alerts = df_filtered.sort_values(by='percentage_difference', ascending=False).head(3)
    summary = ""
    if not top_alerts.empty:
        summary += "<h3>Top 3 Activity Alerts by % Difference</h3><ul>"
        for _, row in top_alerts.iterrows():
            summary += (
                f"<li><b>{row['project']}</b> on {row['timestamp']} — "
                f"Edits: {row['edit_count']}, "
                f"Δ: {row['percentage_difference']:.2f}%</li>"
            )
        summary += "</ul>"

    return intro + summary + "<h3>All Activity Peaks</h3>" + html_table

# --- Main ---
def main():
    try:
        df = pd.read_sql(f"SELECT * FROM {ALERTS_TABLE}", conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        logging.info(f"Loaded {len(df)} alerts from DB.")
    except Exception as e:
        logging.error(f"Error loading alerts: {e}")
        return

    now = datetime.now().replace(day=1)
    last_month = now - relativedelta(months=1)

    df_filtered = df[
        (df['year'] == last_month.year) & (df['month'] == last_month.month)
    ].copy()

    if df_filtered.empty:
        logging.info("No alerts found for the previous month.")
        return

    df_filtered.drop(columns=['year', 'month'], inplace=True)
    df_filtered['timestamp'] = df_filtered['timestamp'].dt.strftime("%Y-%m-%d")

    subject = "[Wiki Alerts] Peak Edit Activity for Last Month"
    email_body = "<h2>Alerts for Last Month</h2>" + build_email_content(df_filtered)
    send_email(subject, email_body, MAILING_LIST)

if __name__ == "__main__":
    main()

