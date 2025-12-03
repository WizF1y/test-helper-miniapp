#!/bin/bash

set -e

echo "=========================================="
echo "Starting Politics Solver Backend"
echo "=========================================="

# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."
max_retries=30
retry_count=0

while ! nc -z mysql 3306; do
  retry_count=$((retry_count + 1))
  if [ $retry_count -ge $max_retries ]; then
    echo "Error: MySQL failed to start within expected time"
    exit 1
  fi
  echo "MySQL is unavailable - sleeping (attempt $retry_count/$max_retries)"
  sleep 2
done

echo "MySQL is up and running!"

# Additional wait to ensure MySQL is fully initialized
sleep 5

# Test database connection
echo "Testing database connection..."
python -c "
import pymysql
import os
try:
    conn = pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'mysql'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DATABASE', 'sz_exam'),
        charset='utf8mb4'
    )
    print('Database connection successful!')
    conn.close()
except Exception as e:
    print(f'Database connection error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "Error: Database connection test failed"
    exit 1
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p questions

# Database tables are created by init.sql during MySQL container startup
echo "Database initialization complete!"

# Start the application
echo "Starting Flask application..."
if [ "${DEBUG_MODE}" = "True" ]; then
    echo "Running in DEBUG mode"
    python app.py
else
    echo "Running in PRODUCTION mode with gunicorn"
    gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log app:app
fi
