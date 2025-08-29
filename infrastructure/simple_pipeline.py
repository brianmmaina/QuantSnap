#!/usr/bin/env python3
"""
Simplified data pipeline inspired by the basketball scout approach
Saves processed data to CSV files for easier management
"""

import pandas as pd
import yfinance as yf
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import os

# Import our core modules
from src.core.factors import calculate_all_factors
from src.core.scoring import create_composite_reputation_factors, rank_tickers
from src.core.universe import get_universe

logger = logging.getLogger(__name__)

class SimpleDataPipeline:
    """Simplified data pipeline that saves to CSV files"""
    
    def __init__(self):
        self.today = datetime.now().date()
        self.data_dir = Path("data/processed")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_stock_data(self, tickers: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
        """Fetch stock data from Yahoo Finance"""
        logger.info(f"Fetching data for {len(tickers)} tickers")
        
        all_data = {}
        batch_size = 10  # Smaller batches to avoid rate limiting
        
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {batch}")
            
            try:
                data = yf.download(
                    batch,
                    period=period,
                    interval="1d",
                    auto_adjust=True,
                    group_by='ticker',
                    progress=False
                )
                
                # Handle single ticker case
                if len(batch) == 1:
                    data.columns = pd.MultiIndex.from_product([[batch[0]], data.columns])
                
                # Process each ticker
                for ticker in batch:
                    if ticker in data.columns.get_level_values(0):
                        ticker_data = data.xs(ticker, axis=1, level=0)
                        if not ticker_data.empty and len(ticker_data) >= 65:
                            all_data[ticker] = ticker_data
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching batch {batch}: {e}")
                continue
        
        logger.info(f"Successfully fetched data for {len(all_data)} tickers")
        return all_data
    
    def calculate_factors_for_ticker(self, ticker: str, price_data: pd.DataFrame) -> Dict:
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
            factors['date'] = self.today
            
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
    
    def process_universe(self, universe_name: str) -> None:
        """Process a universe and save to CSV files"""
        logger.info(f"Processing universe: {universe_name}")
        
        try:
            # Get universe tickers
            universe_df = get_universe(universe_name)
            tickers = universe_df['Ticker'].tolist()
            
            logger.info(f"Processing {len(tickers)} tickers for {universe_name}")
            
            # Fetch stock data
            stock_data = self.fetch_stock_data(tickers)
            
            # Calculate factors and company info
            factors_list = []
            companies_list = []
            
            for ticker in tickers:
                if ticker in stock_data:
                    # Get company info
                    company_info = self.get_company_info(ticker)
                    companies_list.append(company_info)
                    
                    # Calculate factors
                    factors = self.calculate_factors_for_ticker(ticker, stock_data[ticker])
                    if factors:
                        factors_list.append(factors)
            
            if factors_list:
                # Create factors DataFrame
                factors_df = pd.DataFrame(factors_list)
                
                # Add reputation factors
                factors_df = create_composite_reputation_factors(factors_df)
                
                # Calculate rankings
                rankings_df = rank_tickers(factors_df)
                
                # Save to CSV files
                factors_file = self.data_dir / f"{universe_name}_factors.csv"
                rankings_file = self.data_dir / f"{universe_name}_rankings.csv"
                companies_file = self.data_dir / f"{universe_name}_companies.csv"
                
                factors_df.to_csv(factors_file, index=False)
                rankings_df.to_csv(rankings_file, index=False)
                
                if companies_list:
                    companies_df = pd.DataFrame(companies_list)
                    companies_df.to_csv(companies_file, index=False)
                
                logger.info(f"Successfully processed {universe_name}: {len(factors_list)} stocks")
                logger.info(f"Files saved: {factors_file}, {rankings_file}, {companies_file}")
                
            else:
                logger.warning(f"No factors calculated for {universe_name}")
                
        except Exception as e:
            logger.error(f"Error processing universe {universe_name}: {e}")
            raise
    
    def get_rankings(self, universe_name: str, limit: int = 50) -> pd.DataFrame:
        """Get rankings from CSV file"""
        rankings_file = self.data_dir / f"{universe_name}_rankings.csv"
        
        if rankings_file.exists():
            df = pd.read_csv(rankings_file)
            return df.head(limit)
        else:
            logger.warning(f"Rankings file not found: {rankings_file}")
            return pd.DataFrame()
    
    def get_stock_data(self, ticker: str) -> Dict:
        """Get stock data from CSV files"""
        # Find which universe contains this ticker
        for universe_file in self.data_dir.glob("*_rankings.csv"):
            universe_name = universe_file.stem.replace("_rankings", "")
            
            df = pd.read_csv(universe_file)
            if ticker in df['ticker'].values:
                stock_row = df[df['ticker'] == ticker].iloc[0]
                return stock_row.to_dict()
        
        return {}
    
    def list_available_universes(self) -> List[str]:
        """List available universes based on CSV files"""
        universes = []
        for file in self.data_dir.glob("*_rankings.csv"):
            universe_name = file.stem.replace("_rankings", "")
            universes.append(universe_name)
        return universes

def quick_populate():
    """Quick populate function for popular stocks"""
    pipeline = SimpleDataPipeline()
    pipeline.process_universe('popular_stocks')
    return {
        "status": "success",
        "message": "Popular stocks processed and saved to CSV",
        "files_created": list(pipeline.data_dir.glob("*_*.csv"))
    }
