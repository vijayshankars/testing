#!/usr/bin/env python3
"""
VAHAN Vehicle Verification System Testing
Tests the new VAHAN vehicle verification integration as requested in the review
"""

import requests
import json
import time
import random
import string
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://87aa55a7-7445-442a-b69c-85a42d10dc65.preview.emergentagent.com/api"
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
        print(f"VAHAN VEHICLE VERIFICATION TEST SUMMARY")
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

def generate_unique_phone():
    """Generate a unique phone number for testing"""
    random_digits = ''.join(random.choices(string.digits, k=6))
    return f"+91 98765{random_digits}"

def test_vahan_vehicle_verification_system():
    """Test VAHAN vehicle verification integration as requested in the review"""
    print(f"🚗 VAHAN VEHICLE VERIFICATION SYSTEM TESTING")
    print(f"Testing against: {BASE_URL}")
    print(f"{'='*60}")
    
    result = TestResult()
    
    # Generate unique phone number for this test
    test_phone = generate_unique_phone()
    print(f"Using test phone number: {test_phone}")
    
    driver_token = None
    
    # Step 1: Create a test driver user via mobile OTP authentication
    print(f"\n--- Step 1: Create Test Driver User via Mobile OTP ---")
    
    # Send OTP for driver registration
    try:
        otp_data = {
            "phone_number": test_phone,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result.log_success("Driver OTP sent successfully")
                demo_otp = data.get("demo_otp", "123456")  # Use demo OTP
            else:
                result.log_failure("Driver OTP send", f"Failed: {data}")
                return result
        else:
            result.log_failure("Driver OTP send", f"Status {response.status_code}: {response.text}")
            return result
    except Exception as e:
        result.log_failure("Driver OTP send", str(e))
        return result
    
    # Verify OTP and create driver user
    try:
        verify_data = {
            "phone_number": test_phone,
            "otp_code": demo_otp,
            "user_type": "driver",
            "name": "Test Driver for VAHAN Vehicle Verification"
        }
        response = make_request("POST", "/auth/verify-otp", verify_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("token"):
                driver_token = data["token"]
                result.log_success("Driver OTP verification and registration")
            else:
                result.log_failure("Driver OTP verification", f"Failed: {data}")
                return result
        else:
            result.log_failure("Driver OTP verification", f"Status {response.status_code}: {response.text}")
            return result
    except Exception as e:
        result.log_failure("Driver OTP verification", str(e))
        return result
    
    if not driver_token:
        result.log_failure("Vehicle verification setup", "No driver token available")
        return result
    
    headers = get_auth_headers(driver_token)
    
    # Step 2: Test Vehicle Verification Endpoint with Valid Indian Vehicle Numbers
    print(f"\n--- Step 2: Test Valid Indian Vehicle Numbers ---")
    
    valid_vehicles = [
        {"number": "KA01AB1234", "state": "Karnataka"},
        {"number": "TN02CD5678", "state": "Tamil Nadu"},
        {"number": "MH12EF9012", "state": "Maharashtra"},
        {"number": "DL03GH3456", "state": "Delhi"}
    ]
    
    for vehicle in valid_vehicles:
        try:
            vehicle_data = {
                "vehicle_number": vehicle["number"],
                "vehicle_type": "car"
            }
            response = make_request("POST", "/driver/verify-vehicle", vehicle_data, headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("vehicle_data"):
                    vehicle_info = data["vehicle_data"]
                    # Verify required fields in response
                    required_fields = ["registration_number", "owner_name", "vehicle_class", 
                                     "fuel_type", "registration_date", "status"]
                    if all(field in vehicle_info for field in required_fields):
                        result.log_success(f"Vehicle verification for {vehicle['number']} ({vehicle['state']})")
                        
                        # Verify verification ID is generated
                        if data.get("verification_id"):
                            result.log_success(f"Verification ID generated for {vehicle['number']}")
                        else:
                            result.log_failure(f"Verification ID for {vehicle['number']}", "Missing verification_id")
                        
                        # Check specific data structure
                        if vehicle_info.get("registration_number") == vehicle["number"]:
                            result.log_success(f"Registration number matches for {vehicle['number']}")
                        else:
                            result.log_failure(f"Registration number mismatch for {vehicle['number']}", 
                                             f"Expected {vehicle['number']}, got {vehicle_info.get('registration_number')}")
                    else:
                        missing_fields = [f for f in required_fields if f not in vehicle_info]
                        result.log_failure(f"Vehicle data structure for {vehicle['number']}", 
                                         f"Missing fields: {missing_fields}")
                else:
                    result.log_failure(f"Vehicle verification for {vehicle['number']}", 
                                     f"Invalid response: {data}")
            else:
                result.log_failure(f"Vehicle verification for {vehicle['number']}", 
                                 f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure(f"Vehicle verification for {vehicle['number']}", str(e))
    
    # Step 3: Test Vehicle Number Format Validation
    print(f"\n--- Step 3: Test Vehicle Number Format Validation ---")
    
    invalid_vehicles = [
        {"number": "KA1AB123", "reason": "too short"},
        {"number": "INVALID123", "reason": "wrong pattern"},
        {"number": "123456789", "reason": "no state code"},
        {"number": "AB01CD12345", "reason": "too long"},
        {"number": "", "reason": "empty"},
        {"number": "XX01YZ1234", "reason": "unsupported state code"}
    ]
    
    for vehicle in invalid_vehicles:
        try:
            vehicle_data = {
                "vehicle_number": vehicle["number"],
                "vehicle_type": "car"
            }
            response = make_request("POST", "/driver/verify-vehicle", vehicle_data, headers)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("success"):
                    result.log_success(f"Invalid vehicle rejection: {vehicle['number']} ({vehicle['reason']})")
                else:
                    result.log_failure(f"Invalid vehicle handling for {vehicle['number']}", 
                                     f"Should have been rejected but was accepted: {data}")
            else:
                # Some invalid formats might return 400, which is also acceptable
                if response.status_code == 400:
                    result.log_success(f"Invalid vehicle rejection: {vehicle['number']} ({vehicle['reason']})")
                else:
                    result.log_failure(f"Invalid vehicle handling for {vehicle['number']}", 
                                     f"Unexpected status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure(f"Invalid vehicle handling for {vehicle['number']}", str(e))
    
    # Step 4: Test Different State Codes
    print(f"\n--- Step 4: Test Different State Codes ---")
    
    state_vehicles = [
        {"number": "GJ05PQ1234", "state": "Gujarat"},
        {"number": "UP32RS5678", "state": "Uttar Pradesh"},
        {"number": "AP28TU9012", "state": "Andhra Pradesh"},
        {"number": "TS07VW3456", "state": "Telangana"},
        {"number": "RJ14XY7890", "state": "Rajasthan"},
        {"number": "WB19ZA2345", "state": "West Bengal"}
    ]
    
    for vehicle in state_vehicles:
        try:
            vehicle_data = {
                "vehicle_number": vehicle["number"],
                "vehicle_type": "auto"
            }
            response = make_request("POST", "/driver/verify-vehicle", vehicle_data, headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("vehicle_data"):
                    result.log_success(f"State code verification: {vehicle['number']} ({vehicle['state']})")
                else:
                    result.log_failure(f"State code verification for {vehicle['number']}", f"Failed: {data}")
            else:
                result.log_failure(f"State code verification for {vehicle['number']}", 
                                 f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure(f"State code verification for {vehicle['number']}", str(e))
    
    # Step 5: Test Vehicle Data Response Structure
    print(f"\n--- Step 5: Test Vehicle Data Response Structure ---")
    
    try:
        vehicle_data = {
            "vehicle_number": "KA09BC5678",
            "vehicle_type": "suv"
        }
        response = make_request("POST", "/driver/verify-vehicle", vehicle_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("vehicle_data"):
                vehicle_info = data["vehicle_data"]
                
                # Check all expected fields
                expected_fields = {
                    "registration_number": str,
                    "owner_name": str,
                    "vehicle_class": str,
                    "fuel_type": str,
                    "registration_date": str,
                    "validity_until": str,
                    "engine_number": str,
                    "chassis_number": str,
                    "fitness_validity": str,
                    "insurance_validity": str,
                    "status": str
                }
                
                all_fields_present = True
                for field, expected_type in expected_fields.items():
                    if field not in vehicle_info:
                        result.log_failure(f"Vehicle data structure", f"Missing field: {field}")
                        all_fields_present = False
                    elif not isinstance(vehicle_info[field], expected_type):
                        result.log_failure(f"Vehicle data structure", 
                                         f"Field {field} has wrong type: expected {expected_type.__name__}, got {type(vehicle_info[field]).__name__}")
                        all_fields_present = False
                
                if all_fields_present:
                    result.log_success("Vehicle data response structure complete")
                    
                    # Check specific values
                    if vehicle_info.get("status") == "ACTIVE":
                        result.log_success("Vehicle status field correct")
                    else:
                        result.log_failure("Vehicle status field", f"Expected ACTIVE, got {vehicle_info.get('status')}")
                        
            else:
                result.log_failure("Vehicle data response structure", f"Invalid response: {data}")
        else:
            result.log_failure("Vehicle data response structure", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Vehicle data response structure", str(e))
    
    # Step 6: Test Error Scenarios
    print(f"\n--- Step 6: Test Error Scenarios ---")
    
    # Test unauthorized access (without token)
    try:
        vehicle_data = {
            "vehicle_number": "KA01AB1234",
            "vehicle_type": "car"
        }
        response = make_request("POST", "/driver/verify-vehicle", vehicle_data)
        
        if response.status_code == 401 or response.status_code == 403:
            result.log_success("Unauthorized access properly rejected")
        else:
            result.log_failure("Unauthorized access handling", 
                             f"Should return 401/403 but got {response.status_code}")
    except Exception as e:
        result.log_failure("Unauthorized access handling", str(e))
    
    # Test malformed request (missing vehicle_number)
    try:
        vehicle_data = {
            "vehicle_type": "car"
        }
        response = make_request("POST", "/driver/verify-vehicle", vehicle_data, headers)
        
        if response.status_code == 422 or response.status_code == 400:
            result.log_success("Malformed request properly rejected")
        else:
            result.log_failure("Malformed request handling", 
                             f"Should return 422/400 but got {response.status_code}")
    except Exception as e:
        result.log_failure("Malformed request handling", str(e))
    
    # Step 7: Test Integration with Driver Profile Creation
    print(f"\n--- Step 7: Test Integration with Driver Profile ---")
    
    try:
        # First verify a vehicle
        vehicle_data = {
            "vehicle_number": "TN09PQ5678",
            "vehicle_type": "auto"
        }
        verify_response = make_request("POST", "/driver/verify-vehicle", vehicle_data, headers)
        
        if verify_response.status_code == 200 and verify_response.json().get("success"):
            result.log_success("Vehicle verified before profile creation")
            
            # Now create driver profile with the same vehicle number
            profile_data = {
                "vehicle_type": "auto",
                "vehicle_number": "TN09PQ5678",
                "license_number": "DL1234567890"
            }
            profile_response = make_request("POST", "/driver/profile", profile_data, headers)
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                if "profile" in profile_data:
                    result.log_success("Driver profile created with verified vehicle")
                    
                    # Verify auto-assigned rates work with vehicle verification
                    profile_info = profile_data["profile"]
                    if profile_info.get("per_km_rate") == 8.0:  # Auto rate
                        result.log_success("Auto-assigned rate applied correctly for auto vehicle")
                    else:
                        result.log_failure("Auto-assigned rate", 
                                         f"Expected 8.0 for auto, got {profile_info.get('per_km_rate')}")
                else:
                    result.log_failure("Driver profile creation", f"Invalid response: {profile_data}")
            else:
                result.log_failure("Driver profile creation", 
                                 f"Status {profile_response.status_code}: {profile_response.text}")
        else:
            result.log_failure("Vehicle verification for profile integration", 
                             f"Failed to verify vehicle: {verify_response.text}")
    except Exception as e:
        result.log_failure("Vehicle verification and profile integration", str(e))
    
    # Step 8: Test Both License and Vehicle Verification Together
    print(f"\n--- Step 8: Test License and Vehicle Verification Together ---")
    
    try:
        # Test license verification first
        license_data = {
            "license_number": "DL9876543210"
        }
        license_response = make_request("POST", "/driver/verify-license", license_data, headers)
        
        if license_response.status_code == 200 and license_response.json().get("success"):
            result.log_success("License verification working")
            
            # Then test vehicle verification
            vehicle_data = {
                "vehicle_number": "MH14CD7890",
                "vehicle_type": "car"
            }
            vehicle_response = make_request("POST", "/driver/verify-vehicle", vehicle_data, headers)
            
            if vehicle_response.status_code == 200 and vehicle_response.json().get("success"):
                result.log_success("Vehicle verification working alongside license verification")
                
                # Both verifications should work independently
                result.log_success("License and vehicle verification integration complete")
            else:
                result.log_failure("Vehicle verification with license", 
                                 f"Vehicle verification failed: {vehicle_response.text}")
        else:
            result.log_failure("License verification for integration", 
                             f"License verification failed: {license_response.text}")
    except Exception as e:
        result.log_failure("License and vehicle verification integration", str(e))
    
    return result

if __name__ == "__main__":
    result = test_vahan_vehicle_verification_system()
    result.summary()
    
    # Return appropriate exit code
    exit(0 if result.failed == 0 else 1)