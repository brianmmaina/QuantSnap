"""
Database connection and models for AI Daily Draft
Following the basketball scout pattern with PostgreSQL
"""

import os
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/ai_daily_draft')

def get_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def get_engine():
    """Get SQLAlchemy engine for pandas operations"""
    try:
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        logger.error(f"Database engine creation failed: {e}")
        raise

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self):
        self.engine = get_engine()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results as list of dicts"""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()
    
    def execute_update(self, query: str, params: tuple = None) -> None:
        """Execute INSERT/UPDATE/DELETE query without returning results"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute multiple queries"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, params_list)
                conn.commit()
    
    def insert_dataframe(self, df: pd.DataFrame, table: str, if_exists: str = 'append') -> None:
        """Insert DataFrame into database table"""
        try:
            df.to_sql(table, self.engine, if_exists=if_exists, index=False)
            logger.info(f"Inserted {len(df)} rows into {table}")
        except Exception as e:
            logger.error(f"Failed to insert DataFrame into {table}: {e}")
            raise
    
    def read_dataframe(self, query: str) -> pd.DataFrame:
        """Read query results into DataFrame"""
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logger.error(f"Failed to read DataFrame: {e}")
            raise

# Database operations for stocks
class StockDatabase:
    """Stock-specific database operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def insert_company(self, ticker: str, name: str, sector: str = None, 
                      industry: str = None, market_cap: int = None, 
                      enterprise_value: int = None) -> None:
        """Insert or update company information"""
        query = """
        INSERT INTO companies (ticker, name, sector, industry, market_cap, enterprise_value)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticker) 
        DO UPDATE SET 
            name = EXCLUDED.name,
            sector = EXCLUDED.sector,
            industry = EXCLUDED.industry,
            market_cap = EXCLUDED.market_cap,
            enterprise_value = EXCLUDED.enterprise_value,
            updated_at = CURRENT_TIMESTAMP
        """
        self.db.execute_update(query, (ticker, name, sector, industry, market_cap, enterprise_value))
    
    def insert_daily_prices(self, df: pd.DataFrame) -> None:
        """Insert daily price data"""
        # Clean and prepare data
        df_clean = df.reset_index(drop=True)  # Drop the index instead of keeping it
        
        # Handle both 'date' and 'Date' column names
        if 'Date' in df_clean.columns:
            df_clean = df_clean.rename(columns={'Date': 'date'})
        
        df_clean['date'] = pd.to_datetime(df_clean['date']).dt.date
        
        # Rename columns to match schema
        column_mapping = {
            'Open': 'open_price',
            'High': 'high_price', 
            'Low': 'low_price',
            'Close': 'close_price',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        }
        df_clean = df_clean.rename(columns=column_mapping)
        
        # Insert into database
        self.db.insert_dataframe(df_clean, 'daily_prices', if_exists='append')
    
    def insert_daily_factors(self, df: pd.DataFrame) -> None:
        """Insert calculated factors"""
        df_clean = df.reset_index(drop=True)  # Drop the index instead of keeping it
        
        # Handle both 'date' and 'Date' column names
        if 'Date' in df_clean.columns:
            df_clean = df_clean.rename(columns={'Date': 'date'})
        
        df_clean['date'] = pd.to_datetime(df_clean['date']).dt.date
        
        self.db.insert_dataframe(df_clean, 'daily_factors', if_exists='append')
    
    def insert_daily_rankings(self, df: pd.DataFrame, universe: str) -> None:
        """Insert daily rankings"""
        df_clean = df.reset_index(drop=True)  # Drop the index instead of keeping it
        df_clean['date'] = pd.to_datetime(df_clean['date']).dt.date
        df_clean['universe'] = universe
        
        self.db.insert_dataframe(df_clean, 'daily_rankings', if_exists='append')
    
    def get_latest_prices(self, tickers: List[str], days: int = 252) -> pd.DataFrame:
        """Get latest price data for tickers"""
        tickers_str = "','".join(tickers)
        query = f"""
        SELECT ticker, date, open_price, high_price, low_price, 
               close_price, adj_close, volume
        FROM daily_prices 
        WHERE ticker IN ('{tickers_str}')
        AND date >= CURRENT_DATE - INTERVAL '{days} days'
        ORDER BY ticker, date
        """
        return self.db.read_dataframe(query)
    
    def get_latest_factors(self, tickers: List[str]) -> pd.DataFrame:
        """Get latest factors for tickers"""
        tickers_str = "','".join(tickers)
        query = f"""
        SELECT f.*, c.name, c.sector, c.industry
        FROM daily_factors f
        JOIN companies c ON f.ticker = c.ticker
        WHERE f.ticker IN ('{tickers_str}')
        AND f.date = (SELECT MAX(date) FROM daily_factors)
        ORDER BY f.score DESC
        """
        return self.db.read_dataframe(query)
    
    def get_latest_rankings(self, universe: str, limit: int = 50) -> pd.DataFrame:
        """Get latest rankings for universe"""
        query = f"""
        SELECT r.*, c.name, c.sector, c.industry
        FROM daily_rankings r
        JOIN companies c ON r.ticker = c.ticker
        WHERE r.universe = '{universe}'
        AND r.date = (SELECT MAX(date) FROM daily_rankings WHERE universe = '{universe}')
        ORDER BY r.rank
        LIMIT {limit}
        """
        return self.db.read_dataframe(query)
    
    def get_historical_rankings(self, ticker: str, universe: str, days: int = 30) -> pd.DataFrame:
        """Get historical rankings for a ticker"""
        query = f"""
        SELECT date, rank, score
        FROM daily_rankings
        WHERE ticker = '{ticker}'
        AND universe = '{universe}'
        AND date >= CURRENT_DATE - INTERVAL '{days} days'
        ORDER BY date
        """
        return self.db.read_dataframe(query)

# Initialize database
def init_database():
    """Initialize database tables"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Read and execute schema
                schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
                with open(schema_path, 'r') as f:
                    schema = f.read()
                    cur.execute(schema)
                conn.commit()
                logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
