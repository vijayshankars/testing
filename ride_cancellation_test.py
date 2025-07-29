#!/usr/bin/env python3
"""
Ride Cancellation and Enhanced Location Display Testing
Tests the specific functionality requested in the review
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://06841ea6-50ad-424b-b520-f2f741bf6fdb.preview.emergentagent.com/api"
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
        print(f"RIDE CANCELLATION TEST SUMMARY")
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

def test_ride_cancellation_functionality(result: TestResult):
    """Test the complete ride cancellation functionality with Chennai locations"""
    print(f"\n{'='*60}")
    print("RIDE CANCELLATION & ENHANCED LOCATION DISPLAY TESTING")
    print(f"{'='*60}")
    
    # Test data with Chennai locations
    test_rider_phone = "+91 9876543210"  # As requested
    test_driver_phone = "+91 9876543211"
    
    # Chennai locations for realistic testing
    chennai_locations = {
        "airport": {
            "lat": 12.9941,
            "lng": 80.1709,
            "address": "Chennai International Airport, Chennai, Tamil Nadu"
        },
        "tnagar": {
            "lat": 13.0418,
            "lng": 80.2341,
            "address": "T. Nagar, Chennai, Tamil Nadu"
        }
    }
    
    rider_token = None
    driver_token = None
    ride_id = None
    
    # Step 1: Create test rider user with mobile OTP authentication
    print(f"\n--- Step 1: Create test rider with mobile OTP (+91 9876543210) ---")
    try:
        # Send OTP
        otp_request = {
            "phone_number": test_rider_phone,
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            result.log_success("Step 1a - OTP sent to +91 9876543210")
            
            # Verify OTP and register
            verify_request = {
                "phone_number": test_rider_phone,
                "otp_code": "123456",  # Demo OTP
                "user_type": "rider",
                "name": "Chennai Test Rider"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    rider_token = data["token"]
                    result.log_success("Step 1b - Test rider created with mobile OTP authentication")
                else:
                    result.log_failure("Step 1b", f"OTP verification failed: {data}")
                    return
            else:
                result.log_failure("Step 1b", f"OTP verification failed: {response.status_code} - {response.text}")
                return
        else:
            result.log_failure("Step 1a", f"OTP send failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 1", f"Rider creation error: {str(e)}")
        return
    
    # Step 2: Create test driver for ride matching
    print(f"\n--- Step 2: Create test driver for ride matching ---")
    try:
        # Send OTP for driver
        otp_request = {
            "phone_number": test_driver_phone,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            # Verify OTP and register driver
            verify_request = {
                "phone_number": test_driver_phone,
                "otp_code": "123456",  # Demo OTP
                "user_type": "driver",
                "name": "Chennai Test Driver"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    driver_token = data["token"]
                    result.log_success("Step 2a - Test driver created")
                    
                    # Create driver profile
                    driver_headers = get_auth_headers(driver_token)
                    profile_data = {
                        "per_km_rate": 18.0,
                        "vehicle_type": "sedan",
                        "vehicle_number": "TN01AB1234",  # Tamil Nadu registration
                        "license_number": "TN1234567890"
                    }
                    response = make_request("POST", "/driver/profile", profile_data, driver_headers)
                    if response.status_code == 200:
                        result.log_success("Step 2b - Driver profile created")
                        
                        # Set driver location near Chennai Airport
                        location_data = {"lat": 12.9941, "lng": 80.1709}
                        response = make_request("PUT", "/driver/location", location_data, driver_headers)
                        if response.status_code == 200:
                            result.log_success("Step 2c - Driver location set to Chennai Airport area")
                            
                            # Set driver as available
                            response = make_request("PUT", "/driver/availability/true", headers=driver_headers)
                            if response.status_code == 200:
                                result.log_success("Step 2d - Driver set as available")
                            else:
                                result.log_failure("Step 2d", f"Driver availability failed: {response.status_code}")
                        else:
                            result.log_failure("Step 2c", f"Driver location failed: {response.status_code}")
                    else:
                        result.log_failure("Step 2b", f"Driver profile creation failed: {response.status_code}")
                else:
                    result.log_failure("Step 2a", f"Driver OTP verification failed: {data}")
            else:
                result.log_failure("Step 2a", f"Driver OTP verification failed: {response.status_code}")
        else:
            result.log_failure("Step 2", f"Driver OTP send failed: {response.status_code}")
    except Exception as e:
        result.log_failure("Step 2", f"Driver creation error: {str(e)}")
    
    # Step 3: Create ride request from Chennai Airport to T. Nagar
    print(f"\n--- Step 3: Create ride request (Chennai Airport → T. Nagar) ---")
    try:
        rider_headers = get_auth_headers(rider_token)
        ride_data = {
            "pickup_location": chennai_locations["airport"],
            "drop_location": chennai_locations["tnagar"],
            "estimated_distance": 15.2,  # Realistic distance
            "estimated_fare": 273.6  # 15.2 km * 18 INR/km
        }
        response = make_request("POST", "/rider/request-ride", ride_data, rider_headers)
        if response.status_code == 200:
            data = response.json()
            ride_id = data["id"]
            result.log_success("Step 3a - Ride request created (Chennai Airport → T. Nagar)")
            
            # Verify enhanced location display format
            pickup_addr = data.get("pickup_location", {}).get("address", "")
            drop_addr = data.get("drop_location", {}).get("address", "")
            if "Chennai International Airport" in pickup_addr and "T. Nagar" in drop_addr:
                result.log_success("Step 3b - Enhanced location display shows proper Chennai locations")
            else:
                result.log_failure("Step 3b", f"Location display issue - pickup: {pickup_addr}, drop: {drop_addr}")
        else:
            result.log_failure("Step 3a", f"Ride request failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 3", f"Ride request error: {str(e)}")
        return
    
    # Step 4: Test POST /api/rider/cancel-ride endpoint
    print(f"\n--- Step 4: Test ride cancellation endpoint ---")
    try:
        cancellation_data = {
            "ride_id": ride_id,
            "reason": "User cancelled - testing functionality"
        }
        response = make_request("POST", "/rider/cancel-ride", cancellation_data, rider_headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "cancelled" in data["message"].lower():
                result.log_success("Step 4a - POST /api/rider/cancel-ride endpoint working")
                
                # Check response format
                if data.get("status") == "cancelled":
                    result.log_success("Step 4b - Cancellation response format correct")
                else:
                    result.log_failure("Step 4b", f"Expected status 'cancelled', got: {data.get('status')}")
            else:
                result.log_failure("Step 4a", f"Unexpected cancellation response: {data}")
        else:
            result.log_failure("Step 4a", f"Ride cancellation failed: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 4", f"Ride cancellation error: {str(e)}")
    
    # Step 5: Verify ride status changes to 'cancelled' and cancelled_at timestamp is set
    print(f"\n--- Step 5: Verify ride status and timestamp updates ---")
    try:
        response = make_request("GET", "/rider/rides", headers=rider_headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                # Find our cancelled ride
                cancelled_ride = None
                for ride in data:
                    if ride.get("id") == ride_id:
                        cancelled_ride = ride
                        break
                
                if cancelled_ride:
                    # Check status
                    if cancelled_ride.get("status") == "cancelled":
                        result.log_success("Step 5a - Ride status changed to 'cancelled'")
                    else:
                        result.log_failure("Step 5a", f"Ride status is {cancelled_ride.get('status')}, expected 'cancelled'")
                    
                    # Check cancelled_at timestamp
                    if cancelled_ride.get("cancelled_at"):
                        result.log_success("Step 5b - cancelled_at timestamp is set")
                    else:
                        result.log_failure("Step 5b", "cancelled_at timestamp not set")
                    
                    # Check cancellation reason
                    if cancelled_ride.get("cancellation_reason"):
                        result.log_success("Step 5c - Cancellation reason stored")
                    else:
                        result.log_failure("Step 5c", "Cancellation reason not stored")
                else:
                    result.log_failure("Step 5", "Could not find the cancelled ride")
            else:
                result.log_failure("Step 5", "No rides found for rider")
        else:
            result.log_failure("Step 5", f"Failed to get rider rides: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 5", f"Ride status verification error: {str(e)}")
    
    # Step 6: Test ride history with proper location display
    print(f"\n--- Step 6: Test ride history with enhanced location display ---")
    try:
        response = make_request("GET", "/rider/ride-history", headers=rider_headers)
        if response.status_code == 200:
            data = response.json()
            if "rides" in data and isinstance(data["rides"], list):
                # Find our cancelled ride in history
                history_ride = None
                for ride in data["rides"]:
                    if ride.get("id") == ride_id:
                        history_ride = ride
                        break
                
                if history_ride:
                    result.log_success("Step 6a - Cancelled ride appears in ride history")
                    
                    # Check enhanced location display format
                    pickup_location = history_ride.get("pickup_location", {})
                    drop_location = history_ride.get("drop_location", {})
                    
                    pickup_addr = pickup_location.get("address", "")
                    drop_addr = drop_location.get("address", "")
                    
                    if pickup_addr and drop_addr:
                        # Verify "from location to location" format
                        location_display = f"{pickup_addr} to {drop_addr}"
                        if "Chennai International Airport" in pickup_addr and "T. Nagar" in drop_addr:
                            result.log_success("Step 6b - Enhanced location display shows 'from Chennai Airport to T. Nagar' format")
                        else:
                            result.log_failure("Step 6b", f"Location display format issue: {location_display}")
                        
                        # Check that both locations have coordinates
                        if (pickup_location.get("lat") and pickup_location.get("lng") and 
                            drop_location.get("lat") and drop_location.get("lng")):
                            result.log_success("Step 6c - Location coordinates preserved in history")
                        else:
                            result.log_failure("Step 6c", "Location coordinates missing in history")
                    else:
                        result.log_failure("Step 6b", f"Location addresses missing - pickup: {pickup_addr}, drop: {drop_addr}")
                    
                    # Verify ride status in history
                    if history_ride.get("status") == "cancelled":
                        result.log_success("Step 6d - Cancelled status preserved in ride history")
                    else:
                        result.log_failure("Step 6d", f"Status in history: {history_ride.get('status')}, expected 'cancelled'")
                else:
                    result.log_failure("Step 6a", "Cancelled ride not found in ride history")
            else:
                result.log_failure("Step 6", f"Invalid ride history format: {data}")
        else:
            result.log_failure("Step 6", f"Failed to get ride history: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 6", f"Ride history error: {str(e)}")
    
    # Step 7: Test edge cases for ride cancellation
    print(f"\n--- Step 7: Test ride cancellation edge cases ---")
    
    # Test 7a: Try to cancel already cancelled ride
    try:
        cancellation_data = {
            "ride_id": ride_id,
            "reason": "Trying to cancel already cancelled ride"
        }
        response = make_request("POST", "/rider/cancel-ride", cancellation_data, rider_headers)
        if response.status_code == 404:
            result.log_success("Step 7a - Cannot cancel already cancelled ride (404 response)")
        elif response.status_code == 400:
            result.log_success("Step 7a - Cannot cancel already cancelled ride (400 response)")
        else:
            result.log_failure("Step 7a", f"Should not allow cancelling already cancelled ride: {response.status_code}")
    except Exception as e:
        result.log_failure("Step 7a", f"Edge case test error: {str(e)}")
    
    # Test 7b: Try to cancel non-existent ride
    try:
        cancellation_data = {
            "ride_id": "non_existent_ride_id",
            "reason": "Testing non-existent ride"
        }
        response = make_request("POST", "/rider/cancel-ride", cancellation_data, rider_headers)
        if response.status_code == 404:
            result.log_success("Step 7b - Cannot cancel non-existent ride (404 response)")
        else:
            result.log_failure("Step 7b", f"Should return 404 for non-existent ride: {response.status_code}")
    except Exception as e:
        result.log_failure("Step 7b", f"Edge case test error: {str(e)}")
    
    # Test 7c: Try to cancel ride without proper authorization
    try:
        # Create another rider to test unauthorized cancellation
        otp_request = {
            "phone_number": "+91 9876543212",
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            verify_request = {
                "phone_number": "+91 9876543212",
                "otp_code": "123456",
                "user_type": "rider",
                "name": "Unauthorized Test Rider"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                unauthorized_token = response.json().get("token")
                unauthorized_headers = get_auth_headers(unauthorized_token)
                
                # Try to cancel original rider's ride
                cancellation_data = {
                    "ride_id": ride_id,
                    "reason": "Unauthorized cancellation attempt"
                }
                response = make_request("POST", "/rider/cancel-ride", cancellation_data, unauthorized_headers)
                if response.status_code == 404:
                    result.log_success("Step 7c - Unauthorized ride cancellation prevented (404 response)")
                else:
                    result.log_failure("Step 7c", f"Should prevent unauthorized cancellation: {response.status_code}")
            else:
                result.log_failure("Step 7c", "Could not create unauthorized rider for test")
        else:
            result.log_failure("Step 7c", "Could not send OTP for unauthorized rider test")
    except Exception as e:
        result.log_failure("Step 7c", f"Unauthorized cancellation test error: {str(e)}")
    
    # Step 8: Test location display consistency across different endpoints
    print(f"\n--- Step 8: Test location display consistency ---")
    try:
        # Create a new ride to test location display
        ride_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Marina Beach, Chennai, Tamil Nadu"
            },
            "drop_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "Fort St. George, Chennai, Tamil Nadu"
            },
            "estimated_distance": 2.5,
            "estimated_fare": 45.0
        }
        response = make_request("POST", "/rider/request-ride", ride_data, rider_headers)
        if response.status_code == 200:
            new_ride_data = response.json()
            new_ride_id = new_ride_data["id"]
            
            # Check location display in ride creation response
            pickup_display = new_ride_data.get("pickup_location", {}).get("address", "")
            drop_display = new_ride_data.get("drop_location", {}).get("address", "")
            
            if "Marina Beach" in pickup_display and "Fort St. George" in drop_display:
                result.log_success("Step 8a - Location display consistent in ride creation")
            else:
                result.log_failure("Step 8a", f"Location display inconsistent: {pickup_display} → {drop_display}")
            
            # Check location display in rider rides list
            response = make_request("GET", "/rider/rides", headers=rider_headers)
            if response.status_code == 200:
                rides_data = response.json()
                new_ride_in_list = None
                for ride in rides_data:
                    if ride.get("id") == new_ride_id:
                        new_ride_in_list = ride
                        break
                
                if new_ride_in_list:
                    list_pickup = new_ride_in_list.get("pickup_location", {}).get("address", "")
                    list_drop = new_ride_in_list.get("drop_location", {}).get("address", "")
                    
                    if list_pickup == pickup_display and list_drop == drop_display:
                        result.log_success("Step 8b - Location display consistent across endpoints")
                    else:
                        result.log_failure("Step 8b", f"Location display inconsistent across endpoints")
                else:
                    result.log_failure("Step 8b", "New ride not found in rides list")
            else:
                result.log_failure("Step 8b", f"Failed to get rides list: {response.status_code}")
        else:
            result.log_failure("Step 8", f"Failed to create test ride: {response.status_code}")
    except Exception as e:
        result.log_failure("Step 8", f"Location display consistency test error: {str(e)}")

def main():
    """Run ride cancellation tests"""
    print("🚗 RideShare Ride Cancellation & Enhanced Location Display Testing")
    print("=" * 80)
    
    result = TestResult()
    
    try:
        test_ride_cancellation_functionality(result)
    except Exception as e:
        print(f"Critical error during testing: {e}")
    
    result.summary()
    
    # Return exit code based on test results
    return 0 if result.failed == 0 else 1

if __name__ == "__main__":
    exit(main())