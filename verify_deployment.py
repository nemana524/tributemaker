#!/usr/bin/env python3
"""
TributeMaker Deployment Verification Script
Tests all critical endpoints after Railway deployment
"""

import requests
import json
import sys
import time
from datetime import datetime

class DeploymentVerifier:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.jwt_token = None
        
    def test_health_check(self):
        """Test the health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health Check: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ Health Check Failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health Check Error: {e}")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        try:
            test_email = f"test_{int(time.time())}@example.com"
            data = {
                "email": test_email,
                "password": "test123456",
                "name": "Test User"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                print("✅ User Registration: Success")
                return True, test_email
            else:
                print(f"❌ User Registration Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ User Registration Error: {e}")
            return False, None
    
    def test_user_login(self, email):
        """Test user login"""
        try:
            data = {
                "email": email,
                "password": "test123456"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.jwt_token = result.get('access_token')
                print("✅ User Login: Success")
                return True
            else:
                print(f"❌ User Login Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ User Login Error: {e}")
            return False
    
    def test_protected_endpoint(self):
        """Test a protected endpoint with JWT"""
        if not self.jwt_token:
            print("❌ Protected Endpoint: No JWT token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = self.session.get(
                f"{self.base_url}/api/tributes",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Protected Endpoint: Success")
                return True
            else:
                print(f"❌ Protected Endpoint Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Protected Endpoint Error: {e}")
            return False
    
    def test_music_status(self):
        """Test music system status"""
        if not self.jwt_token:
            print("❌ Music Status: No JWT token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = self.session.get(
                f"{self.base_url}/api/music/status",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                ffmpeg_status = "✅" if data.get('ffmpeg_available') else "⚠️"
                print(f"✅ Music Status: {ffmpeg_status} FFmpeg available: {data.get('ffmpeg_available')}")
                print(f"   Available music files: {data.get('available_count', 0)}/{data.get('total_count', 0)}")
                return True
            else:
                print(f"❌ Music Status Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Music Status Error: {e}")
            return False
    
    def run_verification(self):
        """Run all verification tests"""
        print("🚀 TributeMaker Deployment Verification")
        print("=" * 50)
        print(f"Testing: {self.base_url}")
        print(f"Time: {datetime.now().isoformat()}")
        print()
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", lambda: self.test_user_registration()[0]),
            ("User Login", lambda: self.test_user_login(self.test_user_registration()[1]) if self.test_user_registration()[1] else False),
            ("Protected Endpoint", self.test_protected_endpoint),
            ("Music System", self.test_music_status)
        ]
        
        # Run registration and login together
        reg_success, test_email = self.test_user_registration()
        if reg_success and test_email:
            login_success = self.test_user_login(test_email)
        else:
            login_success = False
        
        # Run other tests
        results = {
            "Health Check": self.test_health_check(),
            "User Registration": reg_success,
            "User Login": login_success,
            "Protected Endpoint": self.test_protected_endpoint(),
            "Music System": self.test_music_status()
        }
        
        print()
        print("📊 Verification Summary")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print()
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Deployment is successful!")
            return True
        else:
            print("⚠️ Some tests failed. Check the logs above for details.")
            return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python verify_deployment.py <base_url>")
        print("Example: python verify_deployment.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    verifier = DeploymentVerifier(base_url)
    success = verifier.run_verification()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 