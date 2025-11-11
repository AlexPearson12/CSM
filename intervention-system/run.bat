@echo off
echo ==========================================
echo   Intervention Tracking System
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -q -r requirements.txt

REM Check if demo data exists
if not exist "data\demo_graph.ttl" (
    echo.
    echo No demo data found. Generating...
    python demo_data_generator.py
)

REM Run the app
echo.
echo ==========================================
echo   Starting server...
echo ==========================================
echo.
echo. Intervention Tracking System
echo.
echo. Open your browser and visit:
echo    http://localhost:5000
echo.
echo. Available pages:
echo    * Home: http://localhost:5000/
echo    * Participants: http://localhost:5000/participants
echo    * Encounters: http://localhost:5000/encounters
echo    * Analytics: http://localhost:5000/analytics
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

python app.py
