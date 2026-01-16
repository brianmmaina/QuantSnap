#!/usr/bin/env python3
"""
Data Collection Script
Fetches historical stock data using yfinance and saves to CSV files.

Usage:
    python scripts/collect_data.py
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data" / "raw" / "stocks"
YEARS_OF_DATA = 3
START_DATE = (datetime.now() - timedelta(days=YEARS_OF_DATA * 365)).strftime('%Y-%m-%d')
END_DATE = datetime.now().strftime('%Y-%m-%d')

# Test stocks to start with
TEST_STOCKS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META", "NFLX", "AMD", "INTC"]

# Rate limiting: delay between API calls (seconds)
API_DELAY = 0.1


def ensure_data_directory() -> None:
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory ready: {DATA_DIR}")


def fetch_stock_data(ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    Fetch historical stock data for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        DataFrame with OHLCV data or None if fetch fails
    """
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
    """
    Save stock data to CSV file.
    
    Args:
        df: DataFrame with stock data
        ticker: Stock ticker symbol
    
    Returns:
        True if save successful, False otherwise
    """
    try:
        file_path = DATA_DIR / f"{ticker}.csv"
        df.to_csv(file_path, index=False)
        logger.info(f"Saved {len(df)} rows to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving data for {ticker}: {str(e)}")
        return False


def collect_stock_data(tickers: List[str], start_date: str, end_date: str) -> dict:
    """
    Collect data for multiple stocks.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Dictionary with collection statistics
    """
    stats = {
        'total': len(tickers),
        'success': 0,
        'failed': 0,
        'failed_tickers': []
    }
    
    logger.info(f"Starting data collection for {stats['total']} stocks...")
    logger.info(f"Date range: {start_date} to {end_date}")
    
    # Process each ticker with progress bar
    for ticker in tqdm(tickers, desc="Collecting data"):
        # Fetch data
        df = fetch_stock_data(ticker, start_date, end_date)
        
        if df is not None and not df.empty:
            # Save to CSV
            if save_stock_data(df, ticker):
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_tickers'].append(ticker)
        else:
            stats['failed'] += 1
            stats['failed_tickers'].append(ticker)
        
        # Rate limiting: small delay between API calls
        time.sleep(API_DELAY)
    
    return stats


def main():
    """Main function to run data collection."""
    print("=" * 60)
    print("Stock Data Collection Script")
    print("=" * 60)
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Collect data for test stocks
    logger.info(f"Collecting data for {len(TEST_STOCKS)} test stocks...")
    stats = collect_stock_data(TEST_STOCKS, START_DATE, END_DATE)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Collection Summary")
    print("=" * 60)
    print(f"Total stocks: {stats['total']}")
    print(f"Successfully collected: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    
    if stats['failed_tickers']:
        print(f"\nFailed tickers: {', '.join(stats['failed_tickers'])}")
    
    print(f"\nData saved to: {DATA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
