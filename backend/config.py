import os
import configparser
from dotenv import load_dotenv
import pymysql

load_dotenv()

ENV = os.getenv("ENV", "dev")

def get_db_credentials():
    if ENV == "prod":
        cfg = configparser.ConfigParser()
        cfg.read("/data/project/community-activity-alerts-system/replica.my.cnf")
        return {
            "user": cfg["client"]["user"],
            "password": cfg["client"]["password"],
            "host": "tools.db.svc.wikimedia.cloud",
            "database": "s56391__community_alerts", #Your toolforge db name
            "DB_TABLE": "edit_counts"
        }
    else:
        return {
            "user": "wikim",
            "password": "wikimedia",
            "host": "db",  # db for docker setup
            "database": "community_alerts",
            "DB_TABLE": "edit_counts"
        }
    
def get_db_connection():
    credentials = get_db_credentials()
    return pymysql.connect(
        host=credentials["host"],
        user=credentials["user"],
        password=credentials["password"],
        database=credentials["database"],
        charset="utf8mb4",
        autocommit=True
    )

API_CONFIG = {
    "base_url": os.getenv("WIKIMEDIA_API_BASE", "https://wikimedia.org/api/rest_v1/metrics/edits/aggregate"),
    "editor_type": "all-editor-types",
    "page_type": "content",
    "granularity": "monthly"
}
