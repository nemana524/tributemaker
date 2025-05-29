#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script
Tests all major backend functions before deployment
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_EMAIL = "test@tributemaker.com"
TEST_PASSWORD = "test123456"
TEST_NAME = "Test User"

class BackendTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.tribute_id = None
        self.generation_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        if not success and details:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, "Connection failed", str(e))
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        try:
            data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": TEST_NAME
            }
            
            response = requests.post(f"{BASE_URL}/api/auth/register", json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.user_id = result.get('user_id')
                self.log_test("User Registration", True, f"User ID: {self.user_id}")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, "Request failed", str(e))
            return False
    
    def test_user_login(self):
        """Test user login"""
        try:
            data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = requests.post(f"{BASE_URL}/api/auth/login", json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                user_info = result.get('user', {})
                self.log_test("User Login", True, f"Token received, User: {user_info.get('name')}")
                return True
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Login", False, "Request failed", str(e))
            return False
    
    def test_protected_endpoint(self):
        """Test protected endpoint access"""
        if not self.access_token:
            self.log_test("Protected Endpoint", False, "No access token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{BASE_URL}/api/tributes", headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                tributes = result.get('tributes', [])
                self.log_test("Protected Endpoint", True, f"Retrieved {len(tributes)} tributes")
                return True
            else:
                self.log_test("Protected Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Protected Endpoint", False, "Request failed", str(e))
            return False
    
    def test_tribute_creation(self):
        """Test tribute creation"""
        if not self.access_token:
            self.log_test("Tribute Creation", False, "No access token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            data = {
                "title": "Test Tribute",
                "message": "This is a test tribute message for backend testing.",
                "music_choice": "custom",
                "custom_music_url": "/api/files/music/test.mp3",
                "images": []  # Empty for custom music tribute
            }
            
            response = requests.post(f"{BASE_URL}/api/tributes", json=data, headers=headers, timeout=10)
            
            if response.status_code == 201:
                result = response.json()
                self.tribute_id = result.get('tribute_id')
                self.log_test("Tribute Creation", True, f"Tribute ID: {self.tribute_id}")
                return True
            else:
                self.log_test("Tribute Creation", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Tribute Creation", False, "Request failed", str(e))
            return False
    
    def test_video_generation(self):
        """Test video generation"""
        if not self.access_token or not self.tribute_id:
            self.log_test("Video Generation", False, "Missing access token or tribute ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            data = {"tribute_id": self.tribute_id}
            
            response = requests.post(f"{BASE_URL}/api/video/generate", json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.generation_id = result.get('generation_id')
                self.log_test("Video Generation", True, f"Generation ID: {self.generation_id}")
                return True
            else:
                self.log_test("Video Generation", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Video Generation", False, "Request failed", str(e))
            return False
    
    def test_video_status(self):
        """Test video generation status"""
        if not self.access_token or not self.generation_id:
            self.log_test("Video Status", False, "Missing access token or generation ID")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{BASE_URL}/api/video/status/{self.generation_id}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                progress = result.get('progress', 0)
                self.log_test("Video Status", True, f"Status: {status}, Progress: {progress}%")
                return True
            else:
                self.log_test("Video Status", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Video Status", False, "Request failed", str(e))
            return False
    
    def test_music_endpoints(self):
        """Test music-related endpoints"""
        if not self.access_token:
            self.log_test("Music Endpoints", False, "No access token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test available music
            response = requests.get(f"{BASE_URL}/api/music/available", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                music_count = len(result.get('music', []))
                self.log_test("Music Available", True, f"Found {music_count} music options")
            else:
                self.log_test("Music Available", False, f"Status: {response.status_code}")
                return False
            
            # Test music status
            response = requests.get(f"{BASE_URL}/api/music/status", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                ffmpeg_available = result.get('ffmpeg_available', False)
                available_count = result.get('available_count', 0)
                self.log_test("Music Status", True, f"FFmpeg: {ffmpeg_available}, Available: {available_count}")
                return True
            else:
                self.log_test("Music Status", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Music Endpoints", False, "Request failed", str(e))
            return False
    
    def test_database_connection(self):
        """Test database connection by checking if we can query users"""
        try:
            # Import here to avoid circular imports
            from app import app, db, User
            
            with app.app_context():
                # Try to query the database
                user_count = User.query.count()
                self.log_test("Database Connection", True, f"Found {user_count} users in database")
                return True
                
        except Exception as e:
            self.log_test("Database Connection", False, "Database query failed", str(e))
            return False
    
    def test_file_upload_directories(self):
        """Test if upload directories exist and are writable"""
        try:
            from app import app
            
            upload_folder = app.config['UPLOAD_FOLDER']
            directories = ['images', 'videos', 'music']
            
            all_good = True
            for directory in directories:
                dir_path = os.path.join(upload_folder, directory)
                
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    # Test write permission
                    test_file = os.path.join(dir_path, 'test_write.tmp')
                    try:
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        self.log_test(f"Upload Directory ({directory})", True, f"Writable: {dir_path}")
                    except:
                        self.log_test(f"Upload Directory ({directory})", False, f"Not writable: {dir_path}")
                        all_good = False
                else:
                    self.log_test(f"Upload Directory ({directory})", False, f"Missing: {dir_path}")
                    all_good = False
            
            return all_good
            
        except Exception as e:
            self.log_test("Upload Directories", False, "Check failed", str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Backend Testing...")
        print("=" * 50)
        
        # Basic connectivity tests
        if not self.test_health_check():
            print("❌ Server is not running or not accessible!")
            return False
        
        # Database tests
        self.test_database_connection()
        
        # File system tests
        self.test_file_upload_directories()
        
        # Authentication tests
        self.test_user_registration()
        self.test_user_login()
        
        # Protected endpoint tests
        if self.access_token:
            self.test_protected_endpoint()
            self.test_tribute_creation()
            self.test_music_endpoints()
            
            # Video generation tests (optional, takes time)
            if self.tribute_id:
                self.test_video_generation()
                if self.generation_id:
                    time.sleep(2)  # Wait a bit for processing
                    self.test_video_status()
        
        # Summary
        print("\n" + "=" * 50)
        print("🧪 Test Summary:")
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed! Backend is ready for deployment.")
            return True
        else:
            print("⚠️ Some tests failed. Please check the issues above.")
            return False

def main():
    """Main testing function"""
    print("TributeMaker Backend Testing")
    print("=" * 50)
    
    # Check if server is running
    print("Checking if Flask server is running...")
    print(f"Expected URL: {BASE_URL}")
    print("Make sure to run: python app.py")
    print()
    
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Save test results
    results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    
    print(f"\n📄 Test results saved to: {results_file}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 