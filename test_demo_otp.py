#!/usr/bin/env python3
"""
Test Demo OTP functionality with fresh sessions
"""

import requests
import json

BASE_URL = "https://9bc251d5-e3ce-47e0-a729-c8aabb368f35.preview.emergentagent.com/api"

def test_demo_otp():
    print("🔍 Testing Demo OTP Functionality")
    print("=" * 60)
    
    # Test with fresh phone number for demo OTP 123456
    print("\n1. Testing with demo OTP 123456:")
    otp_request = {
        "phone_number": "+91 8888888888",
        "user_type": "rider"
    }
    
    response = requests.post(f"{BASE_URL}/auth/send-otp", json=otp_request)
    print(f"Send OTP Status: {response.status_code}")
    print(f"Send OTP Response: {response.json()}")
    
    if response.status_code == 200:
        verify_request = {
            "phone_number": "+91 8888888888",
            "otp_code": "123456",  # Demo OTP
            "user_type": "rider",
            "name": "Demo OTP Test User"
        }
        
        verify_response = requests.post(f"{BASE_URL}/auth/verify-otp", json=verify_request)
        print(f"Verify Status: {verify_response.status_code}")
        print(f"Verify Response: {verify_response.json()}")
    
    # Test with fresh phone number for demo OTP 000000
    print("\n2. Testing with demo OTP 000000:")
    otp_request = {
        "phone_number": "+91 7777777777",
        "user_type": "driver"
    }
    
    response = requests.post(f"{BASE_URL}/auth/send-otp", json=otp_request)
    print(f"Send OTP Status: {response.status_code}")
    
    if response.status_code == 200:
        verify_request = {
            "phone_number": "+91 7777777777",
            "otp_code": "000000",  # Demo OTP
            "user_type": "driver",
            "name": "Demo OTP Driver Test"
        }
        
        verify_response = requests.post(f"{BASE_URL}/auth/verify-otp", json=verify_request)
        print(f"Verify Status: {verify_response.status_code}")
        print(f"Verify Response: {verify_response.json()}")

if __name__ == "__main__":
    test_demo_otp()