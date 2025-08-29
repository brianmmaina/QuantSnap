#!/usr/bin/env python3
"""
Test Alpha Vantage API integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app directory to path
sys.path.append('app')

from data_provider import AlphaVantageProvider

def test_alpha_vantage():
    """Test Alpha Vantage API key and data fetching"""
    
    # Get API key
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not found in .env file")
        return False
    
    print(f"🔑 API Key found: {api_key[:8]}...")
    
    # Initialize provider
    try:
        provider = AlphaVantageProvider()
        print("✅ Alpha Vantage provider initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing provider: {e}")
        return False
    
    # Test with a popular stock
    test_ticker = "AAPL"
    print(f"\n📊 Testing with {test_ticker}...")
    
    try:
        # Test live price
        print("🔍 Fetching live price...")
        live_prices = provider.get_live_prices([test_ticker])
        
        if live_prices and test_ticker in live_prices:
            price_data = live_prices[test_ticker]
            print(f"✅ Live price: ${price_data['price']}")
            print(f"   Change: {price_data['change']:+.2f} ({price_data['change_pct']:+.2f}%)")
            print(f"   Volume: {price_data['volume']:,}")
        else:
            print("❌ Failed to get live price")
            return False
        
        # Test comprehensive data
        print("\n📈 Fetching comprehensive data...")
        stock_data = provider.get_stock_data(test_ticker)
        
        if stock_data:
            print(f"✅ Company: {stock_data['name']}")
            print(f"   Sector: {stock_data['sector']}")
            print(f"   Price: ${stock_data['price']}")
            print(f"   1M Growth: {stock_data['momentum_1m']:+.2f}%")
            print(f"   3M Growth: {stock_data['momentum_3m']:+.2f}%")
            print(f"   Sharpe Ratio: {stock_data['sharpe_ratio']:.2f}")
            print(f"   Score: {stock_data['score']:.2f}")
        else:
            print("❌ Failed to get comprehensive data")
            return False
        
        print("\n🎉 Alpha Vantage integration test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Alpha Vantage Integration...")
    print("=" * 50)
    
    success = test_alpha_vantage()
    
    if success:
        print("\n✅ Ready to deploy with Alpha Vantage!")
        print("📝 Don't forget to add ALPHA_VANTAGE_API_KEY to your Render environment variables")
    else:
        print("\n❌ Alpha Vantage test failed. Check your API key and try again.")
