#!/usr/bin/env python3
"""
Comprehensive Ride Booking Creation Testing
Tests specifically for ride booking creation to identify why bookings are not being created
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
        print(f"\n{'='*60}")
        print(f"RIDE BOOKING CREATION TEST SUMMARY")
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

def create_test_rider_with_mobile_otp(result: TestResult) -> Optional[str]:
    """Create a test rider user with mobile OTP (+91 9876543210) as requested"""
    print(f"\n--- Creating Test Rider User with Mobile OTP ---")
    
    test_phone = "+91 9876543210"
    
    # Step 1: Send OTP
    try:
        otp_data = {
            "phone_number": test_phone,
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result.log_success("Test rider OTP sent successfully")
                demo_otp = data.get("demo_otp", "123456")
            else:
                result.log_failure("Test rider OTP send", f"Failed: {data}")
                return None
        else:
            result.log_failure("Test rider OTP send", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.log_failure("Test rider OTP send", str(e))
        return None
    
    # Step 2: Verify OTP and create rider user
    try:
        verify_data = {
            "phone_number": test_phone,
            "otp_code": demo_otp,
            "user_type": "rider",
            "name": "Test Rider for Booking"
        }
        response = make_request("POST", "/auth/verify-otp", verify_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("token"):
                rider_token = data["token"]
                result.log_success("Test rider OTP verification and registration")
                return rider_token
            else:
                result.log_failure("Test rider OTP verification", f"Failed: {data}")
                return None
        else:
            result.log_failure("Test rider OTP verification", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.log_failure("Test rider OTP verification", str(e))
        return None

def test_ride_creation_endpoint_directly(result: TestResult, rider_token: str):
    """Test POST /api/rider/request-ride endpoint directly with realistic Chennai data"""
    print(f"\n--- Testing Ride Creation Endpoint Directly ---")
    
    headers = get_auth_headers(rider_token)
    
    # Test 1: Basic ride creation with Chennai locations
    try:
        ride_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central Railway Station, Chennai"
            },
            "drop_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "Marina Beach, Chennai"
            },
            "estimated_distance": 5.2,
            "estimated_fare": 156.0
        }
        
        response = make_request("POST", "/rider/request-ride", ride_data, headers)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "rider_id", "pickup_location", "drop_location", "status", "estimated_fare"]
            
            if all(field in data for field in required_fields):
                if data["status"] == "requested":
                    result.log_success("POST /api/rider/request-ride - Basic ride creation successful")
                    
                    # Verify ride ID is returned
                    if data.get("id"):
                        result.log_success("Ride ID returned properly in response")
                        return data["id"]  # Return ride ID for further testing
                    else:
                        result.log_failure("Ride ID verification", "No ride ID in response")
                else:
                    result.log_failure("Ride status verification", f"Expected 'requested', got '{data['status']}'")
            else:
                missing_fields = [f for f in required_fields if f not in data]
                result.log_failure("POST /api/rider/request-ride", f"Missing required fields: {missing_fields}")
        else:
            result.log_failure("POST /api/rider/request-ride", f"Status {response.status_code}: {response.text}")
            
    except Exception as e:
        result.log_failure("POST /api/rider/request-ride", str(e))
    
    return None

def test_database_persistence(result: TestResult, rider_token: str, ride_id: Optional[str]):
    """Test that ride entries are actually created in the database"""
    print(f"\n--- Testing Database Persistence ---")
    
    headers = get_auth_headers(rider_token)
    
    # Test 1: Check if ride appears in GET /api/rider/rides
    try:
        response = make_request("GET", "/rider/rides", headers=headers)
        print(f"GET /rider/rides Response Status: {response.status_code}")
        print(f"GET /rider/rides Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                if len(data) > 0:
                    result.log_success("Rides found in database via GET /api/rider/rides")
                    
                    # Check if our specific ride is there
                    if ride_id:
                        found_ride = any(ride.get("id") == ride_id for ride in data)
                        if found_ride:
                            result.log_success("Specific ride found in database")
                            
                            # Verify ride has all required fields
                            our_ride = next((ride for ride in data if ride.get("id") == ride_id), None)
                            if our_ride:
                                required_fields = ["id", "rider_id", "pickup_location", "drop_location", "status", "created_at"]
                                if all(field in our_ride for field in required_fields):
                                    result.log_success("Ride record has all required fields")
                                    
                                    # Verify ride status
                                    if our_ride.get("status") == "requested":
                                        result.log_success("Ride status correctly set to 'requested'")
                                    else:
                                        result.log_failure("Ride status verification", f"Expected 'requested', got '{our_ride.get('status')}'")
                                else:
                                    missing_fields = [f for f in required_fields if f not in our_ride]
                                    result.log_failure("Ride record completeness", f"Missing fields: {missing_fields}")
                        else:
                            result.log_failure("Specific ride persistence", f"Ride {ride_id} not found in database")
                    
                    # Print first ride for debugging
                    print(f"Sample ride record: {json.dumps(data[0], indent=2, default=str)}")
                else:
                    result.log_failure("Database persistence", "No rides found in database")
            else:
                result.log_failure("GET /api/rider/rides", f"Expected list, got {type(data)}")
        else:
            result.log_failure("GET /api/rider/rides", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/rider/rides", str(e))

def test_different_scenarios(result: TestResult, rider_token: str):
    """Test ride creation with different scenarios"""
    print(f"\n--- Testing Different Ride Creation Scenarios ---")
    
    headers = get_auth_headers(rider_token)
    
    # Test 1: Ride creation with promo code
    try:
        # First initialize sample discount codes
        init_response = make_request("POST", "/admin/init-sample-discounts")
        print(f"Discount initialization: {init_response.status_code}")
        
        ride_data_with_promo = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Airport Terminal 1"
            },
            "drop_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "T. Nagar, Chennai"
            },
            "estimated_distance": 8.5,
            "estimated_fare": 200.0,
            "promo_code": "SAVE10"
        }
        
        response = make_request("POST", "/rider/request-ride", ride_data_with_promo, headers)
        print(f"Ride with promo code response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "discount_applied" in data and data["discount_applied"]:
                result.log_success("Ride creation with promo code successful")
                
                # Verify discount was applied
                discount_info = data["discount_applied"]
                if discount_info.get("discount_amount", 0) > 0:
                    result.log_success("Promo code discount applied correctly")
                else:
                    result.log_failure("Promo code discount", "No discount amount applied")
            else:
                result.log_success("Ride creation with promo code (no discount applied)")
        else:
            result.log_failure("Ride with promo code", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride with promo code", str(e))
    
    # Test 2: Ride creation without promo code
    try:
        ride_data_no_promo = {
            "pickup_location": {
                "lat": 13.0475,
                "lng": 80.2824,
                "address": "Fort St. George, Chennai"
            },
            "drop_location": {
                "lat": 13.0524,
                "lng": 80.2511,
                "address": "Egmore Railway Station, Chennai"
            },
            "estimated_distance": 4.2,
            "estimated_fare": 126.0
        }
        
        response = make_request("POST", "/rider/request-ride", ride_data_no_promo, headers)
        print(f"Ride without promo code response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("estimated_fare") == 126.0:
                result.log_success("Ride creation without promo code successful")
            else:
                result.log_failure("Ride without promo code", f"Fare mismatch: expected 126.0, got {data.get('estimated_fare')}")
        else:
            result.log_failure("Ride without promo code", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride without promo code", str(e))
    
    # Test 3: Different location formats
    try:
        ride_data_different_format = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Chennai Central"
            },
            "drop_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "Marina Beach"
            },
            "estimated_distance": 5.0,
            "estimated_fare": 150.0
        }
        
        response = make_request("POST", "/rider/request-ride", ride_data_different_format, headers)
        print(f"Different location format response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            result.log_success("Ride creation with different location format successful")
        else:
            result.log_failure("Different location format", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Different location format", str(e))
    
    # Test 4: Various fare amounts
    fare_tests = [
        {"fare": 50.0, "distance": 2.5, "desc": "low fare"},
        {"fare": 500.0, "distance": 25.0, "desc": "high fare"},
        {"fare": 99.99, "distance": 4.8, "desc": "decimal fare"}
    ]
    
    for fare_test in fare_tests:
        try:
            ride_data_fare = {
                "pickup_location": {
                    "lat": 13.0827,
                    "lng": 80.2707,
                    "address": "Test Pickup Location"
                },
                "drop_location": {
                    "lat": 13.0878,
                    "lng": 80.2785,
                    "address": "Test Drop Location"
                },
                "estimated_distance": fare_test["distance"],
                "estimated_fare": fare_test["fare"]
            }
            
            response = make_request("POST", "/rider/request-ride", ride_data_fare, headers)
            print(f"Fare test ({fare_test['desc']}) response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if abs(data.get("estimated_fare", 0) - fare_test["fare"]) < 0.01:
                    result.log_success(f"Ride creation with {fare_test['desc']} successful")
                else:
                    result.log_failure(f"Fare test {fare_test['desc']}", f"Fare mismatch: expected {fare_test['fare']}, got {data.get('estimated_fare')}")
            else:
                result.log_failure(f"Fare test {fare_test['desc']}", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure(f"Fare test {fare_test['desc']}", str(e))

def test_api_response_structure(result: TestResult, rider_token: str):
    """Test API response structure from POST /api/rider/request-ride"""
    print(f"\n--- Testing API Response Structure ---")
    
    headers = get_auth_headers(rider_token)
    
    try:
        ride_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Response Test Pickup"
            },
            "drop_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "Response Test Drop"
            },
            "estimated_distance": 6.0,
            "estimated_fare": 180.0
        }
        
        response = make_request("POST", "/rider/request-ride", ride_data, headers)
        print(f"Response structure test: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required response fields
            required_fields = [
                "id", "rider_id", "pickup_location", "drop_location", 
                "estimated_distance", "estimated_fare", "status", "created_at"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if not missing_fields:
                result.log_success("All required response fields present")
                
                # Verify field types and values
                if isinstance(data["id"], str) and len(data["id"]) > 0:
                    result.log_success("Ride ID is valid string")
                else:
                    result.log_failure("Ride ID validation", f"Invalid ride ID: {data.get('id')}")
                
                if isinstance(data["pickup_location"], dict) and "lat" in data["pickup_location"]:
                    result.log_success("Pickup location structure valid")
                else:
                    result.log_failure("Pickup location structure", f"Invalid pickup location: {data.get('pickup_location')}")
                
                if isinstance(data["drop_location"], dict) and "lat" in data["drop_location"]:
                    result.log_success("Drop location structure valid")
                else:
                    result.log_failure("Drop location structure", f"Invalid drop location: {data.get('drop_location')}")
                
                if data.get("status") == "requested":
                    result.log_success("Status field correctly set to 'requested'")
                else:
                    result.log_failure("Status field validation", f"Expected 'requested', got '{data.get('status')}'")
                
                if isinstance(data.get("estimated_fare"), (int, float)) and data["estimated_fare"] > 0:
                    result.log_success("Estimated fare is valid number")
                else:
                    result.log_failure("Estimated fare validation", f"Invalid fare: {data.get('estimated_fare')}")
                    
            else:
                result.log_failure("Response structure", f"Missing required fields: {missing_fields}")
        else:
            result.log_failure("Response structure test", f"Status {response.status_code}: {response.text}")
            
    except Exception as e:
        result.log_failure("Response structure test", str(e))

def test_error_cases(result: TestResult, rider_token: str):
    """Test error cases for ride creation"""
    print(f"\n--- Testing Error Cases ---")
    
    headers = get_auth_headers(rider_token)
    
    # Test 1: Missing required fields
    try:
        incomplete_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Test Pickup"
            }
            # Missing drop_location, estimated_distance, estimated_fare
        }
        
        response = make_request("POST", "/rider/request-ride", incomplete_data, headers)
        print(f"Missing fields test response: {response.status_code} - {response.text}")
        
        if response.status_code in [400, 422]:  # Bad request or validation error
            result.log_success("Missing required fields properly rejected")
        else:
            result.log_failure("Missing fields handling", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        result.log_failure("Missing fields test", str(e))
    
    # Test 2: Invalid data types
    try:
        invalid_data = {
            "pickup_location": "invalid_location_string",  # Should be dict
            "drop_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "Test Drop"
            },
            "estimated_distance": "invalid_distance",  # Should be number
            "estimated_fare": 180.0
        }
        
        response = make_request("POST", "/rider/request-ride", invalid_data, headers)
        print(f"Invalid data types test response: {response.status_code} - {response.text}")
        
        if response.status_code in [400, 422]:
            result.log_success("Invalid data types properly rejected")
        else:
            result.log_failure("Invalid data handling", f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid data test", str(e))
    
    # Test 3: Invalid token
    try:
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        valid_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Test Pickup"
            },
            "drop_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "Test Drop"
            },
            "estimated_distance": 5.0,
            "estimated_fare": 150.0
        }
        
        response = make_request("POST", "/rider/request-ride", valid_data, invalid_headers)
        print(f"Invalid token test response: {response.status_code} - {response.text}")
        
        if response.status_code == 401:
            result.log_success("Invalid token properly rejected")
        else:
            result.log_failure("Invalid token handling", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.log_failure("Invalid token test", str(e))
    
    # Test 4: Invalid promo code
    try:
        invalid_promo_data = {
            "pickup_location": {
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Test Pickup"
            },
            "drop_location": {
                "lat": 13.0878,
                "lng": 80.2785,
                "address": "Test Drop"
            },
            "estimated_distance": 5.0,
            "estimated_fare": 150.0,
            "promo_code": "INVALID_PROMO_CODE"
        }
        
        response = make_request("POST", "/rider/request-ride", invalid_promo_data, headers)
        print(f"Invalid promo code test response: {response.status_code} - {response.text}")
        
        # Invalid promo code should not prevent ride creation, just not apply discount
        if response.status_code == 200:
            data = response.json()
            if not data.get("discount_applied"):
                result.log_success("Invalid promo code handled gracefully (no discount applied)")
            else:
                result.log_failure("Invalid promo code handling", "Discount should not be applied for invalid code")
        else:
            result.log_failure("Invalid promo code handling", f"Unexpected status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Invalid promo code test", str(e))

def main():
    """Main test execution"""
    result = TestResult()
    
    print("🚗 COMPREHENSIVE RIDE BOOKING CREATION TESTING")
    print("=" * 60)
    print("Testing ride booking creation specifically to identify why bookings are not being created")
    print("=" * 60)
    
    # Step 1: Create test rider user with mobile OTP
    rider_token = create_test_rider_with_mobile_otp(result)
    if not rider_token:
        print("❌ Failed to create test rider user. Cannot proceed with ride booking tests.")
        result.summary()
        return
    
    # Step 2: Test ride creation endpoint directly
    ride_id = test_ride_creation_endpoint_directly(result, rider_token)
    
    # Step 3: Test database persistence
    test_database_persistence(result, rider_token, ride_id)
    
    # Step 4: Test different scenarios
    test_different_scenarios(result, rider_token)
    
    # Step 5: Test API response structure
    test_api_response_structure(result, rider_token)
    
    # Step 6: Test error cases
    test_error_cases(result, rider_token)
    
    # Final summary
    result.summary()
    
    # Additional debugging information
    print(f"\n{'='*60}")
    print("DEBUGGING INFORMATION")
    print(f"{'='*60}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if result.failed > 0:
        print(f"\n⚠️  {result.failed} tests failed. Check the detailed error messages above.")
        print("Common issues to investigate:")
        print("- Database connectivity problems")
        print("- API endpoint routing issues")
        print("- Authentication token problems")
        print("- Data validation errors")
        print("- MongoDB collection/document creation issues")
    else:
        print(f"\n🎉 All {result.passed} tests passed! Ride booking creation is working correctly.")

if __name__ == "__main__":
    main()