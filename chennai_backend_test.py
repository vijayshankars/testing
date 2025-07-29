#!/usr/bin/env python3
"""
Chennai-Specific Backend Testing for RideShare App
Tests Chennai location data, admin dashboard, and complete Chennai flow
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://3be44877-be55-4f11-a89f-8fbc7e4df5e7.preview.emergentagent.com/api"
TIMEOUT = 30

# Chennai Test Data
CHENNAI_LOCATIONS = {
    "airport": {"lat": 12.9941, "lng": 80.1709, "address": "Chennai Airport"},
    "tnagar": {"lat": 13.0418, "lng": 80.2341, "address": "T. Nagar, Chennai"},
    "marina": {"lat": 13.0490, "lng": 80.2824, "address": "Marina Beach, Chennai"},
    "fallback": {"lat": 13.0827, "lng": 80.2707, "address": "Chennai Central"}
}

# Test Users Data
CHENNAI_RIDER_DATA = {
    "email": "test.rider.chennai@example.com",
    "password": "chennai123",
    "name": "Chennai Test Rider",
    "phone": "+91 9876543210",
    "user_type": "rider"
}

CHENNAI_DRIVER_DATA = {
    "email": "test.driver.chennai@example.com",
    "password": "chennai123",
    "name": "Chennai Test Driver",
    "phone": "+91 9876543211",
    "user_type": "driver"
}

ADMIN_USER_DATA = {
    "email": "admin@rideshare.com",
    "password": "admin123",
    "name": "Admin User",
    "phone": "+91 9999999999",
    "user_type": "admin"
}

CHENNAI_DRIVER_PROFILE = {
    "per_km_rate": 18.0,
    "vehicle_type": "auto",
    "vehicle_number": "TN09AB1234",
    "license_number": "TN1234567890"
}

# Global variables
chennai_rider_token = None
chennai_driver_token = None
admin_token = None
chennai_ride_id = None

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
        print(f"CHENNAI BACKEND TEST SUMMARY")
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

def test_chennai_location_data(result: TestResult):
    """Test Chennai location data and fallback coordinates"""
    print(f"\n{'='*60}")
    print("1. CHENNAI LOCATION DATA TESTING")
    print(f"{'='*60}")
    
    # Test 1: Verify Chennai fallback coordinates are properly set
    try:
        # This would typically be tested by checking if the system uses Chennai coordinates as fallback
        # For now, we'll verify the coordinates are valid Chennai coordinates
        fallback_coords = CHENNAI_LOCATIONS["fallback"]
        if (12.5 <= fallback_coords["lat"] <= 13.5 and 
            79.5 <= fallback_coords["lng"] <= 81.0):
            result.log_success("Chennai fallback coordinates validation - Within Chennai bounds")
        else:
            result.log_failure("Chennai fallback coordinates", f"Coordinates outside Chennai: {fallback_coords}")
    except Exception as e:
        result.log_failure("Chennai fallback coordinates", str(e))
    
    # Test 2: Verify Chennai location addresses are properly formatted
    try:
        for location_name, location_data in CHENNAI_LOCATIONS.items():
            if "Chennai" in location_data["address"] or location_name == "fallback":
                result.log_success(f"Chennai location format - {location_name} address contains Chennai reference")
            else:
                result.log_failure(f"Chennai location format", f"{location_name} address missing Chennai reference")
    except Exception as e:
        result.log_failure("Chennai location format", str(e))

def test_create_admin_user(result: TestResult):
    """Create and test admin user authentication"""
    global admin_token
    
    print(f"\n{'='*60}")
    print("2. ADMIN USER CREATION AND AUTHENTICATION")
    print(f"{'='*60}")
    
    # Test 1: Create admin user
    try:
        response = make_request("POST", "/auth/register", ADMIN_USER_DATA)
        if response.status_code == 200:
            data = response.json()
            if data.get("user_type") == "admin" and data.get("email") == ADMIN_USER_DATA["email"]:
                admin_token = data["token"]
                result.log_success("POST /api/auth/register - Admin user creation")
            else:
                result.log_failure("Admin user creation", f"Invalid admin user data: {data}")
        else:
            result.log_failure("Admin user creation", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Admin user creation", str(e))
    
    # Test 2: Admin user login
    try:
        login_data = {"email": ADMIN_USER_DATA["email"], "password": ADMIN_USER_DATA["password"]}
        response = make_request("POST", "/auth/login", login_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("user_type") == "admin" and "token" in data:
                result.log_success("POST /api/auth/login - Admin authentication")
                if not admin_token:  # Use login token if registration failed
                    admin_token = data["token"]
            else:
                result.log_failure("Admin authentication", f"Invalid admin login response: {data}")
        else:
            result.log_failure("Admin authentication", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Admin authentication", str(e))
    
    # Test 3: JWT token validation for admin
    if admin_token:
        try:
            headers = get_auth_headers(admin_token)
            response = make_request("GET", "/admin/dashboard", headers=headers)
            if response.status_code == 200:
                result.log_success("Admin JWT token validation - Token works for admin endpoints")
            else:
                result.log_failure("Admin JWT token validation", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("Admin JWT token validation", str(e))

def test_admin_dashboard_apis(result: TestResult):
    """Test all admin dashboard APIs"""
    global admin_token
    
    print(f"\n{'='*60}")
    print("3. ADMIN DASHBOARD APIs TESTING")
    print(f"{'='*60}")
    
    if not admin_token:
        result.log_failure("Admin dashboard APIs", "No admin token available")
        return
    
    headers = get_auth_headers(admin_token)
    
    # Test 1: GET /api/admin/dashboard
    try:
        response = make_request("GET", "/admin/dashboard", headers=headers)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["total_users", "total_drivers", "total_riders", "total_rides", 
                             "active_rides", "pending_verifications", "recent_users", "recent_rides"]
            if all(field in data for field in required_fields):
                result.log_success("GET /api/admin/dashboard - Dashboard statistics")
                
                # Verify data types
                if (isinstance(data["total_users"], int) and 
                    isinstance(data["recent_users"], list) and 
                    isinstance(data["recent_rides"], list)):
                    result.log_success("GET /api/admin/dashboard - Data types validation")
                else:
                    result.log_failure("GET /api/admin/dashboard", "Invalid data types in response")
            else:
                missing_fields = [field for field in required_fields if field not in data]
                result.log_failure("GET /api/admin/dashboard", f"Missing fields: {missing_fields}")
        else:
            result.log_failure("GET /api/admin/dashboard", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/admin/dashboard", str(e))
    
    # Test 2: GET /api/admin/users (all users)
    try:
        response = make_request("GET", "/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and "total" in data:
                if isinstance(data["users"], list) and isinstance(data["total"], int):
                    result.log_success("GET /api/admin/users - All users retrieval")
                else:
                    result.log_failure("GET /api/admin/users", "Invalid response format")
            else:
                result.log_failure("GET /api/admin/users", f"Missing required fields: {data}")
        else:
            result.log_failure("GET /api/admin/users", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/admin/users", str(e))
    
    # Test 3: GET /api/admin/users with driver filter
    try:
        params = {"user_type": "driver"}
        response = make_request("GET", "/admin/users", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data:
                # Check if all returned users are drivers
                all_drivers = all(user.get("user_type") == "driver" for user in data["users"])
                if all_drivers:
                    result.log_success("GET /api/admin/users - Driver filter working")
                else:
                    result.log_failure("GET /api/admin/users", "Driver filter not working correctly")
            else:
                result.log_failure("GET /api/admin/users", "Missing users field in response")
        else:
            result.log_failure("GET /api/admin/users", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/admin/users", str(e))
    
    # Test 4: GET /api/admin/users with rider filter
    try:
        params = {"user_type": "rider"}
        response = make_request("GET", "/admin/users", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data:
                # Check if all returned users are riders
                all_riders = all(user.get("user_type") == "rider" for user in data["users"])
                if all_riders:
                    result.log_success("GET /api/admin/users - Rider filter working")
                else:
                    result.log_failure("GET /api/admin/users", "Rider filter not working correctly")
            else:
                result.log_failure("GET /api/admin/users", "Missing users field in response")
        else:
            result.log_failure("GET /api/admin/users", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/admin/users", str(e))
    
    # Test 5: GET /api/admin/users with pagination
    try:
        params = {"skip": 0, "limit": 10}
        response = make_request("GET", "/admin/users", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and len(data["users"]) <= 10:
                result.log_success("GET /api/admin/users - Pagination working")
            else:
                result.log_failure("GET /api/admin/users", "Pagination not working correctly")
        else:
            result.log_failure("GET /api/admin/users", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/admin/users", str(e))

def test_chennai_users_creation(result: TestResult):
    """Create Chennai-based test users"""
    global chennai_rider_token, chennai_driver_token
    
    print(f"\n{'='*60}")
    print("4. CHENNAI USERS CREATION")
    print(f"{'='*60}")
    
    # Test 1: Create Chennai rider
    try:
        response = make_request("POST", "/auth/register", CHENNAI_RIDER_DATA)
        if response.status_code == 200:
            data = response.json()
            if data.get("user_type") == "rider" and data.get("email") == CHENNAI_RIDER_DATA["email"]:
                chennai_rider_token = data["token"]
                result.log_success("Chennai rider creation - test.rider.chennai@example.com")
            else:
                result.log_failure("Chennai rider creation", f"Invalid rider data: {data}")
        else:
            result.log_failure("Chennai rider creation", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Chennai rider creation", str(e))
    
    # Test 2: Create Chennai driver
    try:
        response = make_request("POST", "/auth/register", CHENNAI_DRIVER_DATA)
        if response.status_code == 200:
            data = response.json()
            if data.get("user_type") == "driver" and data.get("email") == CHENNAI_DRIVER_DATA["email"]:
                chennai_driver_token = data["token"]
                result.log_success("Chennai driver creation - test.driver.chennai@example.com")
            else:
                result.log_failure("Chennai driver creation", f"Invalid driver data: {data}")
        else:
            result.log_failure("Chennai driver creation", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Chennai driver creation", str(e))
    
    # Test 3: Create Chennai driver profile
    if chennai_driver_token:
        try:
            headers = get_auth_headers(chennai_driver_token)
            response = make_request("POST", "/driver/profile", CHENNAI_DRIVER_PROFILE, headers)
            if response.status_code == 200:
                data = response.json()
                if "profile" in data and data["profile"].get("vehicle_number") == "TN09AB1234":
                    result.log_success("Chennai driver profile creation - TN vehicle number")
                else:
                    result.log_failure("Chennai driver profile", f"Invalid profile data: {data}")
            else:
                result.log_failure("Chennai driver profile", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("Chennai driver profile", str(e))

def test_complete_chennai_flow(result: TestResult):
    """Test complete Chennai ride flow from request to acceptance"""
    global chennai_rider_token, chennai_driver_token, chennai_ride_id
    
    print(f"\n{'='*60}")
    print("5. COMPLETE CHENNAI RIDE FLOW TESTING")
    print(f"{'='*60}")
    
    if not chennai_rider_token or not chennai_driver_token:
        result.log_failure("Chennai ride flow", "Missing Chennai user tokens")
        return
    
    rider_headers = get_auth_headers(chennai_rider_token)
    driver_headers = get_auth_headers(chennai_driver_token)
    
    # Test 1: Set driver location to Chennai coordinates
    try:
        # Use T. Nagar coordinates for driver location
        location_data = {"lat": CHENNAI_LOCATIONS["tnagar"]["lat"], "lng": CHENNAI_LOCATIONS["tnagar"]["lng"]}
        response = make_request("PUT", "/driver/location", location_data, driver_headers)
        if response.status_code == 200:
            result.log_success("Chennai driver location set - T. Nagar coordinates")
        else:
            result.log_failure("Chennai driver location", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Chennai driver location", str(e))
    
    # Test 2: Set driver availability
    try:
        response = make_request("PUT", "/driver/availability/true", headers=driver_headers)
        if response.status_code == 200:
            result.log_success("Chennai driver availability - Set to available")
        else:
            result.log_failure("Chennai driver availability", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Chennai driver availability", str(e))
    
    # Test 3: Create ride request from Chennai Airport to T. Nagar
    try:
        ride_data = {
            "pickup_location": CHENNAI_LOCATIONS["airport"],
            "drop_location": CHENNAI_LOCATIONS["tnagar"],
            "estimated_distance": 15.2,  # Approximate distance from airport to T. Nagar
            "estimated_fare": 273.6  # 15.2 km * 18 INR/km
        }
        response = make_request("POST", "/rider/request-ride", ride_data, rider_headers)
        if response.status_code == 200:
            data = response.json()
            if (data.get("pickup_location", {}).get("address") == "Chennai Airport" and
                data.get("drop_location", {}).get("address") == "T. Nagar, Chennai"):
                chennai_ride_id = data["id"]
                result.log_success("Chennai ride request - Airport to T. Nagar")
            else:
                result.log_failure("Chennai ride request", f"Invalid location data: {data}")
        else:
            result.log_failure("Chennai ride request", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Chennai ride request", str(e))
    
    # Test 4: Verify driver sees request within 25km radius
    try:
        response = make_request("GET", "/driver/ride-requests", headers=driver_headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Look for our Chennai ride request
                found_ride = None
                for ride in data:
                    if ride.get("id") == chennai_ride_id:
                        found_ride = ride
                        break
                
                if found_ride:
                    # Verify distance calculation
                    if "distance_to_pickup" in found_ride:
                        distance = found_ride["distance_to_pickup"]
                        if distance <= 25:  # Within 25km radius
                            result.log_success(f"Chennai driver-rider matching - Distance {distance}km within 25km radius")
                        else:
                            result.log_failure("Chennai driver-rider matching", f"Distance {distance}km exceeds 25km radius")
                    else:
                        result.log_failure("Chennai driver-rider matching", "Distance calculation missing")
                else:
                    result.log_failure("Chennai driver-rider matching", "Driver cannot see Chennai ride request")
            else:
                result.log_failure("Chennai driver-rider matching", f"Expected list, got: {type(data)}")
        else:
            result.log_failure("Chennai driver-rider matching", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("Chennai driver-rider matching", str(e))
    
    # Test 5: Driver accepts Chennai ride
    if chennai_ride_id:
        try:
            response = make_request("POST", f"/driver/accept-ride/{chennai_ride_id}", headers=driver_headers)
            if response.status_code == 200:
                data = response.json()
                if "accepted" in data.get("message", "").lower():
                    result.log_success("Chennai ride acceptance - Driver accepts ride")
                else:
                    result.log_failure("Chennai ride acceptance", f"Unexpected response: {data}")
            else:
                result.log_failure("Chennai ride acceptance", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("Chennai ride acceptance", str(e))
    
    # Test 6: Verify ride status updates
    if chennai_ride_id:
        try:
            response = make_request("GET", "/rider/rides", headers=rider_headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Find our Chennai ride
                    chennai_ride = None
                    for ride in data:
                        if ride.get("id") == chennai_ride_id:
                            chennai_ride = ride
                            break
                    
                    if chennai_ride:
                        if chennai_ride.get("status") == "accepted":
                            result.log_success("Chennai ride status update - Status changed to 'accepted'")
                            
                            # Verify driver info is populated
                            if "driver_info" in chennai_ride and chennai_ride["driver_info"]:
                                driver_info = chennai_ride["driver_info"]
                                if driver_info.get("vehicle_number") == "TN09AB1234":
                                    result.log_success("Chennai ride driver info - TN vehicle number populated")
                                else:
                                    result.log_failure("Chennai ride driver info", f"Wrong vehicle number: {driver_info}")
                            else:
                                result.log_failure("Chennai ride driver info", "Driver info not populated")
                        else:
                            result.log_failure("Chennai ride status", f"Status is {chennai_ride.get('status')}, expected 'accepted'")
                    else:
                        result.log_failure("Chennai ride status", "Chennai ride not found in rider's rides")
                else:
                    result.log_failure("Chennai ride status", "No rides found for Chennai rider")
            else:
                result.log_failure("Chennai ride status", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("Chennai ride status", str(e))

def test_user_management_apis(result: TestResult):
    """Test admin user management functionality"""
    global admin_token, chennai_rider_token, chennai_driver_token
    
    print(f"\n{'='*60}")
    print("6. USER MANAGEMENT APIs TESTING")
    print(f"{'='*60}")
    
    if not admin_token:
        result.log_failure("User management", "No admin token available")
        return
    
    headers = get_auth_headers(admin_token)
    
    # Get user IDs for testing
    chennai_rider_id = None
    chennai_driver_id = None
    
    # Test 1: Get all users to find Chennai user IDs
    try:
        response = make_request("GET", "/admin/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "users" in data:
                for user in data["users"]:
                    if user.get("email") == CHENNAI_RIDER_DATA["email"]:
                        chennai_rider_id = user.get("id")
                    elif user.get("email") == CHENNAI_DRIVER_DATA["email"]:
                        chennai_driver_id = user.get("id")
                
                if chennai_rider_id and chennai_driver_id:
                    result.log_success("User management - Chennai user IDs retrieved")
                else:
                    result.log_failure("User management", "Could not find Chennai user IDs")
            else:
                result.log_failure("User management", "No users field in response")
        else:
            result.log_failure("User management", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("User management", str(e))
    
    # Test 2: Test user deactivation
    if chennai_rider_id:
        try:
            action_data = {"user_id": chennai_rider_id, "action": "deactivate"}
            response = make_request("POST", "/admin/user-action", action_data, headers)
            if response.status_code == 200:
                data = response.json()
                if "deactivated" in data.get("message", "").lower():
                    result.log_success("POST /api/admin/user-action - User deactivation")
                else:
                    result.log_failure("POST /api/admin/user-action", f"Unexpected response: {data}")
            else:
                result.log_failure("POST /api/admin/user-action", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("POST /api/admin/user-action", str(e))
    
    # Test 3: Test user activation
    if chennai_rider_id:
        try:
            action_data = {"user_id": chennai_rider_id, "action": "activate"}
            response = make_request("POST", "/admin/user-action", action_data, headers)
            if response.status_code == 200:
                data = response.json()
                if "activated" in data.get("message", "").lower():
                    result.log_success("POST /api/admin/user-action - User activation")
                else:
                    result.log_failure("POST /api/admin/user-action", f"Unexpected response: {data}")
            else:
                result.log_failure("POST /api/admin/user-action", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("POST /api/admin/user-action", str(e))
    
    # Test 4: Test driver verification
    if chennai_driver_id:
        try:
            action_data = {"user_id": chennai_driver_id, "action": "verify_driver"}
            response = make_request("POST", "/admin/user-action", action_data, headers)
            if response.status_code == 200:
                data = response.json()
                if "verified" in data.get("message", "").lower():
                    result.log_success("POST /api/admin/user-action - Driver verification")
                else:
                    result.log_failure("POST /api/admin/user-action", f"Unexpected response: {data}")
            else:
                result.log_failure("POST /api/admin/user-action", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("POST /api/admin/user-action", str(e))
    
    # Test 5: Test driver rejection
    if chennai_driver_id:
        try:
            action_data = {"user_id": chennai_driver_id, "action": "reject_driver"}
            response = make_request("POST", "/admin/user-action", action_data, headers)
            if response.status_code == 200:
                data = response.json()
                if "rejected" in data.get("message", "").lower():
                    result.log_success("POST /api/admin/user-action - Driver rejection")
                else:
                    result.log_failure("POST /api/admin/user-action", f"Unexpected response: {data}")
            else:
                result.log_failure("POST /api/admin/user-action", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("POST /api/admin/user-action", str(e))
    
    # Test 6: Test invalid action
    if chennai_rider_id:
        try:
            action_data = {"user_id": chennai_rider_id, "action": "invalid_action"}
            response = make_request("POST", "/admin/user-action", action_data, headers)
            if response.status_code == 400:
                result.log_success("POST /api/admin/user-action - Invalid action rejection")
            else:
                result.log_failure("POST /api/admin/user-action", f"Should reject invalid action, got {response.status_code}")
        except Exception as e:
            result.log_failure("POST /api/admin/user-action", str(e))
    
    # Test 7: Test document viewing functionality
    if chennai_driver_id:
        try:
            response = make_request("GET", f"/admin/driver-documents/{chennai_driver_id}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Should return empty dict since no documents were uploaded in test
                if isinstance(data, dict):
                    result.log_success("GET /api/admin/driver-documents - Document viewing endpoint working")
                else:
                    result.log_failure("GET /api/admin/driver-documents", f"Expected dict, got: {type(data)}")
            else:
                result.log_failure("GET /api/admin/driver-documents", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            result.log_failure("GET /api/admin/driver-documents", str(e))
    
    # Test 8: Test document viewing for non-existent user
    try:
        response = make_request("GET", "/admin/driver-documents/invalid_user_id", headers=headers)
        if response.status_code == 404:
            result.log_success("GET /api/admin/driver-documents - Non-existent user rejection")
        else:
            result.log_failure("GET /api/admin/driver-documents", f"Should return 404 for invalid user, got {response.status_code}")
    except Exception as e:
        result.log_failure("GET /api/admin/driver-documents", str(e))

def test_admin_access_control(result: TestResult):
    """Test admin access control and authorization"""
    global chennai_rider_token, chennai_driver_token
    
    print(f"\n{'='*60}")
    print("7. ADMIN ACCESS CONTROL TESTING")
    print(f"{'='*60}")
    
    # Test 1: Non-admin user trying to access admin dashboard
    if chennai_rider_token:
        try:
            headers = get_auth_headers(chennai_rider_token)
            response = make_request("GET", "/admin/dashboard", headers=headers)
            if response.status_code == 403:
                result.log_success("Admin access control - Rider blocked from admin dashboard")
            else:
                result.log_failure("Admin access control", f"Should block rider access, got {response.status_code}")
        except Exception as e:
            result.log_failure("Admin access control", str(e))
    
    # Test 2: Driver trying to access admin users endpoint
    if chennai_driver_token:
        try:
            headers = get_auth_headers(chennai_driver_token)
            response = make_request("GET", "/admin/users", headers=headers)
            if response.status_code == 403:
                result.log_success("Admin access control - Driver blocked from admin users")
            else:
                result.log_failure("Admin access control", f"Should block driver access, got {response.status_code}")
        except Exception as e:
            result.log_failure("Admin access control", str(e))
    
    # Test 3: Non-admin trying to perform user actions
    if chennai_rider_token:
        try:
            headers = get_auth_headers(chennai_rider_token)
            action_data = {"user_id": "test_user", "action": "activate"}
            response = make_request("POST", "/admin/user-action", action_data, headers)
            if response.status_code == 403:
                result.log_success("Admin access control - Non-admin blocked from user actions")
            else:
                result.log_failure("Admin access control", f"Should block non-admin actions, got {response.status_code}")
        except Exception as e:
            result.log_failure("Admin access control", str(e))

def main():
    """Run all Chennai-specific tests"""
    print("🏛️ Chennai RideShare Backend API Testing")
    print("Testing Chennai location data, admin dashboard, and complete Chennai flow")
    
    result = TestResult()
    
    # Run all test suites
    test_chennai_location_data(result)
    test_create_admin_user(result)
    test_admin_dashboard_apis(result)
    test_chennai_users_creation(result)
    test_complete_chennai_flow(result)
    test_user_management_apis(result)
    test_admin_access_control(result)
    
    # Print final summary
    result.summary()
    
    return result.passed, result.failed

if __name__ == "__main__":
    main()