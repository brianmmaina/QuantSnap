 #!/usr/bin/env python3
"""
Quick database population script for QuantSnap
Faster initial population with essential data only
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.infrastructure.database import StockDatabase, init_database
from src.core.universe import get_universe
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_populate():
    """Quick population with essential data only"""
    try:
        logger.info("Starting quick database population...")
        
        # Initialize database
        init_database()
        db = StockDatabase()
        
        # Start with popular stocks only (fastest)
        universe_name = 'popular_stocks'
        logger.info(f"Processing {universe_name}...")
        
        # Get tickers
        universe_df = get_universe(universe_name)
        tickers = universe_df['Ticker'].tolist()
        
        logger.info(f"Processing {len(tickers)} tickers: {tickers}")
        
        # Process each ticker
        for ticker in tickers:
            try:
                logger.info(f"Processing {ticker}...")
                
                # Fetch price data (1 year)
                ticker_obj = yf.Ticker(ticker)
                hist = ticker_obj.history(period="1y")
                
                if hist.empty:
                    logger.warning(f"No data for {ticker}")
                    continue
                
                # Get company info
                info = ticker_obj.info
                company_data = {
                    'ticker': ticker,
                    'name': info.get('longName', info.get('shortName', ticker)),
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'market_cap': info.get('marketCap', 0),
                    'enterprise_value': info.get('enterpriseValue', 0)
                }
                
                # Insert company data
                db.insert_company(**company_data)
                
                # Insert price data
                price_data = hist.reset_index()
                price_data['ticker'] = ticker
                price_data = price_data.rename(columns={
                    'Date': 'date',
                    'Open': 'open_price',
                    'High': 'high_price',
                    'Low': 'low_price',
                    'Close': 'close_price',
                    'Adj Close': 'adj_close',
                    'Volume': 'volume'
                })
                db.insert_daily_prices(price_data)
                
                logger.info(f"✅ {ticker} processed successfully")
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                continue
        
        logger.info("Quick population completed!")
        
        # Test the data
        test_query = "SELECT COUNT(*) as count FROM companies"
        result = db.db.read_dataframe(test_query)
        logger.info(f"Companies in database: {result['count'].iloc[0]}")
        
        test_query = "SELECT COUNT(*) as count FROM daily_prices"
        result = db.db.read_dataframe(test_query)
        logger.info(f"Price records in database: {result['count'].iloc[0]}")
        
    except Exception as e:
        logger.error(f"Quick population failed: {e}")
        raise

if __name__ == "__main__":
    quick_populate()
