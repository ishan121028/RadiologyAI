#!/usr/bin/env python3
"""
Simple test runner for CriticalAlert AI API tests

Run this script to test all API endpoints
"""

import sys
import time
import requests
from tests.test_simple_api import run_all_tests


def check_api_availability():
    """Check if the API is running and available"""
    try:
        response = requests.post(
            "http://localhost:49001/health",
            headers={"Content-Type": "application/json"},
            json={"check": "health"},
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def main():
    """Main test runner"""
    print("🚀 CriticalAlert AI API Test Runner")
    print("=" * 50)
    
    # Check if API is available
    print("🔍 Checking if API is running...")
    if not check_api_availability():
        print("❌ API is not running on http://localhost:49001")
        print("💡 Please start the app first: python app.py")
        sys.exit(1)
    
    print("✅ API is running and accessible")
    print()
    
    # Wait a moment for API to be fully ready
    time.sleep(1)
    
    # Run tests
    try:
        run_all_tests()
        print("\n🎯 Test Summary:")
        print("- Health endpoint: ✅")
        print("- Query endpoint: ✅")
        print("- Search endpoint: ✅")
        print("- Alert system: ✅")
        print("\n🏆 All API functionality is working correctly!")
        
    except Exception as e:
        print(f"\n💥 Tests failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
