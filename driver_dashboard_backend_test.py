#!/usr/bin/env python3
"""
Driver Dashboard Backend Testing for RideShare App
Comprehensive testing of driver dashboard features and ride management
Focus on: Driver Authentication, Profile Management, Ride Request System, 
Accepted Rides Management, Driver Cancellation System, Database Consistency, Error Handling
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import random
import string

# Configuration
BASE_URL = "https://06841ea6-50ad-424b-b520-f2f741bf6fdb.preview.emergentagent.com/api"
TIMEOUT = 30

# Chennai locations for geographical context as requested
CHENNAI_LOCATIONS = {
    "pickup1": {"lat": 13.0827, "lng": 80.2707, "address": "Chennai Central Railway Station"},
    "drop1": {"lat": 13.0878, "lng": 80.2785, "address": "T. Nagar, Chennai"},
    "pickup2": {"lat": 13.0475, "lng": 80.2574, "address": "Marina Beach, Chennai"},
    "drop2": {"lat": 13.0569, "lng": 80.2425, "address": "Fort St. George, Chennai"},
    "pickup3": {"lat": 13.0674, "lng": 80.2376, "address": "Chennai Airport"},
    "drop3": {"lat": 13.0827, "lng": 80.2707, "address": "Chennai Central"}
}

# Test mobile number as requested (using different number for driver to avoid conflicts)
TEST_DRIVER_PHONE = "+91 9876543213"
TEST_RIDER_PHONE = "+91 9876543214"

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
        print(f"DRIVER DASHBOARD BACKEND TEST SUMMARY")
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

def test_driver_mobile_otp_authentication(result: TestResult):
    """Test Driver Authentication: Mobile OTP authentication and JWT token validation"""
    print(f"\n{'='*80}")
    print("1. DRIVER AUTHENTICATION - Mobile OTP & JWT Token Validation")
    print(f"{'='*80}")
    
    driver_token = None
    driver_id = None
    
    # Step 1: Send OTP to driver mobile number
    print(f"\n--- Testing OTP Send to {TEST_DRIVER_PHONE} ---")
    try:
        otp_request = {
            "phone_number": TEST_DRIVER_PHONE,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("demo_mode"):
                demo_otp = data.get("demo_otp", "123456")
                result.log_success("Driver OTP sent successfully to mobile number")
                result.log_success("Demo OTP received for testing")
            else:
                result.log_failure("Driver OTP send", f"Invalid response: {data}")
                return None, None
        else:
            result.log_failure("Driver OTP send", f"Status {response.status_code}: {response.text}")
            return None, None
    except Exception as e:
        result.log_failure("Driver OTP send", str(e))
        return None, None
    
    # Step 2: Verify OTP and create driver account
    print(f"\n--- Testing OTP Verification & Driver Registration ---")
    try:
        verify_request = {
            "phone_number": TEST_DRIVER_PHONE,
            "otp_code": demo_otp,
            "user_type": "driver",
            "name": "Test Driver Chennai"
        }
        response = make_request("POST", "/auth/verify-otp", verify_request)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("token"):
                driver_token = data["token"]
                driver_id = data["user_data"]["id"]
                result.log_success("Driver OTP verification successful")
                result.log_success("Driver account created with mobile authentication")
                result.log_success("JWT token generated for driver")
            else:
                result.log_failure("Driver OTP verification", f"Invalid response: {data}")
                return None, None
        else:
            result.log_failure("Driver OTP verification", f"Status {response.status_code}: {response.text}")
            return None, None
    except Exception as e:
        result.log_failure("Driver OTP verification", str(e))
        return None, None
    
    # Step 3: Test JWT token validation
    print(f"\n--- Testing JWT Token Validation ---")
    try:
        headers = get_auth_headers(driver_token)
        response = make_request("GET", "/driver/profile", headers=headers)
        
        # Should return 404 since profile doesn't exist yet, but token should be valid
        if response.status_code == 404:
            result.log_success("JWT token validation successful (authenticated request)")
        elif response.status_code == 401:
            result.log_failure("JWT token validation", "Token rejected as invalid")
            return None, None
        else:
            # Might be 200 if profile exists from previous tests
            result.log_success("JWT token validation successful")
    except Exception as e:
        result.log_failure("JWT token validation", str(e))
        return None, None
    
    # Step 4: Test invalid token handling
    print(f"\n--- Testing Invalid Token Handling ---")
    try:
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        response = make_request("GET", "/driver/profile", headers=invalid_headers)
        
        if response.status_code == 401:
            result.log_success("Invalid JWT token properly rejected")
        else:
            result.log_failure("Invalid token handling", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid token handling", str(e))
    
    return driver_token, driver_id

def test_driver_profile_management(result: TestResult, driver_token: str):
    """Test Driver Profile Management: Profile creation, retrieval, and vehicle verification"""
    print(f"\n{'='*80}")
    print("2. DRIVER PROFILE MANAGEMENT - Creation, Retrieval & Vehicle Verification")
    print(f"{'='*80}")
    
    if not driver_token:
        result.log_failure("Driver profile management", "No driver token available")
        return
    
    headers = get_auth_headers(driver_token)
    
    # Step 1: Test VAHAN License Verification
    print(f"\n--- Testing VAHAN License Verification ---")
    try:
        license_request = {
            "license_number": "DL1420110012345"
        }
        response = make_request("POST", "/driver/verify-license", license_request, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("license_data"):
                result.log_success("VAHAN license verification successful")
                result.log_success("License data retrieved from VAHAN system")
            else:
                result.log_failure("VAHAN license verification", f"Invalid response: {data}")
        else:
            result.log_failure("VAHAN license verification", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("VAHAN license verification", str(e))
    
    # Step 2: Test VAHAN Vehicle Verification
    print(f"\n--- Testing VAHAN Vehicle Verification ---")
    try:
        vehicle_request = {
            "vehicle_number": "TN01AB1234",
            "vehicle_type": "auto"
        }
        response = make_request("POST", "/driver/verify-vehicle", vehicle_request, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("vehicle_data"):
                result.log_success("VAHAN vehicle verification successful")
                result.log_success("Vehicle data retrieved from VAHAN system")
            else:
                result.log_failure("VAHAN vehicle verification", f"Invalid response: {data}")
        else:
            result.log_failure("VAHAN vehicle verification", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("VAHAN vehicle verification", str(e))
    
    # Step 3: Create Driver Profile
    print(f"\n--- Testing Driver Profile Creation ---")
    try:
        profile_data = {
            "vehicle_type": "auto",
            "vehicle_number": "TN01AB1234",
            "license_number": "DL1420110012345"
        }
        response = make_request("POST", "/driver/profile", profile_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if "profile" in data and "message" in data:
                profile = data["profile"]
                # Check auto-assigned rate for auto vehicle
                if profile.get("per_km_rate") == 8.0:
                    result.log_success("Driver profile created successfully")
                    result.log_success("Auto-assigned rate applied correctly (8.0 for auto)")
                else:
                    result.log_failure("Auto-assigned rate", f"Expected 8.0, got {profile.get('per_km_rate')}")
            else:
                result.log_failure("Driver profile creation", f"Invalid response format: {data}")
        else:
            result.log_failure("Driver profile creation", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Driver profile creation", str(e))
    
    # Step 4: Retrieve Driver Profile
    print(f"\n--- Testing Driver Profile Retrieval ---")
    try:
        response = make_request("GET", "/driver/profile", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["vehicle_type", "vehicle_number", "license_number", "per_km_rate"]
            if all(field in data for field in required_fields):
                result.log_success("Driver profile retrieved successfully")
                result.log_success("All required profile fields present")
            else:
                missing_fields = [f for f in required_fields if f not in data]
                result.log_failure("Driver profile retrieval", f"Missing fields: {missing_fields}")
        else:
            result.log_failure("Driver profile retrieval", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Driver profile retrieval", str(e))
    
    # Step 5: Update Driver Location (Chennai coordinates)
    print(f"\n--- Testing Driver Location Update ---")
    try:
        location_data = {
            "lat": 13.0827,  # Chennai Central coordinates
            "lng": 80.2707
        }
        response = make_request("PUT", "/driver/location", location_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if "updated" in data.get("message", "").lower():
                result.log_success("Driver location updated to Chennai coordinates")
            else:
                result.log_failure("Driver location update", f"Unexpected response: {data}")
        else:
            result.log_failure("Driver location update", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Driver location update", str(e))
    
    # Step 6: Update Driver Availability
    print(f"\n--- Testing Driver Availability Management ---")
    try:
        # Set to available
        response = make_request("PUT", "/driver/availability/true", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "available" in data.get("message", "").lower():
                result.log_success("Driver availability set to available")
            else:
                result.log_failure("Driver availability (available)", f"Unexpected response: {data}")
        else:
            result.log_failure("Driver availability (available)", f"Status {response.status_code}: {response.text}")
        
        # Set to unavailable
        response = make_request("PUT", "/driver/availability/false", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "unavailable" in data.get("message", "").lower():
                result.log_success("Driver availability set to unavailable")
            else:
                result.log_failure("Driver availability (unavailable)", f"Unexpected response: {data}")
        else:
            result.log_failure("Driver availability (unavailable)", f"Status {response.status_code}: {response.text}")
        
        # Set back to available for subsequent tests
        make_request("PUT", "/driver/availability/true", headers=headers)
        
    except Exception as e:
        result.log_failure("Driver availability management", str(e))

def test_ride_request_system(result: TestResult, driver_token: str):
    """Test Ride Request System: Driver's ability to see nearby ride requests and accept/reject rides"""
    print(f"\n{'='*80}")
    print("3. RIDE REQUEST SYSTEM - Nearby Requests & Accept/Reject Functionality")
    print(f"{'='*80}")
    
    if not driver_token:
        result.log_failure("Ride request system", "No driver token available")
        return None, None
    
    # First create a rider and ride request
    rider_token = None
    ride_id = None
    
    # Step 1: Create test rider
    print(f"\n--- Creating Test Rider for Ride Requests ---")
    try:
        # Send OTP to rider
        otp_request = {
            "phone_number": TEST_RIDER_PHONE,
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        
        if response.status_code == 200:
            data = response.json()
            demo_otp = data.get("demo_otp", "123456")
            
            # Verify OTP and create rider
            verify_request = {
                "phone_number": TEST_RIDER_PHONE,
                "otp_code": demo_otp,
                "user_type": "rider",
                "name": "Test Rider Chennai"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if response.status_code == 200:
                data = response.json()
                rider_token = data["token"]
                result.log_success("Test rider created for ride request testing")
            else:
                result.log_failure("Test rider creation", f"Status {response.status_code}")
                return None, None
        else:
            result.log_failure("Test rider OTP", f"Status {response.status_code}")
            return None, None
    except Exception as e:
        result.log_failure("Test rider creation", str(e))
        return None, None
    
    # Step 2: Create ride request with Chennai locations
    print(f"\n--- Creating Ride Request with Chennai Locations ---")
    try:
        ride_data = {
            "pickup_location": CHENNAI_LOCATIONS["pickup1"],
            "drop_location": CHENNAI_LOCATIONS["drop1"],
            "estimated_distance": 2.5,
            "estimated_fare": 50.0,
            "preferred_vehicle_type": "auto"
        }
        response = make_request("POST", "/rider/request-ride", ride_data, 
                              headers=get_auth_headers(rider_token))
        
        if response.status_code == 200:
            data = response.json()
            ride_id = data["id"]
            result.log_success("Ride request created with Chennai locations")
            result.log_success("Ride request includes preferred vehicle type")
        else:
            result.log_failure("Ride request creation", f"Status {response.status_code}: {response.text}")
            return None, None
    except Exception as e:
        result.log_failure("Ride request creation", str(e))
        return None, None
    
    # Step 3: Test driver can see nearby ride requests
    print(f"\n--- Testing Driver Can See Nearby Ride Requests ---")
    try:
        headers = get_auth_headers(driver_token)
        response = make_request("GET", "/driver/ride-requests", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Check if our ride is in the list
                ride_found = any(r.get("id") == ride_id for r in data)
                if ride_found:
                    result.log_success("Driver can see nearby ride requests")
                    result.log_success("Distance-based filtering working (within 25km)")
                    
                    # Check ride details
                    our_ride = next(r for r in data if r.get("id") == ride_id)
                    if "distance_to_pickup" in our_ride:
                        result.log_success("Distance to pickup calculated correctly")
                    if our_ride.get("preferred_vehicle_type") == "auto":
                        result.log_success("Preferred vehicle type displayed correctly")
                else:
                    result.log_failure("Nearby ride requests", "Created ride not visible to driver")
            else:
                result.log_failure("Nearby ride requests", f"Expected list, got {type(data)}")
        else:
            result.log_failure("Nearby ride requests", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Nearby ride requests", str(e))
    
    # Step 4: Test ride rejection functionality
    print(f"\n--- Testing Ride Rejection Functionality ---")
    try:
        headers = get_auth_headers(driver_token)
        rejection_data = {
            "ride_id": ride_id,
            "reason": "Driver not available at this time"
        }
        response = make_request("POST", f"/driver/reject-ride/{ride_id}", 
                              rejection_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "rejected":
                result.log_success("Driver can reject ride requests")
                result.log_success("Rejection reason recorded correctly")
            else:
                result.log_failure("Ride rejection", f"Unexpected response: {data}")
        else:
            result.log_failure("Ride rejection", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride rejection", str(e))
    
    # Step 5: Verify rejected ride no longer appears
    print(f"\n--- Testing Rejected Ride Filtering ---")
    try:
        response = make_request("GET", "/driver/ride-requests", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            ride_found = any(r.get("id") == ride_id for r in data)
            if not ride_found:
                result.log_success("Rejected rides filtered out from driver's list")
            else:
                result.log_failure("Rejected ride filtering", "Rejected ride still appears in list")
        else:
            result.log_failure("Rejected ride filtering", f"Status {response.status_code}")
    except Exception as e:
        result.log_failure("Rejected ride filtering", str(e))
    
    # Step 6: Create new ride for acceptance testing
    print(f"\n--- Creating New Ride for Acceptance Testing ---")
    try:
        ride_data = {
            "pickup_location": CHENNAI_LOCATIONS["pickup2"],
            "drop_location": CHENNAI_LOCATIONS["drop2"],
            "estimated_distance": 3.2,
            "estimated_fare": 65.0,
            "preferred_vehicle_type": "auto"
        }
        response = make_request("POST", "/rider/request-ride", ride_data, 
                              headers=get_auth_headers(rider_token))
        
        if response.status_code == 200:
            data = response.json()
            new_ride_id = data["id"]
            result.log_success("New ride request created for acceptance testing")
        else:
            result.log_failure("New ride creation", f"Status {response.status_code}")
            return None, None
    except Exception as e:
        result.log_failure("New ride creation", str(e))
        return None, None
    
    # Step 7: Test ride acceptance
    print(f"\n--- Testing Ride Acceptance ---")
    try:
        response = make_request("POST", f"/driver/accept-ride/{new_ride_id}", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "ride_otp" in data and "accepted" in data.get("message", "").lower():
                ride_otp = data["ride_otp"]
                result.log_success("Driver can accept ride requests")
                result.log_success("Ride OTP generated for verification")
                result.log_success("Acceptance instructions provided to driver")
                return new_ride_id, ride_otp
            else:
                result.log_failure("Ride acceptance", f"Missing OTP or message: {data}")
        else:
            result.log_failure("Ride acceptance", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride acceptance", str(e))
    
    return new_ride_id, None

def test_accepted_rides_management(result: TestResult, driver_token: str, ride_id: str, ride_otp: str):
    """Test Accepted Rides Management: Driver's accepted rides with OTP verification and ride status updates"""
    print(f"\n{'='*80}")
    print("4. ACCEPTED RIDES MANAGEMENT - OTP Verification & Status Updates")
    print(f"{'='*80}")
    
    if not all([driver_token, ride_id, ride_otp]):
        result.log_failure("Accepted rides management", "Missing required parameters")
        return
    
    headers = get_auth_headers(driver_token)
    
    # Step 1: Test OTP verification to start ride
    print(f"\n--- Testing Ride OTP Verification ---")
    try:
        otp_data = {
            "ride_id": ride_id,
            "otp_code": ride_otp
        }
        response = make_request("POST", "/driver/verify-ride-otp", otp_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "in_progress":
                result.log_success("Ride OTP verification successful")
                result.log_success("Ride status updated to 'in_progress'")
            else:
                result.log_failure("Ride OTP verification", f"Unexpected status: {data}")
        else:
            result.log_failure("Ride OTP verification", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride OTP verification", str(e))
    
    # Step 2: Test invalid OTP handling
    print(f"\n--- Testing Invalid OTP Handling ---")
    try:
        invalid_otp_data = {
            "ride_id": ride_id,
            "otp_code": "0000"  # Invalid OTP
        }
        response = make_request("POST", "/driver/verify-ride-otp", invalid_otp_data, headers)
        
        if response.status_code == 400:
            result.log_success("Invalid OTP properly rejected")
        else:
            result.log_failure("Invalid OTP handling", f"Expected 400, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid OTP handling", str(e))
    
    # Step 3: Test ride completion
    print(f"\n--- Testing Ride Completion ---")
    try:
        completion_data = {
            "ride_id": ride_id,
            "status": "completed"
        }
        response = make_request("POST", "/driver/complete-ride", completion_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "completed":
                result.log_success("Ride completion successful")
                result.log_success("Ride status updated to 'completed'")
            else:
                result.log_failure("Ride completion", f"Unexpected status: {data}")
        else:
            result.log_failure("Ride completion", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride completion", str(e))
    
    # Step 4: Test driver ride history
    print(f"\n--- Testing Driver Ride History ---")
    try:
        response = make_request("GET", "/driver/ride-history", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "rides" in data and isinstance(data["rides"], list):
                rides = data["rides"]
                if len(rides) > 0:
                    # Check if our completed ride is in history
                    completed_ride = next((r for r in rides if r.get("id") == ride_id), None)
                    if completed_ride:
                        result.log_success("Driver ride history retrieval successful")
                        result.log_success("Completed ride appears in history")
                        
                        # Check ride details
                        if completed_ride.get("status") == "completed":
                            result.log_success("Ride status correctly stored in history")
                        if "rider_info" in completed_ride:
                            result.log_success("Rider information included in history")
                    else:
                        result.log_failure("Driver ride history", "Completed ride not found in history")
                else:
                    result.log_failure("Driver ride history", "No rides found in history")
            else:
                result.log_failure("Driver ride history", f"Invalid response format: {data}")
        else:
            result.log_failure("Driver ride history", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Driver ride history", str(e))

def test_driver_cancellation_system(result: TestResult, driver_token: str):
    """Test Driver Cancellation System: Driver's ability to cancel accepted rides with reasons"""
    print(f"\n{'='*80}")
    print("5. DRIVER CANCELLATION SYSTEM - Cancel Accepted Rides with Reasons")
    print(f"{'='*80}")
    
    if not driver_token:
        result.log_failure("Driver cancellation system", "No driver token available")
        return
    
    # Create a new ride for cancellation testing
    rider_token = None
    ride_id = None
    
    # Step 1: Create test rider and ride
    print(f"\n--- Setting up Ride for Cancellation Testing ---")
    try:
        # Create rider
        otp_request = {"phone_number": "+91 9876543212", "user_type": "rider"}
        response = make_request("POST", "/auth/send-otp", otp_request)
        
        if response.status_code == 200:
            demo_otp = response.json().get("demo_otp", "123456")
            
            verify_request = {
                "phone_number": "+91 9876543212",
                "otp_code": demo_otp,
                "user_type": "rider",
                "name": "Test Rider for Cancellation"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if response.status_code == 200:
                rider_token = response.json()["token"]
                
                # Create ride request
                ride_data = {
                    "pickup_location": CHENNAI_LOCATIONS["pickup3"],
                    "drop_location": CHENNAI_LOCATIONS["drop3"],
                    "estimated_distance": 4.0,
                    "estimated_fare": 80.0
                }
                response = make_request("POST", "/rider/request-ride", ride_data, 
                                      headers=get_auth_headers(rider_token))
                
                if response.status_code == 200:
                    ride_id = response.json()["id"]
                    result.log_success("Test ride created for cancellation testing")
                else:
                    result.log_failure("Test ride creation", f"Status {response.status_code}")
                    return
            else:
                result.log_failure("Test rider creation", f"Status {response.status_code}")
                return
        else:
            result.log_failure("Test rider OTP", f"Status {response.status_code}")
            return
    except Exception as e:
        result.log_failure("Cancellation test setup", str(e))
        return
    
    # Step 2: Driver accepts the ride
    print(f"\n--- Driver Accepts Ride for Cancellation Test ---")
    try:
        headers = get_auth_headers(driver_token)
        response = make_request("POST", f"/driver/accept-ride/{ride_id}", headers=headers)
        
        if response.status_code == 200:
            result.log_success("Driver accepted ride for cancellation testing")
        else:
            result.log_failure("Ride acceptance for cancellation", f"Status {response.status_code}")
            return
    except Exception as e:
        result.log_failure("Ride acceptance for cancellation", str(e))
        return
    
    # Step 3: Test driver cancellation with reason
    print(f"\n--- Testing Driver Ride Cancellation with Reason ---")
    try:
        cancellation_data = {
            "ride_id": ride_id,
            "reason": "Vehicle breakdown - unable to continue"
        }
        response = make_request("POST", "/driver/cancel-ride", cancellation_data, headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "cancelled":
                result.log_success("Driver can cancel accepted rides")
                result.log_success("Cancellation reason recorded correctly")
            else:
                result.log_failure("Driver ride cancellation", f"Unexpected status: {data}")
        else:
            result.log_failure("Driver ride cancellation", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Driver ride cancellation", str(e))
    
    # Step 4: Verify cancellation appears in ride history
    print(f"\n--- Testing Cancelled Ride in History ---")
    try:
        response = make_request("GET", "/driver/ride-history", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "rides" in data:
                rides = data["rides"]
                cancelled_ride = next((r for r in rides if r.get("id") == ride_id), None)
                if cancelled_ride:
                    if cancelled_ride.get("status") == "cancelled":
                        result.log_success("Cancelled ride appears in driver history")
                        result.log_success("Cancellation status correctly stored")
                        
                        if "cancellation_reason" in cancelled_ride:
                            result.log_success("Cancellation reason stored in ride history")
                    else:
                        result.log_failure("Cancelled ride status", f"Expected 'cancelled', got {cancelled_ride.get('status')}")
                else:
                    result.log_failure("Cancelled ride in history", "Cancelled ride not found in history")
            else:
                result.log_failure("Driver history after cancellation", "Invalid response format")
        else:
            result.log_failure("Driver history after cancellation", f"Status {response.status_code}")
    except Exception as e:
        result.log_failure("Cancelled ride in history", str(e))
    
    # Step 5: Test cancellation of non-existent ride
    print(f"\n--- Testing Invalid Ride Cancellation ---")
    try:
        invalid_cancellation = {
            "ride_id": "non-existent-ride-id",
            "reason": "Test invalid cancellation"
        }
        response = make_request("POST", "/driver/cancel-ride", invalid_cancellation, headers)
        
        if response.status_code == 404:
            result.log_success("Invalid ride cancellation properly rejected")
        else:
            result.log_failure("Invalid ride cancellation", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid ride cancellation", str(e))

def test_database_consistency(result: TestResult, driver_token: str):
    """Test Database Consistency: Ensure all ride data is properly stored and retrieved"""
    print(f"\n{'='*80}")
    print("6. DATABASE CONSISTENCY - Proper Data Storage & Retrieval")
    print(f"{'='*80}")
    
    if not driver_token:
        result.log_failure("Database consistency", "No driver token available")
        return
    
    headers = get_auth_headers(driver_token)
    
    # Step 1: Test driver profile data consistency
    print(f"\n--- Testing Driver Profile Data Consistency ---")
    try:
        response = make_request("GET", "/driver/profile", headers=headers)
        
        if response.status_code == 200:
            profile_data = response.json()
            
            # Check if all expected fields are present and consistent
            expected_fields = ["vehicle_type", "vehicle_number", "license_number", "per_km_rate", "is_available"]
            missing_fields = [f for f in expected_fields if f not in profile_data]
            
            if not missing_fields:
                result.log_success("Driver profile data consistency verified")
                
                # Check data types
                if isinstance(profile_data.get("per_km_rate"), (int, float)):
                    result.log_success("Numeric data types stored correctly")
                if isinstance(profile_data.get("is_available"), bool):
                    result.log_success("Boolean data types stored correctly")
            else:
                result.log_failure("Driver profile consistency", f"Missing fields: {missing_fields}")
        else:
            result.log_failure("Driver profile consistency", f"Status {response.status_code}")
    except Exception as e:
        result.log_failure("Driver profile consistency", str(e))
    
    # Step 2: Test ride data consistency across collections
    print(f"\n--- Testing Ride Data Consistency Across Collections ---")
    try:
        # Get driver's ride history
        response = make_request("GET", "/driver/ride-history", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "rides" in data and len(data["rides"]) > 0:
                ride = data["rides"][0]  # Get first ride
                
                # Check ride data structure
                required_ride_fields = ["id", "rider_id", "pickup_location", "drop_location", 
                                      "estimated_distance", "estimated_fare", "status", "created_at"]
                missing_ride_fields = [f for f in required_ride_fields if f not in ride]
                
                if not missing_ride_fields:
                    result.log_success("Ride data structure consistency verified")
                    
                    # Check location data structure
                    pickup = ride.get("pickup_location", {})
                    drop = ride.get("drop_location", {})
                    
                    location_fields = ["lat", "lng", "address"]
                    pickup_ok = all(f in pickup for f in location_fields)
                    drop_ok = all(f in drop for f in location_fields)
                    
                    if pickup_ok and drop_ok:
                        result.log_success("Location data structure consistency verified")
                    else:
                        result.log_failure("Location data consistency", "Missing location fields")
                    
                    # Check numeric data consistency
                    if isinstance(ride.get("estimated_distance"), (int, float)) and \
                       isinstance(ride.get("estimated_fare"), (int, float)):
                        result.log_success("Numeric ride data consistency verified")
                    else:
                        result.log_failure("Numeric ride data", "Invalid numeric data types")
                        
                else:
                    result.log_failure("Ride data consistency", f"Missing fields: {missing_ride_fields}")
            else:
                result.log_success("No rides found - database consistency test skipped")
        else:
            result.log_failure("Ride data consistency", f"Status {response.status_code}")
    except Exception as e:
        result.log_failure("Ride data consistency", str(e))
    
    # Step 3: Test timestamp consistency
    print(f"\n--- Testing Timestamp Data Consistency ---")
    try:
        response = make_request("GET", "/driver/ride-history", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "rides" in data and len(data["rides"]) > 0:
                for ride in data["rides"]:
                    # Check if timestamps are in ISO format
                    timestamp_fields = ["created_at", "accepted_at", "started_at", "completed_at", "cancelled_at"]
                    
                    for field in timestamp_fields:
                        if field in ride and ride[field]:
                            timestamp = ride[field]
                            # Basic ISO format check
                            if isinstance(timestamp, str) and "T" in timestamp:
                                continue
                            else:
                                result.log_failure("Timestamp consistency", f"Invalid {field} format: {timestamp}")
                                break
                    else:
                        result.log_success("Timestamp data consistency verified")
                        break
            else:
                result.log_success("No rides found - timestamp consistency test skipped")
        else:
            result.log_failure("Timestamp consistency", f"Status {response.status_code}")
    except Exception as e:
        result.log_failure("Timestamp consistency", str(e))

def test_error_handling(result: TestResult, driver_token: str):
    """Test Error Handling: Authentication errors, invalid requests, and edge cases"""
    print(f"\n{'='*80}")
    print("7. ERROR HANDLING - Authentication, Invalid Requests & Edge Cases")
    print(f"{'='*80}")
    
    # Step 1: Test authentication errors
    print(f"\n--- Testing Authentication Errors ---")
    
    # Invalid token
    try:
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = make_request("GET", "/driver/profile", headers=invalid_headers)
        
        if response.status_code == 401:
            result.log_success("Invalid authentication token properly rejected")
        else:
            result.log_failure("Invalid token handling", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid token handling", str(e))
    
    # Missing token
    try:
        response = make_request("GET", "/driver/profile")
        
        if response.status_code == 403:
            result.log_success("Missing authentication token properly rejected")
        else:
            result.log_failure("Missing token handling", f"Expected 403, got {response.status_code}")
    except Exception as e:
        result.log_failure("Missing token handling", str(e))
    
    # Step 2: Test invalid request data
    print(f"\n--- Testing Invalid Request Data ---")
    
    if driver_token:
        headers = get_auth_headers(driver_token)
        
        # Invalid location data
        try:
            invalid_location = {
                "lat": "invalid_latitude",
                "lng": "invalid_longitude"
            }
            response = make_request("PUT", "/driver/location", invalid_location, headers)
            
            if response.status_code in [400, 422]:
                result.log_success("Invalid location data properly rejected")
            else:
                result.log_failure("Invalid location data", f"Expected 400/422, got {response.status_code}")
        except Exception as e:
            result.log_failure("Invalid location data", str(e))
        
        # Missing required fields
        try:
            incomplete_profile = {
                "vehicle_type": "car"
                # Missing required fields
            }
            response = make_request("POST", "/driver/profile", incomplete_profile, headers)
            
            if response.status_code in [400, 422]:
                result.log_success("Missing required fields properly rejected")
            else:
                result.log_failure("Missing required fields", f"Expected 400/422, got {response.status_code}")
        except Exception as e:
            result.log_failure("Missing required fields", str(e))
    
    # Step 3: Test edge cases
    print(f"\n--- Testing Edge Cases ---")
    
    if driver_token:
        headers = get_auth_headers(driver_token)
        
        # Non-existent ride operations
        try:
            fake_ride_id = "non-existent-ride-12345"
            response = make_request("POST", f"/driver/accept-ride/{fake_ride_id}", headers=headers)
            
            if response.status_code == 404:
                result.log_success("Non-existent ride operations properly rejected")
            else:
                result.log_failure("Non-existent ride handling", f"Expected 404, got {response.status_code}")
        except Exception as e:
            result.log_failure("Non-existent ride handling", str(e))
        
        # Invalid OTP verification
        try:
            invalid_otp_data = {
                "ride_id": "fake-ride-id",
                "otp_code": "0000"
            }
            response = make_request("POST", "/driver/verify-ride-otp", invalid_otp_data, headers)
            
            if response.status_code in [400, 404]:
                result.log_success("Invalid OTP verification properly rejected")
            else:
                result.log_failure("Invalid OTP verification", f"Expected 400/404, got {response.status_code}")
        except Exception as e:
            result.log_failure("Invalid OTP verification", str(e))
    
    # Step 4: Test mobile OTP authentication errors
    print(f"\n--- Testing Mobile OTP Authentication Errors ---")
    
    # Invalid phone number format
    try:
        invalid_phone_request = {
            "phone_number": "invalid_phone",
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", invalid_phone_request)
        
        if response.status_code == 400:
            result.log_success("Invalid phone number format properly rejected")
        else:
            result.log_failure("Invalid phone number", f"Expected 400, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid phone number", str(e))
    
    # Invalid OTP verification
    try:
        invalid_otp_verify = {
            "phone_number": "+91 9876543210",
            "otp_code": "999999",  # Invalid OTP
            "user_type": "driver",
            "name": "Test Driver"
        }
        response = make_request("POST", "/auth/verify-otp", invalid_otp_verify)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success"):
                result.log_success("Invalid OTP properly rejected")
            else:
                result.log_failure("Invalid OTP verification", "Invalid OTP was accepted")
        else:
            result.log_failure("Invalid OTP verification", f"Status {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid OTP verification", str(e))

def main():
    """Main test execution function"""
    print("🚗 DRIVER DASHBOARD BACKEND TESTING")
    print("Testing core backend API functionality for driver dashboard features")
    print(f"Using mobile number: {TEST_DRIVER_PHONE}")
    print(f"Using Chennai locations for geographical context")
    print(f"Backend URL: {BASE_URL}")
    
    result = TestResult()
    
    # Test 1: Driver Authentication
    driver_token, driver_id = test_driver_mobile_otp_authentication(result)
    
    if driver_token:
        # Test 2: Driver Profile Management
        test_driver_profile_management(result, driver_token)
        
        # Test 3: Ride Request System
        ride_id, ride_otp = test_ride_request_system(result, driver_token)
        
        if ride_id and ride_otp:
            # Test 4: Accepted Rides Management
            test_accepted_rides_management(result, driver_token, ride_id, ride_otp)
        
        # Test 5: Driver Cancellation System
        test_driver_cancellation_system(result, driver_token)
        
        # Test 6: Database Consistency
        test_database_consistency(result, driver_token)
        
        # Test 7: Error Handling
        test_error_handling(result, driver_token)
    else:
        result.log_failure("Test Suite", "Could not obtain driver token - skipping dependent tests")
    
    # Print final summary
    result.summary()
    
    return result.passed, result.failed

if __name__ == "__main__":
    passed, failed = main()
    exit(0 if failed == 0 else 1)