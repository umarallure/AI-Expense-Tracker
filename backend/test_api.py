"""
Quick start script to test the AI-Powered Expense Tracker API.
This script helps verify that all Phase 1 endpoints are working correctly.
"""
import requests
import json
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

class APITester:
    """Helper class to test API endpoints."""
    
    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.business_id: Optional[str] = None
    
    def print_response(self, response: requests.Response, title: str):
        """Pretty print API response."""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
    
    def test_health(self):
        """Test health check endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        self.print_response(response, "Health Check")
        return response.status_code == 200
    
    def test_signup(self, email: str, password: str, full_name: str):
        """Test user signup."""
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name
        }
        response = requests.post(f"{API_V1}/auth/signup", json=payload)
        self.print_response(response, "User Signup")
        
        # Handle rate limiting
        if "21 seconds" in response.text:
            print("⏳ Rate limited, waiting 25 seconds...")
            import time
            time.sleep(25)
            response = requests.post(f"{API_V1}/auth/signup", json=payload)
            self.print_response(response, "User Signup (Retry)")
        
        return response.status_code in [200, 201]
    
    def test_login(self, email: str, password: str):
        """Test user login and save token."""
        payload = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{API_V1}/auth/login", json=payload)
        self.print_response(response, "User Login")
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            print(f"\n✅ Token saved: {self.token[:20]}...")
            return True
        return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if not self.token:
            raise ValueError("No token available. Please login first.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_profile(self):
        """Test get current user profile."""
        response = requests.get(f"{API_V1}/auth/me", headers=self.get_headers())
        self.print_response(response, "Get User Profile")
        return response.status_code == 200
    
    def test_create_business(self, business_name: str):
        """Test create business."""
        payload = {
            "business_name": business_name,
            "business_type": "llc",
            "currency": "USD",
            "industry": "Technology",
            "fiscal_year_start": 1
        }
        response = requests.post(
            f"{API_V1}/businesses/",
            json=payload,
            headers=self.get_headers()
        )
        self.print_response(response, "Create Business")
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.business_id = data.get("id")
            print(f"\n✅ Business ID saved: {self.business_id}")
            return True
        return False
    
    def test_list_businesses(self):
        """Test list businesses."""
        response = requests.get(f"{API_V1}/businesses/", headers=self.get_headers())
        self.print_response(response, "List Businesses")
        return response.status_code == 200
    
    def test_get_business(self):
        """Test get business details."""
        if not self.business_id:
            print("❌ No business ID available")
            return False
        
        response = requests.get(
            f"{API_V1}/businesses/{self.business_id}",
            headers=self.get_headers()
        )
        self.print_response(response, "Get Business Details")
        return response.status_code == 200
    
    def test_update_business(self):
        """Test update business."""
        if not self.business_id:
            print("❌ No business ID available")
            return False
        
        payload = {
            "city": "San Francisco",
            "state": "CA",
            "country": "USA"
        }
        response = requests.patch(
            f"{API_V1}/businesses/{self.business_id}",
            json=payload,
            headers=self.get_headers()
        )
        self.print_response(response, "Update Business")
        return response.status_code == 200
    
    def test_list_members(self):
        """Test list business members."""
        if not self.business_id:
            print("❌ No business ID available")
            return False
        
        response = requests.get(
            f"{API_V1}/businesses/{self.business_id}/members",
            headers=self.get_headers()
        )
        self.print_response(response, "List Business Members")
        return response.status_code == 200
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        print("\n" + "="*60)
        print("🚀 AI-POWERED EXPENSE TRACKER - API TEST SUITE")
        print("="*60)
        
        # Test data
        test_email = "agenticfyai1@gmail.com"
        test_password = "SecureTest123"
        test_name = "Test User"
        test_business = "Test Corporation"
        
        results = []
        
        # Phase 1: Health & Authentication
        print("\n📋 Phase 1: Health & Authentication Tests")
        results.append(("Health Check", self.test_health()))
        results.append(("User Signup", self.test_signup(test_email, test_password, test_name)))
        results.append(("User Login", self.test_login(test_email, test_password)))
        
        if self.token:
            results.append(("Get Profile", self.test_get_profile()))
            
            # Phase 2: Business Management
            print("\n📋 Phase 2: Business Management Tests")
            results.append(("Create Business", self.test_create_business(test_business)))
            results.append(("List Businesses", self.test_list_businesses()))
            
            if self.business_id:
                results.append(("Get Business", self.test_get_business()))
                results.append(("Update Business", self.test_update_business()))
                results.append(("List Members", self.test_list_members()))
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n{'='*60}")
        print(f"Results: {passed}/{total} tests passed")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print("="*60)
        
        if passed == total:
            print("\n🎉 All tests passed! Backend is working correctly!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
        
        return passed == total


def main():
    """Main test runner."""
    print("\n🔧 Starting API Test Suite...")
    print("⚠️  Make sure the API server is running on http://localhost:8000")
    print("⚠️  Make sure Supabase is configured correctly")
    
    # Auto-start server
    print("\n🚀 Auto-starting server...")
    import subprocess
    import sys
    import time
    import signal
    import os
    
    # Start server
    server = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    try:
        tester = APITester()
        success = tester.run_all_tests()
    finally:
        # Stop server
        print("\n🛑 Stopping server...")
        if server.poll() is None:  # Still running
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        print("✅ Server stopped")
    
    if not success:
        print("\n💡 Troubleshooting Tips:")
        print("1. Check if the API server is running: uvicorn app.main:app --reload")
        print("2. Verify Supabase credentials in .env file")
        print("3. Make sure the database migration has been run")
        print("4. Check the API logs for detailed error messages")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
