#!/bin/bash
# Pothole Detection Frontend — Linux/Mac Startup Script

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   🎨 Pothole Detection Frontend — Launcher             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo ""
    echo "Please install Node.js 16+ from: https://nodejs.org/"
    echo ""
    exit 1
fi

echo "✅ Node.js detected: $(node --version)"

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo ""
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ npm install failed"
        exit 1
    fi
fi

echo ""
echo "⚡ Starting React development server..."
echo ""
echo "   🎨 Frontend:   http://localhost:5173"
echo "   🔗 Backend:    http://localhost:5000/api"
echo "   📡 API Base:   http://localhost:5000/api"
echo ""
echo "   Press CTRL+C to stop the server"
echo ""

npm run dev
