#!/usr/bin/env python3
"""
Test script to verify all endpoints on Railway deployment
Usage: python test_endpoints.py <your-railway-url>
Example: python test_endpoints.py https://your-app-name.up.railway.app
"""

import sys
import requests
import json
from datetime import datetime

def test_endpoint(url, endpoint, method="GET", data=None, headers=None):
    """Test a single endpoint"""
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    try:
        if method == "GET":
            response = requests.get(full_url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(full_url, json=data, headers=headers, timeout=10)
        
        print(f"✅ {method} {endpoint}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2) if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]}")
        print()
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ {method} {endpoint}")
        print(f"   Error: {str(e)}")
        print()
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_endpoints.py <your-railway-url>")
        print("Example: python test_endpoints.py https://your-app-name.up.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    print(f"🚀 Testing endpoints on: {base_url}")
    print("=" * 50)
    
    # Test basic endpoints
    endpoints = [
        ("", "GET"),  # Root endpoint
        ("v1/healthz", "GET"),  # Health check
        ("v1/account", "GET"),  # Account status
        ("v1/positions", "GET"),  # Positions and orders
        ("v1/trade-history", "GET"),  # Trade history
        ("docs", "GET"),  # API documentation
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint, method in endpoints:
        if test_endpoint(base_url, endpoint, method):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 Results: {success_count}/{total_count} endpoints working")
    
    if success_count == total_count:
        print("🎉 All endpoints are working correctly!")
    else:
        print("⚠️  Some endpoints failed. Check your deployment.")
    
    print("\n🔗 Next steps:")
    print("1. Test with a real trading decision using Make.com")
    print("2. Monitor your Bybit dashboard for trades")
    print("3. Check Railway logs for any errors")

if __name__ == "__main__":
    main()
