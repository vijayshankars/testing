#!/usr/bin/env python3
"""
Comprehensive Ride OTP Testing - Final Version
Tests all aspects of ride OTP generation and verification as requested
"""

import requests
import json
import time
import random
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
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE RIDE OTP TEST SUMMARY")
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

def create_mobile_user(phone: str, user_type: str, name: str, result: TestResult) -> Optional[str]:
    """Helper function to create a user via mobile OTP"""
    try:
        # Send OTP
        otp_request = {
            "phone_number": phone,
            "user_type": user_type
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code != 200:
            result.log_failure(f"Create {user_type}", f"Failed to send OTP: {response.status_code}")
            return None
        
        # Verify OTP
        verify_request = {
            "phone_number": phone,
            "otp_code": "123456",  # Demo OTP
            "user_type": user_type,
            "name": name
        }
        response = make_request("POST", "/auth/verify-otp", verify_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("token"):
                return data["token"]
        
        result.log_failure(f"Create {user_type}", f"OTP verification failed: {response.status_code}")
        return None
    except Exception as e:
        result.log_failure(f"Create {user_type}", f"Error: {str(e)}")
        return None

def test_complete_ride_otp_flow(result: TestResult):
    """Test the complete ride OTP flow as requested in the review"""
    print(f"\n{'='*60}")
    print("COMPREHENSIVE RIDE OTP TESTING")
    print("Testing as requested: Mobile OTP auth, ride creation, OTP generation, verification, edge cases")
    print(f"{'='*60}")
    
    # Generate unique phone numbers to avoid conflicts
    random_suffix = str(random.randint(10000, 99999))
    rider_phone = f"+91 9876{random_suffix}"  # Based on requested +91 9876543210 format
    driver_phone = f"+91 9877{random_suffix}"
    
    print(f"\nUsing test phones: Rider: {rider_phone}, Driver: {driver_phone}")
    
    # Step 1: Create test rider user with mobile OTP authentication (+91 9876543210 format)
    print(f"\n--- STEP 1: Create test rider user with mobile OTP authentication ---")
    rider_token = create_mobile_user(rider_phone, "rider", "Test Rider OTP Flow", result)
    if not rider_token:
        return
    result.log_success("STEP 1 - Test rider user created with mobile OTP authentication")
    
    # Step 2: Create test driver user and driver profile
    print(f"\n--- STEP 2: Create test driver user and driver profile ---")
    driver_token = create_mobile_user(driver_phone, "driver", "Test Driver OTP Flow", result)
    if not driver_token:
        return
    result.log_success("STEP 2a - Test driver user created with mobile OTP authentication")
    
    # Create driver profile
    try:
        driver_headers = get_auth_headers(driver_token)
        profile_data = {
            "per_km_rate": 20.0,
            "vehicle_type": "hatchback",
            "vehicle_number": f"KA01AB{random_suffix[-4:]}",
            "license_number": f"DL{random_suffix}890"
        }
        response = make_request("POST", "/driver/profile", profile_data, driver_headers)
        if response.status_code == 200:
            result.log_success("STEP 2b - Driver profile created successfully")
        else:
            result.log_failure("STEP 2b", f"Driver profile creation failed: {response.status_code}")
            return
    except Exception as e:
        result.log_failure("STEP 2b", f"Driver profile creation error: {str(e)}")
        return
    
    # Set driver location and availability
    try:
        location_data = {"lat": 13.0827, "lng": 80.2707}  # Chennai coordinates
        response = make_request("PUT", "/driver/location", location_data, driver_headers)
        if response.status_code == 200:
            result.log_success("STEP 2c - Driver location set to Chennai")
        else:
            result.log_failure("STEP 2c", f"Driver location update failed: {response.status_code}")
            return
        
        response = make_request("PUT", "/driver/availability/true", headers=driver_headers)
        if response.status_code == 200:
            result.log_success("STEP 2d - Driver availability set to available")
        else:
            result.log_failure("STEP 2d", f"Driver availability update failed: {response.status_code}")
            return
    except Exception as e:
        result.log_failure("STEP 2c/2d", f"Driver setup error: {str(e)}")
        return
    
    # Step 3: Create a ride request from the rider
    print(f"\n--- STEP 3: Create ride request from rider ---")
    try:
        rider_headers = get_auth_headers(rider_token)
        ride_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central Railway Station"
            },
            "drop_location": {
                "lat": 13.0569,
                "lng": 80.2427,
                "address": "Marina Beach, Chennai"
            },
            "estimated_distance": 6.8,
            "estimated_fare": 136.0
        }
        response = make_request("POST", "/rider/request-ride", ride_data, rider_headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("id") and data.get("status") == "requested":
                ride_id = data["id"]
                result.log_success("STEP 3 - Ride request created successfully")
            else:
                result.log_failure("STEP 3", f"Invalid ride request response: {data}")
                return
        else:
            result.log_failure("STEP 3", f"Ride request creation failed: {response.status_code}")
            return
    except Exception as e:
        result.log_failure("STEP 3", f"Ride request creation error: {str(e)}")
        return
    
    # Step 4: Have the driver accept the ride (this should generate a ride OTP)
    print(f"\n--- STEP 4: Driver accepts ride and generates OTP ---")
    try:
        response = make_request("POST", f"/driver/accept-ride/{ride_id}", headers=driver_headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "accepted" in data["message"].lower():
                result.log_success("STEP 4a - Driver successfully accepted ride")
                
                # Check if ride OTP is generated and returned
                if "ride_otp" in data:
                    ride_otp = data["ride_otp"]
                    if len(ride_otp) == 4 and ride_otp.isdigit():
                        result.log_success("STEP 4b - Ride OTP generated correctly (4-digit numeric)")
                        print(f"    🔑 Generated OTP: {ride_otp}")
                    else:
                        result.log_failure("STEP 4b", f"Invalid OTP format: {ride_otp}")
                        return
                else:
                    result.log_failure("STEP 4b", "Ride OTP not returned in response")
                    return
                
                # Check instructions
                if "instructions" in data and "share" in data["instructions"].lower():
                    result.log_success("STEP 4c - OTP sharing instructions provided to driver")
                else:
                    result.log_failure("STEP 4c", "OTP sharing instructions missing or incomplete")
            else:
                result.log_failure("STEP 4a", f"Unexpected acceptance response: {data}")
                return
        else:
            result.log_failure("STEP 4a", f"Ride acceptance failed: {response.status_code}")
            return
    except Exception as e:
        result.log_failure("STEP 4", f"Ride acceptance error: {str(e)}")
        return
    
    # Step 5: Verify that the ride OTP is generated and stored correctly
    print(f"\n--- STEP 5: Verify OTP generation and storage ---")
    try:
        # Check rider's rides to verify ride status and OTP handling
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
                        result.log_success("STEP 5a - Ride status correctly updated to 'accepted'")
                    else:
                        result.log_failure("STEP 5a", f"Ride status is {accepted_ride.get('status')}, expected 'accepted'")
                    
                    # Security check: OTP should not be exposed to rider
                    if "ride_otp" not in accepted_ride:
                        result.log_success("STEP 5b - Security verified: Ride OTP not exposed to rider")
                    else:
                        result.log_failure("STEP 5b", "SECURITY ISSUE: Ride OTP exposed to rider")
                    
                    # Check OTP verification status
                    if accepted_ride.get("otp_verified") is False:
                        result.log_success("STEP 5c - OTP verification status correctly set to False")
                    else:
                        result.log_failure("STEP 5c", f"OTP verification status incorrect: {accepted_ride.get('otp_verified')}")
                    
                    # Check timestamps
                    if accepted_ride.get("accepted_at"):
                        result.log_success("STEP 5d - Ride acceptance timestamp recorded")
                    else:
                        result.log_failure("STEP 5d", "Ride acceptance timestamp missing")
                else:
                    result.log_failure("STEP 5", "Could not find accepted ride in rider's rides")
            else:
                result.log_failure("STEP 5", "No rides found for rider")
        else:
            result.log_failure("STEP 5", f"Failed to get rider rides: {response.status_code}")
    except Exception as e:
        result.log_failure("STEP 5", f"OTP storage verification error: {str(e)}")
    
    # Step 6: Test the ride OTP verification process where driver enters the OTP to start the ride
    print(f"\n--- STEP 6: Test OTP verification process ---")
    try:
        verification_data = {
            "ride_id": ride_id,
            "otp_code": ride_otp
        }
        response = make_request("POST", "/driver/verify-ride-otp", verification_data, driver_headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "started" in data["message"].lower():
                result.log_success("STEP 6a - Driver successfully verified ride OTP")
                
                if data.get("status") == "in_progress":
                    result.log_success("STEP 6b - Ride status correctly returned as 'in_progress'")
                else:
                    result.log_failure("STEP 6b", f"Expected status 'in_progress', got: {data.get('status')}")
            else:
                result.log_failure("STEP 6a", f"Unexpected OTP verification response: {data}")
        else:
            result.log_failure("STEP 6a", f"OTP verification failed: {response.status_code}")
    except Exception as e:
        result.log_failure("STEP 6", f"OTP verification error: {str(e)}")
    
    # Step 7: Verify the ride status changes from 'accepted' to 'in_progress' after OTP verification
    print(f"\n--- STEP 7: Verify ride status change after OTP verification ---")
    try:
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
                        result.log_success("STEP 7a - Ride status successfully changed to 'in_progress'")
                    else:
                        result.log_failure("STEP 7a", f"Ride status is {in_progress_ride.get('status')}, expected 'in_progress'")
                    
                    if in_progress_ride.get("otp_verified") is True:
                        result.log_success("STEP 7b - OTP verification status updated to True")
                    else:
                        result.log_failure("STEP 7b", f"OTP verification status not updated: {in_progress_ride.get('otp_verified')}")
                    
                    if in_progress_ride.get("started_at"):
                        result.log_success("STEP 7c - Ride start timestamp recorded")
                    else:
                        result.log_failure("STEP 7c", "Ride start timestamp missing")
                else:
                    result.log_failure("STEP 7", "Could not find ride after OTP verification")
            else:
                result.log_failure("STEP 7", "No rides found for rider after OTP verification")
        else:
            result.log_failure("STEP 7", f"Failed to get rider rides: {response.status_code}")
    except Exception as e:
        result.log_failure("STEP 7", f"Status change verification error: {str(e)}")
    
    # Step 8: Test edge cases like invalid OTP, wrong driver trying to verify, etc.
    print(f"\n--- STEP 8: Test edge cases ---")
    
    # Create a new ride for edge case testing
    try:
        edge_case_ride_data = {
            "pickup_location": {
                "lat": 13.0569,
                "lng": 80.2427,
                "address": "Marina Beach, Chennai"
            },
            "drop_location": {
                "lat": 13.0878, 
                "lng": 80.2785,
                "address": "T. Nagar, Chennai"
            },
            "estimated_distance": 4.2,
            "estimated_fare": 84.0
        }
        response = make_request("POST", "/rider/request-ride", edge_case_ride_data, rider_headers)
        if response.status_code == 200:
            edge_ride_data = response.json()
            edge_ride_id = edge_ride_data["id"]
            
            # Accept the ride to get OTP
            response = make_request("POST", f"/driver/accept-ride/{edge_ride_id}", headers=driver_headers)
            if response.status_code == 200:
                edge_otp_data = response.json()
                edge_ride_otp = edge_otp_data.get("ride_otp")
                result.log_success("STEP 8 Setup - Created test ride for edge cases")
            else:
                result.log_failure("STEP 8 Setup", "Failed to accept edge case ride")
                return
        else:
            result.log_failure("STEP 8 Setup", "Failed to create edge case ride")
            return
    except Exception as e:
        result.log_failure("STEP 8 Setup", f"Edge case setup error: {str(e)}")
        return
    
    # Edge case 1: Invalid OTP
    try:
        invalid_otp_data = {
            "ride_id": edge_ride_id,
            "otp_code": "9999"  # Invalid OTP
        }
        response = make_request("POST", "/driver/verify-ride-otp", invalid_otp_data, driver_headers)
        if response.status_code == 400:
            data = response.json()
            if "invalid" in data.get("detail", "").lower():
                result.log_success("STEP 8a - Invalid OTP correctly rejected with 400 error")
            else:
                result.log_failure("STEP 8a", f"Wrong error message for invalid OTP: {data}")
        else:
            result.log_failure("STEP 8a", f"Invalid OTP should return 400, got: {response.status_code}")
    except Exception as e:
        result.log_failure("STEP 8a", f"Invalid OTP test error: {str(e)}")
    
    # Edge case 2: Wrong driver trying to verify OTP
    try:
        # Create another driver
        wrong_driver_phone = f"+91 9878{random_suffix}"
        wrong_driver_token = create_mobile_user(wrong_driver_phone, "driver", "Wrong Driver", result)
        
        if wrong_driver_token:
            wrong_driver_headers = get_auth_headers(wrong_driver_token)
            
            # Try to verify OTP with wrong driver
            wrong_verification_data = {
                "ride_id": edge_ride_id,
                "otp_code": edge_ride_otp
            }
            response = make_request("POST", "/driver/verify-ride-otp", wrong_verification_data, wrong_driver_headers)
            if response.status_code == 404:
                result.log_success("STEP 8b - Wrong driver correctly prevented from verifying OTP")
            else:
                result.log_failure("STEP 8b", f"Wrong driver should get 404, got: {response.status_code}")
        else:
            result.log_failure("STEP 8b", "Failed to create wrong driver for test")
    except Exception as e:
        result.log_failure("STEP 8b", f"Wrong driver test error: {str(e)}")
    
    # Edge case 3: Non-existent ride ID
    try:
        invalid_ride_data = {
            "ride_id": "invalid_ride_id_12345",
            "otp_code": "1234"
        }
        response = make_request("POST", "/driver/verify-ride-otp", invalid_ride_data, driver_headers)
        if response.status_code == 404:
            result.log_success("STEP 8c - Non-existent ride ID correctly rejected")
        else:
            result.log_failure("STEP 8c", f"Non-existent ride should return 404, got: {response.status_code}")
    except Exception as e:
        result.log_failure("STEP 8c", f"Non-existent ride test error: {str(e)}")
    
    # Edge case 4: Trying to verify OTP for ride not in 'accepted' status
    try:
        # Create another ride but don't accept it
        unaccepted_ride_data = {
            "pickup_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "T. Nagar, Chennai"
            },
            "drop_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central"
            },
            "estimated_distance": 3.5,
            "estimated_fare": 70.0
        }
        response = make_request("POST", "/rider/request-ride", unaccepted_ride_data, rider_headers)
        if response.status_code == 200:
            unaccepted_ride_response = response.json()
            unaccepted_ride_id = unaccepted_ride_response["id"]
            
            # Try to verify OTP without accepting the ride
            unaccepted_verification_data = {
                "ride_id": unaccepted_ride_id,
                "otp_code": "1234"
            }
            response = make_request("POST", "/driver/verify-ride-otp", unaccepted_verification_data, driver_headers)
            if response.status_code == 404:
                result.log_success("STEP 8d - OTP verification correctly rejected for unaccepted ride")
            else:
                result.log_failure("STEP 8d", f"Unaccepted ride should return 404, got: {response.status_code}")
        else:
            result.log_failure("STEP 8d", "Failed to create unaccepted ride for test")
    except Exception as e:
        result.log_failure("STEP 8d", f"Unaccepted ride test error: {str(e)}")
    
    # Edge case 5: Trying to verify OTP twice (already verified)
    try:
        # Try to verify the original ride OTP again (should fail since it's already in_progress)
        double_verification_data = {
            "ride_id": ride_id,
            "otp_code": ride_otp
        }
        response = make_request("POST", "/driver/verify-ride-otp", double_verification_data, driver_headers)
        if response.status_code == 404:
            result.log_success("STEP 8e - Double OTP verification correctly rejected")
        else:
            result.log_failure("STEP 8e", f"Double verification should return 404, got: {response.status_code}")
    except Exception as e:
        result.log_failure("STEP 8e", f"Double verification test error: {str(e)}")
    
    print(f"\n{'='*60}")
    print("COMPREHENSIVE RIDE OTP TESTING COMPLETED")
    print("All requested functionality has been tested:")
    print("✓ Mobile OTP authentication for rider (+91 9876543210 format)")
    print("✓ Driver user creation and profile setup")
    print("✓ Ride request creation")
    print("✓ Ride acceptance and OTP generation")
    print("✓ OTP storage and security verification")
    print("✓ OTP verification process")
    print("✓ Ride status changes (requested → accepted → in_progress)")
    print("✓ Edge cases (invalid OTP, wrong driver, non-existent ride, etc.)")
    print(f"{'='*60}")

def main():
    """Run the comprehensive ride OTP tests"""
    print("🚗 RideShare Ride OTP Generation & Verification Testing")
    print("=" * 60)
    print("Testing the complete ride OTP functionality as requested:")
    print("1. Create test rider user with mobile OTP authentication (+91 9876543210)")
    print("2. Create test driver user and driver profile")
    print("3. Create ride request from rider")
    print("4. Driver accepts ride (generates ride OTP)")
    print("5. Verify OTP generation and storage")
    print("6. Test OTP verification process")
    print("7. Verify ride status changes from 'accepted' to 'in_progress'")
    print("8. Test edge cases (invalid OTP, wrong driver, etc.)")
    print("=" * 60)
    
    result = TestResult()
    
    # Run the comprehensive ride OTP test
    test_complete_ride_otp_flow(result)
    
    # Print summary
    result.summary()
    
    return result.passed, result.failed

if __name__ == "__main__":
    passed, failed = main()
    exit(0 if failed == 0 else 1)