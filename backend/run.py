#!/usr/bin/env python
"""Run the Pothole Detection Backend Server."""

import os
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

if __name__ == '__main__':
    app = create_app()
    
    print("\n" + "="*60)
    print("🚀 Pothole Detection Backend Server")
    print("="*60)
    print("\n📍 Starting Flask server...")
    print("   🌐 Local:     http://localhost:5000")
    print("   📡 API Docs:  http://localhost:5000/api/*")
    print("\n⚡ Press CTRL+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
