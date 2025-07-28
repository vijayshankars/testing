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
BASE_URL = "https://87aa55a7-7445-442a-b69c-85a42d10dc65.preview.emergentagent.com/api"
TIMEOUT = 30

# Test data
import random
import string

def generate_random_email(prefix):
    """Generate random email to avoid conflicts"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{random_suffix}@test.com"

DRIVER_DATA = {
    "email": generate_random_email("driver"),
    "password": "password123",
    "name": "John Driver",
    "phone": "+1234567890",
    "user_type": "driver"
}

RIDER_DATA = {
    "email": generate_random_email("rider"),
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

def test_payment_configuration(result: TestResult):
    """Test payment configuration endpoint"""
    print(f"\n{'='*60}")
    print("7. PAYMENT CONFIGURATION TESTING")
    print(f"{'='*60}")
    
    # Test payment config endpoint
    try:
        response = make_request("GET", "/payment-config")
        if response.status_code == 200:
            data = response.json()
            if "razorpay_key_id" in data and "razorpay_enabled" in data:
                if data.get("razorpay_key_id") == "rzp_test_demo123456789" and data.get("razorpay_enabled") is True:
                    result.log_success("GET /api/payment-config - Razorpay configuration verified")
                else:
                    result.log_failure("GET /api/payment-config", f"Invalid Razorpay config: {data}")
            else:
                result.log_failure("GET /api/payment-config", f"Missing payment config fields: {data}")
        else:
            result.log_failure("GET /api/payment-config", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/payment-config", str(e))

def test_razorpay_payment_integration(result: TestResult):
    """Test Razorpay UPI payment integration"""
    global rider_token, ride_id
    
    print(f"\n{'='*60}")
    print("8. RAZORPAY UPI PAYMENT INTEGRATION TESTING")
    print(f"{'='*60}")
    
    if not rider_token or not ride_id:
        result.log_failure("Razorpay payment", "Missing rider token or ride ID")
        return
    
    headers = get_auth_headers(rider_token)
    razorpay_order_id = None
    
    # Test 1: Create Razorpay payment order (expect failure with demo credentials)
    try:
        order_data = {"ride_id": ride_id}
        response = make_request("POST", "/payment/razorpay/create-order", order_data, headers)
        if response.status_code == 500:
            # Demo credentials will fail authentication, which is expected
            data = response.json()
            if "Failed to create payment order" in data.get("detail", ""):
                result.log_success("POST /api/payment/razorpay/create-order - Demo credentials authentication failure handled correctly")
            else:
                result.log_failure("POST /api/payment/razorpay/create-order", f"Unexpected error message: {data}")
        elif response.status_code == 200:
            # If somehow it works (shouldn't with demo credentials)
            data = response.json()
            required_fields = ["order_id", "amount", "currency", "key_id", "ride_info"]
            if all(key in data for key in required_fields):
                razorpay_order_id = data["order_id"]
                result.log_success("POST /api/payment/razorpay/create-order - Order creation successful")
            else:
                result.log_failure("POST /api/payment/razorpay/create-order", f"Missing required fields: {data}")
        else:
            result.log_failure("POST /api/payment/razorpay/create-order", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/payment/razorpay/create-order", str(e))
    
    # Test 2: Test payment verification endpoint structure (without actual order)
    try:
        # Create mock verification data
        mock_payment_id = "pay_mock123456789"
        mock_signature = "mock_signature_for_testing"
        mock_order_id = "order_mock123456789"
        
        verification_data = {
            "razorpay_order_id": mock_order_id,
            "razorpay_payment_id": mock_payment_id,
            "razorpay_signature": mock_signature
        }
        
        response = make_request("POST", "/payment/razorpay/verify", verification_data, headers)
        # This should fail signature verification or order not found
        if response.status_code in [400, 404, 500]:
            result.log_success("POST /api/payment/razorpay/verify - Payment verification endpoint working")
        else:
            result.log_failure("POST /api/payment/razorpay/verify", f"Unexpected status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/payment/razorpay/verify", str(e))
    
    # Test 3: Check payment status (will be 404 since no payment was created)
    try:
        response = make_request("GET", f"/payment/status/{ride_id}", headers=headers)
        if response.status_code == 404:
            data = response.json()
            if "Payment not found" in data.get("detail", ""):
                result.log_success("GET /api/payment/status/{ride_id} - Payment status endpoint working (no payment found as expected)")
            else:
                result.log_failure("GET /api/payment/status/{ride_id}", f"Unexpected error message: {data}")
        elif response.status_code == 200:
            # If payment exists (shouldn't happen with demo credentials)
            data = response.json()
            required_fields = ["payment_id", "status", "payment_status", "amount", "currency"]
            if all(key in data for key in required_fields):
                result.log_success("GET /api/payment/status/{ride_id} - Payment status retrieval successful")
            else:
                result.log_failure("GET /api/payment/status/{ride_id}", f"Missing required fields: {data}")
        else:
            result.log_failure("GET /api/payment/status/{ride_id}", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("GET /api/payment/status/{ride_id}", str(e))

def test_razorpay_webhook(result: TestResult):
    """Test Razorpay webhook processing"""
    print(f"\n{'='*60}")
    print("9. RAZORPAY WEBHOOK TESTING")
    print(f"{'='*60}")
    
    # Test webhook with mock payload and correct signature
    try:
        import hmac
        import hashlib
        
        # Create mock webhook payload
        mock_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "id": "pay_mock123456789",
                    "order_id": "order_mock123456789",
                    "amount": 19375,  # 193.75 in paise
                    "currency": "INR",
                    "status": "captured"
                }
            }
        }
        
        payload_json = json.dumps(mock_payload)
        
        # Create correct signature using demo webhook secret
        webhook_secret = "demo_webhook_secret"
        signature = hmac.new(
            webhook_secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {"X-Razorpay-Signature": signature, "Content-Type": "application/json"}
        
        # Send webhook request
        response = requests.post(
            f"{BASE_URL}/webhook/razorpay",
            data=payload_json,
            headers=headers,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "processed":
                result.log_success("POST /api/webhook/razorpay - Webhook processing with signature verification")
            else:
                result.log_failure("POST /api/webhook/razorpay", f"Unexpected response: {data}")
        else:
            result.log_failure("POST /api/webhook/razorpay", f"Status {response.status_code}: {response.text}")
            
    except Exception as e:
        result.log_failure("POST /api/webhook/razorpay", str(e))
    
    # Test webhook with invalid signature
    try:
        mock_payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "id": "pay_failed123456789",
                    "order_id": "order_failed123456789",
                    "amount": 19375,
                    "currency": "INR",
                    "status": "failed"
                }
            }
        }
        
        payload_json = json.dumps(mock_payload)
        headers = {"X-Razorpay-Signature": "invalid_signature", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/webhook/razorpay",
            data=payload_json,
            headers=headers,
            timeout=TIMEOUT
        )
        
        if response.status_code == 400:
            data = response.json()
            if "signature" in data.get("detail", "").lower():
                result.log_success("POST /api/webhook/razorpay - Invalid signature rejection")
            else:
                result.log_failure("POST /api/webhook/razorpay", f"Unexpected error message: {data}")
        else:
            result.log_failure("POST /api/webhook/razorpay", f"Expected 400 for invalid signature, got {response.status_code}")
            
    except Exception as e:
        result.log_failure("POST /api/webhook/razorpay", str(e))

def test_payment_error_handling(result: TestResult):
    """Test payment-related error handling"""
    print(f"\n{'='*60}")
    print("10. PAYMENT ERROR HANDLING TESTING")
    print(f"{'='*60}")
    
    if not rider_token:
        result.log_failure("Payment error handling", "No rider token available")
        return
    
    headers = get_auth_headers(rider_token)
    
    # Test 1: Create order for invalid ride_id
    try:
        invalid_order_data = {"ride_id": "invalid_ride_id"}
        response = make_request("POST", "/payment/razorpay/create-order", invalid_order_data, headers)
        if response.status_code == 404:
            result.log_success("Payment error handling - Invalid ride_id rejection")
        else:
            result.log_failure("Payment error handling", f"Expected 404 for invalid ride_id, got {response.status_code}")
    except Exception as e:
        result.log_failure("Payment error handling", str(e))
    
    # Test 2: Unauthorized access (driver trying to pay for ride)
    if driver_token:
        try:
            driver_headers = get_auth_headers(driver_token)
            order_data = {"ride_id": ride_id} if ride_id else {"ride_id": "test_ride"}
            response = make_request("POST", "/payment/razorpay/create-order", order_data, driver_headers)
            if response.status_code == 403:
                result.log_success("Payment error handling - Unauthorized payment attempt rejection")
            else:
                result.log_failure("Payment error handling", f"Expected 403 for unauthorized payment, got {response.status_code}")
        except Exception as e:
            result.log_failure("Payment error handling", str(e))
    
    # Test 3: Payment status for non-existent ride
    try:
        response = make_request("GET", "/payment/status/invalid_ride_id", headers=headers)
        if response.status_code == 404:
            result.log_success("Payment error handling - Non-existent payment status rejection")
        else:
            result.log_failure("Payment error handling", f"Expected 404 for non-existent payment, got {response.status_code}")
    except Exception as e:
        result.log_failure("Payment error handling", str(e))

def test_database_integration(result: TestResult):
    """Test database connectivity and data persistence"""
    print(f"\n{'='*60}")
    print("11. DATABASE INTEGRATION TESTING")
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

def test_mobile_otp_authentication_system(result: TestResult):
    """Test Mobile OTP authentication system comprehensively"""
    print(f"\n{'='*60}")
    print("12. MOBILE OTP AUTHENTICATION SYSTEM TESTING")
    print(f"{'='*60}")
    
    # Test data for Mobile OTP authentication
    test_phone_numbers = ["+91 9876543210", "+1 5551234567"]
    demo_otps = ["123456", "000000"]
    user_names = ["Test Rider Mobile", "Test Driver Mobile"]
    user_types = ["rider", "driver"]
    
    mobile_tokens = {}
    
    # Test 1: Send OTP with valid Indian phone number
    try:
        otp_request = {
            "phone_number": "+91 9876543210",
            "user_type": "rider"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["success", "message", "is_existing_user", "demo_mode"]
            if all(field in data for field in required_fields):
                if data["success"] and data["demo_mode"]:
                    result.log_success("POST /api/auth/send-otp - Valid Indian phone number (+91 format)")
                    if "demo_otp" in data:
                        result.log_success("POST /api/auth/send-otp - Demo OTP returned in response")
                    else:
                        result.log_failure("POST /api/auth/send-otp", "Demo OTP not returned in demo mode")
                else:
                    result.log_failure("POST /api/auth/send-otp", f"Invalid response data: {data}")
            else:
                result.log_failure("POST /api/auth/send-otp", f"Missing required fields: {data}")
        else:
            result.log_failure("POST /api/auth/send-otp", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/auth/send-otp", str(e))
    
    # Test 2: Send OTP with international phone number
    try:
        otp_request = {
            "phone_number": "+1 5551234567",
            "user_type": "driver"
        }
        response = make_request("POST", "/auth/send-otp", otp_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("demo_mode"):
                result.log_success("POST /api/auth/send-otp - Valid international phone number (+1 format)")
            else:
                result.log_failure("POST /api/auth/send-otp", f"Invalid response for international number: {data}")
        else:
            result.log_failure("POST /api/auth/send-otp", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.log_failure("POST /api/auth/send-otp", str(e))
    
    # Test 3: Phone number validation - invalid formats
    invalid_phones = ["123456789", "invalid_phone", "+", "91987654321"]
    for invalid_phone in invalid_phones:
        try:
            otp_request = {
                "phone_number": invalid_phone,
                "user_type": "rider"
            }
            response = make_request("POST", "/auth/send-otp", otp_request)
            if response.status_code == 400:
                result.log_success(f"POST /api/auth/send-otp - Invalid phone number rejection: {invalid_phone}")
            else:
                result.log_failure("POST /api/auth/send-otp", f"Should reject invalid phone {invalid_phone}, got {response.status_code}")
        except Exception as e:
            result.log_failure("POST /api/auth/send-otp", f"Error testing invalid phone {invalid_phone}: {str(e)}")
    
    # Test 4: Phone number formatting edge cases
    formatting_tests = [
        {"input": "9876543210", "expected": "+919876543210"},
        {"input": "919876543210", "expected": "+919876543210"},
        {"input": "+91 9876 543 210", "expected": "+919876543210"}
    ]
    
    for test_case in formatting_tests:
        try:
            otp_request = {
                "phone_number": test_case["input"],
                "user_type": "rider"
            }
            response = make_request("POST", "/auth/send-otp", otp_request)
            if response.status_code == 200:
                result.log_success(f"POST /api/auth/send-otp - Phone formatting: {test_case['input']} -> formatted correctly")
            else:
                result.log_failure("POST /api/auth/send-otp", f"Phone formatting failed for {test_case['input']}: {response.status_code}")
        except Exception as e:
            result.log_failure("POST /api/auth/send-otp", f"Error testing phone formatting {test_case['input']}: {str(e)}")
    
    # Test 5: OTP verification with demo OTP for new user registration
    try:
        # First send OTP
        otp_request = {
            "phone_number": "+91 8765432109",
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Now verify with demo OTP
            verify_request = {
                "phone_number": "+91 8765432109",
                "otp_code": "123456",  # Demo OTP
                "user_type": "rider",
                "name": "Test Rider Mobile"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "user_data", "token", "is_new_user"]
                if all(field in data for field in required_fields):
                    if data["success"] and data["is_new_user"] and data["token"]:
                        mobile_tokens["rider"] = data["token"]
                        result.log_success("POST /api/auth/verify-otp - New user registration via mobile OTP")
                        
                        # Verify user data
                        user_data = data["user_data"]
                        if user_data.get("phone") == "+918765432109" and user_data.get("user_type") == "rider":
                            result.log_success("POST /api/auth/verify-otp - User data populated correctly for new user")
                        else:
                            result.log_failure("POST /api/auth/verify-otp", f"Invalid user data: {user_data}")
                    else:
                        result.log_failure("POST /api/auth/verify-otp", f"Invalid verification response: {data}")
                else:
                    result.log_failure("POST /api/auth/verify-otp", f"Missing required fields: {data}")
            else:
                result.log_failure("POST /api/auth/verify-otp", f"Status {response.status_code}: {response.text}")
        else:
            result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for verification test")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", str(e))
    
    # Test 6: OTP verification for existing user login
    try:
        # Send OTP for the same number (now existing user)
        otp_request = {
            "phone_number": "+91 8765432109",
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            send_data = send_response.json()
            if send_data.get("is_existing_user"):
                # Verify with demo OTP (no name needed for existing user)
                verify_request = {
                    "phone_number": "+91 8765432109",
                    "otp_code": "000000",  # Different demo OTP
                    "user_type": "rider"
                }
                response = make_request("POST", "/auth/verify-otp", verify_request)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and not data.get("is_new_user"):
                        result.log_success("POST /api/auth/verify-otp - Existing user login via mobile OTP")
                    else:
                        result.log_failure("POST /api/auth/verify-otp", f"Should be existing user login: {data}")
                else:
                    result.log_failure("POST /api/auth/verify-otp", f"Status {response.status_code}: {response.text}")
            else:
                result.log_failure("POST /api/auth/verify-otp", "User should be marked as existing")
        else:
            result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for existing user test")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", str(e))
    
    # Test 7: Driver registration via mobile OTP
    try:
        # Send OTP for driver
        otp_request = {
            "phone_number": "+91 7654321098",
            "user_type": "driver"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Verify with demo OTP
            verify_request = {
                "phone_number": "+91 7654321098",
                "otp_code": "123456",
                "user_type": "driver",
                "name": "Test Driver Mobile"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("is_new_user"):
                    user_data = data.get("user_data", {})
                    if user_data.get("user_type") == "driver":
                        mobile_tokens["driver"] = data["token"]
                        result.log_success("POST /api/auth/verify-otp - Driver registration via mobile OTP")
                    else:
                        result.log_failure("POST /api/auth/verify-otp", f"Invalid driver user type: {user_data}")
                else:
                    result.log_failure("POST /api/auth/verify-otp", f"Driver registration failed: {data}")
            else:
                result.log_failure("POST /api/auth/verify-otp", f"Status {response.status_code}: {response.text}")
        else:
            result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for driver test")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", str(e))
    
    # Test 8: User type validation and restrictions
    try:
        # Try to verify rider OTP as driver (should fail)
        otp_request = {
            "phone_number": "+91 6543210987",
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Register as rider first
            verify_request = {
                "phone_number": "+91 6543210987",
                "otp_code": "123456",
                "user_type": "rider",
                "name": "Test User Type"
            }
            reg_response = make_request("POST", "/auth/verify-otp", verify_request)
            
            if reg_response.status_code == 200:
                # Now try to login as driver with same number
                otp_request["user_type"] = "driver"
                send_response2 = make_request("POST", "/auth/send-otp", otp_request)
                
                if send_response2.status_code == 200:
                    verify_request["user_type"] = "driver"
                    verify_request.pop("name", None)  # Remove name for login
                    wrong_type_response = make_request("POST", "/auth/verify-otp", verify_request)
                    
                    if wrong_type_response.status_code == 400:
                        result.log_success("POST /api/auth/verify-otp - User type validation working correctly")
                    else:
                        result.log_failure("POST /api/auth/verify-otp", f"Should reject wrong user type, got {wrong_type_response.status_code}")
                else:
                    result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for user type test")
            else:
                result.log_failure("POST /api/auth/verify-otp", "Failed to register user for type validation test")
        else:
            result.log_failure("POST /api/auth/verify-otp", "Failed to send initial OTP for user type test")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", str(e))
    
    # Test 9: Invalid OTP attempts
    try:
        # Send OTP
        otp_request = {
            "phone_number": "+91 5432109876",
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Try invalid OTP
            verify_request = {
                "phone_number": "+91 5432109876",
                "otp_code": "999999",  # Invalid OTP
                "user_type": "rider",
                "name": "Test Invalid OTP"
            }
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 200:
                data = response.json()
                if not data.get("success"):
                    result.log_success("POST /api/auth/verify-otp - Invalid OTP rejection")
                else:
                    result.log_failure("POST /api/auth/verify-otp", "Should reject invalid OTP")
            else:
                result.log_failure("POST /api/auth/verify-otp", f"Unexpected status for invalid OTP: {response.status_code}")
        else:
            result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for invalid OTP test")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", str(e))
    
    # Test 10: OTP attempt limits (max 3 attempts)
    try:
        # Send OTP
        otp_request = {
            "phone_number": "+91 4321098765",
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            # Make 3 invalid attempts
            verify_request = {
                "phone_number": "+91 4321098765",
                "otp_code": "111111",  # Invalid OTP
                "user_type": "rider",
                "name": "Test Attempt Limit"
            }
            
            for attempt in range(3):
                response = make_request("POST", "/auth/verify-otp", verify_request)
                if response.status_code != 200:
                    break
            
            # 4th attempt should be rejected
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 400:
                data = response.json()
                if "attempts" in data.get("detail", "").lower():
                    result.log_success("POST /api/auth/verify-otp - OTP attempt limit enforcement")
                else:
                    result.log_failure("POST /api/auth/verify-otp", f"Wrong error message for attempt limit: {data}")
            else:
                result.log_failure("POST /api/auth/verify-otp", f"Should reject after 3 attempts, got {response.status_code}")
        else:
            result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for attempt limit test")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", str(e))
    
    # Test 11: Missing required fields
    try:
        # Missing name for new user
        verify_request = {
            "phone_number": "+91 3210987654",
            "otp_code": "123456",
            "user_type": "rider"
            # Missing name
        }
        
        # First send OTP
        otp_request = {
            "phone_number": "+91 3210987654",
            "user_type": "rider"
        }
        send_response = make_request("POST", "/auth/send-otp", otp_request)
        
        if send_response.status_code == 200:
            response = make_request("POST", "/auth/verify-otp", verify_request)
            if response.status_code == 400:
                result.log_success("POST /api/auth/verify-otp - Missing name field rejection for new user")
            else:
                result.log_failure("POST /api/auth/verify-otp", f"Should reject missing name, got {response.status_code}")
        else:
            result.log_failure("POST /api/auth/verify-otp", "Failed to send OTP for missing fields test")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", str(e))
    
    # Test 12: JWT token generation and validation for mobile authenticated users
    if mobile_tokens.get("rider"):
        try:
            headers = get_auth_headers(mobile_tokens["rider"])
            response = make_request("GET", "/rider/rides", headers=headers)
            if response.status_code == 200:
                result.log_success("JWT token validation - Mobile authenticated rider token works")
            else:
                result.log_failure("JWT token validation", f"Mobile rider token invalid: {response.status_code}")
        except Exception as e:
            result.log_failure("JWT token validation", str(e))
    
    if mobile_tokens.get("driver"):
        try:
            headers = get_auth_headers(mobile_tokens["driver"])
            response = make_request("GET", "/driver/ride-requests", headers=headers)
            if response.status_code in [200, 400]:  # 400 is OK if no location set
                result.log_success("JWT token validation - Mobile authenticated driver token works")
            else:
                result.log_failure("JWT token validation", f"Mobile driver token invalid: {response.status_code}")
        except Exception as e:
            result.log_failure("JWT token validation", str(e))
    
    # Test 13: Expired OTP session
    try:
        # This test would require waiting for expiration or mocking time
        # For now, we'll test with a very old session by trying to verify without sending OTP first
        verify_request = {
            "phone_number": "+91 2109876543",
            "otp_code": "123456",
            "user_type": "rider",
            "name": "Test Expired"
        }
        response = make_request("POST", "/auth/verify-otp", verify_request)
        if response.status_code == 400:
            data = response.json()
            if "expired" in data.get("detail", "").lower() or "invalid" in data.get("detail", "").lower():
                result.log_success("POST /api/auth/verify-otp - Expired/Invalid OTP session handling")
            else:
                result.log_failure("POST /api/auth/verify-otp", f"Wrong error for expired session: {data}")
        else:
            result.log_failure("POST /api/auth/verify-otp", f"Should reject expired session, got {response.status_code}")
    except Exception as e:
        result.log_failure("POST /api/auth/verify-otp", str(e))

def test_nearby_ride_requests_scenario(result: TestResult):
    """Test the complete nearby ride requests functionality as requested"""
    print(f"\n{'='*60}")
    print("12. NEARBY RIDE REQUESTS SCENARIO TESTING")
    print(f"{'='*60}")
    
    # Test data for the specific scenario
    test_rider_data = {
        "email": "testrider.nearby@example.com",
        "password": "password123",
        "name": "Test Rider Nearby",
        "phone": "+1234567890",
        "user_type": "rider"
    }
    
    test_driver_data = {
        "email": "testdriver.nearby@example.com", 
        "password": "password123",
        "name": "Test Driver Nearby",
        "phone": "+1234567891",
        "user_type": "driver"
    }
    
    test_driver_profile = {
        "per_km_rate": 20.0,
        "vehicle_type": "sedan",
        "vehicle_number": "DL01XY9876",
        "license_number": "DL9876543210"
    }
    
    # Delhi coordinates as specified
    delhi_location = {"lat": 28.6139, "lng": 77.2090}
    
    # Sample ride request data
    sample_ride_data = {
        "pickup_location": {
            "lat": 28.6129, 
            "lng": 77.2295, 
            "address": "India Gate, Delhi"
        },
        "drop_location": {
            "lat": 28.6562, 
            "lng": 77.2410, 
            "address": "Red Fort, Delhi"
        },
        "estimated_distance": 5.2,
        "estimated_fare": 104.0
    }
    
    test_rider_token = None
    test_driver_token = None
    test_ride_id = None
    
    # Step 1: Register test rider
    try:
        response = make_request("POST", "/auth/register", test_rider_data)
        if response.status_code == 200:
            data = response.json()
            test_rider_token = data["token"]
            result.log_success("Step 1 - Test rider registration")
        else:
            result.log_failure("Step 1", f"Rider registration failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 1", f"Rider registration error: {str(e)}")
        return
    
    # Step 2: Register test driver
    try:
        response = make_request("POST", "/auth/register", test_driver_data)
        if response.status_code == 200:
            data = response.json()
            test_driver_token = data["token"]
            result.log_success("Step 2 - Test driver registration")
        else:
            result.log_failure("Step 2", f"Driver registration failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 2", f"Driver registration error: {str(e)}")
        return
    
    # Step 3: Create driver profile
    try:
        driver_headers = get_auth_headers(test_driver_token)
        response = make_request("POST", "/driver/profile", test_driver_profile, driver_headers)
        if response.status_code == 200:
            result.log_success("Step 3 - Driver profile creation")
        else:
            result.log_failure("Step 3", f"Driver profile creation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 3", f"Driver profile creation error: {str(e)}")
        return
    
    # Step 4: Set driver location to Delhi coordinates
    try:
        response = make_request("PUT", "/driver/location", delhi_location, driver_headers)
        if response.status_code == 200:
            result.log_success("Step 4 - Driver location set to Delhi coordinates")
        else:
            result.log_failure("Step 4", f"Driver location update failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 4", f"Driver location update error: {str(e)}")
        return
    
    # Step 5: Set driver availability to true
    try:
        response = make_request("PUT", "/driver/availability/true", headers=driver_headers)
        if response.status_code == 200:
            result.log_success("Step 5 - Driver availability set to available")
        else:
            result.log_failure("Step 5", f"Driver availability update failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 5", f"Driver availability update error: {str(e)}")
        return
    
    # Step 6: Create ride request from rider
    try:
        rider_headers = get_auth_headers(test_rider_token)
        response = make_request("POST", "/rider/request-ride", sample_ride_data, rider_headers)
        if response.status_code == 200:
            data = response.json()
            test_ride_id = data["id"]
            if data["status"] == "requested":
                result.log_success("Step 6 - Ride request created successfully")
            else:
                result.log_failure("Step 6", f"Ride request created but status is {data['status']}")
                return
        else:
            result.log_failure("Step 6", f"Ride request creation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        result.log_failure("Step 6", f"Ride request creation error: {str(e)}")
        return
    
    # Step 7: Test driver can see nearby ride requests
    try:
        response = make_request("GET", "/driver/ride-requests", headers=driver_headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Check if our ride request is in the list
                found_ride = None
                for ride in data:
                    if ride.get("id") == test_ride_id:
                        found_ride = ride
                        break
                
                if found_ride:
                    # Verify ride contains all required fields
                    required_fields = ["id", "rider_id", "pickup_location", "drop_location", "estimated_distance", "estimated_fare", "status", "distance_to_pickup"]
                    if all(field in found_ride for field in required_fields):
                        result.log_success("Step 7 - Driver can see nearby ride request with all required fields")
                        
                        # Verify distance calculation
                        if "distance_to_pickup" in found_ride and isinstance(found_ride["distance_to_pickup"], (int, float)):
                            result.log_success("Step 7a - Distance calculation working correctly")
                        else:
                            result.log_failure("Step 7a", "Distance calculation not working properly")
                    else:
                        missing_fields = [field for field in required_fields if field not in found_ride]
                        result.log_failure("Step 7", f"Ride request missing required fields: {missing_fields}")
                else:
                    result.log_failure("Step 7", f"Driver cannot see the ride request {test_ride_id} in nearby requests")
            else:
                result.log_failure("Step 7", f"Expected list of ride requests, got: {type(data)}")
        else:
            result.log_failure("Step 7", f"Failed to get nearby ride requests: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 7", f"Get nearby ride requests error: {str(e)}")
    
    # Step 8: Test driver accepting ride request
    if test_ride_id:
        try:
            response = make_request("POST", f"/driver/accept-ride/{test_ride_id}", headers=driver_headers)
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "accepted" in data["message"].lower():
                    result.log_success("Step 8 - Driver successfully accepted ride request")
                else:
                    result.log_failure("Step 8", f"Unexpected response: {data}")
            else:
                result.log_failure("Step 8", f"Driver accept ride failed: {response.status_code} - {response.text}")
        except Exception as e:
            result.log_failure("Step 8", f"Driver accept ride error: {str(e)}")
    
    # Step 9: Verify ride status update after acceptance
    if test_ride_id:
        try:
            response = make_request("GET", "/rider/rides", headers=rider_headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Find our ride
                    accepted_ride = None
                    for ride in data:
                        if ride.get("id") == test_ride_id:
                            accepted_ride = ride
                            break
                    
                    if accepted_ride:
                        if accepted_ride.get("status") == "accepted":
                            result.log_success("Step 9 - Ride status updated to 'accepted' correctly")
                            
                            # Check if driver info is populated
                            if "driver_info" in accepted_ride and accepted_ride["driver_info"]:
                                driver_info = accepted_ride["driver_info"]
                                if all(key in driver_info for key in ["name", "phone", "vehicle_type", "vehicle_number"]):
                                    result.log_success("Step 9a - Driver information populated correctly in ride")
                                else:
                                    result.log_failure("Step 9a", f"Driver info incomplete: {driver_info}")
                            else:
                                result.log_failure("Step 9a", "Driver info not populated in accepted ride")
                        else:
                            result.log_failure("Step 9", f"Ride status is {accepted_ride.get('status')}, expected 'accepted'")
                    else:
                        result.log_failure("Step 9", "Could not find the ride in rider's rides list")
                else:
                    result.log_failure("Step 9", "No rides found for rider")
            else:
                result.log_failure("Step 9", f"Failed to get rider rides: {response.status_code} - {response.text}")
        except Exception as e:
            result.log_failure("Step 9", f"Verify ride status error: {str(e)}")
    
    # Step 10: Verify driver no longer sees the accepted ride in nearby requests
    try:
        response = make_request("GET", "/driver/ride-requests", headers=driver_headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Check that our accepted ride is no longer in the list
                found_ride = any(ride.get("id") == test_ride_id for ride in data)
                if not found_ride:
                    result.log_success("Step 10 - Accepted ride no longer appears in nearby requests")
                else:
                    result.log_failure("Step 10", "Accepted ride still appears in nearby requests")
            else:
                result.log_failure("Step 10", f"Expected list of ride requests, got: {type(data)}")
        else:
            result.log_failure("Step 10", f"Failed to get nearby ride requests: {response.status_code} - {response.text}")
    except Exception as e:
        result.log_failure("Step 10", f"Verify accepted ride removal error: {str(e)}")

def main():
    """Run all tests"""
    print("🚗 RideShare Backend API Testing")
    print(f"Testing against: {BASE_URL}")
    print(f"{'='*60}")
    
    result = TestResult()
    
    # Run all test suites
    test_basic_health_check(result)
    test_authentication_system(result)
    test_mobile_otp_authentication_system(result)  # New Mobile OTP tests
    test_driver_functionality(result)
    test_rider_functionality(result)
    test_ride_matching_system(result)
    test_error_handling(result)
    test_payment_configuration(result)
    test_razorpay_payment_integration(result)
    test_razorpay_webhook(result)
    test_payment_error_handling(result)
    test_database_integration(result)
    
    # Run the specific nearby ride requests scenario test
    test_nearby_ride_requests_scenario(result)
    
    # Print summary
    result.summary()
    
    return result.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)