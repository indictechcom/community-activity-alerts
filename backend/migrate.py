import os
import logging
import pymysql
# Ensure we can import config relative to this script
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_migration_table(cursor):
    """Ensures the table that tracks migrations exists."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            migration_file VARCHAR(255) NOT NULL UNIQUE,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

def run_sql_file(cursor, filepath):
    """Reads a SQL file and executes commands."""
    with open(filepath, 'r') as f:
        sql_content = f.read()
    
    # Simple split by semicolon to handle multiple statements
    statements = sql_content.split(';')
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)

def migrate():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    migrations_dir = os.path.join(base_dir, 'migrations')

    if not os.path.exists(migrations_dir):
        logger.error(f"Migrations directory not found at {migrations_dir}")
        return

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Ensure we can track what we've done
            setup_migration_table(cursor)

            # 2. Get list of already applied migrations
            cursor.execute("SELECT migration_file FROM schema_migrations")
            applied_migrations = {row[0] for row in cursor.fetchall()}

            # 3. Get all available migration files and sort them (001, 002, etc.)
            migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])

            # 4. Apply pending migrations
            files_applied = 0
            for mig_file in migration_files:
                if mig_file not in applied_migrations:
                    logger.info(f"Applying migration: {mig_file}...")
                    
                    file_path = os.path.join(migrations_dir, mig_file)
                    try:
                        run_sql_file(cursor, file_path)
                        
                        # Record success
                        cursor.execute("INSERT INTO schema_migrations (migration_file) VALUES (%s)", (mig_file,))
                        conn.commit() # Commit after each file for safety
                        logger.info(f"Successfully applied {mig_file}")
                        files_applied += 1
                    except Exception as e:
                        logger.error(f"Failed to apply {mig_file}: {e}")
                        conn.rollback() # Rollback this specific file's changes
                        raise e # Stop the entire process
                else:
                    logger.debug(f"Skipping {mig_file} (already applied)")
            
            if files_applied == 0:
                logger.info("Database is up to date. No new migrations.")
            else:
                logger.info(f"Migration process complete. Applied {files_applied} files.")

    except Exception as e:
        logger.error(f"Critical Migration Error: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()