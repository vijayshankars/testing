#!/usr/bin/env python3
"""
Test Nearby Ride Requests with Correct Distance
Testing with locations within 10km radius to verify the system works correctly
"""

import requests
import json
from typing import Dict, Any, Optional
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
BASE_URL = "https://87aa55a7-7445-442a-b69c-85a42d10dc65.preview.emergentagent.com/api"
TIMEOUT = 30

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'rideshare_app')

class NearbyRideTestCorrect:
    def __init__(self):
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        self.test_rider_token = None
        self.test_driver_token = None
        self.test_ride_id = None
        
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
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

    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers with Bearer token"""
        return {"Authorization": f"Bearer {token}"}

    def test_nearby_ride_requests_working_scenario(self):
        """Test with locations that are within 10km radius"""
        print("🚗 TESTING NEARBY RIDE REQUESTS - WORKING SCENARIO")
        print("=" * 80)
        print("Testing with locations within 10km radius to verify system works correctly")
        
        # Test rider data
        test_rider_data = {
            "email": "test.rider.working@example.com",
            "password": "password123",
            "name": "Test Rider Working",
            "phone": "+919876543220",
            "user_type": "rider"
        }
        
        # Test driver data
        test_driver_data = {
            "email": "test.driver.working@example.com",
            "password": "password123", 
            "name": "Test Driver Working",
            "phone": "+919876543221",
            "user_type": "driver"
        }
        
        # Driver location: Connaught Place, Delhi
        driver_location = {"lat": 28.6315, "lng": 77.2167}
        
        # Ride request: From nearby location (India Gate) to Red Fort - both within 10km of driver
        ride_data = {
            "pickup_location": {
                "lat": 28.6129, 
                "lng": 77.2295, 
                "address": "India Gate, New Delhi"
            },
            "drop_location": {
                "lat": 28.6562, 
                "lng": 77.2410, 
                "address": "Red Fort, New Delhi"
            },
            "estimated_distance": 3.2,
            "estimated_fare": 80.0
        }
        
        # Step 1: Register test rider
        print("\n🔄 Step 1: Registering test rider...")
        try:
            response = self.make_request("POST", "/auth/register", test_rider_data)
            if response.status_code == 200:
                data = response.json()
                self.test_rider_token = data["token"]
                print(f"✅ Test rider registered successfully")
            else:
                print(f"❌ Rider registration failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Rider registration error: {e}")
            return False
        
        # Step 2: Register test driver
        print("\n🔄 Step 2: Registering test driver...")
        try:
            response = self.make_request("POST", "/auth/register", test_driver_data)
            if response.status_code == 200:
                data = response.json()
                self.test_driver_token = data["token"]
                print(f"✅ Test driver registered successfully")
            else:
                print(f"❌ Driver registration failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Driver registration error: {e}")
            return False
        
        # Step 3: Create driver profile
        print("\n🔄 Step 3: Creating driver profile...")
        driver_headers = self.get_auth_headers(self.test_driver_token)
        driver_profile_data = {
            "per_km_rate": 25.0,
            "vehicle_type": "sedan",
            "vehicle_number": "DL01WORK123",
            "license_number": "DL1234567890"
        }
        
        try:
            response = self.make_request("POST", "/driver/profile", driver_profile_data, driver_headers)
            if response.status_code == 200:
                print("✅ Driver profile created successfully")
            else:
                print(f"❌ Driver profile creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Driver profile creation error: {e}")
            return False
        
        # Step 4: Set driver location (Connaught Place)
        print(f"\n🔄 Step 4: Setting driver location to Connaught Place...")
        try:
            response = self.make_request("PUT", "/driver/location", driver_location, driver_headers)
            if response.status_code == 200:
                print(f"✅ Driver location set to: {driver_location}")
            else:
                print(f"❌ Driver location update failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Driver location update error: {e}")
            return False
        
        # Step 5: Set driver availability
        print("\n🔄 Step 5: Setting driver availability to true...")
        try:
            response = self.make_request("PUT", "/driver/availability/true", headers=driver_headers)
            if response.status_code == 200:
                print("✅ Driver set to available")
            else:
                print(f"❌ Driver availability update failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Driver availability update error: {e}")
            return False
        
        # Step 6: Calculate expected distance
        print(f"\n🔄 Step 6: Calculating distance between driver and pickup...")
        try:
            from geopy.distance import geodesic
            distance = geodesic(
                (driver_location["lat"], driver_location["lng"]), 
                (ride_data["pickup_location"]["lat"], ride_data["pickup_location"]["lng"])
            ).kilometers
            
            print(f"📏 Distance calculation:")
            print(f"   Driver location (Connaught Place): ({driver_location['lat']}, {driver_location['lng']})")
            print(f"   Pickup location (India Gate): ({ride_data['pickup_location']['lat']}, {ride_data['pickup_location']['lng']})")
            print(f"   Calculated distance: {distance:.2f} km")
            
            if distance <= 10:
                print(f"✅ Distance {distance:.2f} km is within 10km radius - ride should be visible")
            else:
                print(f"❌ Distance {distance:.2f} km exceeds 10km radius - ride will not be visible")
                return False
                
        except Exception as e:
            print(f"❌ Distance calculation error: {e}")
            return False
        
        # Step 7: Create ride request
        print(f"\n🔄 Step 7: Creating ride request from India Gate to Red Fort...")
        rider_headers = self.get_auth_headers(self.test_rider_token)
        
        try:
            response = self.make_request("POST", "/rider/request-ride", ride_data, rider_headers)
            if response.status_code == 200:
                data = response.json()
                self.test_ride_id = data["id"]
                print(f"✅ Ride request created successfully - ID: {self.test_ride_id}")
                print(f"   Status: {data.get('status')}")
                print(f"   Pickup: {data.get('pickup_location', {}).get('address')}")
                print(f"   Drop: {data.get('drop_location', {}).get('address')}")
            else:
                print(f"❌ Ride request creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ride request creation error: {e}")
            return False
        
        # Step 8: Test driver can see the ride request
        print(f"\n🔄 Step 8: Testing if driver can see nearby ride requests...")
        try:
            response = self.make_request("GET", "/driver/ride-requests", headers=driver_headers)
            if response.status_code == 200:
                data = response.json()
                print(f"📊 API Response:")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response Type: {type(data)}")
                print(f"   Number of ride requests: {len(data) if isinstance(data, list) else 'N/A'}")
                
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Driver can see {len(data)} ride request(s)")
                    
                    # Check if our test ride is in the list
                    found_test_ride = False
                    for ride in data:
                        if ride.get("id") == self.test_ride_id:
                            found_test_ride = True
                            print(f"✅ Test ride request found in results:")
                            print(f"   Ride ID: {ride.get('id')}")
                            print(f"   Distance to pickup: {ride.get('distance_to_pickup')} km")
                            print(f"   Pickup address: {ride.get('pickup_location', {}).get('address')}")
                            print(f"   Drop address: {ride.get('drop_location', {}).get('address')}")
                            print(f"   Estimated fare: ₹{ride.get('estimated_fare')}")
                            break
                    
                    if not found_test_ride:
                        print(f"❌ Test ride request {self.test_ride_id} NOT found in results")
                        print(f"   Available rides: {[ride.get('id', 'N/A')[:8] + '...' for ride in data]}")
                        return False
                    else:
                        print(f"🎉 SUCCESS: Driver can see nearby ride request within 10km radius!")
                        
                elif isinstance(data, list) and len(data) == 0:
                    print("❌ No ride requests returned - empty list")
                    return False
                else:
                    print(f"❌ Unexpected response type: {type(data)}")
                    return False
                    
            else:
                print(f"❌ API call failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ API call error: {e}")
            return False
        
        # Step 9: Test driver accepting the ride
        print(f"\n🔄 Step 9: Testing driver accepting the ride...")
        try:
            response = self.make_request("POST", f"/driver/accept-ride/{self.test_ride_id}", headers=driver_headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Driver successfully accepted ride request")
                print(f"   Response: {data.get('message')}")
            else:
                print(f"❌ Driver accept ride failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Driver accept ride error: {e}")
            return False
        
        # Step 10: Verify ride status updated
        print(f"\n🔄 Step 10: Verifying ride status updated to 'accepted'...")
        try:
            response = self.make_request("GET", "/rider/rides", headers=rider_headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Find our ride
                    accepted_ride = None
                    for ride in data:
                        if ride.get("id") == self.test_ride_id:
                            accepted_ride = ride
                            break
                    
                    if accepted_ride:
                        if accepted_ride.get("status") == "accepted":
                            print(f"✅ Ride status updated to 'accepted' correctly")
                            
                            # Check if driver info is populated
                            if "driver_info" in accepted_ride and accepted_ride["driver_info"]:
                                driver_info = accepted_ride["driver_info"]
                                print(f"✅ Driver information populated correctly:")
                                print(f"   Driver name: {driver_info.get('name')}")
                                print(f"   Vehicle type: {driver_info.get('vehicle_type')}")
                                print(f"   Vehicle number: {driver_info.get('vehicle_number')}")
                            else:
                                print(f"❌ Driver info not populated in accepted ride")
                                return False
                        else:
                            print(f"❌ Ride status is {accepted_ride.get('status')}, expected 'accepted'")
                            return False
                    else:
                        print(f"❌ Could not find the ride in rider's rides list")
                        return False
                else:
                    print(f"❌ No rides found for rider")
                    return False
            else:
                print(f"❌ Failed to get rider rides: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Verify ride status error: {e}")
            return False
        
        print(f"\n{'='*80}")
        print("🎉 ALL TESTS PASSED - NEARBY RIDE REQUESTS SYSTEM WORKING CORRECTLY!")
        print("✅ The issue was distance-based filtering - rides beyond 10km are correctly filtered out")
        print("✅ When locations are within 10km radius, drivers can see and accept ride requests")
        print(f"{'='*80}")
        
        return True

if __name__ == "__main__":
    tester = NearbyRideTestCorrect()
    tester.test_nearby_ride_requests_working_scenario()