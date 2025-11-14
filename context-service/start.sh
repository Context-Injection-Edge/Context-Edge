#!/bin/bash
set -e

echo "Waiting for database to be ready..."
sleep 5

echo "Initializing database tables..."
python -c "from src.database.init_db import init_db; init_db()"

echo "Starting Context Edge Service..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
