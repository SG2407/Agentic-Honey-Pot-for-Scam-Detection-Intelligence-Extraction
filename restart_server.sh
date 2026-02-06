#!/bin/bash

echo "============================================"
echo "Restarting Server with Fixed Dependencies"
echo "============================================"
echo ""

# Find and kill existing server process
echo "Stopping existing server..."
pkill -f "uvicorn app.main:app" || echo "No server running"
sleep 2

# Start server
echo ""
echo "Starting server with fixed OpenAI dependency..."
cd /Users/sahil/Documents/Projects/Delhi_Hackathon

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start server in background
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
SERVER_PID=$!

echo "Server started with PID: $SERVER_PID"
echo ""
echo "Waiting for server to start..."
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server is running successfully!"
    echo ""
    echo "Logs are being written to: server.log"
    echo "To view logs: tail -f server.log"
    echo "To stop server: kill $SERVER_PID"
else
    echo "❌ Server failed to start. Check server.log for errors"
fi

echo ""
echo "============================================"
