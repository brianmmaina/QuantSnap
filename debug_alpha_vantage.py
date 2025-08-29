#!/usr/bin/env python3
"""
Debug Alpha Vantage API integration
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_alpha_vantage_api():
    """Test Alpha Vantage API directly"""
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not found")
        return
    
    print(f"🔑 API Key: {api_key[:8]}...")
    
    # Test 1: Global Quote (live price)
    print("\n📊 Testing Global Quote for AAPL...")
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': 'AAPL',
        'apikey': api_key
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    
    if response.status_code == 200:
        data = response.json()
        if 'Global Quote' in data:
            quote = data['Global Quote']
            print(f"✅ Success! Price: ${quote.get('05. price', 'N/A')}")
        elif 'Error Message' in data:
            print(f"❌ Error: {data['Error Message']}")
        elif 'Note' in data:
            print(f"⚠️ Note: {data['Note']}")
        else:
            print(f"❓ Unexpected response: {data}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
    
    # Test 2: Daily Time Series
    print("\n📈 Testing Daily Time Series for AAPL...")
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': 'AAPL',
        'apikey': api_key,
        'outputsize': 'compact'
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    
    if response.status_code == 200:
        data = response.json()
        if 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            latest_date = list(time_series.keys())[0]
            latest_data = time_series[latest_date]
            print(f"✅ Success! Latest close: ${latest_data.get('4. close', 'N/A')}")
        elif 'Error Message' in data:
            print(f"❌ Error: {data['Error Message']}")
        elif 'Note' in data:
            print(f"⚠️ Note: {data['Note']}")
        else:
            print(f"❓ Unexpected response: {data}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")

if __name__ == "__main__":
    print("🔍 Debugging Alpha Vantage API...")
    test_alpha_vantage_api()
