"""
Test script to verify account creation works with the fixed field names.
"""
import requests
import json
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

class AccountTester:
    """Helper class to test account creation."""

    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.business_id: Optional[str] = None

    def login(self, email: str, password: str):
        """Login and get token."""
        payload = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{API_V1}/auth/login", json=payload)

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            print(f"✅ Login successful, token: {self.token[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if not self.token:
            raise ValueError("No token available. Please login first.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def create_business(self):
        """Create a test business."""
        payload = {
            "business_name": "Test Business for Accounts",
            "business_type": "llc",
            "currency": "USD",
            "industry": "Technology"
        }
        response = requests.post(
            f"{API_V1}/businesses/",
            json=payload,
            headers=self.get_headers()
        )

        if response.status_code in [200, 201]:
            data = response.json()
            self.business_id = data.get("id")
            print(f"✅ Business created: {self.business_id}")
            return True
        else:
            print(f"❌ Business creation failed: {response.status_code} - {response.text}")
            return False

    def test_create_account(self):
        """Test creating an account with the correct field names."""
        if not self.business_id:
            print("❌ No business ID available")
            return False

        payload = {
            "business_id": self.business_id,
            "account_name": "Test Checking Account",
            "account_type": "checking",
            "account_number_masked": "****1234",
            "institution_name": "Test Bank",
            "current_balance": 1000.00,
            "currency": "USD"
        }

        print(f"📤 Sending account creation request with payload: {json.dumps(payload, indent=2)}")

        response = requests.post(
            f"{API_V1}/accounts/?business_id={self.business_id}",
            json=payload,
            headers=self.get_headers()
        )

        print(f"📥 Response status: {response.status_code}")
        try:
            print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"📥 Response body: {response.text}")

        if response.status_code in [200, 201]:
            print("✅ Account creation successful!")
            return True
        else:
            print("❌ Account creation failed!")
            return False

def main():
    """Main test function."""
    print("🔧 Testing Account Creation Fix...")

    tester = AccountTester()

    # Use test credentials (assuming they exist from previous tests)
    test_email = "agenticfyai1@gmail.com"
    test_password = "SecureTest123"

    if not tester.login(test_email, test_password):
        print("❌ Could not login. Please run the main test suite first to create a user.")
        return False

    if not tester.create_business():
        print("❌ Could not create business.")
        return False

    success = tester.test_create_account()

    if success:
        print("\n🎉 Account creation fix verified successfully!")
    else:
        print("\n💥 Account creation still failing. Check the error messages above.")

    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)