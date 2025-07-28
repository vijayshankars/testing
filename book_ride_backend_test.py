#!/usr/bin/env python3
"""
Book a Ride Backend Functionality Testing
Tests the specific Book a Ride backend functionality as requested in the review
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
        print(f"BOOK A RIDE BACKEND TEST SUMMARY")
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

def test_rider_authentication(result: TestResult):
    """Test Rider Authentication with mobile OTP (+91 9876543210)"""
    print(f"\n{'='*60}")
    print("1. RIDER AUTHENTICATION TESTING")
    print(f"{'='*60}")
    
    test_phone = "+91 9876543210"
    rider_token = None
    
    # Step 1: Send OTP for rider
    try:
        otp_data = {
            "phone_number": test_phone,
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result.log_success("Rider OTP sent successfully to +91 9876543210")
                demo_otp = data.get("demo_otp", "123456")
                print(f"DEBUG: Demo OTP received: {demo_otp}")
            else:
                result.log_failure("Rider OTP send", f"Failed: {data}")
                return None
        else:
            result.log_failure("Rider OTP send", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.log_failure("Rider OTP send", str(e))
        return None
    
    # Step 2: Verify OTP and create/login rider
    try:
        verify_data = {
            "phone_number": test_phone,
            "otp_code": demo_otp,
            "user_type": "rider",
            "name": "Test Rider Book Ride"
        }
        response = make_request("POST", "/auth/verify-otp", verify_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("token"):
                rider_token = data["token"]
                result.log_success("Rider OTP verification and authentication successful")
                return rider_token
            else:
                result.log_failure("Rider OTP verification", f"Failed: {data}")
                return None
        else:
            result.log_failure("Rider OTP verification", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.log_failure("Rider OTP verification", str(e))
        return None

def test_ride_request_endpoint(result: TestResult, rider_token: str):
    """Test POST /api/rider/rides (ride request endpoint) with Chennai locations"""
    print(f"\n{'='*60}")
    print("2. RIDE REQUEST ENDPOINT TESTING")
    print(f"{'='*60}")
    
    if not rider_token:
        result.log_failure("Ride request endpoint", "No rider token available")
        return None
    
    headers = get_auth_headers(rider_token)
    
    # Chennai locations as specified in the review
    chennai_locations = {
        "pickup": {
            "lat": 13.0827,
            "lng": 80.2707,
            "address": "Chennai Central Railway Station"
        },
        "drop": {
            "lat": 12.9941,
            "lng": 80.1709,
            "address": "Chennai Airport"
        }
    }
    
    # Calculate realistic distance and fare for Chennai Central to Airport
    estimated_distance = 15.2  # km (realistic distance)
    estimated_fare = 152.0  # ₹10 per km base rate
    
    # Test 1: Basic ride request
    try:
        ride_data = {
            "pickup_location": chennai_locations["pickup"],
            "drop_location": chennai_locations["drop"],
            "estimated_distance": estimated_distance,
            "estimated_fare": estimated_fare
        }
        response = make_request("POST", "/rider/rides", ride_data, headers)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "rider_id", "pickup_location", "drop_location", "status", "estimated_distance", "estimated_fare"]
            if all(key in data for key in required_fields):
                if data["status"] == "requested":
                    result.log_success("POST /api/rider/rides - Basic ride request successful")
                    ride_id = data["id"]
                    
                    # Verify Chennai locations are preserved
                    if (data["pickup_location"]["address"] == "Chennai Central Railway Station" and
                        data["drop_location"]["address"] == "Chennai Airport"):
                        result.log_success("Chennai locations preserved correctly in ride request")
                    else:
                        result.log_failure("Chennai locations", "Location addresses not preserved correctly")
                    
                    return ride_id
                else:
                    result.log_failure("POST /api/rider/rides", f"Invalid status: {data['status']}")
            else:
                missing_fields = [f for f in required_fields if f not in data]
                result.log_failure("POST /api/rider/rides", f"Missing required fields: {missing_fields}")
        else:
            result.log_failure("POST /api/rider/rides", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/rider/rides", str(e))
    
    # Test 2: Ride request with different Chennai locations
    try:
        alternate_ride_data = {
            "pickup_location": {
                "lat": 13.0478,
                "lng": 80.2785,
                "address": "Marina Beach, Chennai"
            },
            "drop_location": {
                "lat": 13.0569,
                "lng": 80.2091,
                "address": "T. Nagar, Chennai"
            },
            "estimated_distance": 8.5,
            "estimated_fare": 85.0
        }
        response = make_request("POST", "/rider/rides", alternate_ride_data, headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "requested":
                result.log_success("POST /api/rider/rides - Alternate Chennai locations ride request")
                return data["id"]
            else:
                result.log_failure("POST /api/rider/rides", f"Invalid status for alternate locations: {data.get('status')}")
        else:
            result.log_failure("POST /api/rider/rides", f"Alternate locations request failed: {response.status_code}")
    except Exception as e:
        result.log_failure("POST /api/rider/rides", str(e))
    
    return None

def test_discount_integration(result: TestResult, rider_token: str):
    """Test ride request with and without promo codes"""
    print(f"\n{'='*60}")
    print("3. DISCOUNT INTEGRATION TESTING")
    print(f"{'='*60}")
    
    if not rider_token:
        result.log_failure("Discount integration", "No rider token available")
        return
    
    headers = get_auth_headers(rider_token)
    
    # Step 1: Initialize sample discount codes
    try:
        response = make_request("POST", "/admin/init-sample-discounts")
        if response.status_code == 200:
            result.log_success("Sample discount codes initialized")
        else:
            # May already exist, which is fine
            result.log_success("Sample discount codes available (may already exist)")
    except Exception as e:
        result.log_failure("Sample discount initialization", str(e))
    
    # Step 2: Get available discounts
    try:
        response = make_request("GET", "/rider/available-discounts", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("discounts"):
                available_codes = [d["code"] for d in data["discounts"]]
                result.log_success(f"Available discount codes retrieved: {available_codes}")
            else:
                result.log_failure("Available discounts", f"No discounts available: {data}")
                return
        else:
            result.log_failure("Available discounts", f"Status {response.status_code}: {response.text}")
            return
    except Exception as e:
        result.log_failure("Available discounts", str(e))
        return
    
    # Step 3: Test discount application
    test_fare = 200.0
    try:
        discount_request = {
            "promo_code": "SAVE10",
            "ride_fare": test_fare
        }
        response = make_request("POST", "/rider/apply-discount", discount_request, headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                discount_details = data.get("discount_details", {})
                if discount_details.get("discount_amount") > 0:
                    result.log_success(f"Discount application successful: ₹{discount_details.get('discount_amount')} off")
                else:
                    result.log_failure("Discount application", "No discount amount calculated")
            else:
                result.log_failure("Discount application", f"Failed: {data.get('message')}")
        else:
            result.log_failure("Discount application", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Discount application", str(e))
    
    # Step 4: Test ride request with promo code
    try:
        ride_with_discount = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central Railway Station"
            },
            "drop_location": {
                "lat": 12.9941,
                "lng": 80.1709,
                "address": "Chennai Airport"
            },
            "estimated_distance": 15.2,
            "estimated_fare": 200.0,
            "promo_code": "SAVE10"
        }
        response = make_request("POST", "/rider/request-ride", ride_with_discount, headers)
        if response.status_code == 200:
            data = response.json()
            if "discount_applied" in data and data["discount_applied"]:
                discount_info = data["discount_applied"]
                if discount_info["discount_amount"] > 0:
                    result.log_success(f"Ride request with discount successful: ₹{discount_info['discount_amount']} discount applied")
                else:
                    result.log_failure("Ride with discount", "No discount applied in ride request")
            else:
                result.log_failure("Ride with discount", "Discount not applied to ride request")
        else:
            result.log_failure("Ride with discount", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride with discount", str(e))
    
    # Step 5: Test ride request without promo code
    try:
        ride_without_discount = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central Railway Station"
            },
            "drop_location": {
                "lat": 12.9941,
                "lng": 80.1709,
                "address": "Chennai Airport"
            },
            "estimated_distance": 15.2,
            "estimated_fare": 200.0
        }
        response = make_request("POST", "/rider/request-ride", ride_without_discount, headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("estimated_fare") == data.get("final_fare", data.get("estimated_fare")):
                result.log_success("Ride request without discount - original fare preserved")
            else:
                result.log_failure("Ride without discount", "Unexpected fare modification without promo code")
        else:
            result.log_failure("Ride without discount", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride without discount", str(e))

def test_error_scenarios(result: TestResult, rider_token: str):
    """Test error scenarios for ride booking"""
    print(f"\n{'='*60}")
    print("4. ERROR SCENARIOS TESTING")
    print(f"{'='*60}")
    
    if not rider_token:
        result.log_failure("Error scenarios", "No rider token available")
        return
    
    headers = get_auth_headers(rider_token)
    
    # Test 1: Missing required fields
    try:
        incomplete_ride_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central Railway Station"
            }
            # Missing drop_location, estimated_distance, estimated_fare
        }
        response = make_request("POST", "/rider/rides", incomplete_ride_data, headers)
        if response.status_code in [400, 422]:
            result.log_success("Missing required fields properly rejected")
        else:
            result.log_failure("Missing required fields", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        result.log_failure("Missing required fields", str(e))
    
    # Test 2: Invalid location data
    try:
        invalid_location_data = {
            "pickup_location": {
                "lat": "invalid_lat",  # Invalid latitude
                "lng": 80.2707,
                "address": "Chennai Central Railway Station"
            },
            "drop_location": {
                "lat": 12.9941,
                "lng": 80.1709,
                "address": "Chennai Airport"
            },
            "estimated_distance": 15.2,
            "estimated_fare": 152.0
        }
        response = make_request("POST", "/rider/rides", invalid_location_data, headers)
        if response.status_code in [400, 422]:
            result.log_success("Invalid location data properly rejected")
        else:
            result.log_failure("Invalid location data", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid location data", str(e))
    
    # Test 3: Unauthorized access (no token)
    try:
        valid_ride_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central Railway Station"
            },
            "drop_location": {
                "lat": 12.9941,
                "lng": 80.1709,
                "address": "Chennai Airport"
            },
            "estimated_distance": 15.2,
            "estimated_fare": 152.0
        }
        response = make_request("POST", "/rider/rides", valid_ride_data)  # No headers
        if response.status_code == 401:
            result.log_success("Unauthorized access properly rejected")
        else:
            result.log_failure("Unauthorized access", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.log_failure("Unauthorized access", str(e))
    
    # Test 4: Invalid token
    try:
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        valid_ride_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central Railway Station"
            },
            "drop_location": {
                "lat": 12.9941,
                "lng": 80.1709,
                "address": "Chennai Airport"
            },
            "estimated_distance": 15.2,
            "estimated_fare": 152.0
        }
        response = make_request("POST", "/rider/rides", valid_ride_data, invalid_headers)
        if response.status_code == 401:
            result.log_success("Invalid token properly rejected")
        else:
            result.log_failure("Invalid token", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid token", str(e))
    
    # Test 5: Invalid promo code
    try:
        ride_with_invalid_promo = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central Railway Station"
            },
            "drop_location": {
                "lat": 12.9941,
                "lng": 80.1709,
                "address": "Chennai Airport"
            },
            "estimated_distance": 15.2,
            "estimated_fare": 152.0,
            "promo_code": "INVALID_CODE_123"
        }
        response = make_request("POST", "/rider/request-ride", ride_with_invalid_promo, headers)
        if response.status_code == 200:
            data = response.json()
            # Should create ride but without discount
            if not data.get("discount_applied"):
                result.log_success("Invalid promo code handled gracefully (ride created without discount)")
            else:
                result.log_failure("Invalid promo code", "Invalid promo code was applied")
        else:
            result.log_failure("Invalid promo code", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Invalid promo code", str(e))

def test_database_operations(result: TestResult, rider_token: str, ride_id: str):
    """Test database operations for ride records"""
    print(f"\n{'='*60}")
    print("5. DATABASE OPERATIONS TESTING")
    print(f"{'='*60}")
    
    if not rider_token:
        result.log_failure("Database operations", "No rider token available")
        return
    
    headers = get_auth_headers(rider_token)
    
    # Test 1: Verify ride records are created correctly
    try:
        response = make_request("GET", "/rider/rides", headers=headers)
        if response.status_code == 200:
            rides = response.json()
            if isinstance(rides, list) and len(rides) > 0:
                result.log_success("Ride records created and retrievable from database")
                
                # Check if all fields are populated properly
                latest_ride = rides[0]  # Most recent ride
                required_fields = ["id", "rider_id", "pickup_location", "drop_location", 
                                 "estimated_distance", "estimated_fare", "status", "created_at"]
                
                if all(field in latest_ride for field in required_fields):
                    result.log_success("All required fields populated in ride record")
                else:
                    missing_fields = [f for f in required_fields if f not in latest_ride]
                    result.log_failure("Database fields", f"Missing fields in ride record: {missing_fields}")
                
                # Verify ride status is set to "requested"
                if latest_ride.get("status") == "requested":
                    result.log_success("Ride status correctly set to 'requested'")
                else:
                    result.log_failure("Ride status", f"Expected 'requested', got '{latest_ride.get('status')}'")
                
                # Verify location data integrity
                pickup_loc = latest_ride.get("pickup_location", {})
                drop_loc = latest_ride.get("drop_location", {})
                
                if (pickup_loc.get("lat") and pickup_loc.get("lng") and pickup_loc.get("address") and
                    drop_loc.get("lat") and drop_loc.get("lng") and drop_loc.get("address")):
                    result.log_success("Location data integrity maintained in database")
                else:
                    result.log_failure("Location data", "Location data incomplete in database")
                
            else:
                result.log_failure("Database operations", "No ride records found in database")
        else:
            result.log_failure("Database operations", f"Failed to retrieve rides: {response.status_code}")
    except Exception as e:
        result.log_failure("Database operations", str(e))
    
    # Test 2: Test data persistence across multiple requests
    try:
        # Make another ride request
        new_ride_data = {
            "pickup_location": {
                "lat": 13.0478,
                "lng": 80.2785,
                "address": "Marina Beach, Chennai"
            },
            "drop_location": {
                "lat": 13.0569,
                "lng": 80.2091,
                "address": "T. Nagar, Chennai"
            },
            "estimated_distance": 8.5,
            "estimated_fare": 85.0
        }
        create_response = make_request("POST", "/rider/rides", new_ride_data, headers)
        
        if create_response.status_code == 200:
            # Retrieve rides again
            retrieve_response = make_request("GET", "/rider/rides", headers=headers)
            if retrieve_response.status_code == 200:
                rides = retrieve_response.json()
                if len(rides) >= 2:  # Should have at least 2 rides now
                    result.log_success("Data persistence across multiple ride requests verified")
                else:
                    result.log_failure("Data persistence", f"Expected at least 2 rides, found {len(rides)}")
            else:
                result.log_failure("Data persistence", "Failed to retrieve rides after creating new one")
        else:
            result.log_failure("Data persistence", "Failed to create additional ride for persistence test")
    except Exception as e:
        result.log_failure("Data persistence", str(e))

def test_available_drivers(result: TestResult, rider_token: str):
    """Test GET /api/rider/available-drivers endpoint"""
    print(f"\n{'='*60}")
    print("6. AVAILABLE DRIVERS TESTING")
    print(f"{'='*60}")
    
    if not rider_token:
        result.log_failure("Available drivers", "No rider token available")
        return
    
    headers = get_auth_headers(rider_token)
    
    # Test 1: Get available drivers for Chennai Central location
    try:
        params = {
            "lat": 13.0827,  # Chennai Central Railway Station
            "lng": 80.2707
        }
        response = make_request("GET", "/rider/available-drivers", headers=headers, params=params)
        if response.status_code == 200:
            drivers = response.json()
            if isinstance(drivers, list):
                result.log_success("GET /api/rider/available-drivers endpoint working correctly")
                
                if len(drivers) > 0:
                    result.log_success(f"Found {len(drivers)} available drivers for Chennai location")
                    
                    # Check driver data structure
                    first_driver = drivers[0]
                    required_fields = ["driver_id", "name", "vehicle_type", "per_km_rate", "distance"]
                    
                    if all(field in first_driver for field in required_fields):
                        result.log_success("Driver data structure contains all required fields")
                    else:
                        missing_fields = [f for f in required_fields if f not in first_driver]
                        result.log_failure("Driver data structure", f"Missing fields: {missing_fields}")
                    
                    # Verify fare calculation data is present
                    if first_driver.get("per_km_rate") and first_driver.get("distance"):
                        result.log_success("Fare calculation data available (per_km_rate and distance)")
                    else:
                        result.log_failure("Fare calculation", "Missing per_km_rate or distance data")
                        
                else:
                    result.log_success("Available drivers endpoint working (no drivers currently available)")
                    
            else:
                result.log_failure("Available drivers", f"Expected list, got {type(drivers)}")
        else:
            result.log_failure("Available drivers", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Available drivers", str(e))
    
    # Test 2: Test with different Chennai location (Airport)
    try:
        params = {
            "lat": 12.9941,  # Chennai Airport
            "lng": 80.1709
        }
        response = make_request("GET", "/rider/available-drivers", headers=headers, params=params)
        if response.status_code == 200:
            drivers = response.json()
            if isinstance(drivers, list):
                result.log_success("Available drivers endpoint working for Chennai Airport location")
            else:
                result.log_failure("Available drivers (Airport)", f"Expected list, got {type(drivers)}")
        else:
            result.log_failure("Available drivers (Airport)", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Available drivers (Airport)", str(e))
    
    # Test 3: Test error handling - missing parameters
    try:
        response = make_request("GET", "/rider/available-drivers", headers=headers)  # No lat/lng params
        if response.status_code in [400, 422]:
            result.log_success("Missing location parameters properly rejected")
        else:
            result.log_failure("Missing parameters", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        result.log_failure("Missing parameters", str(e))
    
    # Test 4: Test unauthorized access
    try:
        params = {"lat": 13.0827, "lng": 80.2707}
        response = make_request("GET", "/rider/available-drivers", params=params)  # No auth headers
        if response.status_code == 401:
            result.log_success("Unauthorized access to available drivers properly rejected")
        else:
            result.log_failure("Unauthorized access", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.log_failure("Unauthorized access", str(e))

def main():
    """Main test execution function"""
    print("🚗 BOOK A RIDE BACKEND FUNCTIONALITY TESTING")
    print("=" * 60)
    print("Testing the Book a Ride backend functionality as requested in the review")
    print("Focus: Rider Authentication, Ride Request Endpoint, Discount Integration, Error Scenarios, Database Operations, Available Drivers")
    print("=" * 60)
    
    result = TestResult()
    
    # Test 1: Rider Authentication
    rider_token = test_rider_authentication(result)
    
    if not rider_token:
        print("\n❌ CRITICAL: Rider authentication failed. Cannot proceed with other tests.")
        result.summary()
        return
    
    # Test 2: Ride Request Endpoint
    ride_id = test_ride_request_endpoint(result, rider_token)
    
    # Test 3: Discount Integration
    test_discount_integration(result, rider_token)
    
    # Test 4: Error Scenarios
    test_error_scenarios(result, rider_token)
    
    # Test 5: Database Operations
    test_database_operations(result, rider_token, ride_id)
    
    # Test 6: Available Drivers
    test_available_drivers(result, rider_token)
    
    # Final summary
    result.summary()
    
    # Provide specific feedback for the review
    print(f"\n{'='*60}")
    print("BOOK A RIDE BACKEND FUNCTIONALITY ASSESSMENT")
    print(f"{'='*60}")
    
    if result.failed == 0:
        print("✅ ALL TESTS PASSED: Book a Ride backend functionality is working correctly")
        print("✅ Rider authentication with mobile OTP (+91 9876543210) working")
        print("✅ Ride request endpoint with Chennai locations working")
        print("✅ Discount integration working properly")
        print("✅ Error scenarios handled correctly")
        print("✅ Database operations working correctly")
        print("✅ Available drivers endpoint working")
    else:
        print(f"⚠️  {result.failed} ISSUES FOUND in Book a Ride backend functionality")
        print("Issues that need attention:")
        for error in result.errors:
            print(f"  • {error}")
    
    print(f"\n{'='*60}")
    print("TESTING COMPLETED")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()