#!/usr/bin/env python3
"""
Quick Backend Test Script
Simple connectivity test for your Railway deployment
"""

import requests
import sys

def quick_test(base_url):
    """Quick test of basic backend functionality"""
    base_url = base_url.rstrip('/')
    
    print(f"🧪 Quick Testing: {base_url}")
    print("=" * 50)
    
    # Test 1: Health Check
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data.get('status', 'unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False
    
    # Test 2: CORS Check
    try:
        response = requests.options(f"{base_url}/api/health", timeout=10)
        print(f"✅ CORS Check: {response.status_code}")
    except Exception as e:
        print(f"⚠️ CORS Check Warning: {e}")
    
    # Test 3: Registration Endpoint (without actually registering)
    try:
        response = requests.post(f"{base_url}/api/auth/register", 
                               json={}, timeout=10)
        if response.status_code == 400:  # Expected for empty data
            print("✅ Registration Endpoint: Accessible")
        else:
            print(f"⚠️ Registration Endpoint: Unexpected response {response.status_code}")
    except Exception as e:
        print(f"❌ Registration Endpoint Error: {e}")
    
    print("\n🎉 Basic connectivity test completed!")
    print("For comprehensive testing, use: python verify_deployment.py <url>")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_test.py <base_url>")
        print("Example: python quick_test.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    success = quick_test(base_url)
    sys.exit(0 if success else 1) 