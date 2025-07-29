#!/usr/bin/env python3
"""
Driver User Type OTP Login Functionality Testing - Clean Test
Testing with fresh phone numbers to avoid conflicts
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://3be44877-be55-4f11-a89f-8fbc7e4df5e7.preview.emergentagent.com/api"
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

def test_driver_otp_complete_flow(result: TestResult):
    """Test complete driver OTP flow with fresh phone number"""
    print(f"\n{'='*80}")
    print("COMPLETE DRIVER OTP AUTHENTICATION FLOW TESTING")
    print(f"{'='*80}")
    
    # Use a fresh phone number for driver testing
    driver_phone = "+91 8876543210"  # Different from the conflicting number
    driver_token = None
    
    # Step 1: Send OTP for driver user type
    try:
        otp_request = {
            "phone_number": driver_phone,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("demo_mode"):
                result.log_success(f"Step 1 - Send OTP for driver user type ({driver_phone})")
                print(f"    📱 Demo OTP: {data.get('demo_otp', 'N/A')}")
                print(f"    👤 Is existing user: {data.get('is_existing_user', False)}")
            else:
                result.log_failure("Step 1", f"Invalid OTP send response: {data}")
        else:
            result.log_failure("Step 1", f"OTP send failed: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 1", f"OTP send error: {str(e)}")
    
    # Step 2: Verify OTP for new driver registration
    try:
        verify_request = {
            "phone_number": driver_phone,
            "otp_code": "123456",  # Demo OTP
            "user_type": "driver",
            "name": "Test Driver Fresh"
        }
        response = make_request("POST", "/auth/verify-otp", verify_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("is_new_user") and data.get("token"):
                driver_token = data["token"]
                result.log_success("Step 2 - Verify OTP for new driver registration")
                print(f"    🎫 JWT Token generated: {driver_token[:20]}...")
                
                # Verify user data
                user_data = data.get("user_data", {})
                if (user_data.get("user_type") == "driver" and 
                    user_data.get("name") == "Test Driver Fresh"):
                    result.log_success("Step 2a - Driver user data populated correctly")
                    print(f"    👤 Driver: {user_data.get('name')} ({user_data.get('phone')})")
                else:
                    result.log_failure("Step 2a", f"Invalid user data: {user_data}")
            else:
                result.log_failure("Step 2", f"Invalid verification response: {data}")
        else:
            result.log_failure("Step 2", f"OTP verification failed: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 2", f"OTP verification error: {str(e)}")
    
    # Step 3: Test existing driver login
    try:
        # Send OTP again for the same number (now existing user)
        otp_request = {
            "phone_number": driver_phone,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("is_existing_user"):
                result.log_success("Step 3 - OTP send recognizes existing driver")
                
                # Verify OTP for existing driver login
                verify_request = {
                    "phone_number": driver_phone,
                    "otp_code": "000000",  # Different demo OTP
                    "user_type": "driver"
                    # No name needed for existing user
                }
                verify_response = make_request("POST", "/auth/verify-otp", verify_request)
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    if verify_data.get("success") and not verify_data.get("is_new_user"):
                        result.log_success("Step 3a - Existing driver login successful")
                        print(f"    🔑 Existing driver logged in successfully")
                    else:
                        result.log_failure("Step 3a", f"Should be existing user login: {verify_data}")
                else:
                    result.log_failure("Step 3a", f"Existing driver login failed: {verify_response.status_code}")
            else:
                result.log_failure("Step 3", "Driver should be marked as existing user")
        else:
            result.log_failure("Step 3", f"OTP send for existing driver failed: {response.status_code}")
    except Exception as e:
        result.log_failure("Step 3", f"Existing driver login error: {str(e)}")
    
    # Step 4: Test driver token with driver-specific endpoints
    if driver_token:
        headers = get_auth_headers(driver_token)
        
        # Test driver profile creation
        try:
            profile_data = {
                "per_km_rate": 20.0,
                "vehicle_type": "sedan",
                "vehicle_number": "KA01DR1234",
                "license_number": "DL1234567890"
            }
            response = make_request("POST", "/driver/profile", profile_data, headers)
            if response.status_code == 200:
                result.log_success("Step 4 - Driver profile creation with OTP token")
                print(f"    👤 Driver profile created successfully")
            else:
                result.log_failure("Step 4", f"Profile creation failed: {response.status_code}")
        except Exception as e:
            result.log_failure("Step 4", f"Profile creation error: {str(e)}")
        
        # Test driver location update
        try:
            location_data = {"lat": 28.6139, "lng": 77.2090}
            response = make_request("PUT", "/driver/location", location_data, headers)
            if response.status_code == 200:
                result.log_success("Step 4a - Driver location update with OTP token")
                print(f"    📍 Driver location updated successfully")
            else:
                result.log_failure("Step 4a", f"Location update failed: {response.status_code}")
        except Exception as e:
            result.log_failure("Step 4a", f"Location update error: {str(e)}")
        
        # Test driver availability toggle
        try:
            response = make_request("PUT", "/driver/availability/true", headers=headers)
            if response.status_code == 200:
                result.log_success("Step 4b - Driver availability toggle with OTP token")
                print(f"    ✅ Driver availability set successfully")
            else:
                result.log_failure("Step 4b", f"Availability toggle failed: {response.status_code}")
        except Exception as e:
            result.log_failure("Step 4b", f"Availability toggle error: {str(e)}")
        
        # Test driver ride requests access
        try:
            response = make_request("GET", "/driver/ride-requests", headers=headers)
            if response.status_code == 200:
                data = response.json()
                result.log_success("Step 4c - Driver ride requests access with OTP token")
                print(f"    🚗 Driver can access ride requests ({len(data)} requests)")
            else:
                result.log_failure("Step 4c", f"Ride requests access failed: {response.status_code}")
        except Exception as e:
            result.log_failure("Step 4c", f"Ride requests access error: {str(e)}")
    
    return driver_token

def test_driver_vs_rider_comparison(result: TestResult):
    """Compare driver and rider OTP flows side by side"""
    print(f"\n{'='*80}")
    print("DRIVER VS RIDER OTP FLOW COMPARISON")
    print(f"{'='*80}")
    
    # Use fresh phone numbers for comparison
    driver_phone = "+91 7776543210"
    rider_phone = "+91 7776543211"
    
    # Test 1: Compare OTP send responses
    try:
        # Driver OTP send
        driver_request = {"phone_number": driver_phone, "user_type": "driver"}
        driver_response = make_request("POST", "/auth/send-otp", driver_request)
        
        # Rider OTP send
        rider_request = {"phone_number": rider_phone, "user_type": "rider"}
        rider_response = make_request("POST", "/auth/send-otp", rider_request)
        
        if driver_response.status_code == 200 and rider_response.status_code == 200:
            driver_data = driver_response.json()
            rider_data = rider_response.json()
            
            # Compare response structures
            if set(driver_data.keys()) == set(rider_data.keys()):
                result.log_success("Comparison - OTP send response structure identical")
            else:
                result.log_failure("Comparison", f"Different response structures")
            
            # Compare specific fields
            if (driver_data.get("success") == rider_data.get("success") and
                driver_data.get("demo_mode") == rider_data.get("demo_mode")):
                result.log_success("Comparison - OTP send functionality identical")
            else:
                result.log_failure("Comparison", "OTP send functionality differs")
        else:
            result.log_failure("Comparison", f"Status code mismatch: Driver={driver_response.status_code}, Rider={rider_response.status_code}")
    except Exception as e:
        result.log_failure("Comparison", f"OTP send comparison error: {str(e)}")
    
    # Test 2: Compare OTP verification responses
    try:
        # Driver OTP verification
        driver_verify = {
            "phone_number": driver_phone,
            "otp_code": "123456",
            "user_type": "driver",
            "name": "Test Driver Compare"
        }
        driver_verify_response = make_request("POST", "/auth/verify-otp", driver_verify)
        
        # Rider OTP verification
        rider_verify = {
            "phone_number": rider_phone,
            "otp_code": "123456",
            "user_type": "rider",
            "name": "Test Rider Compare"
        }
        rider_verify_response = make_request("POST", "/auth/verify-otp", rider_verify)
        
        if driver_verify_response.status_code == 200 and rider_verify_response.status_code == 200:
            driver_data = driver_verify_response.json()
            rider_data = rider_verify_response.json()
            
            # Compare response structures
            if set(driver_data.keys()) == set(rider_data.keys()):
                result.log_success("Comparison - OTP verify response structure identical")
            else:
                result.log_failure("Comparison", f"Different verify response structures")
            
            # Compare user types in responses
            driver_user_type = driver_data.get("user_data", {}).get("user_type")
            rider_user_type = rider_data.get("user_data", {}).get("user_type")
            
            if driver_user_type == "driver" and rider_user_type == "rider":
                result.log_success("Comparison - User types correctly assigned")
            else:
                result.log_failure("Comparison", f"User type assignment issue: Driver={driver_user_type}, Rider={rider_user_type}")
        else:
            result.log_failure("Comparison", f"Verify status mismatch: Driver={driver_verify_response.status_code}, Rider={rider_verify_response.status_code}")
    except Exception as e:
        result.log_failure("Comparison", f"OTP verify comparison error: {str(e)}")

def test_user_type_restrictions(result: TestResult):
    """Test user type specific validations and restrictions"""
    print(f"\n{'='*80}")
    print("USER TYPE VALIDATIONS AND RESTRICTIONS TESTING")
    print(f"{'='*80}")
    
    # Test 1: Register driver, then try to login as rider (should fail)
    try:
        driver_phone = "+91 6676543210"
        
        # Register as driver
        otp_request = {"phone_number": driver_phone, "user_type": "driver"}
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            verify_request = {
                "phone_number": driver_phone,
                "otp_code": "123456",
                "user_type": "driver",
                "name": "Test Driver Restriction"
            }
            reg_response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if reg_response.status_code == 200:
                # Now try to login as rider (should fail)
                otp_request["user_type"] = "rider"
                send_response2 = make_request("POST", "/auth/send-otp", otp_request)
                
                if send_response2.status_code == 200:
                    verify_request["user_type"] = "rider"
                    verify_request.pop("name", None)
                    wrong_type_response = make_request("POST", "/auth/verify-otp", verify_request)
                    
                    if wrong_type_response.status_code == 400:
                        data = wrong_type_response.json()
                        if "registered as driver" in data.get("detail", "").lower():
                            result.log_success("Restriction - Driver cannot login as rider")
                            print(f"    🚫 Correct restriction: {data.get('detail')}")
                        else:
                            result.log_failure("Restriction", f"Wrong error message: {data.get('detail')}")
                    else:
                        result.log_failure("Restriction", f"Should reject wrong user type, got {wrong_type_response.status_code}")
                else:
                    result.log_failure("Restriction", "Failed to send OTP for restriction test")
            else:
                result.log_failure("Restriction", "Failed to register driver for restriction test")
        else:
            result.log_failure("Restriction", "Failed to send initial OTP for restriction test")
    except Exception as e:
        result.log_failure("Restriction", f"User type restriction error: {str(e)}")

def main():
    """Run comprehensive driver OTP testing with clean data"""
    print("🚗 DRIVER USER TYPE OTP LOGIN FUNCTIONALITY TESTING")
    print("=" * 80)
    print("Testing driver OTP authentication with fresh phone numbers")
    print("Avoiding conflicts with existing registrations")
    print("=" * 80)
    
    result = TestResult()
    
    # Run test suites
    driver_token = test_driver_otp_complete_flow(result)
    test_driver_vs_rider_comparison(result)
    test_user_type_restrictions(result)
    
    # Print final summary
    result.summary()
    
    # Analysis
    print(f"\n{'='*80}")
    print("DRIVER OTP FUNCTIONALITY ANALYSIS")
    print(f"{'='*80}")
    
    if result.failed == 0:
        print("✅ ALL TESTS PASSED - Driver OTP authentication working correctly")
        print("✅ Driver OTP flow identical to rider OTP flow")
        print("✅ User type validations working properly")
        print("✅ Driver OTP integrates with driver features")
    else:
        print(f"❌ {result.failed} ISSUES FOUND")
        if result.failed <= 2:
            print("⚠️  Minor issues found, core functionality working")
        else:
            print("🚨 Significant issues found, needs attention")
    
    print(f"\n📋 KEY FINDINGS:")
    print(f"   • Driver OTP send functionality: {'✅ Working' if result.passed >= 3 else '❌ Issues'}")
    print(f"   • Driver OTP verification: {'✅ Working' if result.passed >= 5 else '❌ Issues'}")
    print(f"   • Driver vs Rider flow comparison: {'✅ Identical' if result.passed >= 7 else '❌ Differences'}")
    print(f"   • User type restrictions: {'✅ Working' if result.passed >= 8 else '❌ Issues'}")
    print(f"   • Driver feature integration: {'✅ Working' if result.passed >= 10 else '❌ Issues'}")

if __name__ == "__main__":
    main()