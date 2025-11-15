#!/bin/sh

echo "=== Debug Info ==="
echo "Current directory:"
pwd
echo ""
echo "Files in /app:"
ls -la /app/
echo ""
echo "Files in /app/src:"
ls -la /app/src/ 2>/dev/null || echo "No /app/src directory"
echo ""
echo "PYTHONPATH: $PYTHONPATH"
echo ""
echo "Python version:"
python3 --version
echo ""
echo "=== Starting uvicorn ==="

# Try to run from src directory
cd /app/src && python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
