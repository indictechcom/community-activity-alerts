import os
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging
import json

# --- Load environment variables ---
load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
ALERT_FROM = os.getenv("ALERT_FROM")

# --- Load mailing list from JSON file ---
MAILING_LIST_FILE = "mailing_list.json"
if not os.path.exists(MAILING_LIST_FILE):
    logging.error("Mailing list file not found.")
    exit(1)
with open(MAILING_LIST_FILE, "r") as f:
    MAILING_LIST = json.load(f)

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PEAK_ALERTS_FILE = "peak_alerts.csv"  # Simulated alerts file

if not os.path.exists(PEAK_ALERTS_FILE):
    logging.error("Peak alerts file not found.")
    exit(1)

df = pd.read_csv(PEAK_ALERTS_FILE)
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

def send_email(subject, body, recipients, project):
    msg = MIMEMultipart()
    msg['From'] = ALERT_FROM
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(ALERT_FROM, recipients, msg.as_string())
        logging.info(f"Email for {project} sent to {recipients}")
    except Exception as e:
        logging.error(f"Failed to send email for {project}: {e}")

def format_alerts(project, alerts):
    lines = [f"Peak alerts for {project}:"]
    for _, alert in alerts.iterrows():
        lines.append(
            f"- {alert['timestamp'].strftime('%Y-%m-%d')}: Edits={alert['edit_count']}, "
            f"Rolling Mean={alert['rolling_mean']:.2f}, Threshold={alert['threshold']:.2f}, "
            f"Diff={alert['percentage_difference']:.2f}%"
        )
    return "\n".join(lines)

def main():
    for project, recipients in MAILING_LIST.items():
        project_alerts = df[df['project'] == project]
        if project_alerts.empty:
            continue
        subject = f"[Wiki Alerts] Peak edit activity for {project}"
        body = format_alerts(project, project_alerts)
        send_email(subject, body, recipients, project)

if __name__ == "__main__":
    main()