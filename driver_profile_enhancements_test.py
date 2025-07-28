#!/usr/bin/env python3
"""
Driver Profile Enhancements Testing
Tests the new VAHAN license verification and auto-assigned rates functionality
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://87aa55a7-7445-442a-b69c-85a42d10dc65.preview.emergentagent.com/api"
TIMEOUT = 30

class DriverProfileEnhancementsTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.driver_token = None
        self.driver_user_id = None
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def create_test_driver_via_otp(self) -> bool:
        """Create a test driver user via mobile OTP authentication"""
        try:
            # Step 1: Send OTP
            phone_number = "+91 8876543212"  # Different test driver phone
            otp_request = {
                "phone_number": phone_number,
                "user_type": "driver"
            }
            
            response = self.session.post(
                f"{BASE_URL}/auth/send-otp",
                json=otp_request,
                timeout=TIMEOUT
            )
            
            if response.status_code != 200:
                self.log_test("Driver OTP Send", False, f"Failed to send OTP: {response.status_code}", response.text)
                return False
            
            otp_data = response.json()
            demo_otp = otp_data.get("demo_otp", "123456")  # Use demo OTP
            
            self.log_test("Driver OTP Send", True, f"OTP sent successfully to {phone_number}")
            
            # Step 2: Verify OTP and create driver
            verify_request = {
                "phone_number": phone_number,
                "otp_code": demo_otp,
                "user_type": "driver",
                "name": "Test Driver Enhanced"
            }
            
            response = self.session.post(
                f"{BASE_URL}/auth/verify-otp",
                json=verify_request,
                timeout=TIMEOUT
            )
            
            if response.status_code != 200:
                self.log_test("Driver OTP Verification", False, f"Failed to verify OTP: {response.status_code}", response.text)
                return False
            
            auth_data = response.json()
            if not auth_data.get("success"):
                self.log_test("Driver OTP Verification", False, "OTP verification failed", auth_data)
                return False
            
            self.driver_token = auth_data.get("token")
            self.driver_user_id = auth_data.get("user_data", {}).get("id")
            
            self.log_test("Driver OTP Verification", True, "Driver created successfully via mobile OTP")
            return True
            
        except Exception as e:
            self.log_test("Driver Creation via OTP", False, f"Exception: {str(e)}")
            return False
    
    def test_vahan_license_verification(self):
        """Test VAHAN license verification endpoint"""
        if not self.driver_token:
            self.log_test("VAHAN License Verification", False, "No driver token available")
            return
        
        headers = {"Authorization": f"Bearer {self.driver_token}"}
        
        # Test 1: Valid license number starting with "DL"
        try:
            valid_license_request = {
                "license_number": "DL1420110012345"
            }
            
            response = self.session.post(
                f"{BASE_URL}/driver/verify-license",
                json=valid_license_request,
                headers=headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and "license_data" in result:
                    self.log_test("VAHAN Valid License Verification", True, 
                                "Valid license verified successfully with VAHAN system",
                                {"license_data": result.get("license_data")})
                else:
                    self.log_test("VAHAN Valid License Verification", False, 
                                "Valid license verification failed", result)
            else:
                self.log_test("VAHAN Valid License Verification", False, 
                            f"HTTP {response.status_code}", response.text)
        
        except Exception as e:
            self.log_test("VAHAN Valid License Verification", False, f"Exception: {str(e)}")
        
        # Test 2: Invalid license number (not starting with "DL")
        try:
            invalid_license_request = {
                "license_number": "INVALID123456"
            }
            
            response = self.session.post(
                f"{BASE_URL}/driver/verify-license",
                json=invalid_license_request,
                headers=headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result.get("success") and "not found in VAHAN database" in result.get("message", ""):
                    self.log_test("VAHAN Invalid License Verification", True, 
                                "Invalid license correctly rejected by VAHAN system")
                else:
                    self.log_test("VAHAN Invalid License Verification", False, 
                                "Invalid license should have been rejected", result)
            else:
                self.log_test("VAHAN Invalid License Verification", False, 
                            f"HTTP {response.status_code}", response.text)
        
        except Exception as e:
            self.log_test("VAHAN Invalid License Verification", False, f"Exception: {str(e)}")
        
        # Test 3: Empty license number
        try:
            empty_license_request = {
                "license_number": ""
            }
            
            response = self.session.post(
                f"{BASE_URL}/driver/verify-license",
                json=empty_license_request,
                headers=headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result.get("success"):
                    self.log_test("VAHAN Empty License Verification", True, 
                                "Empty license correctly rejected")
                else:
                    self.log_test("VAHAN Empty License Verification", False, 
                                "Empty license should have been rejected", result)
            else:
                self.log_test("VAHAN Empty License Verification", False, 
                            f"HTTP {response.status_code}", response.text)
        
        except Exception as e:
            self.log_test("VAHAN Empty License Verification", False, f"Exception: {str(e)}")
    
    def test_auto_assigned_rates(self):
        """Test automatic rate assignment based on vehicle type"""
        if not self.driver_token:
            self.log_test("Auto Rate Assignment", False, "No driver token available")
            return
        
        headers = {"Authorization": f"Bearer {self.driver_token}"}
        
        # Test different vehicle types and their expected rates
        vehicle_test_cases = [
            {"vehicle_type": "bike", "expected_rate": 5.0, "license": "DL1420110012345", "vehicle_number": "TN01AB1234"},
            {"vehicle_type": "auto", "expected_rate": 8.0, "license": "DL1420110012346", "vehicle_number": "TN01AB1235"},
            {"vehicle_type": "car", "expected_rate": 12.0, "license": "DL1420110012347", "vehicle_number": "TN01AB1236"},
            {"vehicle_type": "suv", "expected_rate": 15.0, "license": "DL1420110012348", "vehicle_number": "TN01AB1237"}
        ]
        
        for i, test_case in enumerate(vehicle_test_cases):
            try:
                # Create a new driver for each vehicle type test
                import time
                timestamp = int(time.time())
                phone_number = f"+91 {timestamp % 10000000000:010d}"  # Generate unique phone number
                
                # Send OTP
                otp_request = {
                    "phone_number": phone_number,
                    "user_type": "driver"
                }
                
                response = self.session.post(
                    f"{BASE_URL}/auth/send-otp",
                    json=otp_request,
                    timeout=TIMEOUT
                )
                
                if response.status_code != 200:
                    self.log_test(f"Auto Rate Test - {test_case['vehicle_type']} Driver Creation", 
                                False, f"Failed to send OTP: {response.status_code}")
                    continue
                
                otp_data = response.json()
                demo_otp = otp_data.get("demo_otp", "123456")
                
                # Verify OTP
                verify_request = {
                    "phone_number": phone_number,
                    "otp_code": demo_otp,
                    "user_type": "driver",
                    "name": f"Test Driver {test_case['vehicle_type'].title()}"
                }
                
                response = self.session.post(
                    f"{BASE_URL}/auth/verify-otp",
                    json=verify_request,
                    timeout=TIMEOUT
                )
                
                if response.status_code != 200:
                    self.log_test(f"Auto Rate Test - {test_case['vehicle_type']} Driver Creation", 
                                False, f"Failed to verify OTP: {response.status_code}")
                    continue
                
                auth_data = response.json()
                if not auth_data.get("success"):
                    self.log_test(f"Auto Rate Test - {test_case['vehicle_type']} Driver Creation", 
                                False, "OTP verification failed")
                    continue
                
                temp_token = auth_data.get("token")
                temp_headers = {"Authorization": f"Bearer {temp_token}"}
                
                # Create driver profile WITHOUT per_km_rate field
                profile_data = {
                    "vehicle_type": test_case["vehicle_type"],
                    "vehicle_number": test_case["vehicle_number"],
                    "license_number": test_case["license"]
                }
                
                response = self.session.post(
                    f"{BASE_URL}/driver/profile",
                    json=profile_data,
                    headers=temp_headers,
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    profile = result.get("profile", {})
                    actual_rate = profile.get("per_km_rate")
                    
                    if actual_rate == test_case["expected_rate"]:
                        self.log_test(f"Auto Rate Assignment - {test_case['vehicle_type']}", True,
                                    f"Correct rate {actual_rate} assigned for {test_case['vehicle_type']}")
                    else:
                        self.log_test(f"Auto Rate Assignment - {test_case['vehicle_type']}", False,
                                    f"Expected rate {test_case['expected_rate']}, got {actual_rate}")
                else:
                    self.log_test(f"Auto Rate Assignment - {test_case['vehicle_type']}", False,
                                f"Failed to create profile: {response.status_code}", response.text)
                
            except Exception as e:
                self.log_test(f"Auto Rate Assignment - {test_case['vehicle_type']}", False, f"Exception: {str(e)}")
    
    def test_backward_compatibility(self):
        """Test that existing driver-related endpoints still work properly"""
        # Create a new driver for backward compatibility testing
        try:
            import time
            timestamp = int(time.time())
            phone_number = f"+91 {(timestamp + 1000) % 10000000000:010d}"  # Generate unique phone number
            
            # Send OTP
            otp_request = {
                "phone_number": phone_number,
                "user_type": "driver"
            }
            
            response = self.session.post(
                f"{BASE_URL}/auth/send-otp",
                json=otp_request,
                timeout=TIMEOUT
            )
            
            if response.status_code != 200:
                self.log_test("Backward Compatibility Setup", False, f"Failed to send OTP: {response.status_code}")
                return
            
            otp_data = response.json()
            demo_otp = otp_data.get("demo_otp", "123456")
            
            # Verify OTP
            verify_request = {
                "phone_number": phone_number,
                "otp_code": demo_otp,
                "user_type": "driver",
                "name": "Test Driver Backward Compatibility"
            }
            
            response = self.session.post(
                f"{BASE_URL}/auth/verify-otp",
                json=verify_request,
                timeout=TIMEOUT
            )
            
            if response.status_code != 200:
                self.log_test("Backward Compatibility Setup", False, f"Failed to verify OTP: {response.status_code}")
                return
            
            auth_data = response.json()
            if not auth_data.get("success"):
                self.log_test("Backward Compatibility Setup", False, "OTP verification failed")
                return
            
            compat_token = auth_data.get("token")
            compat_headers = {"Authorization": f"Bearer {compat_token}"}
            
        except Exception as e:
            self.log_test("Backward Compatibility Setup", False, f"Exception: {str(e)}")
            return
        
        # Test 1: Create driver profile (should work with auto-assigned rates)
        try:
            profile_data = {
                "vehicle_type": "car",
                "vehicle_number": "TN01BC9999",
                "license_number": "DL1420110099999"
            }
            
            response = self.session.post(
                f"{BASE_URL}/driver/profile",
                json=profile_data,
                headers=compat_headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                profile = result.get("profile", {})
                if profile.get("per_km_rate") == 12.0:  # Expected rate for car
                    self.log_test("Backward Compatibility - Profile Creation", True,
                                "Driver profile creation works with auto-assigned rates")
                else:
                    self.log_test("Backward Compatibility - Profile Creation", False,
                                "Auto-assigned rate not working correctly")
            else:
                self.log_test("Backward Compatibility - Profile Creation", False,
                            f"Profile creation failed: {response.status_code}", response.text)
        
        except Exception as e:
            self.log_test("Backward Compatibility - Profile Creation", False, f"Exception: {str(e)}")
        
        # Test 2: Get driver profile
        try:
            response = self.session.get(
                f"{BASE_URL}/driver/profile",
                headers=compat_headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                profile = response.json()
                if "per_km_rate" in profile and "vehicle_type" in profile:
                    self.log_test("Backward Compatibility - Profile Retrieval", True,
                                "Driver profile retrieval working correctly")
                else:
                    self.log_test("Backward Compatibility - Profile Retrieval", False,
                                "Profile missing required fields", profile)
            else:
                self.log_test("Backward Compatibility - Profile Retrieval", False,
                            f"Profile retrieval failed: {response.status_code}", response.text)
        
        except Exception as e:
            self.log_test("Backward Compatibility - Profile Retrieval", False, f"Exception: {str(e)}")
        
        # Test 3: Update driver location
        try:
            location_data = {
                "lat": 13.0827,
                "lng": 80.2707
            }
            
            response = self.session.put(
                f"{BASE_URL}/driver/location",
                json=location_data,
                headers=compat_headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                self.log_test("Backward Compatibility - Location Update", True,
                            "Driver location update working correctly")
            else:
                self.log_test("Backward Compatibility - Location Update", False,
                            f"Location update failed: {response.status_code}", response.text)
        
        except Exception as e:
            self.log_test("Backward Compatibility - Location Update", False, f"Exception: {str(e)}")
        
        # Test 4: Toggle availability
        try:
            response = self.session.put(
                f"{BASE_URL}/driver/availability/true",
                headers=compat_headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                self.log_test("Backward Compatibility - Availability Toggle", True,
                            "Driver availability toggle working correctly")
            else:
                self.log_test("Backward Compatibility - Availability Toggle", False,
                            f"Availability toggle failed: {response.status_code}", response.text)
        
        except Exception as e:
            self.log_test("Backward Compatibility - Availability Toggle", False, f"Exception: {str(e)}")
        
        # Test 5: Get ride requests
        try:
            response = self.session.get(
                f"{BASE_URL}/driver/ride-requests",
                headers=compat_headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                self.log_test("Backward Compatibility - Ride Requests", True,
                            "Driver ride requests endpoint working correctly")
            elif response.status_code == 400 and "location not set" in response.text.lower():
                self.log_test("Backward Compatibility - Ride Requests", True,
                            "Ride requests endpoint working (location validation working)")
            else:
                self.log_test("Backward Compatibility - Ride Requests", False,
                            f"Ride requests failed: {response.status_code}", response.text)
        
        except Exception as e:
            self.log_test("Backward Compatibility - Ride Requests", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all driver profile enhancement tests"""
        print("🚀 Starting Driver Profile Enhancements Testing...")
        print("=" * 60)
        
        # Step 1: Create test driver via OTP
        if not self.create_test_driver_via_otp():
            print("❌ Failed to create test driver. Stopping tests.")
            return None
        
        # Step 2: Test VAHAN license verification
        print("\n📋 Testing VAHAN License Verification...")
        self.test_vahan_license_verification()
        
        # Step 3: Test auto-assigned rates
        print("\n💰 Testing Auto-Assigned Rates...")
        self.test_auto_assigned_rates()
        
        # Step 4: Test backward compatibility
        print("\n🔄 Testing Backward Compatibility...")
        self.test_backward_compatibility()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = DriverProfileEnhancementsTest()
    result = tester.run_all_tests()
    
    if result:
        passed, failed = result
        if failed == 0:
            print("\n🎉 All tests passed! Driver profile enhancements are working correctly.")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
    else:
        print("\n❌ Test execution failed.")