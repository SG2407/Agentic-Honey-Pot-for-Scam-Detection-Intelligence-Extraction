#!/bin/bash
# Start UI Backend and Streamlit locally

echo "🚀 Starting Honeypot UI..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv_ui" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv_ui
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv_ui/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r ui/requirements_ui.txt

# Create sessions directory
mkdir -p ui/data

echo ""
echo "✅ Setup complete!"
echo ""
echo "Starting services..."
echo "  - UI Backend: http://localhost:8001"
echo "  - Streamlit UI: http://localhost:8501"
echo ""

# Start UI backend in background
echo "Starting UI Backend..."
python3 -m uvicorn ui.ui_backend:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Streamlit
echo "Starting Streamlit UI..."
streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

echo ""
echo "🎉 Services started!"
echo ""
echo "📱 Open your browser to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $STREAMLIT_PID 2>/dev/null; exit" INT

# Keep script running
wait
