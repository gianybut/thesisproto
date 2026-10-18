#!/bin/bash
# Pothole Detection Backend — Linux/Mac Startup Script

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   🚗 Pothole Detection Backend — Launcher             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found at .venv"
    echo ""
    echo "Please run setup first:"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

echo "✅ Activating virtual environment..."
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
else
    source .venv/Scripts/activate   # Git Bash on Windows
fi

echo ""
echo "⚡ Starting Flask backend server..."
echo ""
echo "   🌐 Backend:   http://localhost:5000"
echo "   📡 Upload:    POST http://localhost:5000/api/videos/upload"
echo "   📊 Dashboard: GET http://localhost:5000/api/dashboard/stats"
echo ""
echo "   Press CTRL+C to stop the server"
echo ""

cd backend
python run.py
