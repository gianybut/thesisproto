@echo off
REM Pothole Detection Frontend — Windows Startup Script

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║   🎨 Pothole Detection Frontend — Windows Launcher    ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Node is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed
    echo.
    echo Please install Node.js 16+ from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo ✅ Node.js detected: 
node --version

cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo.
    echo 📦 Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo ❌ npm install failed
        pause
        exit /b 1
    )
)

echo.
echo ⚡ Starting React development server...
echo.
echo   🎨 Frontend:   http://localhost:5173
echo   🔗 Backend:    http://localhost:5000/api
echo   📡 API Base:   http://localhost:5000/api
echo.
echo   Press CTRL+C to stop the server
echo.

call npm run dev
