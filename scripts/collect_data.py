#!/usr/bin/env python3
"""
Data Collection Script
Fetches historical stock data using yfinance and saves to CSV files.
"""

import yfinance as yf
import pandas as pd
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from tqdm import tqdm
import time

# logs timestamps, levels, and messages to track progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Builds data/raw/stocks/ relative to the script 
DATA_DIR = Path(__file__).parent.parent / "data" / "raw" / "stocks"
YEARS_OF_DATA = 3
START_DATE = (datetime.now() - timedelta(days=YEARS_OF_DATA * 365)).strftime('%Y-%m-%d')
END_DATE = datetime.now().strftime('%Y-%m-%d')

# Import universe configuration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from app.config.universe import get_universe

# Use full universe from config
STOCK_UNIVERSE = get_universe()

# For testing, use a subset (first 10 stocks)
TEST_STOCKS = STOCK_UNIVERSE[:10]

# Rate limiting: delay between API calls (seconds) so we dont get throttle limited
API_DELAY = 0.1

# creates the directory if missing (parents=True creates parents; exist_ok=True avoids errors if it exists)
def ensure_data_directory() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory ready: {DATA_DIR}")


def fetch_stock_data(ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:

# Creates a yfinance ticker object for the symbol
    try:
        logger.debug(f"Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)
        
        # Fetch historical data
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return None
        
        # Reset index to make Date a column
        df.reset_index(inplace=True)
        
        # Rename columns to standard format (Date, Open, High, Low, Close, Volume)
        df.rename(columns={
            'Date': 'Date',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        }, inplace=True)
        
        # Select only the columns we need
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Ensure Date is datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Sort by date
        df.sort_values('Date', inplace=True)
        
        # Reset index
        df.reset_index(drop=True, inplace=True)
        
        logger.debug(f"Successfully fetched {len(df)} rows for {ticker}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return None


def save_stock_data(df: pd.DataFrame, ticker: str) -> bool:

    # Saves the dataframe to a CSV file
    try:
        file_path = DATA_DIR / f"{ticker}.csv"
        df.to_csv(file_path, index=False)
        logger.info(f"Saved {len(df)} rows to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving data for {ticker}: {str(e)}")
        return False


def collect_stock_data(tickers: List[str], start_date: str, end_date: str) -> dict:
    # initializes a dictionary to track statistics
    stats = {
        'total': len(tickers),
        'success': 0,
        'failed': 0,
        'failed_tickers': []
    }
    
    # logs the total number of stocks and the date range
    logger.info(f"Starting data collection for {stats['total']} stocks...")
    logger.info(f"Date range: {start_date} to {end_date}")
    
    # Process each ticker with progress bar to track progress
    for ticker in tqdm(tickers, desc="Collecting data"):
        # Fetches data for the ticker
        df = fetch_stock_data(ticker, start_date, end_date)
        
        if df is not None and not df.empty:
            # Saves the data to a CSV file
            if save_stock_data(df, ticker):
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_tickers'].append(ticker)
        else:
            stats['failed'] += 1
            stats['failed_tickers'].append(ticker)
        
        # Rate limiting: small delay between API calls so we dont get throttle limited
        time.sleep(API_DELAY)
    
    return stats


def main():
    # Main function to run data collection.
    print("=" * 60)
    print("Stock Data Collection Script")
    print("=" * 60)
    
    # Ensures the data directory exists
    ensure_data_directory()
    
    # Collect data for all stocks in universe
    STOCK_UNIVERSE = get_universe()
    logger.info(f"Collecting data for {len(STOCK_UNIVERSE)} stocks in universe...")
    stats = collect_stock_data(STOCK_UNIVERSE, START_DATE, END_DATE)
    
    # Prints the summary
    print("\n" + "=" * 60)
    print("Collection Summary")
    print("=" * 60)
    print(f"Total stocks: {stats['total']}")
    print(f"Successfully collected: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    
    # Prints the failed tickers
    if stats['failed_tickers']:
        print(f"\nFailed tickers: {', '.join(stats['failed_tickers'])}")
    
    # Prints the data saved to
    print(f"\nData saved to the directory: {DATA_DIR}")
    print("=" * 60)


# Runs the main function if the script is executed directly
if __name__ == "__main__":
    main()
