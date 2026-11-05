# Community Activity Alerts

Community Activity Alerts helps users explore editing activity across Wikimedia projects. It collects monthly edit and editor statistics, identifies unusual activity peaks, and displays them through a web dashboard.

## Getting started

The easiest way to run the project locally is with Docker. Docker will set up the database, backend, frontend, and scheduled jobs for you.

## 1. Fork the repository

Before working on the project, fork the repository to your own GitHub account.

1. Visit [Community Activity Alerts](https://github.com/indictechcom/community-activity-alerts).
2. Click **Fork** in the top-right corner.
3. Create a fork under your GitHub account.

Now clone **your fork**, not the original repository:

```bash
git clone https://github.com/<your-github-username>/community-activity-alerts.git
cd community-activity-alerts
```

Replace `<your-github-username>` with your GitHub username.

## 2. Install Docker

You need Docker and Docker Compose to run the project.

- **Windows:** Install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
- **macOS:** Install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/).
- **Linux:** Install [Docker Engine](https://docs.docker.com/engine/install/) and the [Docker Compose plugin](https://docs.docker.com/compose/install/linux/).

After installation, open a terminal and check that Docker is working:

```bash
docker --version
docker compose version
```

Both commands should display their installed versions.

## 3. Configure environment variables

The backend needs a local environment file to connect to the database and configure the application.

First, create the file from the sample.

**Linux / macOS:**

```bash
cp backend/sample.env backend/.env
```

**Windows (PowerShell):**

```powershell
Copy-Item backend/sample.env backend/.env
```

Open `backend/.env` in a text editor and check the following values:

```env
ENV=dev
DB_NAME=community_alerts
BASE_URL=http://localhost:5000
FRONTEND_URL=http://localhost:5173
```

Make sure `DB_NAME` is set to `community_alerts`. This is the database created by the local Docker setup.

Keep the other sample settings unless you need to configure additional features.

**Note:** MediaWiki OAuth credentials (`CONSUMER_KEY` and `CONSUMER_SECRET`) are needed for MediaWiki login. Bot credentials (`BOT_USERNAME` and `BOT_PASSWORD`) are needed for email notifications. You can configure these when working on those features.

Do not commit your `backend/.env` file or share your private credentials.

## 4. Configure the initial data backfill

The project uses Wikimedia's API to fetch historical edit and editor statistics.

For a fresh local setup, you need to fetch historical data before the dashboard can display activity.

Open the **`docker-compose.yml`** file in the project root.

Find the `cron` service and its `environment` section:

```yaml
environment:
  ENV: dev
  SKIP_BACKFILL: "true"
```

For your **first run**, change `SKIP_BACKFILL` to `"false"`:

```yaml
environment:
  ENV: dev
  SKIP_BACKFILL: "false"
```

This tells the cron container to perform the initial historical backfill when it starts.

The backfill covers approximately six years of monthly data for both edit counts and editor counts. It can take some time to finish.

**Important:** After the initial backfill has completed successfully(after setting up the project),don't forget to change `SKIP_BACKFILL` back to `"true"` in `docker-compose.yml`. This prevents the historical backfill from running again whenever you restart the containers.

## 5. Start the application

Make sure Docker is running, then execute this command from the project root:

```bash
docker compose up --build
```

The first run may take a few minutes because Docker needs to download the required images and build the application.

Docker Compose starts the services in the required order:

1. **Database (`db`)** – Starts the MariaDB database.
2. **Migrations (`migrate`)** – Creates the application tables by applying the SQL migration files.
3. **Backend (`backend`)** – Starts the Flask application.
4. **Cron (`cron`)** – Fetches historical data on the first run and handles scheduled jobs.
5. **Frontend (`frontend`)** – Starts the Vue application.

You do not need to run the database migrations manually. The migration service handles them automatically.

Keep the terminal open while the application is running.

## 6. Open the application

Once the services have started, open the following URL in your browser:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:5000 |

The frontend is where you can explore the dashboard.

## 7. Check whether data was fetched

The initial backfill may take some time. You can check the cron logs in another terminal:

```bash
docker compose logs -f cron
```

To check whether the migrations completed successfully:

```bash
docker compose logs migrate
```

You should see messages indicating that the migration files were applied successfully.

You can also check the database directly:

```bash
docker compose exec db mariadb -u wikim -pwikimedia community_alerts
```

Once connected, run:

```sql
SHOW TABLES;

SELECT COUNT(*) FROM edit_counts;
SELECT COUNT(*) FROM editor_counts;
```

Both tables should contain records after the backfill has completed.

Type `exit` to leave the MariaDB prompt.

## 8. Stop the application

To stop the running containers, press `Ctrl + C` in the terminal where Docker Compose is running.

You can also run:

```bash
docker compose down
```

This stops and removes the containers and networks but **keeps your database data**.

To start the application again:

```bash
docker compose up
```

You do not need to run the initial backfill again. Keep `SKIP_BACKFILL` set to `"true"` after the first successful backfill.

## 9. Start with a clean database

If you want to reset your local development environment and start from scratch, run:

```bash
docker compose down --volumes --rmi local --remove-orphans
```

This removes the project's containers, database volume, networks, and locally built images.

**Warning:** This permanently deletes the local database and all data stored in it. Do not run this command if you want to keep your existing data.

After resetting, follow the setup instructions again, including setting `SKIP_BACKFILL` to `"false"` for the new initial backfill.

---

## Project structure

```text
community-activity-alerts/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── migrate.py
│   ├── migrations/
│   ├── alerts/
│   ├── annotation/
│   ├── auth/
│   ├── notification/
│   └── subscription/
│
├── cron/
│   ├── fetch_and_store_cron.py
│   ├── fetch_and_store_editors_cron.py
│   ├── monthly_peak_detection.py
│   ├── cronjob
│   └── Dockerfile
│
├── frontend/
│   └── src/
│
├── docker-compose.yml
└── init.sql
```

### Main components

- **Backend:** Flask application that provides APIs and handles application logic.
- **Frontend:** Vue application used to display activity data and interact with the dashboard.
- **Database:** MariaDB database that stores monthly statistics, detected peaks, annotations, and subscriptions.
- **Cron:** Scripts that fetch Wikimedia statistics, detect activity peaks, and handle scheduled notifications.
- **Migrations:** SQL files in `backend/migrations/` that create and update the database schema.

## Contributing

We welcome contributions! If you want to work on an issue or add a feature:

1. Fork the repository.
2. Clone your fork to your computer.
3. Create a new branch for your changes.
4. Make your changes and test them locally.
5. Push your branch to your fork.
6. Open a Pull Request against the original repository.

For questions or discussions, open an issue in the [GitHub repository](https://github.com/indictechcom/community-activity-alerts).
