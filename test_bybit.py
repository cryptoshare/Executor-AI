#!/usr/bin/env python3
"""
Test script for Bybit integration
Run this to verify your Bybit credentials and test basic functionality
"""

import os
import sys
from bybit_trader import BybitTrader

def test_bybit_connection():
    """Test basic Bybit connection and account info"""
    try:
        print("🔗 Testing Bybit connection...")
        trader = BybitTrader()
        print("✅ BybitTrader initialized successfully")
        
        print("\n📊 Getting account information...")
        account_info = trader.get_account_info()
        print("✅ Account info retrieved")
        print(f"   Response: {account_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bybit connection failed: {e}")
        return False

def test_symbol_info():
    """Test symbol information retrieval"""
    try:
        print("\n🔍 Testing symbol info retrieval...")
        trader = BybitTrader()
        
        # Test with a common symbol
        symbol = "BTCUSDT"
        symbol_info = trader.get_symbol_info(symbol)
        print(f"✅ Symbol info for {symbol} retrieved")
        print(f"   Symbol: {symbol_info.get('symbol')}")
        print(f"   Status: {symbol_info.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Symbol info test failed: {e}")
        return False

def main():
    print("🚀 Bybit Integration Test")
    print("=" * 40)
    
    # Check environment variables
    required_vars = ["BYBIT_API_KEY", "BYBIT_API_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        for var in missing_vars:
            print(f"   export {var}=your_value_here")
        return False
    
    print("✅ Environment variables configured")
    
    # Test connection
    if not test_bybit_connection():
        return False
    
    # Test symbol info
    if not test_symbol_info():
        return False
    
    print("\n🎉 All tests passed! Bybit integration is working correctly.")
    print("\nNext steps:")
    print("1. Deploy to Railway with your Bybit credentials")
    print("2. Test with a real decision payload")
    print("3. Monitor your trades in the Bybit dashboard")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
