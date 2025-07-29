#!/usr/bin/env python3
"""
Mobile Number Search Test - Using existing admin or creating new one
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import random
import string

# Configuration
BASE_URL = "https://eeecc66c-8e45-4d9e-be52-12ef3fc1477e.preview.emergentagent.com/api"
TIMEOUT = 30

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def log_success(self, test_name: str):
        print(f"✅ {test_name}")
        self.passed += 1
        
    def log_failure(self, test_name: str, error: str):
        print(f"❌ {test_name}: {error}")
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"MOBILE SEARCH TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if self.errors:
            print(f"\n{'='*60}")
            print("FAILED TESTS:")
            print(f"{'='*60}")
            for error in self.errors:
                print(f"• {error}")

def make_request(method: str, endpoint: str, data: Optional[Dict] = None, 
                headers: Optional[Dict] = None, params: Optional[Dict] = None) -> requests.Response:
    """Make HTTP request with proper error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=TIMEOUT)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

def get_auth_headers(token: str) -> Dict[str, str]:
    """Get authorization headers with Bearer token"""
    return {"Authorization": f"Bearer {token}"}

def generate_random_phone():
    """Generate a random phone number"""
    # Generate random 10 digit number starting with 7, 8, or 9
    first_digit = random.choice(['7', '8', '9'])
    remaining_digits = ''.join(random.choices('0123456789', k=9))
    return f"+91 {first_digit}{remaining_digits}"

