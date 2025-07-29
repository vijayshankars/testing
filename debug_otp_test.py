#!/usr/bin/env python3
"""
Debug Mobile OTP Authentication Issues
"""

import requests
import json

BASE_URL = "https://06841ea6-50ad-424b-b520-f2f741bf6fdb.preview.emergentagent.com/api"

def debug_otp_flow():
    print("🔍 Debugging Mobile OTP Authentication Flow")
    print("=" * 60)
    
    # Test 1: Send OTP and check response
    print("\n1. Testing OTP Send:")
    otp_request = {
        "phone_number": "+91 9999999999",
        "user_type": "rider"
    }
    
    response = requests.post(f"{BASE_URL}/auth/send-otp", json=otp_request)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        demo_otp = data.get("demo_otp")
        
        print(f"\n2. Testing OTP Verification with demo OTP: {demo_otp}")
        
        # Test with the actual demo OTP returned
        if demo_otp:
            verify_request = {
                "phone_number": "+91 9999999999",
                "otp_code": demo_otp,
                "user_type": "rider",
                "name": "Debug Test User"
            }
            
            verify_response = requests.post(f"{BASE_URL}/auth/verify-otp", json=verify_request)
            print(f"Verification Status: {verify_response.status_code}")
            print(f"Verification Response: {verify_response.json()}")
        
        # Test with standard demo OTPs
        print(f"\n3. Testing with standard demo OTPs:")
        for demo_code in ["123456", "000000"]:
            verify_request = {
                "phone_number": "+91 9999999999",
                "otp_code": demo_code,
                "user_type": "rider",
                "name": "Debug Test User 2"
            }
            
            verify_response = requests.post(f"{BASE_URL}/auth/verify-otp", json=verify_request)
            print(f"Demo OTP {demo_code} - Status: {verify_response.status_code}")
            print(f"Demo OTP {demo_code} - Response: {verify_response.json()}")
    
    # Test 4: Check phone number validation
    print(f"\n4. Testing phone number validation:")
    invalid_phones = ["123456789", "invalid_phone", "91987654321"]
    
    for phone in invalid_phones:
        test_request = {
            "phone_number": phone,
            "user_type": "rider"
        }
        
        response = requests.post(f"{BASE_URL}/auth/send-otp", json=test_request)
        print(f"Phone {phone} - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Phone {phone} - Error: {response.json()}")

if __name__ == "__main__":
    debug_otp_flow()