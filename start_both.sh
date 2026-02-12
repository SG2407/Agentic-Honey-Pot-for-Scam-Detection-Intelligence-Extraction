#!/bin/bash
# Startup script to run both services in one Render deployment

echo "🚀 Starting Honeypot System with UI..."

# Start UI Backend on port 8001 in background
echo "Starting UI Backend on port 8001..."
uvicorn ui.ui_backend:app --host 0.0.0.0 --port 8001 &
UI_PID=$!

# Wait a moment for UI backend to start
sleep 3

# Start main honeypot on $PORT (Render provides this)
echo "Starting Main Honeypot on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# If main app exits, kill UI backend
kill $UI_PID 2>/dev/null
