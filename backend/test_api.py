#!/usr/bin/env python
"""Quick test script for backend API endpoints."""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_auth():
    """Test authentication endpoints."""
    print_section("1️⃣ Testing Authentication")
    
    # Login with default admin
    print("🔐 Testing login...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    user_id = response.json().get('user', {}).get('id')
    return user_id

def test_user_endpoints(user_id):
    """Test user endpoints."""
    headers = {"Authorization": f"Bearer {user_id}"}
    
    print("👤 Testing get current user...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_videos(user_id):
    """Test video endpoints."""
    print_section("2️⃣ Testing Video Management")
    headers = {"Authorization": f"Bearer {user_id}"}
    
    print("📹 Listing videos...")
    response = requests.get(f"{BASE_URL}/videos", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_dashboard(user_id):
    """Test dashboard statistics."""
    print_section("3️⃣ Testing Dashboard Statistics")
    headers = {"Authorization": f"Bearer {user_id}"}
    
    print("📊 Fetching dashboard stats...")
    response = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║    🚗 Pothole Detection Backend — API Test Suite       ║
╚══════════════════════════════════════════════════════════╝

This script tests the backend API endpoints.

Make sure the backend is running:
    python backend/run.py

    """)
    
    try:
        user_id = test_auth()
        if user_id:
            test_user_endpoints(user_id)
            test_videos(user_id)
            test_dashboard(user_id)
            
            print_section("✅ All Tests Completed")
            print("\n📝 Next steps:")
            print("   1. Test video upload with: curl -F 'video=@sample.mp4' ...")
            print("   2. Check backend README for full API documentation")
            print("   3. Build frontend React app")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend at http://localhost:5000")
        print("   Make sure the backend is running: python backend/run.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
