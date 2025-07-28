#!/usr/bin/env python3
"""
Debug Nearby Ride Requests Issue
Comprehensive investigation of why drivers aren't seeing existing ride requests
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
BASE_URL = "https://87aa55a7-7445-442a-b69c-85a42d10dc65.preview.emergentagent.com/api"
TIMEOUT = 30

# MongoDB connection for direct database queries
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'rideshare_app')

class RideRequestDebugger:
    def __init__(self):
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        self.test_rider_token = None
        self.test_driver_token = None
        self.test_rider_id = None
        self.test_driver_id = None
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

    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")

    def check_database_state(self):
        """Check current database state for ride requests"""
        self.print_section("1. CHECKING CURRENT DATABASE STATE")
        
        try:
            # Query all ride requests
            ride_requests = list(self.db.ride_requests.find({}, {"_id": 0}))
            print(f"📊 Total ride requests in database: {len(ride_requests)}")
            
            if ride_requests:
                print("\n🔍 Existing ride requests:")
                for i, ride in enumerate(ride_requests, 1):
                    print(f"\n--- Ride Request {i} ---")
                    print(f"ID: {ride.get('id', 'N/A')}")
                    print(f"Status: {ride.get('status', 'N/A')}")
                    print(f"Rider ID: {ride.get('rider_id', 'N/A')}")
                    print(f"Driver ID: {ride.get('driver_id', 'N/A')}")
                    print(f"Created: {ride.get('created_at', 'N/A')}")
                    
                    # Check pickup location format
                    pickup = ride.get('pickup_location', {})
                    print(f"Pickup Location: {pickup}")
                    if isinstance(pickup, dict) and 'lat' in pickup and 'lng' in pickup:
                        print(f"  ✅ Pickup coordinates: ({pickup['lat']}, {pickup['lng']})")
                    else:
                        print(f"  ❌ Invalid pickup location format")
                    
                    # Check drop location format
                    drop = ride.get('drop_location', {})
                    print(f"Drop Location: {drop}")
                    if isinstance(drop, dict) and 'lat' in drop and 'lng' in drop:
                        print(f"  ✅ Drop coordinates: ({drop['lat']}, {drop['lng']})")
                    else:
                        print(f"  ❌ Invalid drop location format")
            else:
                print("📭 No ride requests found in database")
            
            # Query all driver profiles
            driver_profiles = list(self.db.driver_profiles.find({}, {"_id": 0}))
            print(f"\n📊 Total driver profiles in database: {len(driver_profiles)}")
            
            if driver_profiles:
                print("\n🔍 Existing driver profiles:")
                for i, driver in enumerate(driver_profiles, 1):
                    print(f"\n--- Driver Profile {i} ---")
                    print(f"User ID: {driver.get('user_id', 'N/A')}")
                    print(f"Available: {driver.get('is_available', 'N/A')}")
                    
                    # Check location format
                    location = driver.get('current_location')
                    print(f"Current Location: {location}")
                    if isinstance(location, dict) and 'lat' in location and 'lng' in location:
                        print(f"  ✅ Driver coordinates: ({location['lat']}, {location['lng']})")
                    else:
                        print(f"  ❌ Driver location not set or invalid format")
            else:
                print("📭 No driver profiles found in database")
                
        except Exception as e:
            print(f"❌ Database query error: {e}")

    def setup_test_users(self):
        """Create test rider and driver as specified"""
        self.print_section("2. SETTING UP TEST USERS")
        
        # Test rider data
        test_rider_data = {
            "email": "test.rider.debug@example.com",
            "password": "password123",
            "name": "Test Rider Debug",
            "phone": "+919876543210",
            "user_type": "rider"
        }
        
        # Test driver data
        test_driver_data = {
            "email": "test.driver.debug@example.com",
            "password": "password123", 
            "name": "Test Driver Debug",
            "phone": "+919876543211",
            "user_type": "driver"
        }
        
        # Register test rider
        try:
            print("🔄 Registering test rider...")
            response = self.make_request("POST", "/auth/register", test_rider_data)
            if response.status_code == 200:
                data = response.json()
                self.test_rider_token = data["token"]
                self.test_rider_id = data["id"]
                print(f"✅ Test rider registered successfully - ID: {self.test_rider_id}")
            else:
                print(f"❌ Rider registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Rider registration error: {e}")
            return False
        
        # Register test driver
        try:
            print("🔄 Registering test driver...")
            response = self.make_request("POST", "/auth/register", test_driver_data)
            if response.status_code == 200:
                data = response.json()
                self.test_driver_token = data["token"]
                self.test_driver_id = data["id"]
                print(f"✅ Test driver registered successfully - ID: {self.test_driver_id}")
            else:
                print(f"❌ Driver registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Driver registration error: {e}")
            return False
        
        return True

    def setup_driver_profile(self):
        """Create driver profile and set location"""
        self.print_section("3. SETTING UP DRIVER PROFILE AND LOCATION")
        
        if not self.test_driver_token:
            print("❌ No driver token available")
            return False
        
        driver_headers = self.get_auth_headers(self.test_driver_token)
        
        # Create driver profile
        driver_profile_data = {
            "per_km_rate": 25.0,
            "vehicle_type": "sedan",
            "vehicle_number": "DL01DEBUG123",
            "license_number": "DL1234567890"
        }
        
        try:
            print("🔄 Creating driver profile...")
            response = self.make_request("POST", "/driver/profile", driver_profile_data, driver_headers)
            if response.status_code == 200:
                print("✅ Driver profile created successfully")
            else:
                print(f"❌ Driver profile creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Driver profile creation error: {e}")
            return False
        
        # Set driver location to Delhi coordinates (28.6139, 77.2090)
        delhi_location = {"lat": 28.6139, "lng": 77.2090}
        
        try:
            print("🔄 Setting driver location to Delhi coordinates...")
            response = self.make_request("PUT", "/driver/location", delhi_location, driver_headers)
            if response.status_code == 200:
                print(f"✅ Driver location set to: {delhi_location}")
            else:
                print(f"❌ Driver location update failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Driver location update error: {e}")
            return False
        
        # Set driver availability to true
        try:
            print("🔄 Setting driver availability to true...")
            response = self.make_request("PUT", "/driver/availability/true", headers=driver_headers)
            if response.status_code == 200:
                print("✅ Driver set to available")
            else:
                print(f"❌ Driver availability update failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Driver availability update error: {e}")
            return False
        
        # Verify driver profile in database
        try:
            driver_profile = self.db.driver_profiles.find_one({"user_id": self.test_driver_id}, {"_id": 0})
            if driver_profile:
                print(f"✅ Driver profile verified in database:")
                print(f"   Available: {driver_profile.get('is_available')}")
                print(f"   Location: {driver_profile.get('current_location')}")
            else:
                print("❌ Driver profile not found in database")
                return False
        except Exception as e:
            print(f"❌ Database verification error: {e}")
            return False
        
        return True

    def create_test_ride_request(self):
        """Create a ride request from Delhi Airport to Connaught Place"""
        self.print_section("4. CREATING TEST RIDE REQUEST")
        
        if not self.test_rider_token:
            print("❌ No rider token available")
            return False
        
        rider_headers = self.get_auth_headers(self.test_rider_token)
        
        # Ride request from Delhi Airport to Connaught Place
        ride_data = {
            "pickup_location": {
                "lat": 28.5562, 
                "lng": 77.1000, 
                "address": "Delhi Airport, New Delhi"
            },
            "drop_location": {
                "lat": 28.6315, 
                "lng": 77.2167, 
                "address": "Connaught Place, New Delhi"
            },
            "estimated_distance": 15.2,
            "estimated_fare": 380.0
        }
        
        try:
            print("🔄 Creating ride request from Delhi Airport to Connaught Place...")
            response = self.make_request("POST", "/rider/request-ride", ride_data, rider_headers)
            if response.status_code == 200:
                data = response.json()
                self.test_ride_id = data["id"]
                print(f"✅ Ride request created successfully - ID: {self.test_ride_id}")
                print(f"   Status: {data.get('status')}")
                print(f"   Pickup: {data.get('pickup_location', {}).get('address')}")
                print(f"   Drop: {data.get('drop_location', {}).get('address')}")
                
                # Verify in database
                ride_in_db = self.db.ride_requests.find_one({"id": self.test_ride_id}, {"_id": 0})
                if ride_in_db:
                    print(f"✅ Ride request verified in database with status: {ride_in_db.get('status')}")
                else:
                    print("❌ Ride request not found in database")
                    return False
                
                return True
            else:
                print(f"❌ Ride request creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ride request creation error: {e}")
            return False

    def test_distance_calculation(self):
        """Test distance calculation between driver and ride pickup"""
        self.print_section("5. TESTING DISTANCE CALCULATION")
        
        # Driver location: Delhi coordinates (28.6139, 77.2090)
        driver_location = {"lat": 28.6139, "lng": 77.2090}
        
        # Ride pickup location: Delhi Airport (28.5562, 77.1000)
        pickup_location = {"lat": 28.5562, "lng": 77.1000}
        
        # Calculate distance using geopy (same as backend)
        try:
            from geopy.distance import geodesic
            distance = geodesic(
                (driver_location["lat"], driver_location["lng"]), 
                (pickup_location["lat"], pickup_location["lng"])
            ).kilometers
            
            print(f"📏 Distance calculation:")
            print(f"   Driver location: ({driver_location['lat']}, {driver_location['lng']})")
            print(f"   Pickup location: ({pickup_location['lat']}, {pickup_location['lng']})")
            print(f"   Calculated distance: {distance:.2f} km")
            
            if distance <= 10:
                print(f"✅ Distance {distance:.2f} km is within 10km radius - should be visible")
            else:
                print(f"❌ Distance {distance:.2f} km exceeds 10km radius - will not be visible")
                
            return distance
            
        except Exception as e:
            print(f"❌ Distance calculation error: {e}")
            return None

    def test_driver_ride_requests_api(self):
        """Test the GET /api/driver/ride-requests endpoint with debug logging"""
        self.print_section("6. TESTING DRIVER RIDE REQUESTS API")
        
        if not self.test_driver_token:
            print("❌ No driver token available")
            return False
        
        driver_headers = self.get_auth_headers(self.test_driver_token)
        
        try:
            print("🔄 Calling GET /api/driver/ride-requests...")
            response = self.make_request("GET", "/driver/ride-requests", headers=driver_headers)
            
            print(f"📊 API Response:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Type: {type(data)}")
                print(f"   Response Length: {len(data) if isinstance(data, list) else 'N/A'}")
                print(f"   Response Data: {json.dumps(data, indent=2, default=str)}")
                
                if isinstance(data, list):
                    if len(data) > 0:
                        print(f"✅ Driver can see {len(data)} ride request(s)")
                        
                        # Check if our test ride is in the list
                        found_test_ride = False
                        for ride in data:
                            if ride.get("id") == self.test_ride_id:
                                found_test_ride = True
                                print(f"✅ Test ride request found in results:")
                                print(f"   Distance to pickup: {ride.get('distance_to_pickup')} km")
                                break
                        
                        if not found_test_ride and self.test_ride_id:
                            print(f"❌ Test ride request {self.test_ride_id} NOT found in results")
                    else:
                        print("❌ No ride requests returned - empty list")
                else:
                    print(f"❌ Unexpected response type: {type(data)}")
                
                return True
            else:
                print(f"❌ API call failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ API call error: {e}")
            return False

    def debug_query_filters(self):
        """Debug the database query filters used by the API"""
        self.print_section("7. DEBUGGING DATABASE QUERY FILTERS")
        
        try:
            # Get driver profile
            driver_profile = self.db.driver_profiles.find_one({"user_id": self.test_driver_id}, {"_id": 0})
            if not driver_profile:
                print("❌ Driver profile not found")
                return False
            
            print(f"🔍 Driver Profile Analysis:")
            print(f"   User ID: {driver_profile.get('user_id')}")
            print(f"   Available: {driver_profile.get('is_available')}")
            print(f"   Current Location: {driver_profile.get('current_location')}")
            
            # Check if driver has location set
            if not driver_profile.get('current_location'):
                print("❌ Driver location not set - this would cause API to fail")
                return False
            
            # Query ride requests with same filter as API
            print(f"\n🔍 Querying ride requests with status='requested'...")
            ride_requests = list(self.db.ride_requests.find({"status": "requested"}, {"_id": 0}))
            print(f"   Found {len(ride_requests)} ride requests with status='requested'")
            
            if ride_requests:
                driver_location = driver_profile["current_location"]
                print(f"\n🔍 Distance Analysis:")
                
                from geopy.distance import geodesic
                
                for i, ride in enumerate(ride_requests, 1):
                    pickup_location = ride.get("pickup_location", {})
                    if isinstance(pickup_location, dict) and 'lat' in pickup_location and 'lng' in pickup_location:
                        distance = geodesic(
                            (driver_location["lat"], driver_location["lng"]),
                            (pickup_location["lat"], pickup_location["lng"])
                        ).kilometers
                        
                        print(f"   Ride {i} (ID: {ride.get('id', 'N/A')[:8]}...):")
                        print(f"     Pickup: ({pickup_location['lat']}, {pickup_location['lng']})")
                        print(f"     Distance: {distance:.2f} km")
                        print(f"     Within 10km: {'✅ YES' if distance <= 10 else '❌ NO'}")
                        
                        if ride.get('id') == self.test_ride_id:
                            print(f"     🎯 This is our test ride!")
                    else:
                        print(f"   Ride {i}: ❌ Invalid pickup location format")
            else:
                print("❌ No ride requests found with status='requested'")
            
            return True
            
        except Exception as e:
            print(f"❌ Database query debug error: {e}")
            return False

    def test_location_format_consistency(self):
        """Test location format consistency between rider and driver"""
        self.print_section("8. TESTING LOCATION FORMAT CONSISTENCY")
        
        try:
            # Check ride request location format
            if self.test_ride_id:
                ride = self.db.ride_requests.find_one({"id": self.test_ride_id}, {"_id": 0})
                if ride:
                    pickup = ride.get("pickup_location", {})
                    drop = ride.get("drop_location", {})
                    
                    print(f"🔍 Ride Request Location Format:")
                    print(f"   Pickup Location Type: {type(pickup)}")
                    print(f"   Pickup Location: {pickup}")
                    print(f"   Has lat/lng: {'lat' in pickup and 'lng' in pickup}")
                    
                    print(f"   Drop Location Type: {type(drop)}")
                    print(f"   Drop Location: {drop}")
                    print(f"   Has lat/lng: {'lat' in drop and 'lng' in drop}")
                else:
                    print("❌ Test ride not found in database")
            
            # Check driver location format
            if self.test_driver_id:
                driver_profile = self.db.driver_profiles.find_one({"user_id": self.test_driver_id}, {"_id": 0})
                if driver_profile:
                    location = driver_profile.get("current_location", {})
                    
                    print(f"\n🔍 Driver Location Format:")
                    print(f"   Location Type: {type(location)}")
                    print(f"   Location: {location}")
                    print(f"   Has lat/lng: {'lat' in location and 'lng' in location}")
                else:
                    print("❌ Driver profile not found in database")
            
            # Test coordinate types
            print(f"\n🔍 Coordinate Type Analysis:")
            if self.test_ride_id and self.test_driver_id:
                ride = self.db.ride_requests.find_one({"id": self.test_ride_id}, {"_id": 0})
                driver_profile = self.db.driver_profiles.find_one({"user_id": self.test_driver_id}, {"_id": 0})
                
                if ride and driver_profile:
                    pickup = ride.get("pickup_location", {})
                    driver_loc = driver_profile.get("current_location", {})
                    
                    if pickup and driver_loc:
                        print(f"   Pickup lat type: {type(pickup.get('lat'))}, value: {pickup.get('lat')}")
                        print(f"   Pickup lng type: {type(pickup.get('lng'))}, value: {pickup.get('lng')}")
                        print(f"   Driver lat type: {type(driver_loc.get('lat'))}, value: {driver_loc.get('lat')}")
                        print(f"   Driver lng type: {type(driver_loc.get('lng'))}, value: {driver_loc.get('lng')}")
                        
                        # Check if all are numeric
                        coords_valid = all(isinstance(coord, (int, float)) for coord in [
                            pickup.get('lat'), pickup.get('lng'),
                            driver_loc.get('lat'), driver_loc.get('lng')
                        ])
                        
                        if coords_valid:
                            print("✅ All coordinates are numeric - format is correct")
                        else:
                            print("❌ Some coordinates are not numeric - format issue detected")
            
            return True
            
        except Exception as e:
            print(f"❌ Location format test error: {e}")
            return False

    def comprehensive_debug_summary(self):
        """Provide comprehensive debug summary"""
        self.print_section("9. COMPREHENSIVE DEBUG SUMMARY")
        
        print("🔍 INVESTIGATION SUMMARY:")
        print("=" * 50)
        
        # Check database state
        try:
            total_rides = self.db.ride_requests.count_documents({})
            requested_rides = self.db.ride_requests.count_documents({"status": "requested"})
            total_drivers = self.db.driver_profiles.count_documents({})
            available_drivers = self.db.driver_profiles.count_documents({"is_available": True})
            drivers_with_location = self.db.driver_profiles.count_documents({
                "current_location": {"$exists": True, "$ne": None}
            })
            
            print(f"📊 Database State:")
            print(f"   Total ride requests: {total_rides}")
            print(f"   Ride requests with status 'requested': {requested_rides}")
            print(f"   Total driver profiles: {total_drivers}")
            print(f"   Available drivers: {available_drivers}")
            print(f"   Drivers with location set: {drivers_with_location}")
            
            # Check for potential issues
            issues = []
            
            if requested_rides == 0:
                issues.append("No ride requests with 'requested' status")
            
            if available_drivers == 0:
                issues.append("No available drivers")
            
            if drivers_with_location == 0:
                issues.append("No drivers have location set")
            
            if drivers_with_location < available_drivers:
                issues.append(f"{available_drivers - drivers_with_location} available drivers don't have location set")
            
            if issues:
                print(f"\n⚠️  Potential Issues Detected:")
                for issue in issues:
                    print(f"   • {issue}")
            else:
                print(f"\n✅ No obvious database issues detected")
            
            # Test the specific scenario
            if self.test_ride_id and self.test_driver_id:
                print(f"\n🎯 Test Scenario Analysis:")
                
                # Get test ride
                test_ride = self.db.ride_requests.find_one({"id": self.test_ride_id}, {"_id": 0})
                test_driver = self.db.driver_profiles.find_one({"user_id": self.test_driver_id}, {"_id": 0})
                
                if test_ride and test_driver:
                    print(f"   Test ride status: {test_ride.get('status')}")
                    print(f"   Test driver available: {test_driver.get('is_available')}")
                    print(f"   Test driver has location: {bool(test_driver.get('current_location'))}")
                    
                    if (test_ride.get('status') == 'requested' and 
                        test_driver.get('is_available') and 
                        test_driver.get('current_location')):
                        
                        # Calculate distance
                        from geopy.distance import geodesic
                        pickup = test_ride.get('pickup_location', {})
                        driver_loc = test_driver.get('current_location', {})
                        
                        if pickup and driver_loc and 'lat' in pickup and 'lng' in pickup:
                            distance = geodesic(
                                (driver_loc['lat'], driver_loc['lng']),
                                (pickup['lat'], pickup['lng'])
                            ).kilometers
                            
                            print(f"   Distance between driver and pickup: {distance:.2f} km")
                            
                            if distance <= 10:
                                print(f"   ✅ Distance is within 10km - ride should be visible")
                                print(f"   🔍 If driver still can't see ride, check API implementation")
                            else:
                                print(f"   ❌ Distance exceeds 10km - ride will not be visible")
                        else:
                            print(f"   ❌ Invalid location data format")
                    else:
                        print(f"   ❌ Test scenario conditions not met")
                else:
                    print(f"   ❌ Test data not found in database")
            
        except Exception as e:
            print(f"❌ Summary generation error: {e}")

    def run_debug_investigation(self):
        """Run the complete debug investigation"""
        print("🚗 NEARBY RIDE REQUESTS DEBUG INVESTIGATION")
        print("=" * 80)
        print("Investigating why drivers aren't seeing existing ride requests")
        
        # Step 1: Check current database state
        self.check_database_state()
        
        # Step 2: Setup test users
        if not self.setup_test_users():
            print("❌ Failed to setup test users - aborting investigation")
            return
        
        # Step 3: Setup driver profile and location
        if not self.setup_driver_profile():
            print("❌ Failed to setup driver profile - aborting investigation")
            return
        
        # Step 4: Create test ride request
        if not self.create_test_ride_request():
            print("❌ Failed to create test ride request - aborting investigation")
            return
        
        # Step 5: Test distance calculation
        self.test_distance_calculation()
        
        # Step 6: Test driver ride requests API
        self.test_driver_ride_requests_api()
        
        # Step 7: Debug query filters
        self.debug_query_filters()
        
        # Step 8: Test location format consistency
        self.test_location_format_consistency()
        
        # Step 9: Comprehensive summary
        self.comprehensive_debug_summary()
        
        print(f"\n{'='*80}")
        print("🏁 DEBUG INVESTIGATION COMPLETE")
        print(f"{'='*80}")

if __name__ == "__main__":
    debugger = RideRequestDebugger()
    debugger.run_debug_investigation()