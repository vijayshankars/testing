#!/usr/bin/env python3
"""
Driver Ride Rejection Functionality Testing
Tests the newly implemented driver ride rejection functionality comprehensively
"""

import requests
import json
import time
import random
import string
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
        print(f"TEST SUMMARY")
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
    """Generate unique phone number for testing"""
    random_digits = ''.join(random.choices(string.digits, k=6))
    return f"+91 987{random_digits}"

def test_driver_ride_rejection_functionality():
    """Test driver ride rejection functionality comprehensively"""
    print(f"🚗 DRIVER RIDE REJECTION FUNCTIONALITY TESTING")
    print(f"Testing against: {BASE_URL}")
    print(f"{'='*60}")
    
    result = TestResult()
    
    # Chennai locations for testing
    chennai_locations = {
        "pickup": {"lat": 13.0827, "lng": 80.2707, "address": "Chennai Central Railway Station"},
        "drop": {"lat": 13.0878, "lng": 80.2785, "address": "T. Nagar, Chennai"}
    }
    
    # Generate unique phone numbers for this test run
    driver_phone = generate_unique_phone()
    rider_phone = generate_unique_phone()
    driver2_phone = generate_unique_phone()
    
    driver_token = None
    rider_token = None
    driver2_token = None
    ride_id = None
    
    # Step 1: Create test driver user with mobile OTP authentication
    print("\n1. Creating test driver user with mobile OTP authentication...")
    
    try:
        # Send OTP for driver
        otp_response = make_request("POST", "/auth/send-otp", {
            "phone_number": driver_phone,
            "user_type": "driver"
        })
        
        if otp_response.status_code == 200:
            otp_data = otp_response.json()
            demo_otp = otp_data.get("demo_otp", "123456")
            
            # Verify OTP and create driver
            verify_response = make_request("POST", "/auth/verify-otp", {
                "phone_number": driver_phone,
                "otp_code": demo_otp,
                "user_type": "driver",
                "name": "Test Driver Chennai"
            })
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                driver_token = verify_data["token"]
                result.log_success("Driver user created with mobile OTP authentication")
            else:
                result.log_failure("Driver OTP verification", f"Status {verify_response.status_code}: {verify_response.text}")
                return result
        else:
            result.log_failure("Driver OTP sending", f"Status {otp_response.status_code}: {otp_response.text}")
            return result
    except Exception as e:
        result.log_failure("Driver mobile OTP authentication", str(e))
        return result
    
    # Step 2: Create driver profile
    print("\n2. Creating driver profile...")
    try:
        profile_response = make_request("POST", "/driver/profile", {
            "vehicle_type": "auto",
            "vehicle_number": "TN01AB1234",
            "license_number": "DL1234567890"
        }, headers=get_auth_headers(driver_token))
        
        if profile_response.status_code == 200:
            result.log_success("Driver profile created successfully")
        else:
            result.log_failure("Driver profile creation", f"Status {profile_response.status_code}: {profile_response.text}")
            return result
    except Exception as e:
        result.log_failure("Driver profile creation", str(e))
        return result
    
    # Step 3: Set driver location in Chennai
    print("\n3. Setting driver location in Chennai...")
    try:
        location_response = make_request("PUT", "/driver/location", {
            "lat": 13.0827,
            "lng": 80.2707
        }, headers=get_auth_headers(driver_token))
        
        if location_response.status_code == 200:
            result.log_success("Driver location set to Chennai coordinates")
        else:
            result.log_failure("Driver location update", f"Status {location_response.status_code}: {location_response.text}")
            return result
    except Exception as e:
        result.log_failure("Driver location update", str(e))
        return result
    
    # Step 4: Create test rider user with mobile OTP authentication
    print("\n4. Creating test rider user with mobile OTP authentication...")
    
    try:
        # Send OTP for rider
        otp_response = make_request("POST", "/auth/send-otp", {
            "phone_number": rider_phone,
            "user_type": "rider"
        })
        
        if otp_response.status_code == 200:
            otp_data = otp_response.json()
            demo_otp = otp_data.get("demo_otp", "123456")
            
            # Verify OTP and create rider
            verify_response = make_request("POST", "/auth/verify-otp", {
                "phone_number": rider_phone,
                "otp_code": demo_otp,
                "user_type": "rider",
                "name": "Test Rider Chennai"
            })
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                rider_token = verify_data["token"]
                result.log_success("Rider user created with mobile OTP authentication")
            else:
                result.log_failure("Rider OTP verification", f"Status {verify_response.status_code}: {verify_response.text}")
                return result
        else:
            result.log_failure("Rider OTP sending", f"Status {otp_response.status_code}: {otp_response.text}")
            return result
    except Exception as e:
        result.log_failure("Rider mobile OTP authentication", str(e))
        return result
    
    # Step 5: Create ride request with Chennai locations
    print("\n5. Creating ride request with Chennai locations...")
    try:
        ride_response = make_request("POST", "/rider/request-ride", {
            "pickup_location": chennai_locations["pickup"],
            "drop_location": chennai_locations["drop"],
            "estimated_distance": 2.5,
            "estimated_fare": 50.0
        }, headers=get_auth_headers(rider_token))
        
        if ride_response.status_code == 200:
            ride_data = ride_response.json()
            ride_id = ride_data["id"]
            result.log_success("Ride request created with Chennai locations")
        else:
            result.log_failure("Ride request creation", f"Status {ride_response.status_code}: {ride_response.text}")
            return result
    except Exception as e:
        result.log_failure("Ride request creation", str(e))
        return result
    
    # Step 6: Verify driver can see the ride request initially
    print("\n6. Verifying driver can see ride request initially...")
    try:
        requests_response = make_request("GET", "/driver/ride-requests", 
                                       headers=get_auth_headers(driver_token))
        
        if requests_response.status_code == 200:
            requests_data = requests_response.json()
            ride_found = any(r["id"] == ride_id for r in requests_data)
            if ride_found:
                result.log_success("Driver can see ride request in initial list")
            else:
                result.log_failure("Initial ride visibility", "Ride not found in driver's request list")
                return result
        else:
            result.log_failure("Get ride requests", f"Status {requests_response.status_code}: {requests_response.text}")
            return result
    except Exception as e:
        result.log_failure("Get ride requests", str(e))
        return result
    
    # Step 7: Test driver rejecting the ride request
    print("\n7. Testing driver ride rejection...")
    try:
        reject_response = make_request("POST", f"/driver/reject-ride/{ride_id}", 
                                     headers=get_auth_headers(driver_token))
        
        if reject_response.status_code == 200:
            reject_data = reject_response.json()
            if reject_data.get("status") == "rejected":
                result.log_success("Driver successfully rejected ride request")
            else:
                result.log_failure("Ride rejection response", f"Unexpected response: {reject_data}")
                return result
        else:
            result.log_failure("Driver ride rejection", f"Status {reject_response.status_code}: {reject_response.text}")
            return result
    except Exception as e:
        result.log_failure("Driver ride rejection", str(e))
        return result
    
    # Step 8: Verify rejection is recorded and ride is filtered out
    print("\n8. Verifying rejection is recorded and ride is filtered out...")
    try:
        requests_response = make_request("GET", "/driver/ride-requests", 
                                       headers=get_auth_headers(driver_token))
        
        if requests_response.status_code == 200:
            requests_data = requests_response.json()
            ride_found = any(r["id"] == ride_id for r in requests_data)
            if not ride_found:
                result.log_success("Rejected ride no longer appears in driver's request list")
            else:
                result.log_failure("Ride filtering after rejection", "Rejected ride still appears in request list")
        else:
            result.log_failure("Get ride requests after rejection", f"Status {requests_response.status_code}: {requests_response.text}")
    except Exception as e:
        result.log_failure("Get ride requests after rejection", str(e))
    
    # Step 9: Create second driver to test that other drivers can still see the ride
    print("\n9. Creating second driver to test ride visibility for other drivers...")
    
    try:
        # Send OTP for second driver
        otp_response = make_request("POST", "/auth/send-otp", {
            "phone_number": driver2_phone,
            "user_type": "driver"
        })
        
        if otp_response.status_code == 200:
            otp_data = otp_response.json()
            demo_otp = otp_data.get("demo_otp", "123456")
            
            # Verify OTP and create second driver
            verify_response = make_request("POST", "/auth/verify-otp", {
                "phone_number": driver2_phone,
                "otp_code": demo_otp,
                "user_type": "driver",
                "name": "Test Driver 2 Chennai"
            })
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                driver2_token = verify_data["token"]
                
                # Create driver profile for second driver
                profile_response = make_request("POST", "/driver/profile", {
                    "vehicle_type": "car",
                    "vehicle_number": "TN02CD5678",
                    "license_number": "DL9876543210"
                }, headers=get_auth_headers(driver2_token))
                
                if profile_response.status_code == 200:
                    # Set location for second driver
                    location_response = make_request("PUT", "/driver/location", {
                        "lat": 13.0878,
                        "lng": 80.2785
                    }, headers=get_auth_headers(driver2_token))
                    
                    if location_response.status_code == 200:
                        result.log_success("Second driver created and configured")
                    else:
                        result.log_failure("Second driver location", f"Status {location_response.status_code}")
                        return result
                else:
                    result.log_failure("Second driver profile", f"Status {profile_response.status_code}")
                    return result
            else:
                result.log_failure("Second driver OTP verification", f"Status {verify_response.status_code}")
                return result
        else:
            result.log_failure("Second driver OTP sending", f"Status {otp_response.status_code}")
            return result
    except Exception as e:
        result.log_failure("Second driver creation", str(e))
        return result
    
    # Step 10: Verify second driver can still see the ride request
    print("\n10. Verifying second driver can still see the ride request...")
    try:
        requests_response = make_request("GET", "/driver/ride-requests", 
                                       headers=get_auth_headers(driver2_token))
        
        if requests_response.status_code == 200:
            requests_data = requests_response.json()
            ride_found = any(r["id"] == ride_id for r in requests_data)
            if ride_found:
                result.log_success("Other drivers can still see ride request after one driver's rejection")
            else:
                result.log_failure("Ride visibility for other drivers", "Ride not visible to other drivers")
        else:
            result.log_failure("Get ride requests for second driver", f"Status {requests_response.status_code}: {requests_response.text}")
    except Exception as e:
        result.log_failure("Get ride requests for second driver", str(e))
    
    # Step 11: Test edge cases
    print("\n11. Testing edge cases...")
    
    # Test rejecting non-existent ride
    try:
        fake_ride_id = "non-existent-ride-id"
        reject_response = make_request("POST", f"/driver/reject-ride/{fake_ride_id}", 
                                     headers=get_auth_headers(driver_token))
        
        if reject_response.status_code == 404:
            result.log_success("Non-existent ride rejection properly returns 404")
        else:
            result.log_failure("Non-existent ride rejection", f"Expected 404, got {reject_response.status_code}")
    except Exception as e:
        result.log_failure("Non-existent ride rejection test", str(e))
    
    # Test unauthorized access (no token)
    try:
        reject_response = make_request("POST", f"/driver/reject-ride/{ride_id}")
        
        if reject_response.status_code == 403:
            result.log_success("Unauthorized ride rejection properly returns 403")
        else:
            result.log_failure("Unauthorized ride rejection", f"Expected 403, got {reject_response.status_code}")
    except Exception as e:
        result.log_failure("Unauthorized ride rejection test", str(e))
    
    # Step 12: Test that first driver cannot reject the same ride again
    print("\n12. Testing double rejection prevention...")
    try:
        reject_response = make_request("POST", f"/driver/reject-ride/{ride_id}", 
                                     headers=get_auth_headers(driver_token))
        
        if reject_response.status_code == 404:
            result.log_success("Double rejection properly prevented (404 for already rejected ride)")
        else:
            result.log_failure("Double rejection prevention", f"Expected 404, got {reject_response.status_code}")
    except Exception as e:
        result.log_failure("Double rejection prevention test", str(e))
    
    # Step 13: Test accepting ride after rejection by another driver
    print("\n13. Testing ride acceptance by second driver after first driver's rejection...")
    try:
        accept_response = make_request("POST", f"/driver/accept-ride/{ride_id}", 
                                     headers=get_auth_headers(driver2_token))
        
        if accept_response.status_code == 200:
            accept_data = accept_response.json()
            if "ride_otp" in accept_data:
                result.log_success("Second driver can accept ride after first driver's rejection")
            else:
                result.log_failure("Ride acceptance after rejection", f"Missing ride_otp in response: {accept_data}")
        else:
            result.log_failure("Ride acceptance after rejection", f"Status {accept_response.status_code}: {accept_response.text}")
    except Exception as e:
        result.log_failure("Ride acceptance after rejection", str(e))
    
    # Step 14: Test multiple drivers rejecting the same ride
    print("\n14. Testing multiple drivers rejecting the same ride...")
    
    # Create a third driver
    driver3_phone = generate_unique_phone()
    driver3_token = None
    
    try:
        # Create third driver
        otp_response = make_request("POST", "/auth/send-otp", {
            "phone_number": driver3_phone,
            "user_type": "driver"
        })
        
        if otp_response.status_code == 200:
            otp_data = otp_response.json()
            demo_otp = otp_data.get("demo_otp", "123456")
            
            verify_response = make_request("POST", "/auth/verify-otp", {
                "phone_number": driver3_phone,
                "otp_code": demo_otp,
                "user_type": "driver",
                "name": "Test Driver 3 Chennai"
            })
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                driver3_token = verify_data["token"]
                
                # Create profile and set location
                profile_response = make_request("POST", "/driver/profile", {
                    "vehicle_type": "bike",
                    "vehicle_number": "TN03EF9012",
                    "license_number": "DL5555555555"
                }, headers=get_auth_headers(driver3_token))
                
                if profile_response.status_code == 200:
                    location_response = make_request("PUT", "/driver/location", {
                        "lat": 13.0569,
                        "lng": 80.2091
                    }, headers=get_auth_headers(driver3_token))
                    
                    if location_response.status_code == 200:
                        # Create another ride request for testing multiple rejections
                        ride2_response = make_request("POST", "/rider/request-ride", {
                            "pickup_location": {"lat": 13.0569, "lng": 80.2091, "address": "T. Nagar, Chennai"},
                            "drop_location": {"lat": 13.0827, "lng": 80.2707, "address": "Chennai Central"},
                            "estimated_distance": 2.5,
                            "estimated_fare": 50.0
                        }, headers=get_auth_headers(rider_token))
                        
                        if ride2_response.status_code == 200:
                            ride2_data = ride2_response.json()
                            ride2_id = ride2_data["id"]
                            
                            # Have second driver reject this new ride
                            reject2_response = make_request("POST", f"/driver/reject-ride/{ride2_id}", 
                                                          headers=get_auth_headers(driver2_token))
                            
                            if reject2_response.status_code == 200:
                                # Have third driver also reject the same ride
                                reject3_response = make_request("POST", f"/driver/reject-ride/{ride2_id}", 
                                                              headers=get_auth_headers(driver3_token))
                                
                                if reject3_response.status_code == 200:
                                    result.log_success("Multiple drivers can reject the same ride independently")
                                else:
                                    result.log_failure("Multiple driver rejections", f"Third driver rejection failed: {reject3_response.status_code}")
                            else:
                                result.log_failure("Multiple driver rejections", f"Second driver rejection failed: {reject2_response.status_code}")
                        else:
                            result.log_failure("Second ride creation for multiple rejection test", f"Status {ride2_response.status_code}")
                    else:
                        result.log_failure("Third driver location", f"Status {location_response.status_code}")
                else:
                    result.log_failure("Third driver profile", f"Status {profile_response.status_code}")
            else:
                result.log_failure("Third driver OTP verification", f"Status {verify_response.status_code}")
        else:
            result.log_failure("Third driver OTP sending", f"Status {otp_response.status_code}")
    except Exception as e:
        result.log_failure("Multiple driver rejection test", str(e))
    
    # Step 15: Test distance-based filtering still works correctly with rejection system
    print("\n15. Testing distance-based filtering with rejection system...")
    
    # Create a ride far from drivers (outside 25km radius)
    far_location = {"lat": 12.9716, "lng": 77.5946, "address": "Bangalore (far from Chennai)"}
    
    try:
        far_ride_response = make_request("POST", "/rider/request-ride", {
            "pickup_location": far_location,
            "drop_location": chennai_locations["drop"],
            "estimated_distance": 350.0,
            "estimated_fare": 1000.0
        }, headers=get_auth_headers(rider_token))
        
        if far_ride_response.status_code == 200:
            far_ride_data = far_ride_response.json()
            far_ride_id = far_ride_data["id"]
            
            # Check if Chennai drivers can see this far ride (they shouldn't)
            requests_response = make_request("GET", "/driver/ride-requests", 
                                           headers=get_auth_headers(driver_token))
            
            if requests_response.status_code == 200:
                requests_data = requests_response.json()
                far_ride_found = any(r["id"] == far_ride_id for r in requests_data)
                if not far_ride_found:
                    result.log_success("Distance-based filtering works correctly with rejection system")
                else:
                    result.log_failure("Distance-based filtering", "Far ride incorrectly appears in nearby requests")
            else:
                result.log_failure("Distance filtering test", f"Status {requests_response.status_code}")
        else:
            result.log_failure("Far ride creation for distance test", f"Status {far_ride_response.status_code}")
    except Exception as e:
        result.log_failure("Distance-based filtering test", str(e))
    
    return result

def main():
    """Run driver ride rejection tests"""
    result = test_driver_ride_rejection_functionality()
    result.summary()
    return result.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)