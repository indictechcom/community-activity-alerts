# Community Activity Alerts

## Overview

This project tracks and analyzes edit activity across Wikimedia projects. It consists of scripts for fetching, storing, and analyzing edit data, as well as a web interface for visualization.

## Script Descriptions

### fetch_and_store_cron.py

- **Purpose:** Fetches monthly edit counts for all Wikimedia projects from the Wikimedia API and stores them in the `edit_counts` table in the database.
- **How it works:**
  - Downloads edit count data for each project.
  - Ensures the `edit_counts` table exists.
  - Inserts or updates edit counts for each project and month.
- **Intended use:** Run regularly (e.g., as a cron job) to keep the edit counts up to date.

### fetch_and_store_script.py

- **Purpose:** Similar to `fetch_and_store_cron.py`; may be used for manual runs or testing.
- **How it works:**
  - Fetches edit counts from the Wikimedia API.
  - Stores results in the `edit_counts` table.
- **Intended use:** Manual or ad-hoc data fetching.

### Community alerts .py

- **Purpose:** Detects peaks (unusual spikes) in edit activity for each project and stores these as alerts in the `community_alerts` table.
- **How it works:**
  - Reads all edit data from `edit_counts`.
  - Runs a peak detection algorithm for each project.
  - Stores detected peaks in the `community_alerts` table.
- **Intended use:** Run after edit data is up to date, to analyze and record significant activity spikes.

## Database Tables

- `edit_counts`: Stores raw monthly edit counts for each project.
- `community_alerts`: Stores detected peaks/alerts for each project.

## Local Setup

### Prerequisites
- Python 3.7+
- MySQL server
- Virtual environment (recommended)

### MySQL Installation

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

**macOS:**
```bash
# Using Homebrew
brew install mysql
brew services start mysql
```

**Windows:**
- Download MySQL installer from [mysql.com](https://dev.mysql.com/downloads/installer/)
- Run installer and follow setup wizard
- Start MySQL service 

> **Note:** For production setups, consider running `mysql_secure_installation` to enhance security. For local development, this is optional.

### Installation

1. **Clone and set up environment:**
   ```bash
   git clone <repository-url>
   cd community-activity-alerts
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up MySQL database:**
   
   **Connect to MySQL:**
   ```bash
   # Connect as root (default) or your MySQL user
   mysql -u root -p
   ```
   
   **Create database and user:**
   ```sql
   -- Create the database
   CREATE DATABASE community_alerts;
   
   -- Create a user for the application
   CREATE USER 'wikim'@'localhost' IDENTIFIED BY 'wikimedia';
   
   -- Grant privileges to the user
   GRANT ALL PRIVILEGES ON community_alerts.* TO 'wikim'@'localhost';
   
   -- Apply changes
   FLUSH PRIVILEGES;
   
   -- Exit MySQL
   EXIT;
   ```

3. **Configure database connection:**
   
   Edit the database connection settings in your Python files:
   - In `app.py`: Update the `get_db_connection()` function
   - In other scripts: Update the database configuration variables
   
   ```python
   # Example configuration (adjust as needed)
   conn = pymysql.connect(
       host="localhost",           # Your MySQL host
       user='wikim',              # Your MySQL username
       password='wikimedia',      # Your MySQL password
       database="community_alerts", # Your database name
       charset="utf8mb4",
   )
   ```

4. **Create database tables:**
   
   The tables will be created automatically when you run the scripts for the first time. The application creates:
   - `edit_counts`: Stores raw monthly edit counts
   - `community_alerts`: Stores detected activity peaks

5. **Collect data:**
   ```bash
   python fetch_and_store_cron.py
   ```
   This fetches 3 years of edit data for all Wikimedia projects (may take 30+ minutes).

6. **Generate alerts:**
   ```bash
   python "Community alerts .py"
   ```
   This analyzes the data and detects activity peaks.

7. **Start the web interface:**
   ```bash
   python app.py
   ```
   Visit `http://localhost:5000` to explore the data.

### Troubleshooting

- **MySQL connection issues:** Verify MySQL is running and credentials are correct
- **Permission errors:** Ensure the MySQL user has proper privileges on the database
- **Port conflicts:** Default MySQL port is 3306, Flask runs on port 5000
- **OS-specific MySQL setup:** Refer to official MySQL documentation for your operating system

## Usage

The web interface allows you to:
- Select different Wikimedia language communities and projects
- Set custom date ranges with an interactive slider
- View detected activity peaks in both table and chart format
- Click on chart peaks to add labels and annotations