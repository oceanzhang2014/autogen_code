#!/usr/bin/env python3
"""
Debug script to test login functionality through nginx vs direct access.
"""

import requests
import json

def test_login():
    """Test login functionality through different endpoints."""
    
    test_cases = [
        {
            "name": "Direct access to Flask",
            "url": "http://192.168.0.4:5011/api/login",
            "headers": {}
        },
        {
            "name": "Nginx proxy with /autogen/",
            "url": "https://xpuai.20140806.xyz/autogen/api/login",
            "headers": {}
        }
    ]
    
    login_data = {
        "username": "admin",
        "password": "qw123456"
    }
    
    print("Testing login functionality...")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"URL: {test_case['url']}")
        
        try:
            response = requests.post(
                test_case['url'],
                json=login_data,
                headers={"Content-Type": "application/json", **test_case['headers']},
                timeout=10,
                verify=False  # Disable SSL verification for testing
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "success":
                        print("SUCCESS: Login successful!")
                    else:
                        print(f"FAILED: Login failed: {data.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    print("ERROR: Invalid JSON response")
            else:
                print("ERROR: HTTP error")
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_login()