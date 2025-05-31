import requests
import sys
import json
import os
from datetime import datetime
import uuid

class LostFoundAPITester:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.environ.get('REACT_APP_BACKEND_URL', 'http://10.64.129.37:8001/api')
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.item_id = None
        self.claim_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # For file uploads, don't use JSON
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health(self):
        """Test health check endpoint"""
        return self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )

    def test_register(self, email, full_name, password):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"email": email, "full_name": full_name, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_login(self, email, password):
        """Test login and get token"""
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_item(self, item_type="lost"):
        """Test creating a lost or found item"""
        item_data = {
            "title": f"Test {item_type} item",
            "description": f"This is a test {item_type} item created by the API tester",
            "category": "Electronics",
            "location": "University Library",
            "date_lost_found": datetime.utcnow().isoformat(),
            "item_type": item_type,
            "contact_email": "test@example.com",
            "contact_phone": "123-456-7890",
            "tags": ["test", "api", item_type]
        }
        
        success, response = self.run_test(
            f"Create {item_type.capitalize()} Item",
            "POST",
            "items",
            200,
            data=item_data
        )
        
        if success and 'id' in response:
            self.item_id = response['id']
            return True
        return False

    def test_get_items(self):
        """Test getting all items"""
        success, response = self.run_test(
            "Get Items",
            "GET",
            "items",
            200
        )
        return success

    def test_get_item(self, item_id):
        """Test getting a specific item"""
        success, response = self.run_test(
            "Get Item by ID",
            "GET",
            f"items/{item_id}",
            200
        )
        return success

    def test_update_item(self, item_id):
        """Test updating an item"""
        update_data = {
            "title": "Updated test item",
            "description": "This item has been updated by the API tester"
        }
        
        success, response = self.run_test(
            "Update Item",
            "PUT",
            f"items/{item_id}",
            200,
            data=update_data
        )
        return success

    def test_create_claim(self, item_id):
        """Test creating a claim for an item"""
        claim_data = {
            "item_id": item_id,
            "description": "I believe this is my item because it matches the description of what I lost",
            "contact_email": "claimer@example.com",
            "contact_phone": "987-654-3210"
        }
        
        success, response = self.run_test(
            "Create Claim",
            "POST",
            "claims",
            200,
            data=claim_data
        )
        
        if success and 'id' in response:
            self.claim_id = response['id']
            return True
        return False

    def test_get_claims(self):
        """Test getting all claims for the current user"""
        success, response = self.run_test(
            "Get Claims",
            "GET",
            "claims",
            200
        )
        return success

    def test_dashboard(self):
        """Test getting dashboard data"""
        success, response = self.run_test(
            "Get Dashboard",
            "GET",
            "dashboard",
            200
        )
        return success

def main():
    # Get the backend URL from environment or use default
    import os
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://10.64.129.37:8001/api')
    
    # Setup
    tester = LostFoundAPITester(backend_url)
    print(f"Using backend URL: {backend_url}")
    
    # Generate unique email for testing
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "Test123!"
    test_name = "API Test User"
    
    # Admin credentials
    admin_email = "admin@lostfound.com"
    admin_password = "admin123"

    print(f"\n🚀 Starting Lost & Found Portal API Tests on {backend_url}")
    print("=" * 80)

    # Test health check
    health_success, health_data = tester.test_health()
    if not health_success:
        print("❌ Health check failed, stopping tests")
        return 1
    
    print(f"🔌 Database status: {health_data.get('database', 'unknown')}")

    # Test registration
    if not tester.test_register(test_email, test_name, test_password):
        print("❌ Registration failed, trying login with admin account")
        # Try login with admin account
        if not tester.test_login(admin_email, admin_password):
            print("❌ Login failed with admin account, stopping tests")
            return 1
    
    # Test current user endpoint
    if not tester.test_current_user():
        print("❌ Get current user failed, stopping tests")
        return 1

    # Test creating a lost item
    if not tester.test_create_item("lost"):
        print("❌ Create lost item failed, stopping tests")
        return 1
    
    # Store the item ID
    lost_item_id = tester.item_id
    
    # Test getting all items
    if not tester.test_get_items():
        print("❌ Get items failed")
    
    # Test getting a specific item
    if not tester.test_get_item(lost_item_id):
        print("❌ Get item by ID failed")
    
    # Test updating an item
    if not tester.test_update_item(lost_item_id):
        print("❌ Update item failed")
    
    # Test creating a found item
    if not tester.test_create_item("found"):
        print("❌ Create found item failed")
    
    # Store the found item ID
    found_item_id = tester.item_id
    
    # Test creating a claim
    # We need to login as a different user to claim an item
    # For simplicity, we'll use the admin account if we registered as a test user
    if tester.user_id and tester.user_id != admin_email:
        if tester.test_login(admin_email, admin_password):
            if not tester.test_create_claim(lost_item_id):
                print("❌ Create claim failed")
        else:
            print("❌ Login as admin failed, skipping claim test")
    
    # Test getting claims
    if not tester.test_get_claims():
        print("❌ Get claims failed")
    
    # Test dashboard
    if not tester.test_dashboard():
        print("❌ Get dashboard failed")

    # Print results
    print("\n" + "=" * 80)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
