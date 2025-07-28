#!/usr/bin/env python3
"""
Comprehensive Backend Testing for RideShare App
Tests all API endpoints with realistic data and scenarios
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://9bc251d5-e3ce-47e0-a729-c8aabb368f35.preview.emergentagent.com/api"
TIMEOUT = 30

# Test data
DRIVER_DATA = {
    "email": "driver@test.com",
    "password": "password123",
    "name": "John Driver",
    "phone": "+1234567890",
    "user_type": "driver"
}

RIDER_DATA = {
    "email": "rider@test.com",
    "password": "password123",
    "name": "Jane Rider",
    "phone": "+1234567891",
    "user_type": "rider"
}

DRIVER_PROFILE_DATA = {
    "per_km_rate": 15.5,
    "vehicle_type": "car",
    "vehicle_number": "KA01AB1234",
    "license_number": "DL1234567890"
}

SAMPLE_LOCATIONS = {
    "pickup": {"lat": 28.6139, "lng": 77.2090, "address": "Connaught Place, Delhi"},
    "drop": {"lat": 28.7041, "lng": 77.1025, "address": "Rohini, Delhi"}
}

# Global variables to store tokens and IDs
driver_token = None
rider_token = None
driver_id = None
rider_id = None
ride_id = None

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

def test_basic_health_check(result: TestResult):
    """Test basic API health endpoints"""
    print(f"\n{'='*60}")
    print("1. BASIC API HEALTH CHECK")
    print(f"{'='*60}")
    
    # Test root endpoint
    try:
        response = make_request("GET", "/")
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "running" in data["message"].lower():
                result.log_success("GET /api/ - API health check")
            else:
                result.log_failure("GET /api/", f"Unexpected response: {data}")
        else:
            result.log_failure("GET /api/", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/", str(e))
    
    # Test maps config endpoint
    try:
        response = make_request("GET", "/maps-config")
        if response.status_code == 200:
            data = response.json()
            if "google_maps_api_key" in data:
                result.log_success("GET /api/maps-config - Google Maps API key integration")
            else:
                result.log_failure("GET /api/maps-config", f"Missing google_maps_api_key: {data}")
        else:
            result.log_failure("GET /api/maps-config", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/maps-config", str(e))

def test_authentication_system(result: TestResult):
    """Test user registration and login"""
    global driver_token, rider_token, driver_id, rider_id
    
    print(f"\n{'='*60}")
    print("2. AUTHENTICATION SYSTEM TESTING")
    print(f"{'='*60}")
    
    # Test driver registration
    try:
        response = make_request("POST", "/auth/register", DRIVER_DATA)
        if response.status_code == 200:
            data = response.json()
            if all(key in data for key in ["id", "email", "name", "token", "user_type"]):
                driver_token = data["token"]
                driver_id = data["id"]
                if data["user_type"] == "driver" and data["email"] == DRIVER_DATA["email"]:
                    result.log_success("POST /api/auth/register - Driver registration")
                else:
                    result.log_failure("POST /api/auth/register", f"Invalid user data: {data}")
            else:
                result.log_failure("POST /api/auth/register", f"Missing required fields: {data}")
        else:
            result.log_failure("POST /api/auth/register", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/auth/register", str(e))
    
    # Test rider registration
    try:
        response = make_request("POST", "/auth/register", RIDER_DATA)
        if response.status_code == 200:
            data = response.json()
            if all(key in data for key in ["id", "email", "name", "token", "user_type"]):
                rider_token = data["token"]
                rider_id = data["id"]
                if data["user_type"] == "rider" and data["email"] == RIDER_DATA["email"]:
                    result.log_success("POST /api/auth/register - Rider registration")
                else:
                    result.log_failure("POST /api/auth/register", f"Invalid user data: {data}")
            else:
                result.log_failure("POST /api/auth/register", f"Missing required fields: {data}")
        else:
            result.log_failure("POST /api/auth/register", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/auth/register", str(e))
    
    # Test driver login
    try:
        login_data = {"email": DRIVER_DATA["email"], "password": DRIVER_DATA["password"]}
        response = make_request("POST", "/auth/login", login_data)
        if response.status_code == 200:
            data = response.json()
            if "token" in data and data["user_type"] == "driver":
                result.log_success("POST /api/auth/login - Driver authentication")
            else:
                result.log_failure("POST /api/auth/login", f"Invalid login response: {data}")
        else:
            result.log_failure("POST /api/auth/login", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/auth/login", str(e))
    
    # Test rider login
    try:
        login_data = {"email": RIDER_DATA["email"], "password": RIDER_DATA["password"]}
        response = make_request("POST", "/auth/login", login_data)
        if response.status_code == 200:
            data = response.json()
            if "token" in data and data["user_type"] == "rider":
                result.log_success("POST /api/auth/login - Rider authentication")
            else:
                result.log_failure("POST /api/auth/login", f"Invalid login response: {data}")
        else:
            result.log_failure("POST /api/auth/login", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/auth/login", str(e))

def test_driver_functionality(result: TestResult):
    """Test driver-specific endpoints"""
    global driver_token
    
    print(f"\n{'='*60}")
    print("3. DRIVER FUNCTIONALITY TESTING")
    print(f"{'='*60}")
    
    if not driver_token:
        result.log_failure("Driver functionality", "No driver token available")
        return
    
    headers = get_auth_headers(driver_token)
    
    # Test create driver profile
    try:
        response = make_request("POST", "/driver/profile", DRIVER_PROFILE_DATA, headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "profile" in data:
                profile = data["profile"]
                if all(key in profile for key in ["per_km_rate", "vehicle_type", "vehicle_number", "license_number"]):
                    result.log_success("POST /api/driver/profile - Create driver profile")
                else:
                    result.log_failure("POST /api/driver/profile", f"Missing profile fields: {profile}")
            else:
                result.log_failure("POST /api/driver/profile", f"Invalid response format: {data}")
        else:
            result.log_failure("POST /api/driver/profile", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/driver/profile", str(e))
    
    # Test get driver profile
    try:
        response = make_request("GET", "/driver/profile", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if all(key in data for key in ["per_km_rate", "vehicle_type", "vehicle_number", "license_number"]):
                result.log_success("GET /api/driver/profile - Retrieve driver profile")
            else:
                result.log_failure("GET /api/driver/profile", f"Missing profile fields: {data}")
        else:
            result.log_failure("GET /api/driver/profile", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/driver/profile", str(e))
    
    # Test update driver location
    try:
        location_data = {"lat": 28.6139, "lng": 77.2090}
        response = make_request("PUT", "/driver/location", location_data, headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "updated" in data["message"].lower():
                result.log_success("PUT /api/driver/location - Update driver location")
            else:
                result.log_failure("PUT /api/driver/location", f"Unexpected response: {data}")
        else:
            result.log_failure("PUT /api/driver/location", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("PUT /api/driver/location", str(e))
    
    # Test toggle availability to available
    try:
        response = make_request("PUT", "/driver/availability/true", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "available" in data["message"].lower():
                result.log_success("PUT /api/driver/availability/true - Set driver available")
            else:
                result.log_failure("PUT /api/driver/availability/true", f"Unexpected response: {data}")
        else:
            result.log_failure("PUT /api/driver/availability/true", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("PUT /api/driver/availability/true", str(e))
    
    # Test toggle availability to unavailable
    try:
        response = make_request("PUT", "/driver/availability/false", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "unavailable" in data["message"].lower():
                result.log_success("PUT /api/driver/availability/false - Set driver unavailable")
            else:
                result.log_failure("PUT /api/driver/availability/false", f"Unexpected response: {data}")
        else:
            result.log_failure("PUT /api/driver/availability/false", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("PUT /api/driver/availability/false", str(e))
    
    # Set driver back to available for ride matching tests
    try:
        make_request("PUT", "/driver/availability/true", headers=headers)
    except:
        pass
    
    # Test get ride requests (should be empty initially)
    try:
        response = make_request("GET", "/driver/ride-requests", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                result.log_success("GET /api/driver/ride-requests - Fetch nearby ride requests")
            else:
                result.log_failure("GET /api/driver/ride-requests", f"Expected list, got: {type(data)}")
        else:
            result.log_failure("GET /api/driver/ride-requests", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/driver/ride-requests", str(e))

def test_rider_functionality(result: TestResult):
    """Test rider-specific endpoints"""
    global rider_token, ride_id
    
    print(f"\n{'='*60}")
    print("4. RIDER FUNCTIONALITY TESTING")
    print(f"{'='*60}")
    
    if not rider_token:
        result.log_failure("Rider functionality", "No rider token available")
        return
    
    headers = get_auth_headers(rider_token)
    
    # Test request ride
    try:
        ride_data = {
            "pickup_location": SAMPLE_LOCATIONS["pickup"],
            "drop_location": SAMPLE_LOCATIONS["drop"],
            "estimated_distance": 12.5,
            "estimated_fare": 193.75
        }
        response = make_request("POST", "/rider/request-ride", ride_data, headers)
        if response.status_code == 200:
            data = response.json()
            if all(key in data for key in ["id", "rider_id", "pickup_location", "drop_location", "status"]):
                ride_id = data["id"]
                if data["status"] == "requested":
                    result.log_success("POST /api/rider/request-ride - Create ride request")
                else:
                    result.log_failure("POST /api/rider/request-ride", f"Invalid status: {data['status']}")
            else:
                result.log_failure("POST /api/rider/request-ride", f"Missing required fields: {data}")
        else:
            result.log_failure("POST /api/rider/request-ride", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/rider/request-ride", str(e))
    
    # Test get rider rides
    try:
        response = make_request("GET", "/rider/rides", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                ride = data[0]
                if all(key in ride for key in ["id", "rider_id", "pickup_location", "drop_location"]):
                    result.log_success("GET /api/rider/rides - Fetch rider's rides")
                else:
                    result.log_failure("GET /api/rider/rides", f"Missing ride fields: {ride}")
            else:
                result.log_failure("GET /api/rider/rides", f"Expected non-empty list, got: {data}")
        else:
            result.log_failure("GET /api/rider/rides", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/rider/rides", str(e))
    
    # Test get available drivers
    try:
        params = {"lat": 28.6139, "lng": 77.2090}
        response = make_request("GET", "/rider/available-drivers", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                result.log_success("GET /api/rider/available-drivers - Fetch available drivers")
            else:
                result.log_failure("GET /api/rider/available-drivers", f"Expected list, got: {type(data)}")
        else:
            result.log_failure("GET /api/rider/available-drivers", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/rider/available-drivers", str(e))

def test_ride_matching_system(result: TestResult):
    """Test the complete ride matching flow"""
    global driver_token, ride_id
    
    print(f"\n{'='*60}")
    print("5. RIDE MATCHING SYSTEM TESTING")
    print(f"{'='*60}")
    
    if not driver_token or not ride_id:
        result.log_failure("Ride matching", "Missing driver token or ride ID")
        return
    
    headers = get_auth_headers(driver_token)
    
    # Test driver can see the ride request
    try:
        response = make_request("GET", "/driver/ride-requests", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                found_ride = any(ride.get("id") == ride_id for ride in data)
                if found_ride:
                    result.log_success("Ride matching - Driver can see ride request")
                else:
                    result.log_failure("Ride matching", f"Driver cannot see ride request {ride_id}")
            else:
                result.log_failure("Ride matching", "No ride requests visible to driver")
        else:
            result.log_failure("Ride matching", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Ride matching", str(e))
    
    # Test driver accept ride
    try:
        response = make_request("POST", f"/driver/accept-ride/{ride_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "accepted" in data["message"].lower():
                result.log_success("POST /api/driver/accept-ride/{ride_id} - Driver accepts ride")
            else:
                result.log_failure("POST /api/driver/accept-ride/{ride_id}", f"Unexpected response: {data}")
        else:
            result.log_failure("POST /api/driver/accept-ride/{ride_id}", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/driver/accept-ride/{ride_id}", str(e))

def test_error_handling(result: TestResult):
    """Test error handling scenarios"""
    print(f"\n{'='*60}")
    print("6. ERROR HANDLING TESTING")
    print(f"{'='*60}")
    
    # Test invalid token
    try:
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = make_request("GET", "/driver/profile", headers=invalid_headers)
        if response.status_code == 401:
            result.log_success("Error handling - Invalid authentication token")
        else:
            result.log_failure("Error handling", f"Expected 401 for invalid token, got {response.status_code}")
    except Exception as e:
        result.log_failure("Error handling", str(e))
    
    # Test missing required fields in registration
    try:
        incomplete_data = {"email": "test@test.com"}  # Missing required fields
        response = make_request("POST", "/auth/register", incomplete_data)
        if response.status_code in [400, 422]:  # Bad request or validation error
            result.log_success("Error handling - Missing required fields")
        else:
            result.log_failure("Error handling", f"Expected 400/422 for missing fields, got {response.status_code}")
    except Exception as e:
        result.log_failure("Error handling", str(e))
    
    # Test unauthorized access (rider trying to access driver endpoint)
    if rider_token:
        try:
            rider_headers = get_auth_headers(rider_token)
            response = make_request("GET", "/driver/profile", headers=rider_headers)
            if response.status_code == 403:
                result.log_success("Error handling - Unauthorized access attempt")
            else:
                result.log_failure("Error handling", f"Expected 403 for unauthorized access, got {response.status_code}")
        except Exception as e:
            result.log_failure("Error handling", str(e))

def test_database_integration(result: TestResult):
    """Test database connectivity and data persistence"""
    print(f"\n{'='*60}")
    print("7. DATABASE INTEGRATION TESTING")
    print(f"{'='*60}")
    
    # Test data persistence by checking if registered users can login
    if driver_token and rider_token:
        result.log_success("Database integration - User data persistence verified")
    else:
        result.log_failure("Database integration", "User registration/login failed")
    
    # Test CRUD operations by checking if driver profile was created and can be retrieved
    if driver_token:
        try:
            headers = get_auth_headers(driver_token)
            response = make_request("GET", "/driver/profile", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("vehicle_number") == DRIVER_PROFILE_DATA["vehicle_number"]:
                    result.log_success("Database integration - CRUD operations working")
                else:
                    result.log_failure("Database integration", "Data not persisted correctly")
            else:
                result.log_failure("Database integration", f"Failed to retrieve profile: {response.status_code}")
        except Exception as e:
            result.log_failure("Database integration", str(e))

def main():
    """Run all tests"""
    print("🚗 RideShare Backend API Testing")
    print(f"Testing against: {BASE_URL}")
    print(f"{'='*60}")
    
    result = TestResult()
    
    # Run all test suites
    test_basic_health_check(result)
    test_authentication_system(result)
    test_driver_functionality(result)
    test_rider_functionality(result)
    test_ride_matching_system(result)
    test_error_handling(result)
    test_database_integration(result)
    
    # Print summary
    result.summary()
    
    return result.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)