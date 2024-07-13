@echo off
echo Setting up Finance Tracker...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b 1
)

REM Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt

REM Create SQLite database
echo Creating SQLite database...
python -c "import sqlite3; conn = sqlite3.connect('finance_tracker.db'); conn.close()"

echo Setup complete! You can now run the app using: streamlit run app.py
pause