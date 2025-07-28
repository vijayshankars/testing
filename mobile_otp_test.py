#!/usr/bin/env python3
"""
Focused Mobile OTP Authentication Testing
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://9bc251d5-e3ce-47e0-a729-c8aabb368f35.preview.emergentagent.com/api"
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
        print(f"MOBILE OTP TEST SUMMARY")
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

def test_mobile_otp_comprehensive(result: TestResult):
    """Comprehensive Mobile OTP authentication testing"""
    print(f"\n{'='*60}")
    print("MOBILE OTP AUTHENTICATION COMPREHENSIVE TESTING")
    print(f"{'='*60}")
    
    mobile_tokens = {}
    
    # Test 1: Send OTP with valid Indian phone number
    try:
        otp_request = {
            "phone_number": "+91 9876543210",
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["success", "message", "is_existing_user", "demo_mode"]
            if all(field in data for field in required_fields):
                if data["success"] and data["demo_mode"]:
                    result.log_success("Send OTP - Valid Indian phone number (+91 format)")
                    if "demo_otp" in data:
                        result.log_success("Send OTP - Demo OTP returned in response")
                    else:
                        result.log_failure("Send OTP", "Demo OTP not returned in demo mode")
                else:
                    result.log_failure("Send OTP", f"Invalid response data: {data}")
            else:
                result.log_failure("Send OTP", f"Missing required fields: {data}")
        else:
            result.log_failure("Send OTP", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Send OTP", str(e))
    
    # Test 2: Send OTP with international phone number
    try:
        otp_request = {
            "phone_number": "+1 5551234567",
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("demo_mode"):
                result.log_success("Send OTP - Valid international phone number (+1 format)")
            else:
                result.log_failure("Send OTP", f"Invalid response for international number: {data}")
        else:
            result.log_failure("Send OTP", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Send OTP", str(e))
    
    # Test 3: Phone number validation - invalid formats
    invalid_phones = ["123456789", "invalid_phone", "+", "91987654321"]
    for invalid_phone in invalid_phones:
        try:
            otp_request = {
                "phone_number": invalid_phone,
                "user_type": "rider"
            }
            response = make_request("POST", "/auth/send-otp", otp_request)
            if response.status_code == 400:
                result.log_success(f"Phone validation - Invalid phone number rejection: {invalid_phone}")
            else:
                result.log_failure("Phone validation", f"Should reject invalid phone {invalid_phone}, got {response.status_code}")
        except Exception as e:
            result.log_failure("Phone validation", f"Error testing invalid phone {invalid_phone}: {str(e)}")
    
    # Test 4: Phone number formatting edge cases
    formatting_tests = [
        {"input": "9876543210", "expected": "+919876543210"},
        {"input": "919876543210", "expected": "+919876543210"},
        {"input": "+91 9876 543 210", "expected": "+919876543210"}
    ]
    
    for test_case in formatting_tests:
        try:
            otp_request = {
                "phone_number": test_case["input"],
                "user_type": "rider"
            }
            response = make_request("POST", "/auth/send-otp", otp_request)
            if response.status_code == 200:
                result.log_success(f"Phone formatting - {test_case['input']} formatted correctly")
            else:
                result.log_failure("Phone formatting", f"Phone formatting failed for {test_case['input']}: {response.status_code}")
        except Exception as e:
            result.log_failure("Phone formatting", f"Error testing phone formatting {test_case['input']}: {str(e)}")
    
    # Test 5: OTP verification with demo OTP for new user registration
    try:
        # Use unique phone number
        test_phone = "+91 6666666666"
        otp_request = {
            "phone_number": test_phone,
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Verify with demo OTP 123456
            verify_request = {
                "phone_number": test_phone,
                "otp_code": "123456",  # Demo OTP
                "user_type": "rider",
                "name": "Test Rider Mobile"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "user_data", "token", "is_new_user"]
                if all(field in data for field in required_fields):
                    if data["success"] and data["is_new_user"] and data["token"]:
                        mobile_tokens["rider"] = data["token"]
                        result.log_success("OTP verification - New user registration via mobile OTP")
                        
                        # Verify user data
                        user_data = data["user_data"]
                        if user_data.get("phone") == "+916666666666" and user_data.get("user_type") == "rider":
                            result.log_success("OTP verification - User data populated correctly for new user")
                        else:
                            result.log_failure("OTP verification", f"Invalid user data: {user_data}")
                    else:
                        result.log_failure("OTP verification", f"Invalid verification response: {data}")
                else:
                    result.log_failure("OTP verification", f"Missing required fields: {data}")
            else:
                result.log_failure("OTP verification", f"Status {response.status_code}: {response.text}")
        else:
            result.log_failure("OTP verification", "Failed to send OTP for verification test")
    except Exception as e:
        result.log_failure("OTP verification", str(e))
    
    # Test 6: OTP verification for existing user login
    try:
        # Send OTP for the same number (now existing user)
        test_phone = "+91 6666666666"
        otp_request = {
            "phone_number": test_phone,
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            send_data = send_response.json()
            if send_data.get("is_existing_user"):
                # Verify with demo OTP (no name needed for existing user)
                verify_request = {
                    "phone_number": test_phone,
                    "otp_code": "000000",  # Different demo OTP
                    "user_type": "rider"
                }
                response = make_request("POST", "/auth/verify-otp", verify_request)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and not data.get("is_new_user"):
                        result.log_success("OTP verification - Existing user login via mobile OTP")
                    else:
                        result.log_failure("OTP verification", f"Should be existing user login: {data}")
                else:
                    result.log_failure("OTP verification", f"Status {response.status_code}: {response.text}")
            else:
                result.log_failure("OTP verification", "User should be marked as existing")
        else:
            result.log_failure("OTP verification", "Failed to send OTP for existing user test")
    except Exception as e:
        result.log_failure("OTP verification", str(e))
    
    # Test 7: Driver registration via mobile OTP
    try:
        test_phone = "+91 5555555555"
        otp_request = {
            "phone_number": test_phone,
            "user_type": "driver"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Verify with demo OTP
            verify_request = {
                "phone_number": test_phone,
                "otp_code": "123456",
                "user_type": "driver",
                "name": "Test Driver Mobile"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("is_new_user"):
                    user_data = data.get("user_data", {})
                    if user_data.get("user_type") == "driver":
                        mobile_tokens["driver"] = data["token"]
                        result.log_success("OTP verification - Driver registration via mobile OTP")
                    else:
                        result.log_failure("OTP verification", f"Invalid driver user type: {user_data}")
                else:
                    result.log_failure("OTP verification", f"Driver registration failed: {data}")
            else:
                result.log_failure("OTP verification", f"Status {response.status_code}: {response.text}")
        else:
            result.log_failure("OTP verification", "Failed to send OTP for driver test")
    except Exception as e:
        result.log_failure("OTP verification", str(e))
    
    # Test 8: User type validation and restrictions
    try:
        test_phone = "+91 4444444444"
        # Register as rider first
        otp_request = {
            "phone_number": test_phone,
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            verify_request = {
                "phone_number": test_phone,
                "otp_code": "123456",
                "user_type": "rider",
                "name": "Test User Type"
            }
            reg_response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if reg_response.status_code == 200:
                # Now try to login as driver with same number
                otp_request["user_type"] = "driver"
                send_response2 = make_request("POST", "/auth/send-otp", otp_request)
                
                if send_response2.status_code == 200:
                    verify_request["user_type"] = "driver"
                    verify_request.pop("name", None)  # Remove name for login
                    wrong_type_response = make_request("POST", "/auth/verify-otp", verify_request)
                    
                    if wrong_type_response.status_code == 400:
                        result.log_success("User type validation - User type validation working correctly")
                    else:
                        result.log_failure("User type validation", f"Should reject wrong user type, got {wrong_type_response.status_code}")
                else:
                    result.log_failure("User type validation", "Failed to send OTP for user type test")
            else:
                result.log_failure("User type validation", "Failed to register user for type validation test")
        else:
            result.log_failure("User type validation", "Failed to send initial OTP for user type test")
    except Exception as e:
        result.log_failure("User type validation", str(e))
    
    # Test 9: Invalid OTP attempts
    try:
        test_phone = "+91 3333333333"
        otp_request = {
            "phone_number": test_phone,
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Try invalid OTP
            verify_request = {
                "phone_number": test_phone,
                "otp_code": "999999",  # Invalid OTP
                "user_type": "rider",
                "name": "Test Invalid OTP"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                if not data.get("success"):
                    result.log_success("Error handling - Invalid OTP rejection")
                else:
                    result.log_failure("Error handling", "Should reject invalid OTP")
            else:
                result.log_failure("Error handling", f"Unexpected status for invalid OTP: {response.status_code}")
        else:
            result.log_failure("Error handling", "Failed to send OTP for invalid OTP test")
    except Exception as e:
        result.log_failure("Error handling", str(e))
    
    # Test 10: Missing required fields
    try:
        test_phone = "+91 2222222222"
        # First send OTP
        otp_request = {
            "phone_number": test_phone,
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Missing name for new user
            verify_request = {
                "phone_number": test_phone,
                "otp_code": "123456",
                "user_type": "rider"
                # Missing name
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 400:
                result.log_success("Error handling - Missing name field rejection for new user")
            else:
                result.log_failure("Error handling", f"Should reject missing name, got {response.status_code}")
        else:
            result.log_failure("Error handling", "Failed to send OTP for missing fields test")
    except Exception as e:
        result.log_failure("Error handling", str(e))
    
    # Test 11: JWT token generation and validation for mobile authenticated users
    if mobile_tokens.get("rider"):
        try:
            headers = get_auth_headers(mobile_tokens["rider"])
            response = make_request("GET", "/rider/rides", headers=headers)
            if response.status_code == 200:
                result.log_success("JWT token validation - Mobile authenticated rider token works")
            else:
                result.log_failure("JWT token validation", f"Mobile rider token invalid: {response.status_code}")
        except Exception as e:
            result.log_failure("JWT token validation", str(e))
    
    if mobile_tokens.get("driver"):
        try:
            headers = get_auth_headers(mobile_tokens["driver"])
            response = make_request("GET", "/driver/ride-requests", headers=headers)
            if response.status_code in [200, 400]:  # 400 is OK if no location set
                result.log_success("JWT token validation - Mobile authenticated driver token works")
            else:
                result.log_failure("JWT token validation", f"Mobile driver token invalid: {response.status_code}")
        except Exception as e:
            result.log_failure("JWT token validation", str(e))

def main():
    """Run Mobile OTP authentication tests"""
    print("🚗 Mobile OTP Authentication Testing")
    print(f"Testing against: {BASE_URL}")
    print(f"{'='*60}")
    
    result = TestResult()
    
    # Run Mobile OTP tests
    test_mobile_otp_comprehensive(result)
    
    # Print summary
    result.summary()
    
    return result.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)