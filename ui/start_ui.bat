@echo off
REM Start UI Backend and Streamlit on Windows

echo Starting Honeypot UI...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv_ui" (
    echo Creating virtual environment...
    python -m venv venv_ui
)

REM Activate virtual environment
echo Activating virtual environment...
call venv_ui\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r ui\requirements_ui.txt

REM Create sessions directory
if not exist "ui\data" mkdir ui\data

echo.
echo Setup complete!
echo.
echo Starting services...
echo   - UI Backend: http://localhost:8001
echo   - Streamlit UI: http://localhost:8501
echo.

REM Start UI backend in background
start /B python -m uvicorn ui.ui_backend:app --host 0.0.0.0 --port 8001

REM Wait for backend
timeout /t 3 /nobreak >nul

REM Start Streamlit
start /B streamlit run ui\streamlit_app.py --server.port 8501 --server.address 0.0.0.0

echo.
echo Services started!
echo.
echo Open your browser to: http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo.

pause
