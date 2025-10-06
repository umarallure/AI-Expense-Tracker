"""
Test script for pending transactions functionality.
Tests the approval workflow end-to-end.
"""
import requests
import json
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

class PendingTransactionsTester:
    """Helper class to test pending transactions functionality."""

    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.business_id: Optional[str] = None
        self.account_id: Optional[str] = None
        self.category_id: Optional[str] = None

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

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if not self.token:
            raise ValueError("No token available. Please login first.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

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

    def test_get_businesses(self):
        """Get user's businesses."""
        response = requests.get(f"{API_V1}/businesses/", headers=self.get_headers())
        self.print_response(response, "Get Businesses")

        if response.status_code == 200:
            data = response.json()
            if data.get("businesses"):
                self.business_id = data["businesses"][0]["id"]
                print(f"\n✅ Business ID saved: {self.business_id}")
                return True
        return False

    def test_create_account(self):
        """Create a test account."""
        if not self.business_id:
            print("❌ No business ID available")
            return False

        payload = {
            "business_id": self.business_id,
            "account_name": "Test Checking Account",
            "account_type": "checking",
            "currency": "USD",
            "current_balance": 1000.00
        }
        response = requests.post(
            f"{API_V1}/accounts/?business_id={self.business_id}",
            json=payload,
            headers=self.get_headers()
        )
        self.print_response(response, "Create Account")

        if response.status_code in [200, 201]:
            data = response.json()
            self.account_id = data.get("id")
            print(f"\n✅ Account ID saved: {self.account_id}")
            return True
        return False

    def test_create_category(self):
        """Create a test category."""
        if not self.business_id:
            print("❌ No business ID available")
            return False

        payload = {
            "business_id": self.business_id,
            "category_name": "Office Supplies",
            "category_type": "expense",
            "is_income": False,
            "description": "Office supplies and equipment"
        }
        response = requests.post(
            f"{API_V1}/categories/?business_id={self.business_id}",
            json=payload,
            headers=self.get_headers()
        )
        self.print_response(response, "Create Category")

        if response.status_code in [200, 201]:
            data = response.json()
            self.category_id = data.get("id")
            print(f"\n✅ Category ID saved: {self.category_id}")
            return True
        return False

    def test_create_pending_transaction(self):
        """Create a pending transaction."""
        if not self.business_id or not self.account_id or not self.category_id:
            print("❌ Missing required IDs")
            return False

        payload = {
            "business_id": self.business_id,
            "account_id": self.account_id,
            "category_id": self.category_id,
            "amount": 150.00,
            "currency": "USD",
            "description": "Test Office Supplies Purchase",
            "date": "2025-10-05T10:00:00Z",
            "status": "pending",
            "is_income": False,
            "notes": "Test transaction for approval workflow"
        }
        response = requests.post(
            f"{API_V1}/transactions/?business_id={self.business_id}",
            json=payload,
            headers=self.get_headers()
        )
        self.print_response(response, "Create Pending Transaction")

        return response.status_code in [200, 201]

    def test_get_pending_transactions(self):
        """Test getting pending transactions."""
        if not self.business_id:
            print("❌ No business ID available")
            return False

        response = requests.get(
            f"{API_V1}/transactions/pending/{self.business_id}",
            headers=self.get_headers()
        )
        self.print_response(response, "Get Pending Transactions")

        if response.status_code == 200:
            data = response.json()
            pending_count = len(data.get("transactions", []))
            print(f"\n✅ Found {pending_count} pending transactions")
            return True
        return False

    def test_get_all_transactions(self):
        """Test getting all transactions."""
        if not self.business_id:
            print("❌ No business ID available")
            return False

        response = requests.get(
            f"{API_V1}/transactions/?business_id={self.business_id}",
            headers=self.get_headers()
        )
        self.print_response(response, "Get All Transactions")

        return response.status_code == 200

    def run_tests(self):
        """Run all tests in sequence."""
        print("\n" + "="*60)
        print("🚀 PENDING TRANSACTIONS - APPROVAL WORKFLOW TEST")
        print("="*60)

        # Test data
        test_email = "agenticfyai1@gmail.com"
        test_password = "SecureTest123"

        results = []

        # Login
        print("\n📋 Authentication")
        results.append(("Login", self.test_login(test_email, test_password)))

        if self.token:
            # Get business
            results.append(("Get Businesses", self.test_get_businesses()))

            if self.business_id:
                # Setup test data
                print("\n📋 Setup Test Data")
                results.append(("Create Account", self.test_create_account()))
                results.append(("Create Category", self.test_create_category()))

                # Test transactions
                print("\n📋 Transaction Tests")
                results.append(("Create Pending Transaction", self.test_create_pending_transaction()))
                results.append(("Get All Transactions", self.test_get_all_transactions()))
                results.append(("Get Pending Transactions", self.test_get_pending_transactions()))

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
            print("\n🎉 All tests passed! Pending transactions workflow is working!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")

        return passed == total


def main():
    """Main test runner."""
    print("\n🔧 Starting Pending Transactions Test Suite...")
    print("⚠️  Make sure the API server is running on http://localhost:8000")

    # Auto-start server
    print("\n🚀 Auto-starting server...")
    import subprocess
    import sys
    import time
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
        tester = PendingTransactionsTester()
        success = tester.run_tests()
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

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())