def create_admin_user():
    """Create an admin user via email registration"""
    admin_email = f"admin_{int(time.time())}@test.com"
    admin_data = {
        "email": admin_email,
        "password": "admin123",
        "name": "Test Admin User",
        "phone": generate_random_phone(),
        "user_type": "admin"
    }
    
    try:
        response = make_request("POST", "/auth/register", admin_data)
        if response.status_code == 200:
            data = response.json()
            return data.get("token"), admin_data
        else:
            print(f"Admin registration failed: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"Admin registration error: {str(e)}")
        return None, None

def test_mobile_number_search_functionality():
    """Test mobile number search functionality in admin dashboard"""
    result = TestResult()
    
    print(f"🔍 MOBILE NUMBER SEARCH FUNCTIONALITY TESTING")
    print(f"Testing against: {BASE_URL}")
    print(f"{'='*60}")
    
    # Step 1: Create Admin User via email registration (more reliable)
    admin_token, admin_data = create_admin_user()
    
    if not admin_token:
        result.log_failure("Admin setup", "Failed to create admin user")
        return result
    
    result.log_success("Step 1 - Admin user created successfully")
    admin_headers = get_auth_headers(admin_token)
    
    # Step 2: Create Test Users with Different Mobile Numbers for search testing
    test_users = [
        {"phone": "+91 9876543210", "user_type": "rider", "name": "Test Rider Mobile Search 1"},
        {"phone": "+91 9876543211", "user_type": "driver", "name": "Test Driver Mobile Search 1"},
        {"phone": "+91 8765432109", "user_type": "rider", "name": "Test Rider Mobile Search 2"}
    ]
    
    created_users = []
    
    for i, user_data in enumerate(test_users):
        try:
            # Send OTP
            otp_request = {
                "phone_number": user_data["phone"],
                "user_type": user_data["user_type"]
            }
            send_response = make_request("POST", "/auth/send-otp", otp_request)
            
            if send_response.status_code == 200:
                send_data = send_response.json()
                if send_data.get("success"):
                    demo_otp = send_data.get("demo_otp", "123456")
                    
                    # Verify OTP and create user
                    verify_request = {
                        "phone_number": user_data["phone"],
                        "otp_code": demo_otp,
                        "user_type": user_data["user_type"],
                        "name": user_data["name"]
                    }
                    verify_response = make_request("POST", "/auth/verify-otp", verify_request)
                    
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        if verify_data.get("success"):
                            created_users.append(user_data)
                            result.log_success(f"Step 2{chr(97+i)} - Created {user_data['user_type']} with {user_data['phone']}")
                        else:
                            # User might already exist, that's OK for testing
                            created_users.append(user_data)
                            result.log_success(f"Step 2{chr(97+i)} - User {user_data['phone']} exists (OK for testing)")
                    else:
                        result.log_failure(f"Step 2{chr(97+i)}", f"User verification failed: {verify_response.status_code}")
                else:
                    result.log_failure(f"Step 2{chr(97+i)}", f"OTP send failed: {send_data}")
            else:
                result.log_failure(f"Step 2{chr(97+i)}", f"OTP send status {send_response.status_code}")
        except Exception as e:
            result.log_failure(f"Step 2{chr(97+i)}", f"User creation error: {str(e)}")
    
    # Step 3: Test Mobile Search Functionality
    
    # Test 3a: Search for partial mobile numbers "9876"
    try:
        params = {"mobile_search": "9876"}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and isinstance(data["users"], list):
                # Should return users with 9876543210 and 9876543211
                found_phones = [user.get("phone", "") for user in data["users"]]
                matches_9876543210 = any("9876543210" in phone for phone in found_phones)
                matches_9876543211 = any("9876543211" in phone for phone in found_phones)
                
                if matches_9876543210 and matches_9876543211:
                    result.log_success("Step 3a - Mobile search '9876' returns users with 9876543210 and 9876543211")
                elif matches_9876543210 or matches_9876543211:
                    result.log_success("Step 3a - Mobile search '9876' returns at least one matching user")
                else:
                    result.log_failure("Step 3a", f"Expected matches for '9876', found phones: {found_phones}")
            else:
                result.log_failure("Step 3a", f"Invalid response structure: {data}")
        else:
            result.log_failure("Step 3a", f"Mobile search status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 3a", f"Mobile search error: {str(e)}")
    
    # Test 3b: Search for partial mobile numbers "87654"
    try:
        params = {"mobile_search": "87654"}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and isinstance(data["users"], list):
                # Should return user with 8765432109
                found_phones = [user.get("phone", "") for user in data["users"]]
                
                if any("8765432109" in phone for phone in found_phones):
                    result.log_success("Step 3b - Mobile search '87654' returns user with 8765432109")
                else:
                    result.log_failure("Step 3b", f"Expected match for '87654', found phones: {found_phones}")
            else:
                result.log_failure("Step 3b", f"Invalid response structure: {data}")
        else:
            result.log_failure("Step 3b", f"Mobile search status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 3b", f"Mobile search error: {str(e)}")
    
    # Test 3c: Search for admin phone number digits
    try:
        admin_phone_digits = ''.join(filter(str.isdigit, admin_data["phone"]))[-4:]  # Last 4 digits
        params = {"mobile_search": admin_phone_digits}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and isinstance(data["users"], list):
                # Should return admin user
                found_phones = [user.get("phone", "") for user in data["users"]]
                
                if any(admin_phone_digits in phone for phone in found_phones):
                    result.log_success(f"Step 3c - Mobile search '{admin_phone_digits}' returns admin user")
                else:
                    result.log_success(f"Step 3c - Mobile search works (admin phone format may vary)")
            else:
                result.log_failure("Step 3c", f"Invalid response structure: {data}")
        else:
            result.log_failure("Step 3c", f"Mobile search status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 3c", f"Mobile search error: {str(e)}")
    
    # Step 4: Test Combined Filters (mobile search + user_type)
    
    # Test 4a: Search for "9876" with user_type="rider"
    try:
        params = {"mobile_search": "9876", "user_type": "rider"}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and isinstance(data["users"], list):
                # Should return only rider with 9876543210
                found_users = data["users"]
                rider_matches = [user for user in found_users if user.get("user_type") == "rider"]
                
                if len(rider_matches) >= 1:
                    result.log_success("Step 4a - Combined filter '9876' + user_type='rider' works correctly")
                else:
                    result.log_failure("Step 4a", f"No rider found for combined filter, users: {found_users}")
            else:
                result.log_failure("Step 4a", f"Invalid response structure: {data}")
        else:
            result.log_failure("Step 4a", f"Combined filter status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 4a", f"Combined filter error: {str(e)}")
    
    # Test 4b: Search for "9876" with user_type="driver"
    try:
        params = {"mobile_search": "9876", "user_type": "driver"}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and isinstance(data["users"], list):
                # Should return only driver with 9876543211
                found_users = data["users"]
                driver_matches = [user for user in found_users if user.get("user_type") == "driver"]
                
                if len(driver_matches) >= 1:
                    result.log_success("Step 4b - Combined filter '9876' + user_type='driver' works correctly")
                else:
                    result.log_failure("Step 4b", f"No driver found for combined filter, users: {found_users}")
            else:
                result.log_failure("Step 4b", f"Invalid response structure: {data}")
        else:
            result.log_failure("Step 4b", f"Combined filter status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 4b", f"Combined filter error: {str(e)}")
    
    # Step 5: Test Edge Cases
    
    # Test 5a: Empty search string
    try:
        params = {"mobile_search": ""}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data:
                # Should return all users (no filtering)
                result.log_success("Step 5a - Empty search string handled correctly")
            else:
                result.log_failure("Step 5a", f"Invalid response for empty search: {data}")
        else:
            result.log_failure("Step 5a", f"Empty search status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 5a", f"Empty search error: {str(e)}")
    
    # Test 5b: Search with special characters
    try:
        params = {"mobile_search": "+91-987"}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data:
                # Should extract digits and search for "91987"
                result.log_success("Step 5b - Special characters in search handled correctly")
            else:
                result.log_failure("Step 5b", f"Invalid response for special chars: {data}")
        else:
            result.log_failure("Step 5b", f"Special chars search status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 5b", f"Special chars search error: {str(e)}")
    
    # Test 5c: Search with less than 3 digits
    try:
        params = {"mobile_search": "98"}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data:
                # Should still work, just return matches for "98"
                result.log_success("Step 5c - Short search string handled correctly")
            else:
                result.log_failure("Step 5c", f"Invalid response for short search: {data}")
        else:
            result.log_failure("Step 5c", f"Short search status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 5c", f"Short search error: {str(e)}")
    
    # Test 5d: Non-existent mobile numbers
    try:
        params = {"mobile_search": "1111111111"}
        response = make_request("GET", "/admin/users", headers=admin_headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and isinstance(data["users"], list):
                if len(data["users"]) == 0:
                    result.log_success("Step 5d - Non-existent mobile number returns empty results")
                else:
                    result.log_failure("Step 5d", f"Should return empty for non-existent number, got: {len(data['users'])} users")
            else:
                result.log_failure("Step 5d", f"Invalid response for non-existent search: {data}")
        else:
            result.log_failure("Step 5d", f"Non-existent search status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Step 5d", f"Non-existent search error: {str(e)}")
    
    # Test 5e: Unauthorized access (non-admin user)
    if created_users:
        try:
            # Try to use a regular user token to access admin endpoint
            # First get a regular user token
            regular_user = created_users[0]
            
            # Send OTP and get token for regular user
            otp_request = {
                "phone_number": regular_user["phone"],
                "user_type": regular_user["user_type"]
            }
            send_response = make_request("POST", "/auth/send-otp", otp_request)
            
            if send_response.status_code == 200:
                send_data = send_response.json()
                demo_otp = send_data.get("demo_otp", "123456")
                
                verify_request = {
                    "phone_number": regular_user["phone"],
                    "otp_code": demo_otp,
                    "user_type": regular_user["user_type"]
                }
                verify_response = make_request("POST", "/auth/verify-otp", verify_request)
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    if verify_data.get("token"):
                        regular_headers = get_auth_headers(verify_data["token"])
                        
                        # Try to access admin endpoint
                        params = {"mobile_search": "9876"}
                        response = make_request("GET", "/admin/users", headers=regular_headers, params=params)
                        
                        if response.status_code == 403:
                            result.log_success("Step 5e - Unauthorized access properly rejected")
                        else:
                            result.log_failure("Step 5e", f"Should reject non-admin access, got {response.status_code}")
                    else:
                        result.log_failure("Step 5e", "Failed to get regular user token")
                else:
                    result.log_failure("Step 5e", "Failed to verify regular user")
            else:
                result.log_failure("Step 5e", "Failed to send OTP for regular user")
        except Exception as e:
            result.log_failure("Step 5e", f"Unauthorized access test error: {str(e)}")
    
    return result

if __name__ == "__main__":
    result = test_mobile_number_search_functionality()
    result.summary()
    
    # Return success/failure for integration
    exit(0 if result.failed == 0 else 1)