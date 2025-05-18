#!/bin/bash
# Environment variables are set by Docker Compose via env_file and environment directives.
# The .env file is sourced by docker-compose, and specific overrides like MYSQL_HOST=mysql-db
# are applied from the 'environment' section of docker-compose.yml.

echo "Waiting for MySQL to be ready..."
MAX_RETRIES=30
RETRY_INTERVAL=5
RETRY_COUNT=0
# Add MySQL configuration
export MYSQL_VARIABLES="wait_timeout=600 innodb_lock_wait_timeout=50 innodb_deadlock_detect=ON"

# Function to check if MySQL is ready
check_mysql() {
  python -c "
import pymysql
import os
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        connection = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', 'mysql-db'),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', 'yourrootpassword'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            connect_timeout=10
        )
        connection.close()
        exit(0)
    except Exception as e:
        if attempt == max_retries - 1:
            print(f'MySQL connection failed: {e}')
            exit(1)
        time.sleep(2 ** attempt)  # Exponential backoff
"
}

# Wait for MySQL to be ready
while ! check_mysql; do
  RETRY_COUNT=$((RETRY_COUNT+1))
  if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "Maximum retries reached. MySQL is still not available. Continuing anyway..."
    break
  fi
  echo "Waiting for MySQL to be ready... (attempt $RETRY_COUNT of $MAX_RETRIES)"
  sleep $RETRY_INTERVAL
done

echo "MySQL is ready (or max retries reached)."

echo "Running init_db.py..."
python init_db.py
echo "init_db.py finished."

echo "Starting Uvicorn for FastAPI application..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 