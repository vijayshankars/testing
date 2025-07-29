#!/usr/bin/env python3
"""
Comprehensive OTP Verification and Ride Start Functionality Testing
Tests the complete flow from user creation to ride OTP verification and start
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://06841ea6-50ad-424b-b520-f2f741bf6fdb.preview.emergentagent.com/api"
TIMEOUT = 30

# Test data for OTP verification testing
import time
TIMESTAMP = str(int(time.time()))[-4:]  # Last 4 digits of timestamp for uniqueness
RIDER_PHONE = f"+91 987654{TIMESTAMP[:4]}"
DRIVER_PHONE = f"+91 987655{TIMESTAMP[:4]}"
DEMO_OTP = "123456"

# Chennai locations for testing
CHENNAI_LOCATIONS = {
    "pickup": {
        "lat": 13.0827,
        "lng": 80.2707,
        "address": "Chennai Central Railway Station"
    },
    "drop": {
        "lat": 13.0569,
        "lng": 80.2426,
        "address": "Marina Beach, Chennai"
    }
}

# Global variables to store test data
rider_token = None
driver_token = None
rider_id = None
driver_id = None
ride_id = None
ride_otp = None

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
        print(f"OTP VERIFICATION AND RIDE START FUNCTIONALITY TEST SUMMARY")
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

def test_create_test_users(result: TestResult):
    """Test 1: Create test rider and driver with mobile OTP authentication"""
    global rider_token, driver_token, rider_id, driver_id
    
    print(f"\n{'='*80}")
    print("1. CREATE TEST USERS WITH MOBILE OTP AUTHENTICATION")
    print(f"{'='*80}")
    
    # Create test rider with mobile OTP
    try:
        # Send OTP for rider
        otp_data = {
            "phone_number": RIDER_PHONE,
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_data)
        
        if response.status_code == 200:
            result.log_success("Send OTP for test rider (+91 9876543210)")
            
            # Verify OTP and create rider
            verify_data = {
                "phone_number": RIDER_PHONE,
                "otp_code": DEMO_OTP,
                "user_type": "rider",
                "name": "Test Rider Chennai"
            }
            response = make_request("POST", "/auth/verify-otp", verify_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    rider_token = data["token"]
                    rider_id = data["user_data"]["id"]
                    result.log_success("Create test rider with mobile OTP authentication")
                else:
                    result.log_failure("Create test rider", f"Invalid response: {data}")
            else:
                result.log_failure("Create test rider", f"Status {response.status_code}: {response.text}")
        else:
            result.log_failure("Send OTP for rider", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Create test rider", str(e))
    
    # Create test driver with mobile OTP
    try:
        # Send OTP for driver
        otp_data = {
            "phone_number": DRIVER_PHONE,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_data)
        
        if response.status_code == 200:
            result.log_success("Send OTP for test driver (+91 9876543211)")
            
            # Verify OTP and create driver
            verify_data = {
                "phone_number": DRIVER_PHONE,
                "otp_code": DEMO_OTP,
                "user_type": "driver",
                "name": "Test Driver Chennai"
            }
            response = make_request("POST", "/auth/verify-otp", verify_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    driver_token = data["token"]
                    driver_id = data["user_data"]["id"]
                    result.log_success("Create test driver with mobile OTP authentication")
                else:
                    result.log_failure("Create test driver", f"Invalid response: {data}")
            else:
                result.log_failure("Create test driver", f"Status {response.status_code}: {response.text}")
        else:
            result.log_failure("Send OTP for driver", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Create test driver", str(e))

def test_create_driver_profile(result: TestResult):
    """Test 2: Create driver profile for the test driver"""
    global driver_token
    
    print(f"\n{'='*80}")
    print("2. CREATE DRIVER PROFILE")
    print(f"{'='*80}")
    
    if not driver_token:
        result.log_failure("Create driver profile", "Driver token not available")
        return
    
    try:
        profile_data = {
            "vehicle_type": "auto",
            "vehicle_number": "TN01AB1234",
            "license_number": "DL1234567890"
        }
        
        headers = get_auth_headers(driver_token)
        response = make_request("POST", "/driver/profile", profile_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if "profile" in data and data["profile"].get("per_km_rate") == 8.0:
                result.log_success("Create driver profile with auto-assigned rate (8.0 for auto)")
            else:
                result.log_failure("Create driver profile", f"Invalid profile data: {data}")
        else:
            result.log_failure("Create driver profile", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Create driver profile", str(e))
    
    # Set driver location
    try:
        location_data = {
            "lat": CHENNAI_LOCATIONS["pickup"]["lat"],
            "lng": CHENNAI_LOCATIONS["pickup"]["lng"]
        }
        
        headers = get_auth_headers(driver_token)
        response = make_request("PUT", "/driver/location", location_data, headers)
        
        if response.status_code == 200:
            result.log_success("Set driver location to Chennai Central")
        else:
            result.log_failure("Set driver location", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Set driver location", str(e))

def test_ride_request_and_otp_generation(result: TestResult):
    """Test 3: Create ride request and have driver accept it (generates OTP)"""
    global rider_token, driver_token, ride_id, ride_otp
    
    print(f"\n{'='*80}")
    print("3. RIDE REQUEST AND OTP GENERATION")
    print(f"{'='*80}")
    
    if not rider_token or not driver_token:
        result.log_failure("Ride request", "User tokens not available")
        return
    
    # Create ride request from rider
    try:
        ride_data = {
            "pickup_location": CHENNAI_LOCATIONS["pickup"],
            "drop_location": CHENNAI_LOCATIONS["drop"],
            "estimated_distance": 5.2,
            "estimated_fare": 120.0
        }
        
        headers = get_auth_headers(rider_token)
        response = make_request("POST", "/rider/rides", ride_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("id") and data.get("status") == "requested":
                ride_id = data["id"]
                result.log_success("Create ride request from Chennai Central to Marina Beach")
            else:
                result.log_failure("Create ride request", f"Invalid ride data: {data}")
        else:
            result.log_failure("Create ride request", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Create ride request", str(e))
    
    if not ride_id:
        result.log_failure("Driver accept ride", "Ride ID not available")
        return
    
    # Driver accepts ride (should generate OTP)
    try:
        headers = get_auth_headers(driver_token)
        response = make_request("POST", f"/driver/accept-ride/{ride_id}", {}, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ride_otp") and len(data["ride_otp"]) == 4:
                ride_otp = data["ride_otp"]
                result.log_success(f"Driver accepts ride and generates 4-digit OTP: {ride_otp}")
                
                # Verify ride status is "accepted"
                headers = get_auth_headers(rider_token)
                response = make_request("GET", "/rider/rides", headers=headers)
                
                if response.status_code == 200:
                    rides = response.json()
                    current_ride = next((r for r in rides if r["id"] == ride_id), None)
                    if current_ride and current_ride["status"] == "accepted":
                        result.log_success("Verify ride status changed to 'accepted'")
                    else:
                        result.log_failure("Verify ride status", f"Status not 'accepted': {current_ride}")
                else:
                    result.log_failure("Verify ride status", f"Status {response.status_code}: {response.text}")
            else:
                result.log_failure("Driver accept ride", f"Invalid OTP response: {data}")
        else:
            result.log_failure("Driver accept ride", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Driver accept ride", str(e))

def test_otp_verification_and_start_ride(result: TestResult):
    """Test 4: Test OTP verification and ride start functionality"""
    global driver_token, ride_id, ride_otp
    
    print(f"\n{'='*80}")
    print("4. OTP VERIFICATION AND START RIDE")
    print(f"{'='*80}")
    
    if not driver_token or not ride_id or not ride_otp:
        result.log_failure("OTP verification", "Required data not available")
        return
    
    # Test correct OTP verification
    try:
        verify_data = {
            "ride_id": ride_id,
            "otp_code": ride_otp
        }
        
        headers = get_auth_headers(driver_token)
        response = make_request("POST", "/driver/verify-ride-otp", verify_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "in_progress":
                result.log_success("OTP verification successful - ride status changed to 'in_progress'")
                
                # Verify otp_verified flag and started_at timestamp
                headers = get_auth_headers(rider_token)
                response = make_request("GET", "/rider/rides", headers=headers)
                
                if response.status_code == 200:
                    rides = response.json()
                    current_ride = next((r for r in rides if r["id"] == ride_id), None)
                    if current_ride:
                        if current_ride.get("otp_verified") == True:
                            result.log_success("Verify otp_verified flag set to true")
                        else:
                            result.log_failure("Verify otp_verified flag", f"Flag not true: {current_ride.get('otp_verified')}")
                        
                        if current_ride.get("started_at"):
                            result.log_success("Verify started_at timestamp is set")
                        else:
                            result.log_failure("Verify started_at timestamp", "Timestamp not set")
                    else:
                        result.log_failure("Verify ride data", "Ride not found")
                else:
                    result.log_failure("Verify ride data", f"Status {response.status_code}: {response.text}")
            else:
                result.log_failure("OTP verification", f"Invalid status response: {data}")
        else:
            result.log_failure("OTP verification", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("OTP verification", str(e))

def test_error_scenarios(result: TestResult):
    """Test 5: Test error scenarios for OTP verification"""
    global driver_token, rider_token, ride_id
    
    print(f"\n{'='*80}")
    print("5. ERROR SCENARIOS TESTING")
    print(f"{'='*80}")
    
    if not driver_token or not rider_token:
        result.log_failure("Error scenarios", "Required data not available")
        return
    
    # Create a new ride for error testing
    test_ride_id = None
    test_ride_otp = None
    
    try:
        ride_data = {
            "pickup_location": CHENNAI_LOCATIONS["pickup"],
            "drop_location": CHENNAI_LOCATIONS["drop"],
            "estimated_distance": 3.5,
            "estimated_fare": 80.0
        }
        
        headers = get_auth_headers(rider_token)
        response = make_request("POST", "/rider/rides", ride_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            test_ride_id = data["id"]
            
            # Driver accepts this test ride
            headers = get_auth_headers(driver_token)
            response = make_request("POST", f"/driver/accept-ride/{test_ride_id}", {}, headers)
            
            if response.status_code == 200:
                data = response.json()
                test_ride_otp = data["ride_otp"]
            else:
                result.log_failure("Create test ride for errors", f"Accept failed: {response.status_code}")
                return
        else:
            result.log_failure("Create test ride for errors", f"Create failed: {response.status_code}")
            return
    except Exception as e:
        result.log_failure("Create test ride for errors", str(e))
        return
    
    # Test invalid OTP
    try:
        verify_data = {
            "ride_id": test_ride_id,
            "otp_code": "9999"  # Invalid OTP
        }
        
        headers = get_auth_headers(driver_token)
        response = make_request("POST", "/driver/verify-ride-otp", verify_data, headers)
        
        if response.status_code == 400:
            result.log_success("Invalid OTP correctly rejected with 400 error")
        else:
            result.log_failure("Invalid OTP test", f"Expected 400, got {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Invalid OTP test", str(e))
    
    # Test wrong driver trying to verify (create another driver)
    try:
        # Create another driver
        wrong_driver_phone = f"+91 987656{TIMESTAMP[:4]}"
        otp_data = {
            "phone_number": wrong_driver_phone,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_data)
        
        if response.status_code == 200:
            verify_data = {
                "phone_number": wrong_driver_phone,
                "otp_code": DEMO_OTP,
                "user_type": "driver",
                "name": "Wrong Driver"
            }
            response = make_request("POST", "/auth/verify-otp", verify_data)
            
            if response.status_code == 200:
                wrong_driver_token = response.json()["token"]
                
                # Try to verify OTP with wrong driver
                verify_data = {
                    "ride_id": test_ride_id,
                    "otp_code": test_ride_otp  # Correct OTP but wrong driver
                }
                
                headers = get_auth_headers(wrong_driver_token)
                response = make_request("POST", "/driver/verify-ride-otp", verify_data, headers)
                
                if response.status_code == 404:
                    result.log_success("Wrong driver correctly prevented from verifying OTP (404 error)")
                else:
                    result.log_failure("Wrong driver test", f"Expected 404, got {response.status_code}: {response.text}")
            else:
                result.log_failure("Create wrong driver", f"Status {response.status_code}: {response.text}")
        else:
            result.log_failure("Send OTP for wrong driver", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Wrong driver test", str(e))
    
    # Now verify the test ride with correct OTP to start it
    try:
        verify_data = {
            "ride_id": test_ride_id,
            "otp_code": test_ride_otp
        }
        
        headers = get_auth_headers(driver_token)
        response = make_request("POST", "/driver/verify-ride-otp", verify_data, headers)
        
        if response.status_code == 200:
            # Test verifying already started ride
            try:
                verify_data = {
                    "ride_id": test_ride_id,
                    "otp_code": test_ride_otp  # Same OTP
                }
                
                headers = get_auth_headers(driver_token)
                response = make_request("POST", "/driver/verify-ride-otp", verify_data, headers)
                
                if response.status_code == 404:
                    result.log_success("Already started ride correctly prevents double verification (404 error)")
                else:
                    result.log_failure("Double verification test", f"Expected 404, got {response.status_code}: {response.text}")
            except Exception as e:
                result.log_failure("Double verification test", str(e))
        else:
            result.log_failure("Start test ride", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Start test ride", str(e))

def test_complete_ride_flow(result: TestResult):
    """Test 6: Test complete ride flow from request to completion"""
    global driver_token, ride_id
    
    print(f"\n{'='*80}")
    print("6. COMPLETE RIDE FLOW TESTING")
    print(f"{'='*80}")
    
    if not driver_token or not ride_id:
        result.log_failure("Complete ride flow", "Required data not available")
        return
    
    # Complete the ride
    try:
        complete_data = {
            "ride_id": ride_id,
            "status": "completed"
        }
        
        headers = get_auth_headers(driver_token)
        response = make_request("POST", "/driver/complete-ride", complete_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "completed":
                result.log_success("Ride completed successfully")
                
                # Verify ride status in database
                headers = get_auth_headers(rider_token)
                response = make_request("GET", "/rider/rides", headers=headers)
                
                if response.status_code == 200:
                    rides = response.json()
                    current_ride = next((r for r in rides if r["id"] == ride_id), None)
                    if current_ride and current_ride["status"] == "completed":
                        result.log_success("Verify ride status changed to 'completed'")
                        
                        if current_ride.get("completed_at"):
                            result.log_success("Verify completed_at timestamp is set")
                        else:
                            result.log_failure("Verify completed_at timestamp", "Timestamp not set")
                    else:
                        result.log_failure("Verify completed ride status", f"Status not 'completed': {current_ride}")
                else:
                    result.log_failure("Verify completed ride", f"Status {response.status_code}: {response.text}")
            else:
                result.log_failure("Complete ride", f"Invalid status response: {data}")
        else:
            result.log_failure("Complete ride", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Complete ride", str(e))

def main():
    """Run all OTP verification and ride start functionality tests"""
    print("🚀 STARTING COMPREHENSIVE OTP VERIFICATION AND RIDE START FUNCTIONALITY TESTING")
    print("=" * 80)
    
    result = TestResult()
    
    # Run all tests in sequence
    test_create_test_users(result)
    test_create_driver_profile(result)
    test_ride_request_and_otp_generation(result)
    test_otp_verification_and_start_ride(result)
    test_error_scenarios(result)
    test_complete_ride_flow(result)
    
    # Print final summary
    result.summary()
    
    # Return success/failure for script usage
    return result.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)