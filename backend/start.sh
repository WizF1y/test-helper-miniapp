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
from mysql.database import get_db_connection
try:
    conn = get_db_connection()
    if conn:
        print('Database connection successful!')
        conn.close()
    else:
        print('Failed to connect to database')
        exit(1)
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

# Run database migrations (create tables if they don't exist)
echo "Running database migrations..."
python -c "
from app import app
from mysql.database import get_db_connection
import os

with app.app_context():
    try:
        conn = get_db_connection()
        if conn:
            print('Database tables will be created by init.sql')
            conn.close()
    except Exception as e:
        print(f'Migration error: {e}')
        exit(1)
"

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
