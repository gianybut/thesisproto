@echo off
REM Pothole Detection Backend — Windows Startup Script

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║   🚗 Pothole Detection Backend — Windows Launcher     ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Virtual environment not found at .venv
    echo.
    echo Please run setup first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo ✅ Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo ⚡ Starting Flask backend server...
echo.
echo   🌐 Backend:   http://localhost:5000
echo   📡 Upload:    POST http://localhost:5000/api/videos/upload
echo   📊 Dashboard: GET http://localhost:5000/api/dashboard/stats
echo.
echo   Press CTRL+C to stop the server
echo.

cd backend
set PYTHONUTF8=1
python run.py

pause
