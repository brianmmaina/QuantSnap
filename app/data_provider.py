#!/usr/bin/env python3
"""
Data provider using Alpha Vantage API for accurate financial data
"""

import os
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class AlphaVantageProvider:
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not found. Using fallback to yfinance.")
            self.api_key = None
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive stock data from Alpha Vantage"""
        if not self.api_key:
            return None
            
        try:
            # Rate limiting - Alpha Vantage free tier: 5 requests per minute
            time.sleep(12)  # Wait 12 seconds between requests
            
            # Get daily time series
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': ticker,
                'apikey': self.api_key,
                'outputsize': 'full'
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'Error Message' in data or 'Note' in data:
                logger.error(f"Alpha Vantage error for {ticker}: {data}")
                return None
            
            # Get company overview
            overview_params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            overview_response = requests.get(self.base_url, params=overview_params)
            overview_data = overview_response.json()
            
            if 'Error Message' in overview_data:
                logger.error(f"Alpha Vantage overview error for {ticker}: {overview_data}")
                return None
            
            # Process time series data
            time_series = data.get('Time Series (Daily)', {})
            if not time_series:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            # Calculate metrics
            current_price = float(df['4. close'].iloc[-1])
            returns = df['4. close'].pct_change().dropna()
            
            # Momentum calculations (using exact trading days)
            if len(df) >= 21:
                month_ago_price = float(df['4. close'].iloc[-21])
                momentum_1m = ((current_price / month_ago_price) - 1) * 100
            else:
                momentum_1m = 0
                
            if len(df) >= 63:
                three_months_ago_price = float(df['4. close'].iloc[-63])
                momentum_3m = ((current_price / three_months_ago_price) - 1) * 100
            else:
                momentum_3m = 0
                
            if len(df) >= 126:
                six_months_ago_price = float(df['4. close'].iloc[-126])
                momentum_6m = ((current_price / six_months_ago_price) - 1) * 100
            else:
                momentum_6m = 0
            
            # Volatility
            volatility_30d = returns.tail(30).std() * 100 if len(returns) >= 30 else returns.std() * 100
            
            # Volume
            volume_avg_20d = df['5. volume'].tail(20).mean() if len(df) >= 20 else df['5. volume'].mean()
            
            # Sharpe ratio
            if len(returns) >= 63:
                returns_3m = returns.tail(63)
                sharpe_ratio = (returns_3m.mean() / returns_3m.std()) * np.sqrt(252) if returns_3m.std() > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Daily change
            previous_close = float(df['4. close'].iloc[-2]) if len(df) > 1 else current_price
            daily_change = current_price - previous_close
            daily_change_pct = (daily_change / previous_close) * 100 if previous_close > 0 else 0
            
            # Company info from overview
            company_name = overview_data.get('Name', ticker)
            sector = overview_data.get('Sector', 'Unknown')
            market_cap = float(overview_data.get('MarketCapitalization', 0))
            
            # Calculate composite score
            score = (
                (momentum_1m * 0.4) +      # 1M momentum weight
                (momentum_3m * 0.3) +      # 3M momentum weight
                (sharpe_ratio * 2.0) +     # Sharpe ratio weight
                (volume_avg_20d / 1000000 * 0.1) + # Volume factor
                (market_cap / 1e12 * 0.1)  # Market cap factor
            )
            
            return {
                'ticker': ticker,
                'name': company_name,
                'sector': sector,
                'price': round(current_price, 2),
                'momentum_1m': round(momentum_1m, 2),
                'momentum_3m': round(momentum_3m, 2),
                'momentum_6m': round(momentum_6m, 2),
                'volatility': round(volatility_30d, 2),
                'volume_avg': round(volume_avg_20d, 0),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'daily_change': round(daily_change, 2),
                'daily_change_pct': round(daily_change_pct, 2),
                'market_cap': market_cap,
                'score': round(score, 3),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error getting Alpha Vantage data for {ticker}: {e}")
            return None
    
    def get_live_prices(self, tickers: List[str]) -> Dict:
        """Get live prices for multiple stocks from Alpha Vantage"""
        if not self.api_key:
            return {}
            
        price_data = {}
        
        for ticker in tickers:
            try:
                time.sleep(12)  # Rate limiting
                
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': ticker,
                    'apikey': self.api_key
                }
                
                response = requests.get(self.base_url, params=params)
                data = response.json()
                
                if 'Error Message' in data or 'Note' in data:
                    continue
                
                quote = data.get('Global Quote', {})
                if not quote:
                    continue
                
                current_price = float(quote.get('05. price', 0))
                previous_close = float(quote.get('08. previous close', 0))
                change = float(quote.get('09. change', 0))
                change_pct = float(quote.get('10. change percent', '0%').replace('%', ''))
                volume = int(quote.get('06. volume', 0))
                
                price_data[ticker] = {
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'volume': volume,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error fetching Alpha Vantage live price for {ticker}: {e}")
                continue
        
        return price_data
