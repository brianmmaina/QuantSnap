#!/usr/bin/env python3
"""
Simple in-memory data solution for QuantSnap
Processes stock data on-demand without complex database operations
"""

import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up data directory
DATA_DIR = os.getenv('DATA_DIR', '/var/data')
DATA_DIR = Path(DATA_DIR)
DATA_DIR.mkdir(exist_ok=True)

# Import our core modules
from core.factors import calculate_all_factors
from core.scoring import create_composite_reputation_factors, rank_tickers
from core.universe import get_universe

logger = logging.getLogger(__name__)

class SimpleDataManager:
    """Simple in-memory data manager"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    def get_cached_data(self, key: str):
        """Get cached data if still valid"""
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key)
            if timestamp and datetime.now() - timestamp < self.cache_duration:
                return self.cache[key]
        return None
    
    def set_cached_data(self, key: str, data):
        """Cache data with timestamp"""
        self.cache[key] = data
        self.cache_timestamps[key] = datetime.now()
    
    def fetch_stock_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch data for a single stock"""
        try:
            data = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
            if not data.empty and len(data) >= 65:
                return data
            return None
        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            return None
    
    def calculate_factors_for_ticker(self, ticker: str, price_data: pd.DataFrame) -> Optional[Dict]:
        """Calculate factors for a single ticker"""
        try:
            if price_data.empty or len(price_data) < 65:
                return None
            
            # Extract price series
            close_prices = price_data['Close']
            volume = price_data['Volume']
            returns = close_prices.pct_change().dropna()
            
            # Calculate factors
            factors = calculate_all_factors(close_prices, volume, returns, ticker)
            
            # Add metadata
            factors['ticker'] = ticker
            factors['date'] = datetime.now().date()
            
            return factors
            
        except Exception as e:
            logger.error(f"Error calculating factors for {ticker}: {e}")
            return None
    
    def get_company_info(self, ticker: str) -> Dict:
        """Get basic company information"""
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            return {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'enterprise_value': info.get('enterpriseValue', 0)
            }
        except Exception as e:
            logger.warning(f"Error fetching company info for {ticker}: {e}")
            return {
                'ticker': ticker,
                'name': ticker,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 0,
                'enterprise_value': 0
            }
    
    def process_universe(self, universe_name: str, max_stocks: int = 20) -> pd.DataFrame:
        """Process a universe and return rankings DataFrame"""
        cache_key = f"rankings_{universe_name}"
        
        # Check cache first
        cached_data = self.get_cached_data(cache_key)
        if cached_data is not None:
            logger.info(f"Returning cached data for {universe_name}")
            return cached_data
        
        # Check if CSV file exists
        csv_file = DATA_DIR / f"{universe_name}_rankings.csv"
        if csv_file.exists():
            try:
                logger.info(f"Loading from CSV: {csv_file}")
                rankings_df = pd.read_csv(csv_file)
                self.set_cached_data(cache_key, rankings_df)
                return rankings_df
            except Exception as e:
                logger.error(f"Error loading CSV {csv_file}: {e}")
        
        logger.info(f"Processing universe: {universe_name}")
        
        try:
            # Get universe tickers
            universe_df = get_universe(universe_name)
            tickers = universe_df['Ticker'].tolist()
            
            # Limit to max_stocks for faster processing
            tickers = tickers[:max_stocks]
            
            # Remove duplicates and validate tickers
            tickers = list(set(tickers))
            tickers = [ticker for ticker in tickers if ticker and len(ticker) <= 5]
            
            logger.info(f"Processing {len(tickers)} tickers for {universe_name}")
            
            # Process tickers one by one
            factors_list = []
            companies_list = []
            
            for i, ticker in enumerate(tickers):
                logger.info(f"Processing {i+1}/{len(tickers)}: {ticker}")
                
                # Fetch stock data
                price_data = self.fetch_stock_data(ticker)
                if price_data is None:
                    continue
                
                # Get company info
                company_info = self.get_company_info(ticker)
                companies_list.append(company_info)
                
                # Calculate factors
                factors = self.calculate_factors_for_ticker(ticker, price_data)
                if factors:
                    factors_list.append(factors)
                
                # Rate limiting
                time.sleep(0.2)
            
            if factors_list:
                # Create factors DataFrame
                factors_df = pd.DataFrame(factors_list)
                
                # Add reputation factors
                factors_df = create_composite_reputation_factors(factors_df)
                
                # Calculate rankings
                rankings_df = rank_tickers(factors_df)
                
                # Add company info
                companies_df = pd.DataFrame(companies_list)
                if not companies_df.empty:
                    rankings_df = rankings_df.merge(companies_df, on='ticker', how='left')
                
                # Cache the result
                self.set_cached_data(cache_key, rankings_df)
                
                # Save to CSV file
                try:
                    csv_file = DATA_DIR / f"{universe_name}_rankings.csv"
                    rankings_df.to_csv(csv_file, index=False)
                    logger.info(f"Saved rankings to CSV: {csv_file}")
                except Exception as e:
                    logger.error(f"Error saving CSV: {e}")
                
                logger.info(f"Successfully processed {universe_name}: {len(factors_list)} stocks")
                return rankings_df
            else:
                logger.warning(f"No factors calculated for {universe_name}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error processing universe {universe_name}: {e}")
            return pd.DataFrame()
    
    def get_rankings(self, universe: str, limit: int = 50) -> pd.DataFrame:
        """Get rankings for universe"""
        rankings = self.process_universe(universe)
        if not rankings.empty:
            return rankings.head(limit)
        return pd.DataFrame()
    
    def get_stock_data(self, ticker: str) -> Dict:
        """Get stock data and factors"""
        cache_key = f"stock_{ticker}"
        
        # Check cache first
        cached_data = self.get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Fetch stock data
            price_data = self.fetch_stock_data(ticker)
            if price_data is None:
                return {}
            
            # Get company info
            company_info = self.get_company_info(ticker)
            
            # Calculate factors
            factors = self.calculate_factors_for_ticker(ticker, price_data)
            if factors is None:
                return {}
            
            # Create result
            result = {
                'ticker': ticker,
                'company': company_info,
                'factors': factors,
                'price_data': {
                    'latest_close': float(price_data['Close'].iloc[-1]),
                    'latest_volume': int(price_data['Volume'].iloc[-1]),
                    'price_change_1d': float(price_data['Close'].pct_change().iloc[-1] * 100),
                    'price_change_5d': float(price_data['Close'].pct_change(5).iloc[-1] * 100),
                    'price_change_1m': float(price_data['Close'].pct_change(21).iloc[-1] * 100)
                }
            }
            
            # Cache the result
            self.set_cached_data(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting stock data for {ticker}: {e}")
            return {}

# Global instance
data_manager = SimpleDataManager()

def get_rankings_simple(universe: str, limit: int = 50) -> pd.DataFrame:
    """Simple function to get rankings"""
    return data_manager.get_rankings(universe, limit)

def get_stock_data_simple(ticker: str) -> Dict:
    """Simple function to get stock data"""
    return data_manager.get_stock_data(ticker)

def populate_universe_simple(universe: str) -> Dict:
    """Simple function to populate universe"""
    try:
        rankings = data_manager.process_universe(universe)
        return {
            "status": "success",
            "message": f"Universe {universe} processed successfully",
            "stocks_processed": len(rankings) if not rankings.empty else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
