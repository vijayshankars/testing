#!/usr/bin/env python3
"""
Comprehensive Ride OTP Generation and Verification Testing
Tests the complete ride OTP flow as requested in the review
"""

import requests
import json
import time
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
        print(f"RIDE OTP TEST SUMMARY")
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

def test_ride_otp_generation_flow(result: TestResult):
    """Test the complete ride OTP generation and verification flow"""
    print(f"\n{'='*60}")
    print("RIDE OTP GENERATION & VERIFICATION TESTING")
    print(f"{'='*60}")
    
    # Test data - using unique phone numbers to avoid conflicts
    import random
    random_suffix = str(random.randint(1000, 9999))
    rider_phone = f"+91 987654{random_suffix}"  # Based on requested format
    driver_phone = f"+91 987654{str(int(random_suffix) + 1)}"
    
    rider_token = None
    driver_token = None
    ride_id = None
    ride_otp = None
    
    # Step 1: Create test rider user with mobile OTP authentication
    print("\n--- Step 1: Create test rider user with mobile OTP authentication ---")
    try:
        # Send OTP to rider
        otp_request = {
            "phone_number": rider_phone,
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            result.log_success("Step 1a - OTP sent to rider phone +91 9876543210")
            
            # Verify OTP and register rider
            verify_request = {
                "phone_number": rider_phone,
                "otp_code": "123456",  # Demo OTP
                "user_type": "rider",
                "name": "Test Rider OTP"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    rider_token = data["token"]
                    result.log_success("Step 1b - Rider user created with mobile OTP authentication")
                else:
                    result.log_failure("Step 1b", f"Invalid OTP verification response: {data}")
                    return
            else:
                result.log_failure("Step 1b", f"OTP verification failed: {response.status_code} - {response.text}")
                return
        else:
            result.log_failure("Step 1a", f"Failed to send OTP: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 1", f"Rider creation error: {str(e)}")
        return
    
    # Step 2: Create test driver user and driver profile
    print("\n--- Step 2: Create test driver user and driver profile ---")
    try:
        # Send OTP to driver
        otp_request = {
            "phone_number": driver_phone,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            result.log_success("Step 2a - OTP sent to driver phone")
            
            # Verify OTP and register driver
            verify_request = {
                "phone_number": driver_phone,
                "otp_code": "123456",  # Demo OTP
                "user_type": "driver",
                "name": "Test Driver OTP"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    driver_token = data["token"]
                    result.log_success("Step 2b - Driver user created with mobile OTP authentication")
                else:
                    result.log_failure("Step 2b", f"Invalid driver OTP verification: {data}")
                    return
            else:
                result.log_failure("Step 2b", f"Driver OTP verification failed: {response.status_code} - {response.text}")
                return
        else:
            result.log_failure("Step 2a", f"Failed to send driver OTP: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 2", f"Driver creation error: {str(e)}")
        return
    
    # Create driver profile
    try:
        driver_headers = get_auth_headers(driver_token)
        profile_data = {
            "per_km_rate": 18.0,
            "vehicle_type": "sedan",
            "vehicle_number": "KA05MN1234",
            "license_number": "DL1234567890"
        }
        response = make_request("POST", "/driver/profile", profile_data, driver_headers)
        if response.status_code == 200:
            result.log_success("Step 2c - Driver profile created successfully")
        else:
            result.log_failure("Step 2c", f"Driver profile creation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 2c", f"Driver profile creation error: {str(e)}")
        return
    
    # Set driver location and availability
    try:
        # Set location
        location_data = {"lat": 12.9716, "lng": 77.5946}  # Bangalore coordinates
        response = make_request("PUT", "/driver/location", location_data, driver_headers)
        if response.status_code == 200:
            result.log_success("Step 2d - Driver location set")
        else:
            result.log_failure("Step 2d", f"Driver location update failed: {response.status_code}")
            return
        
        # Set availability
        response = make_request("PUT", "/driver/availability/true", headers=driver_headers)
        if response.status_code == 200:
            result.log_success("Step 2e - Driver availability set to available")
        else:
            result.log_failure("Step 2e", f"Driver availability update failed: {response.status_code}")
            return
    except Exception as e:
        result.log_failure("Step 2d/2e", f"Driver setup error: {str(e)}")
        return
    
    # Step 3: Create a ride request from the rider
    print("\n--- Step 3: Create ride request from rider ---")
    try:
        rider_headers = get_auth_headers(rider_token)
        ride_data = {
            "pickup_location": {
                "lat": 12.9716,
                "lng": 77.5946,
                "address": "MG Road, Bangalore"
            },
            "drop_location": {
                "lat": 12.9352,
                "lng": 77.6245,
                "address": "Koramangala, Bangalore"
            },
            "estimated_distance": 8.5,
            "estimated_fare": 153.0
        }
        response = make_request("POST", "/rider/request-ride", ride_data, rider_headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("id") and data.get("status") == "requested":
                ride_id = data["id"]
                result.log_success("Step 3 - Ride request created successfully")
            else:
                result.log_failure("Step 3", f"Invalid ride request response: {data}")
                return
        else:
            result.log_failure("Step 3", f"Ride request creation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 3", f"Ride request creation error: {str(e)}")
        return
    
    # Step 4: Have the driver accept the ride (this should generate a ride OTP)
    print("\n--- Step 4: Driver accepts ride and OTP generation ---")
    try:
        response = make_request("POST", f"/driver/accept-ride/{ride_id}", headers=driver_headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "accepted" in data["message"].lower():
                result.log_success("Step 4a - Driver successfully accepted ride")
                
                # Check if ride OTP is generated and returned
                if "ride_otp" in data:
                    ride_otp = data["ride_otp"]
                    if len(ride_otp) == 4 and ride_otp.isdigit():
                        result.log_success("Step 4b - Ride OTP generated correctly (4-digit numeric)")
                        print(f"    Generated OTP: {ride_otp}")
                    else:
                        result.log_failure("Step 4b", f"Invalid OTP format: {ride_otp}")
                        return
                else:
                    result.log_failure("Step 4b", "Ride OTP not returned in response")
                    return
                
                # Check instructions
                if "instructions" in data:
                    result.log_success("Step 4c - OTP sharing instructions provided")
                else:
                    result.log_failure("Step 4c", "OTP sharing instructions missing")
            else:
                result.log_failure("Step 4a", f"Unexpected acceptance response: {data}")
                return
        else:
            result.log_failure("Step 4a", f"Ride acceptance failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 4", f"Ride acceptance error: {str(e)}")
        return
    
    # Step 5: Verify that the ride OTP is generated and stored correctly
    print("\n--- Step 5: Verify OTP storage in ride data ---")
    try:
        # Check rider's rides to see if OTP is stored (but not exposed to rider)
        response = make_request("GET", "/rider/rides", headers=rider_headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                accepted_ride = None
                for ride in data:
                    if ride.get("id") == ride_id:
                        accepted_ride = ride
                        break
                
                if accepted_ride:
                    if accepted_ride.get("status") == "accepted":
                        result.log_success("Step 5a - Ride status updated to 'accepted'")
                        
                        # Verify OTP is not exposed to rider (security check)
                        if "ride_otp" not in accepted_ride:
                            result.log_success("Step 5b - Ride OTP not exposed to rider (security verified)")
                        else:
                            result.log_failure("Step 5b", "Security issue: Ride OTP exposed to rider")
                        
                        # Check if otp_verified field is set to False
                        if accepted_ride.get("otp_verified") is False:
                            result.log_success("Step 5c - OTP verification status correctly set to False")
                        else:
                            result.log_failure("Step 5c", f"OTP verification status incorrect: {accepted_ride.get('otp_verified')}")
                        
                        # Check if accepted_at timestamp is set
                        if accepted_ride.get("accepted_at"):
                            result.log_success("Step 5d - Ride acceptance timestamp recorded")
                        else:
                            result.log_failure("Step 5d", "Ride acceptance timestamp missing")
                    else:
                        result.log_failure("Step 5a", f"Ride status is {accepted_ride.get('status')}, expected 'accepted'")
                else:
                    result.log_failure("Step 5", "Could not find accepted ride in rider's rides")
            else:
                result.log_failure("Step 5", "No rides found for rider")
        else:
            result.log_failure("Step 5", f"Failed to get rider rides: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 5", f"OTP storage verification error: {str(e)}")
    
    # Step 6: Test the ride OTP verification process where driver enters the OTP to start the ride
    print("\n--- Step 6: Test OTP verification process ---")
    try:
        if ride_otp:
            verification_data = {
                "ride_id": ride_id,
                "otp_code": ride_otp
            }
            response = make_request("POST", "/driver/verify-ride-otp", verification_data, driver_headers)
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "started" in data["message"].lower():
                    result.log_success("Step 6a - Driver successfully verified ride OTP")
                    
                    if data.get("status") == "in_progress":
                        result.log_success("Step 6b - Ride status returned as 'in_progress'")
                    else:
                        result.log_failure("Step 6b", f"Expected status 'in_progress', got: {data.get('status')}")
                else:
                    result.log_failure("Step 6a", f"Unexpected OTP verification response: {data}")
            else:
                result.log_failure("Step 6a", f"OTP verification failed: {response.status_code} - {response.text}")
        else:
            result.log_failure("Step 6", "No OTP available for verification test")
    except Exception as e:
        result.log_failure("Step 6", f"OTP verification error: {str(e)}")
    
    # Step 7: Verify the ride status changes from 'accepted' to 'in_progress' after OTP verification
    print("\n--- Step 7: Verify ride status change after OTP verification ---")
    try:
        # Check rider's rides to verify status change
        response = make_request("GET", "/rider/rides", headers=rider_headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                in_progress_ride = None
                for ride in data:
                    if ride.get("id") == ride_id:
                        in_progress_ride = ride
                        break
                
                if in_progress_ride:
                    if in_progress_ride.get("status") == "in_progress":
                        result.log_success("Step 7a - Ride status successfully changed to 'in_progress'")
                        
                        # Check if otp_verified is now True
                        if in_progress_ride.get("otp_verified") is True:
                            result.log_success("Step 7b - OTP verification status updated to True")
                        else:
                            result.log_failure("Step 7b", f"OTP verification status not updated: {in_progress_ride.get('otp_verified')}")
                        
                        # Check if started_at timestamp is set
                        if in_progress_ride.get("started_at"):
                            result.log_success("Step 7c - Ride start timestamp recorded")
                        else:
                            result.log_failure("Step 7c", "Ride start timestamp missing")
                    else:
                        result.log_failure("Step 7a", f"Ride status is {in_progress_ride.get('status')}, expected 'in_progress'")
                else:
                    result.log_failure("Step 7", "Could not find ride after OTP verification")
            else:
                result.log_failure("Step 7", "No rides found for rider after OTP verification")
        else:
            result.log_failure("Step 7", f"Failed to get rider rides: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 7", f"Status change verification error: {str(e)}")
    
    # Step 8: Test edge cases
    print("\n--- Step 8: Test edge cases ---")
    
    # Edge case 1: Invalid OTP
    try:
        invalid_otp_data = {
            "ride_id": ride_id,
            "otp_code": "9999"  # Invalid OTP
        }
        response = make_request("POST", "/driver/verify-ride-otp", invalid_otp_data, driver_headers)
        if response.status_code == 400:
            data = response.json()
            if "invalid" in data.get("detail", "").lower():
                result.log_success("Step 8a - Invalid OTP correctly rejected")
            else:
                result.log_failure("Step 8a", f"Wrong error message for invalid OTP: {data}")
        else:
            result.log_failure("Step 8a", f"Invalid OTP should return 400, got: {response.status_code}")
    except Exception as e:
        result.log_failure("Step 8a", f"Invalid OTP test error: {str(e)}")
    
    # Edge case 2: Wrong driver trying to verify OTP
    try:
        # Create another driver
        wrong_driver_phone = "+91 9876543212"
        otp_request = {
            "phone_number": wrong_driver_phone,
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            verify_request = {
                "phone_number": wrong_driver_phone,
                "otp_code": "123456",
                "user_type": "driver",
                "name": "Wrong Driver"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                wrong_driver_data = response.json()
                wrong_driver_token = wrong_driver_data["token"]
                wrong_driver_headers = get_auth_headers(wrong_driver_token)
                
                # Try to verify OTP with wrong driver
                wrong_verification_data = {
                    "ride_id": ride_id,
                    "otp_code": ride_otp if ride_otp else "1234"
                }
                response = make_request("POST", "/driver/verify-ride-otp", wrong_verification_data, wrong_driver_headers)
                if response.status_code == 404:
                    result.log_success("Step 8b - Wrong driver correctly prevented from verifying OTP")
                else:
                    result.log_failure("Step 8b", f"Wrong driver should get 404, got: {response.status_code}")
            else:
                result.log_failure("Step 8b", "Failed to create wrong driver for test")
        else:
            result.log_failure("Step 8b", "Failed to send OTP to wrong driver")
    except Exception as e:
        result.log_failure("Step 8b", f"Wrong driver test error: {str(e)}")
    
    # Edge case 3: Non-existent ride ID
    try:
        invalid_ride_data = {
            "ride_id": "invalid_ride_id",
            "otp_code": "1234"
        }
        response = make_request("POST", "/driver/verify-ride-otp", invalid_ride_data, driver_headers)
        if response.status_code == 404:
            result.log_success("Step 8c - Non-existent ride ID correctly rejected")
        else:
            result.log_failure("Step 8c", f"Non-existent ride should return 404, got: {response.status_code}")
    except Exception as e:
        result.log_failure("Step 8c", f"Non-existent ride test error: {str(e)}")
    
    # Edge case 4: Trying to verify OTP for ride not in 'accepted' status
    try:
        # Create another ride and try to verify without accepting first
        ride_data_2 = {
            "pickup_location": {
                "lat": 12.9716,
                "lng": 77.5946,
                "address": "Brigade Road, Bangalore"
            },
            "drop_location": {
                "lat": 12.9352,
                "lng": 77.6245,
                "address": "Indiranagar, Bangalore"
            },
            "estimated_distance": 6.2,
            "estimated_fare": 111.6
        }
        response = make_request("POST", "/rider/request-ride", ride_data_2, rider_headers)
        if response.status_code == 200:
            ride_data_2_response = response.json()
            ride_id_2 = ride_data_2_response["id"]
            
            # Try to verify OTP without accepting the ride
            unaccepted_ride_data = {
                "ride_id": ride_id_2,
                "otp_code": "1234"
            }
            response = make_request("POST", "/driver/verify-ride-otp", unaccepted_ride_data, driver_headers)
            if response.status_code == 404:
                result.log_success("Step 8d - OTP verification correctly rejected for unaccepted ride")
            else:
                result.log_failure("Step 8d", f"Unaccepted ride should return 404, got: {response.status_code}")
        else:
            result.log_failure("Step 8d", "Failed to create second ride for test")
    except Exception as e:
        result.log_failure("Step 8d", f"Unaccepted ride test error: {str(e)}")
    
    print(f"\n{'='*60}")
    print("RIDE OTP TESTING COMPLETED")
    print(f"{'='*60}")

def main():
    """Run the ride OTP tests"""
    print("🚗 RideShare Ride OTP Generation & Verification Testing")
    print("=" * 60)
    
    result = TestResult()
    
    # Run the comprehensive ride OTP test
    test_ride_otp_generation_flow(result)
    
    # Print summary
    result.summary()
    
    return result.passed, result.failed

if __name__ == "__main__":
    passed, failed = main()
    exit(0 if failed == 0 else 1)