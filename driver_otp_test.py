#!/usr/bin/env python3
"""
Driver User Type OTP Login Functionality Testing
Comprehensive testing of driver OTP authentication as requested in the review
"""

import requests
import json
import time
from typing import Dict, Any, Optional

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
        print(f"\n{'='*80}")
        print(f"DRIVER OTP AUTHENTICATION TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if self.errors:
            print(f"\n{'='*80}")
            print("FAILED TESTS:")
            print(f"{'='*80}")
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

def test_driver_otp_send_functionality(result: TestResult):
    """Test sending OTP for driver user type with specific phone number"""
    print(f"\n{'='*80}")
    print("1. DRIVER OTP SEND FUNCTIONALITY TESTING")
    print(f"{'='*80}")
    
    # Test 1: Send OTP for driver user type with requested phone number
    try:
        otp_request = {
            "phone_number": "+91 9876543210",
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["success", "message", "is_existing_user", "demo_mode"]
            if all(field in data for field in required_fields):
                if data["success"] and data["demo_mode"]:
                    result.log_success("POST /api/auth/send-otp - Driver user type with +91 9876543210")
                    if "demo_otp" in data:
                        result.log_success("POST /api/auth/send-otp - Demo OTP generated for driver")
                        print(f"    📱 Demo OTP for driver: {data['demo_otp']}")
                    else:
                        result.log_failure("POST /api/auth/send-otp", "Demo OTP not returned for driver")
                else:
                    result.log_failure("POST /api/auth/send-otp", f"Invalid response for driver: {data}")
            else:
                result.log_failure("POST /api/auth/send-otp", f"Missing required fields for driver: {data}")
        else:
            result.log_failure("POST /api/auth/send-otp", f"Driver OTP send failed: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("POST /api/auth/send-otp", f"Driver OTP send error: {str(e)}")
    
    # Test 2: Verify OTP generation is working properly for drivers
    try:
        # Send OTP for a new driver phone number
        otp_request = {
            "phone_number": "+91 9876543211",
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("demo_mode"):
                if "demo_otp" in data and len(data["demo_otp"]) == 6:
                    result.log_success("OTP Generation - 6-digit OTP generated properly for driver")
                    print(f"    📱 Generated OTP format verified: {data['demo_otp']}")
                else:
                    result.log_failure("OTP Generation", f"Invalid OTP format for driver: {data.get('demo_otp')}")
            else:
                result.log_failure("OTP Generation", f"OTP generation failed for driver: {data}")
        else:
            result.log_failure("OTP Generation", f"Failed to generate OTP for driver: {response.status_code}")
    except Exception as e:
        result.log_failure("OTP Generation", f"Error generating OTP for driver: {str(e)}")
    
    # Test 3: Test driver vs rider OTP send comparison
    try:
        # Send OTP for rider with same phone number format
        rider_otp_request = {
            "phone_number": "+91 9876543212",
            "user_type": "rider"
        }
        rider_response = make_request("POST", "/auth/send-otp", rider_otp_request)
        
        # Send OTP for driver with same phone number format
        driver_otp_request = {
            "phone_number": "+91 9876543213",
            "user_type": "driver"
        }
        driver_response = make_request("POST", "/auth/send-otp", driver_otp_request)
        
        if rider_response.status_code == 200 and driver_response.status_code == 200:
            rider_data = rider_response.json()
            driver_data = driver_response.json()
            
            # Compare response structures
            if (rider_data.get("success") == driver_data.get("success") and
                rider_data.get("demo_mode") == driver_data.get("demo_mode")):
                result.log_success("Driver vs Rider OTP - Response structure identical for both user types")
            else:
                result.log_failure("Driver vs Rider OTP", f"Response structure differs: Rider={rider_data}, Driver={driver_data}")
                
            # Verify both generate OTPs
            if "demo_otp" in rider_data and "demo_otp" in driver_data:
                result.log_success("Driver vs Rider OTP - Both user types generate OTPs successfully")
            else:
                result.log_failure("Driver vs Rider OTP", "OTP generation differs between user types")
        else:
            result.log_failure("Driver vs Rider OTP", f"Status code mismatch: Rider={rider_response.status_code}, Driver={driver_response.status_code}")
    except Exception as e:
        result.log_failure("Driver vs Rider OTP", f"Comparison error: {str(e)}")

def test_driver_otp_verification_functionality(result: TestResult):
    """Test OTP verification for driver user type"""
    print(f"\n{'='*80}")
    print("2. DRIVER OTP VERIFICATION FUNCTIONALITY TESTING")
    print(f"{'='*80}")
    
    driver_token = None
    
    # Test 1: New driver registration via OTP verification
    try:
        # First send OTP
        otp_request = {
            "phone_number": "+91 9876543210",
            "user_type": "driver"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            send_data = send_response.json()
            if send_data.get("success"):
                # Now verify with demo OTP and name for new driver
                verify_request = {
                    "phone_number": "+91 9876543210",
                    "otp_code": "123456",  # Demo OTP
                    "user_type": "driver",
                    "name": "Test Driver OTP"
                }
                response = make_request("POST", "/auth/verify-otp", verify_request)
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["success", "message", "user_data", "token", "is_new_user"]
                    if all(field in data for field in required_fields):
                        if data["success"] and data["is_new_user"] and data["token"]:
                            driver_token = data["token"]
                            result.log_success("POST /api/auth/verify-otp - New driver registration via OTP")
                            
                            # Verify user data for driver
                            user_data = data["user_data"]
                            if (user_data.get("phone") == "+919876543210" and 
                                user_data.get("user_type") == "driver" and
                                user_data.get("name") == "Test Driver OTP"):
                                result.log_success("Driver OTP Verification - User data populated correctly for new driver")
                                print(f"    👤 Driver created: {user_data['name']} ({user_data['phone']})")
                            else:
                                result.log_failure("Driver OTP Verification", f"Invalid driver user data: {user_data}")
                        else:
                            result.log_failure("POST /api/auth/verify-otp", f"Invalid verification response for driver: {data}")
                    else:
                        result.log_failure("POST /api/auth/verify-otp", f"Missing required fields for driver: {data}")
                else:
                    result.log_failure("POST /api/auth/verify-otp", f"Driver OTP verification failed: {response.status_code} - {response.text}")
            else:
                result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for driver verification test")
        else:
            result.log_failure("POST /api/auth/verify-otp", f"Failed to send OTP for driver: {send_response.status_code}")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", f"New driver registration error: {str(e)}")
    
    # Test 2: Existing driver login via OTP verification
    try:
        # Send OTP for the same driver number (now existing user)
        otp_request = {
            "phone_number": "+91 9876543210",
            "user_type": "driver"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            send_data = send_response.json()
            if send_data.get("is_existing_user"):
                # Verify with demo OTP (no name needed for existing driver)
                verify_request = {
                    "phone_number": "+91 9876543210",
                    "otp_code": "000000",  # Different demo OTP
                    "user_type": "driver"
                }
                response = make_request("POST", "/auth/verify-otp", verify_request)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and not data.get("is_new_user"):
                        result.log_success("POST /api/auth/verify-otp - Existing driver login via OTP")
                        print(f"    🔑 Existing driver logged in successfully")
                    else:
                        result.log_failure("POST /api/auth/verify-otp", f"Should be existing driver login: {data}")
                else:
                    result.log_failure("POST /api/auth/verify-otp", f"Existing driver login failed: {response.status_code} - {response.text}")
            else:
                result.log_failure("POST /api/auth/verify-otp", "Driver should be marked as existing user")
        else:
            result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for existing driver test")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", f"Existing driver login error: {str(e)}")
    
    # Test 3: JWT token generation and validation for driver
    if driver_token:
        try:
            headers = get_auth_headers(driver_token)
            response = make_request("GET", "/driver/ride-requests", headers=headers)
            if response.status_code in [200, 400]:  # 400 is OK if no location set
                result.log_success("JWT Token Generation - Driver token generated and validated correctly")
                print(f"    🎫 Driver JWT token working properly")
            else:
                result.log_failure("JWT Token Generation", f"Driver token validation failed: {response.status_code}")
        except Exception as e:
            result.log_failure("JWT Token Generation", f"Driver token validation error: {str(e)}")
    
    return driver_token

def test_driver_vs_rider_otp_flow_comparison(result: TestResult):
    """Compare driver OTP flow with rider OTP flow to identify differences"""
    print(f"\n{'='*80}")
    print("3. DRIVER VS RIDER OTP FLOW COMPARISON")
    print(f"{'='*80}")
    
    driver_flow_data = {}
    rider_flow_data = {}
    
    # Test 1: Compare OTP send flow
    try:
        # Driver OTP send
        driver_otp_request = {
            "phone_number": "+91 9876543220",
            "user_type": "driver"
        }
        driver_send_response = make_request("POST", "/auth/send-otp", driver_otp_request)
        
        # Rider OTP send
        rider_otp_request = {
            "phone_number": "+91 9876543221",
            "user_type": "rider"
        }
        rider_send_response = make_request("POST", "/auth/send-otp", rider_otp_request)
        
        if driver_send_response.status_code == 200 and rider_send_response.status_code == 200:
            driver_data = driver_send_response.json()
            rider_data = rider_send_response.json()
            
            # Store for later comparison
            driver_flow_data['send'] = driver_data
            rider_flow_data['send'] = rider_data
            
            # Compare response structures
            driver_keys = set(driver_data.keys())
            rider_keys = set(rider_data.keys())
            
            if driver_keys == rider_keys:
                result.log_success("OTP Send Flow Comparison - Identical response structure for both user types")
            else:
                result.log_failure("OTP Send Flow Comparison", f"Different response structures: Driver={driver_keys}, Rider={rider_keys}")
            
            # Compare specific fields
            comparison_fields = ["success", "demo_mode", "is_existing_user"]
            differences = []
            for field in comparison_fields:
                if driver_data.get(field) != rider_data.get(field):
                    differences.append(f"{field}: Driver={driver_data.get(field)}, Rider={rider_data.get(field)}")
            
            if not differences:
                result.log_success("OTP Send Flow Comparison - No functional differences between user types")
            else:
                result.log_failure("OTP Send Flow Comparison", f"Functional differences found: {differences}")
        else:
            result.log_failure("OTP Send Flow Comparison", f"Status code mismatch: Driver={driver_send_response.status_code}, Rider={rider_send_response.status_code}")
    except Exception as e:
        result.log_failure("OTP Send Flow Comparison", f"Send flow comparison error: {str(e)}")
    
    # Test 2: Compare OTP verification flow
    try:
        # Driver OTP verification
        driver_verify_request = {
            "phone_number": "+91 9876543220",
            "otp_code": "123456",
            "user_type": "driver",
            "name": "Test Driver Compare"
        }
        driver_verify_response = make_request("POST", "/auth/verify-otp", driver_verify_request)
        
        # Rider OTP verification
        rider_verify_request = {
            "phone_number": "+91 9876543221",
            "otp_code": "123456",
            "user_type": "rider",
            "name": "Test Rider Compare"
        }
        rider_verify_response = make_request("POST", "/auth/verify-otp", rider_verify_request)
        
        if driver_verify_response.status_code == 200 and rider_verify_response.status_code == 200:
            driver_data = driver_verify_response.json()
            rider_data = rider_verify_response.json()
            
            # Store for later comparison
            driver_flow_data['verify'] = driver_data
            rider_flow_data['verify'] = rider_data
            
            # Compare response structures
            driver_keys = set(driver_data.keys())
            rider_keys = set(rider_data.keys())
            
            if driver_keys == rider_keys:
                result.log_success("OTP Verify Flow Comparison - Identical response structure for both user types")
            else:
                result.log_failure("OTP Verify Flow Comparison", f"Different response structures: Driver={driver_keys}, Rider={rider_keys}")
            
            # Compare user_type in response
            driver_user_type = driver_data.get("user_data", {}).get("user_type")
            rider_user_type = rider_data.get("user_data", {}).get("user_type")
            
            if driver_user_type == "driver" and rider_user_type == "rider":
                result.log_success("OTP Verify Flow Comparison - User types correctly assigned")
            else:
                result.log_failure("OTP Verify Flow Comparison", f"User type assignment issue: Driver={driver_user_type}, Rider={rider_user_type}")
            
            # Compare token generation
            if driver_data.get("token") and rider_data.get("token"):
                result.log_success("OTP Verify Flow Comparison - JWT tokens generated for both user types")
            else:
                result.log_failure("OTP Verify Flow Comparison", "JWT token generation differs between user types")
        else:
            result.log_failure("OTP Verify Flow Comparison", f"Verification status mismatch: Driver={driver_verify_response.status_code}, Rider={rider_verify_response.status_code}")
    except Exception as e:
        result.log_failure("OTP Verify Flow Comparison", f"Verify flow comparison error: {str(e)}")
    
    # Test 3: Summary of differences
    try:
        if driver_flow_data and rider_flow_data:
            print(f"\n    📊 FLOW COMPARISON SUMMARY:")
            print(f"    Driver Send Response: {len(driver_flow_data.get('send', {}))} fields")
            print(f"    Rider Send Response: {len(rider_flow_data.get('send', {}))} fields")
            print(f"    Driver Verify Response: {len(driver_flow_data.get('verify', {}))} fields")
            print(f"    Rider Verify Response: {len(rider_flow_data.get('verify', {}))} fields")
            
            result.log_success("Flow Comparison Summary - Complete comparison analysis performed")
        else:
            result.log_failure("Flow Comparison Summary", "Insufficient data for complete comparison")
    except Exception as e:
        result.log_failure("Flow Comparison Summary", f"Summary generation error: {str(e)}")

def test_driver_user_type_validations_and_restrictions(result: TestResult):
    """Test user type specific validations or restrictions for drivers"""
    print(f"\n{'='*80}")
    print("4. DRIVER USER TYPE VALIDATIONS AND RESTRICTIONS TESTING")
    print(f"{'='*80}")
    
    # Test 1: Driver trying to login with rider user_type (should fail)
    try:
        # First register a driver
        otp_request = {
            "phone_number": "+91 9876543230",
            "user_type": "driver"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Register as driver
            verify_request = {
                "phone_number": "+91 9876543230",
                "otp_code": "123456",
                "user_type": "driver",
                "name": "Test Driver Validation"
            }
            reg_response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if reg_response.status_code == 200:
                # Now try to login as rider with same number (should fail)
                otp_request["user_type"] = "rider"
                send_response2 = make_request("POST", "/auth/send-otp", otp_request)
                
                if send_response2.status_code == 200:
                    verify_request["user_type"] = "rider"
                    verify_request.pop("name", None)  # Remove name for login
                    wrong_type_response = make_request("POST", "/auth/verify-otp", verify_request)
                    
                    if wrong_type_response.status_code == 400:
                        data = wrong_type_response.json()
                        if "registered as driver" in data.get("detail", "").lower():
                            result.log_success("User Type Validation - Driver cannot login as rider (correct restriction)")
                            print(f"    🚫 Restriction working: {data.get('detail')}")
                        else:
                            result.log_failure("User Type Validation", f"Wrong error message: {data.get('detail')}")
                    else:
                        result.log_failure("User Type Validation", f"Should reject wrong user type, got {wrong_type_response.status_code}")
                else:
                    result.log_failure("User Type Validation", "Failed to send OTP for user type validation test")
            else:
                result.log_failure("User Type Validation", "Failed to register driver for validation test")
        else:
            result.log_failure("User Type Validation", "Failed to send initial OTP for validation test")
    except Exception as e:
        result.log_failure("User Type Validation", f"User type validation error: {str(e)}")
    
    # Test 2: Rider trying to login with driver user_type (should fail)
    try:
        # First register a rider
        otp_request = {
            "phone_number": "+91 9876543231",
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Register as rider
            verify_request = {
                "phone_number": "+91 9876543231",
                "otp_code": "123456",
                "user_type": "rider",
                "name": "Test Rider Validation"
            }
            reg_response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if reg_response.status_code == 200:
                # Now try to login as driver with same number (should fail)
                otp_request["user_type"] = "driver"
                send_response2 = make_request("POST", "/auth/send-otp", otp_request)
                
                if send_response2.status_code == 200:
                    verify_request["user_type"] = "driver"
                    verify_request.pop("name", None)  # Remove name for login
                    wrong_type_response = make_request("POST", "/auth/verify-otp", verify_request)
                    
                    if wrong_type_response.status_code == 400:
                        data = wrong_type_response.json()
                        if "registered as rider" in data.get("detail", "").lower():
                            result.log_success("User Type Validation - Rider cannot login as driver (correct restriction)")
                            print(f"    🚫 Restriction working: {data.get('detail')}")
                        else:
                            result.log_failure("User Type Validation", f"Wrong error message: {data.get('detail')}")
                    else:
                        result.log_failure("User Type Validation", f"Should reject wrong user type, got {wrong_type_response.status_code}")
                else:
                    result.log_failure("User Type Validation", "Failed to send OTP for reverse validation test")
            else:
                result.log_failure("User Type Validation", "Failed to register rider for reverse validation test")
        else:
            result.log_failure("User Type Validation", "Failed to send initial OTP for reverse validation test")
    except Exception as e:
        result.log_failure("User Type Validation", f"Reverse user type validation error: {str(e)}")
    
    # Test 3: Driver-specific field requirements
    try:
        # Test missing name for new driver registration
        otp_request = {
            "phone_number": "+91 9876543232",
            "user_type": "driver"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Try to verify without name (should fail for new user)
            verify_request = {
                "phone_number": "+91 9876543232",
                "otp_code": "123456",
                "user_type": "driver"
                # Missing name field
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if response.status_code == 400:
                data = response.json()
                if "name is required" in data.get("detail", "").lower():
                    result.log_success("Driver Field Validation - Name required for new driver registration")
                    print(f"    📝 Field validation working: {data.get('detail')}")
                else:
                    result.log_failure("Driver Field Validation", f"Wrong error message: {data.get('detail')}")
            else:
                result.log_failure("Driver Field Validation", f"Should require name for new driver, got {response.status_code}")
        else:
            result.log_failure("Driver Field Validation", "Failed to send OTP for field validation test")
    except Exception as e:
        result.log_failure("Driver Field Validation", f"Field validation error: {str(e)}")

def test_driver_otp_edge_cases_and_error_handling(result: TestResult):
    """Test edge cases and error handling specific to driver OTP"""
    print(f"\n{'='*80}")
    print("5. DRIVER OTP EDGE CASES AND ERROR HANDLING")
    print(f"{'='*80}")
    
    # Test 1: Invalid OTP for driver
    try:
        # Send OTP for driver
        otp_request = {
            "phone_number": "+91 9876543240",
            "user_type": "driver"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Try invalid OTP
            verify_request = {
                "phone_number": "+91 9876543240",
                "otp_code": "999999",  # Invalid OTP
                "user_type": "driver",
                "name": "Test Driver Invalid OTP"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("success"):
                    result.log_success("Driver Error Handling - Invalid OTP rejection for driver")
                    print(f"    ❌ Invalid OTP properly rejected: {data.get('message')}")
                else:
                    result.log_failure("Driver Error Handling", "Should reject invalid OTP for driver")
            else:
                result.log_failure("Driver Error Handling", f"Unexpected status for invalid driver OTP: {response.status_code}")
        else:
            result.log_failure("Driver Error Handling", "Failed to send OTP for invalid OTP test")
    except Exception as e:
        result.log_failure("Driver Error Handling", f"Invalid OTP test error: {str(e)}")
    
    # Test 2: Expired OTP session for driver
    try:
        # Try to verify OTP without sending it first (simulates expired session)
        verify_request = {
            "phone_number": "+91 9876543241",
            "otp_code": "123456",
            "user_type": "driver",
            "name": "Test Driver Expired"
        }
        response = make_request("POST", "/auth/verify-otp", verify_request)
        
        if response.status_code == 400:
            data = response.json()
            if "expired" in data.get("detail", "").lower() or "invalid" in data.get("detail", "").lower():
                result.log_success("Driver Error Handling - Expired/Invalid OTP session handling for driver")
                print(f"    ⏰ Expired session properly handled: {data.get('detail')}")
            else:
                result.log_failure("Driver Error Handling", f"Wrong error for expired driver session: {data.get('detail')}")
        else:
            result.log_failure("Driver Error Handling", f"Should reject expired driver session, got {response.status_code}")
    except Exception as e:
        result.log_failure("Driver Error Handling", f"Expired session test error: {str(e)}")
    
    # Test 3: Multiple OTP attempts for driver
    try:
        # Send OTP for driver
        otp_request = {
            "phone_number": "+91 9876543242",
            "user_type": "driver"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Make multiple invalid attempts
            verify_request = {
                "phone_number": "+91 9876543242",
                "otp_code": "111111",  # Invalid OTP
                "user_type": "driver",
                "name": "Test Driver Attempts"
            }
            
            attempts_made = 0
            for attempt in range(4):  # Try 4 times
                response = make_request("POST", "/auth/verify-otp", verify_request)
                attempts_made += 1
                if response.status_code == 400:
                    data = response.json()
                    if "attempts" in data.get("detail", "").lower():
                        result.log_success("Driver Error Handling - OTP attempt limit enforcement for driver")
                        print(f"    🔢 Attempt limit reached after {attempts_made} attempts")
                        break
                elif response.status_code == 200:
                    # Continue if it's just invalid OTP response
                    continue
                else:
                    break
            else:
                result.log_failure("Driver Error Handling", "OTP attempt limit not enforced for driver")
        else:
            result.log_failure("Driver Error Handling", "Failed to send OTP for attempt limit test")
    except Exception as e:
        result.log_failure("Driver Error Handling", f"Attempt limit test error: {str(e)}")

def test_driver_otp_integration_with_driver_features(result: TestResult, driver_token: str):
    """Test integration of driver OTP authentication with driver-specific features"""
    print(f"\n{'='*80}")
    print("6. DRIVER OTP INTEGRATION WITH DRIVER FEATURES")
    print(f"{'='*80}")
    
    if not driver_token:
        result.log_failure("Driver Integration", "No driver token available from OTP authentication")
        return
    
    headers = get_auth_headers(driver_token)
    
    # Test 1: Driver profile creation after OTP authentication
    try:
        driver_profile_data = {
            "per_km_rate": 18.0,
            "vehicle_type": "car",
            "vehicle_number": "KA05MN7890",
            "license_number": "DL0987654321"
        }
        response = make_request("POST", "/driver/profile", driver_profile_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "profile" in data:
                result.log_success("Driver Integration - Profile creation after OTP authentication")
                print(f"    👤 Driver profile created successfully")
            else:
                result.log_failure("Driver Integration", f"Invalid profile creation response: {data}")
        else:
            result.log_failure("Driver Integration", f"Profile creation failed: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Driver Integration", f"Profile creation error: {str(e)}")
    
    # Test 2: Driver location update after OTP authentication
    try:
        location_data = {"lat": 28.6139, "lng": 77.2090}
        response = make_request("PUT", "/driver/location", location_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "updated" in data["message"].lower():
                result.log_success("Driver Integration - Location update after OTP authentication")
                print(f"    📍 Driver location updated successfully")
            else:
                result.log_failure("Driver Integration", f"Invalid location update response: {data}")
        else:
            result.log_failure("Driver Integration", f"Location update failed: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Driver Integration", f"Location update error: {str(e)}")
    
    # Test 3: Driver availability toggle after OTP authentication
    try:
        response = make_request("PUT", "/driver/availability/true", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "available" in data["message"].lower():
                result.log_success("Driver Integration - Availability toggle after OTP authentication")
                print(f"    ✅ Driver availability set successfully")
            else:
                result.log_failure("Driver Integration", f"Invalid availability response: {data}")
        else:
            result.log_failure("Driver Integration", f"Availability toggle failed: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Driver Integration", f"Availability toggle error: {str(e)}")
    
    # Test 4: Driver ride requests access after OTP authentication
    try:
        response = make_request("GET", "/driver/ride-requests", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                result.log_success("Driver Integration - Ride requests access after OTP authentication")
                print(f"    🚗 Driver can access ride requests ({len(data)} requests)")
            else:
                result.log_failure("Driver Integration", f"Invalid ride requests response: {type(data)}")
        else:
            result.log_failure("Driver Integration", f"Ride requests access failed: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Driver Integration", f"Ride requests access error: {str(e)}")

def main():
    """Run all driver OTP authentication tests"""
    print("🚗 DRIVER USER TYPE OTP LOGIN FUNCTIONALITY TESTING")
    print("=" * 80)
    print("Testing driver OTP authentication as requested in the review")
    print("Phone number: +91 9876543210")
    print("User type: driver")
    print("=" * 80)
    
    result = TestResult()
    
    # Run all test suites
    test_driver_otp_send_functionality(result)
    driver_token = test_driver_otp_verification_functionality(result)
    test_driver_vs_rider_otp_flow_comparison(result)
    test_driver_user_type_validations_and_restrictions(result)
    test_driver_otp_edge_cases_and_error_handling(result)
    test_driver_otp_integration_with_driver_features(result, driver_token)
    
    # Print final summary
    result.summary()
    
    # Additional analysis
    print(f"\n{'='*80}")
    print("DRIVER OTP FUNCTIONALITY ANALYSIS")
    print(f"{'='*80}")
    
    if result.failed == 0:
        print("✅ ALL TESTS PASSED - Driver OTP authentication is working correctly")
        print("✅ No differences found between driver and rider OTP flows")
        print("✅ User type validations and restrictions are working properly")
        print("✅ Driver OTP integrates correctly with driver-specific features")
    else:
        print(f"❌ {result.failed} ISSUES FOUND - Driver OTP authentication has problems")
        print("🔍 Check the failed tests above for specific issues")
    
    print(f"\n📊 Test Coverage:")
    print(f"   • OTP sending for driver user type: ✅")
    print(f"   • OTP verification for driver user type: ✅")
    print(f"   • New driver registration via OTP: ✅")
    print(f"   • Existing driver login via OTP: ✅")
    print(f"   • Driver vs rider OTP flow comparison: ✅")
    print(f"   • User type validations and restrictions: ✅")
    print(f"   • Driver OTP integration with driver features: ✅")
    print(f"   • Edge cases and error handling: ✅")

if __name__ == "__main__":
    main()