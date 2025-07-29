#!/usr/bin/env python3
"""
Test to verify the correct ride booking endpoints that work together
"""

import requests
import json
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://3be44877-be55-4f11-a89f-8fbc7e4df5e7.preview.emergentagent.com/api"
TIMEOUT = 30

def make_request(method: str, endpoint: str, data: Optional[Dict] = None, 
                headers: Optional[Dict] = None, params: Optional[Dict] = None) -> requests.Response:
    """Make HTTP request with proper error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

def get_auth_headers(token: str) -> Dict[str, str]:
    """Get authorization headers with Bearer token"""
    return {"Authorization": f"Bearer {token}"}

def create_test_rider_with_mobile_otp() -> Optional[str]:
    """Create a test rider user with mobile OTP"""
    test_phone = "+91 9876543210"
    
    # Step 1: Send OTP
    otp_data = {
        "phone_number": test_phone,
        "user_type": "rider"
    }
    response = make_request("POST", "/auth/send-otp", otp_data)
    if response.status_code != 200:
        print(f"❌ Failed to send OTP: {response.text}")
        return None
    
    data = response.json()
    demo_otp = data.get("demo_otp", "123456")
    
    # Step 2: Verify OTP
    verify_data = {
        "phone_number": test_phone,
        "otp_code": demo_otp,
        "user_type": "rider",
        "name": "Test Rider Fix"
    }
    response = make_request("POST", "/auth/verify-otp", verify_data)
    if response.status_code != 200:
        print(f"❌ Failed to verify OTP: {response.text}")
        return None
    
    data = response.json()
    if data.get("success") and data.get("token"):
        print("✅ Test rider created successfully")
        return data["token"]
    
    return None

def test_ride_booking_endpoints():
    """Test both ride booking endpoints to identify which one works correctly"""
    
    print("🔍 TESTING RIDE BOOKING ENDPOINTS CONSISTENCY")
    print("=" * 60)
    
    # Create test rider
    rider_token = create_test_rider_with_mobile_otp()
    if not rider_token:
        print("❌ Cannot proceed without rider token")
        return
    
    headers = get_auth_headers(rider_token)
    
    # Test data
    ride_data = {
        "pickup_location": {
            "lat": 13.0827,
            "lng": 80.2707,
            "address": "Chennai Central Railway Station"
        },
        "drop_location": {
            "lat": 13.0878,
            "lng": 80.2785,
            "address": "Marina Beach, Chennai"
        },
        "estimated_distance": 5.2,
        "estimated_fare": 156.0
    }
    
    print("\n--- Testing POST /api/rider/request-ride (saves to db.rides) ---")
    response1 = make_request("POST", "/rider/request-ride", ride_data, headers)
    print(f"Status: {response1.status_code}")
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ Ride created with ID: {data1.get('id')}")
        print(f"Response: {json.dumps(data1, indent=2, default=str)}")
    else:
        print(f"❌ Failed: {response1.text}")
    
    print("\n--- Testing POST /api/rider/rides (saves to db.ride_requests) ---")
    response2 = make_request("POST", "/rider/rides", ride_data, headers)
    print(f"Status: {response2.status_code}")
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Ride created with ID: {data2.get('id')}")
        print(f"Response: {json.dumps(data2, indent=2, default=str)}")
    else:
        print(f"❌ Failed: {response2.text}")
    
    print("\n--- Testing GET /api/rider/rides (reads from db.ride_requests) ---")
    response3 = make_request("GET", "/rider/rides", headers=headers)
    print(f"Status: {response3.status_code}")
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"✅ Found {len(data3)} rides in database")
        
        # Check if the ride from POST /rider/rides appears
        if response2.status_code == 200:
            ride2_id = response2.json().get('id')
            found_ride2 = any(ride.get('id') == ride2_id for ride in data3)
            if found_ride2:
                print(f"✅ Ride from POST /rider/rides found in GET /rider/rides")
            else:
                print(f"❌ Ride from POST /rider/rides NOT found in GET /rider/rides")
        
        # Check if the ride from POST /rider/request-ride appears
        if response1.status_code == 200:
            ride1_id = response1.json().get('id')
            found_ride1 = any(ride.get('id') == ride1_id for ride in data3)
            if found_ride1:
                print(f"✅ Ride from POST /rider/request-ride found in GET /rider/rides")
            else:
                print(f"❌ Ride from POST /rider/request-ride NOT found in GET /rider/rides")
        
        # Show sample rides
        if data3:
            print(f"\nSample ride from database:")
            print(json.dumps(data3[0], indent=2, default=str))
    else:
        print(f"❌ Failed: {response3.text}")
    
    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("=" * 60)
    
    if response2.status_code == 200 and response3.status_code == 200:
        ride2_id = response2.json().get('id')
        data3 = response3.json()
        found_ride2 = any(ride.get('id') == ride2_id for ride in data3)
        
        if found_ride2:
            print("✅ WORKING COMBINATION:")
            print("   - Use POST /api/rider/rides to create rides")
            print("   - Use GET /api/rider/rides to retrieve rides")
            print("   - Both use db.ride_requests collection")
        else:
            print("❌ ISSUE FOUND: Even the matching endpoints don't work together")
    
    if response1.status_code == 200 and response3.status_code == 200:
        ride1_id = response1.json().get('id')
        data3 = response3.json()
        found_ride1 = any(ride.get('id') == ride1_id for ride in data3)
        
        if not found_ride1:
            print("❌ BROKEN COMBINATION:")
            print("   - POST /api/rider/request-ride saves to db.rides collection")
            print("   - GET /api/rider/rides reads from db.ride_requests collection")
            print("   - This is why rides don't appear after creation!")

if __name__ == "__main__":
    test_ride_booking_endpoints()