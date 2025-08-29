"""
Data pipeline for AI Daily Draft
Following the basketball scout pattern with clean data processing
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import time

from .database import StockDatabase, init_database
from core.factors import calculate_all_factors
from core.scoring import rank_tickers, create_composite_reputation_factors
from core.universe import get_universe

logger = logging.getLogger(__name__)

class DataPipeline:
    """Data pipeline for fetching, cleaning, and storing stock data"""
    
    def __init__(self):
        self.db = StockDatabase()
        self.today = datetime.now().date()
    
    def fetch_and_clean_prices(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        """Fetch and clean price data from Yahoo Finance"""
        logger.info(f"Fetching price data for {len(tickers)} tickers")
        
        try:
            #fetches data in batches to avoid rate limiting
            batch_size = 50
            all_data = {}
            
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} tickers")
                
                data = yf.download(
                    batch,
                    period=period,
                    interval="1d",
                    auto_adjust=True,
                    group_by='ticker',
                    progress=False
                )
                
                # Handles single ticker case
                if len(batch) == 1:
                    data.columns = pd.MultiIndex.from_product([[batch[0]], data.columns])
                
                # Process each ticker
                for ticker in batch:
                    if ticker in data.columns.get_level_values(0):
                        ticker_data = data.xs(ticker, axis=1, level=0)
                        if not ticker_data.empty:
                            all_data[ticker] = ticker_data
                
                # Rate limiting
                time.sleep(1)
            
            logger.info(f"Successfully fetched data for {len(all_data)} tickers")
            return all_data
            
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            raise
    
    def clean_company_data(self, ticker: str) -> Dict:
        """Fetch and clean company information"""
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            # Clean and validate data
            company_data = {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'enterprise_value': info.get('enterpriseValue', 0)
            }
            
            # Validate required fields
            if not company_data['name'] or company_data['name'] == 'None':
                company_data['name'] = ticker
            
            return company_data
            
        except Exception as e:
            logger.warning(f"Error fetching company data for {ticker}: {e}")
            return {
                'ticker': ticker,
                'name': ticker,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 0,
                'enterprise_value': 0
            }
    
    def calculate_factors_for_ticker(self, ticker: str, price_data: pd.DataFrame) -> Dict:
        """Calculate all factors for a single ticker"""
        try:
            if price_data.empty or len(price_data) < 65:
                logger.warning(f"Insufficient data for {ticker}")
                return None
            
            # Extract price series
            close_prices = price_data['Close']
            volume = price_data['Volume']
            returns = close_prices.pct_change().dropna()
            
            # Calculate traditional factors
            factors = calculate_all_factors(close_prices, volume, returns, ticker)
            
            # Add date
            factors['date'] = self.today
            factors['ticker'] = ticker
            
            return factors
            
        except Exception as e:
            logger.error(f"Error calculating factors for {ticker}: {e}")
            return None
    
    def process_universe(self, universe_name: str) -> None:
        """Process entire universe: fetch, clean, calculate, and store"""
        logger.info(f"Processing universe: {universe_name}")
        
        try:
            # Get universe tickers
            universe_df = get_universe(universe_name)
            tickers = universe_df['Ticker'].tolist()
            names = dict(zip(universe_df['Ticker'], universe_df['Name']))
            
            logger.info(f"Processing {len(tickers)} tickers for {universe_name}")
            
            # Step 1: Fetch and clean price data
            price_data_dict = self.fetch_and_clean_prices(tickers)
            
            # Step 2: Process companies and store
            companies_data = []
            factors_data = []
            
            for ticker in tickers:
                if ticker in price_data_dict:
                    # Clean company data
                    company_data = self.clean_company_data(ticker)
                    companies_data.append(company_data)
                    
                    # Calculate factors
                    factors = self.calculate_factors_for_ticker(ticker, price_data_dict[ticker])
                    if factors:
                        factors_data.append(factors)
                    
                    # Store price data
                    self.db.insert_daily_prices(price_data_dict[ticker])
            
            # Step 3: Store company data
            if companies_data:
                companies_df = pd.DataFrame(companies_data)
                self.db.insert_dataframe(companies_df, 'companies', if_exists='replace')
            
            # Step 4: Store factors
            if factors_data:
                factors_df = pd.DataFrame(factors_data)
                # Ensure date column is properly formatted
                if 'date' in factors_df.columns:
                    factors_df['date'] = pd.to_datetime(factors_df['date']).dt.date
                factors_df = create_composite_reputation_factors(factors_df)
                self.db.insert_daily_factors(factors_df)
                
                # Step 5: Calculate rankings
                rankings_df = rank_tickers(factors_df)
                self.db.insert_daily_rankings(rankings_df, universe_name)
            
            logger.info(f"Successfully processed {universe_name}: {len(factors_data)} stocks")
            
        except Exception as e:
            logger.error(f"Error processing universe {universe_name}: {e}")
            raise
    
    def update_single_stock(self, ticker: str) -> None:
        """Update data for a single stock"""
        logger.info(f"Updating data for {ticker}")
        
        try:
            # Fetch price data
            price_data = yf.download(ticker, period="1y", interval="1d", auto_adjust=True, progress=False)
            
            if price_data.empty:
                logger.warning(f"No price data available for {ticker}")
                return
            
            # Clean company data
            company_data = self.clean_company_data(ticker)
            
            # Calculate factors
            factors = self.calculate_factors_for_ticker(ticker, price_data)
            
            if factors:
                # Store data
                self.db.insert_company(**company_data)
                self.db.insert_daily_prices(price_data)
                
                factors_df = pd.DataFrame([factors])
                factors_df = create_composite_reputation_factors(factors_df)
                self.db.insert_daily_factors(factors_df)
                
                logger.info(f"Successfully updated {ticker}")
            else:
                logger.warning(f"Could not calculate factors for {ticker}")
                
        except Exception as e:
            logger.error(f"Error updating {ticker}: {e}")
            raise
    
    def get_data_quality_report(self, universe_name: str) -> Dict:
        """Generate data quality report for universe"""
        try:
            # Get latest data
            rankings = self.db.get_latest_rankings(universe_name, limit=1000)
            
            if rankings.empty:
                return {"error": "No data available"}
            
            # Calculate quality metrics
            total_stocks = len(rankings)
            stocks_with_factors = len(rankings.dropna(subset=['score']))
            stocks_with_reputation = len(rankings.dropna(subset=['reputation_score']))
            
            # Data completeness
            completeness = {
                'total_stocks': total_stocks,
                'stocks_with_factors': stocks_with_factors,
                'stocks_with_reputation': stocks_with_reputation,
                'factor_completeness': stocks_with_factors / total_stocks if total_stocks > 0 else 0,
                'reputation_completeness': stocks_with_reputation / total_stocks if total_stocks > 0 else 0
            }
            
            # Score distribution
            score_stats = {
                'mean_score': rankings['score'].mean(),
                'median_score': rankings['score'].median(),
                'std_score': rankings['score'].std(),
                'min_score': rankings['score'].min(),
                'max_score': rankings['score'].max()
            }
            
            return {
                'universe': universe_name,
                'date': self.today.isoformat(),
                'completeness': completeness,
                'score_statistics': score_stats,
                'top_5_stocks': rankings.head(5)[['ticker', 'name', 'score', 'rank']].to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error generating quality report for {universe_name}: {e}")
            return {"error": str(e)}

def run_daily_pipeline():
    """Run the complete daily data pipeline"""
    logger.info("Starting daily data pipeline")
    
    try:
        # Initialize database
        init_database()
        
        # Initialize pipeline
        pipeline = DataPipeline()
        
        # Process all universes
        universes = ['world_top_stocks', 'sp500', 'top_etfs', 'popular_stocks']
        
        for universe in universes:
            try:
                pipeline.process_universe(universe)
                
                # Generate quality report
                report = pipeline.get_data_quality_report(universe)
                logger.info(f"Quality report for {universe}: {report}")
                
            except Exception as e:
                logger.error(f"Failed to process universe {universe}: {e}")
                continue
        
        logger.info("Daily pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Daily pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_daily_pipeline()
