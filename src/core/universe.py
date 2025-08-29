"""
Universe management functions
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional


def load_sp500() -> pd.DataFrame:
    """Load S&P 500 tickers"""
    data_path = Path(__file__).parent.parent.parent / "data" / "universes" / "sp500.csv"
    if data_path.exists():
        df = pd.read_csv(data_path)
        # Standardize column names
        if 'ticker' in df.columns:
            df = df.rename(columns={'ticker': 'Ticker', 'name': 'Name'})
        return df
    else:
        # Fallback to a small list of major stocks
        return pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'],
            'Name': ['Apple Inc', 'Microsoft Corporation', 'Alphabet Inc', 'Amazon.com Inc', 
                    'Tesla Inc', 'NVIDIA Corporation', 'Meta Platforms Inc', 'Netflix Inc']
        })


def load_top_etfs() -> pd.DataFrame:
    """Load top ETF tickers"""
    data_path = Path(__file__).parent.parent.parent / "data" / "universes" / "top_etfs.csv"
    if data_path.exists():
        df = pd.read_csv(data_path)
        # Standardize column names
        if 'ticker' in df.columns:
            df = df.rename(columns={'ticker': 'Ticker', 'name': 'Name'})
        return df
    else:
        # Fallback to major ETFs
        return pd.DataFrame({
            'Ticker': ['SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'BND'],
            'Name': ['SPDR S&P 500 ETF', 'Invesco QQQ Trust', 'iShares Russell 2000 ETF', 
                    'Vanguard Total Stock Market ETF', 'Vanguard S&P 500 ETF', 
                    'Vanguard FTSE Developed Markets ETF', 'Vanguard FTSE Emerging Markets ETF',
                    'Vanguard Total Bond Market ETF']
        })


def load_popular_stocks() -> pd.DataFrame:
    """Load popular stocks including TSLA and other major companies"""
    data_path = Path(__file__).parent.parent.parent / "data" / "universes" / "popular_stocks.csv"
    if data_path.exists():
        df = pd.read_csv(data_path)
        # Standardize column names
        if 'ticker' in df.columns:
            df = df.rename(columns={'ticker': 'Ticker', 'name': 'Name'})
        return df
    else:
        # Fallback to major popular stocks
        return pd.DataFrame({
            'Ticker': ['TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'NFLX', 'AMD', 'CRM'],
            'Name': ['Tesla Inc', 'Apple Inc', 'Microsoft Corporation', 'Alphabet Inc', 'Amazon.com Inc',
                    'NVIDIA Corporation', 'Meta Platforms Inc', 'Netflix Inc', 'Advanced Micro Devices Inc',
                    'Salesforce Inc']
        })


def load_world_top_stocks() -> pd.DataFrame:
    """Load world's top 500+ stocks including major US, international, and emerging market stocks"""
    data_path = Path(__file__).parent.parent.parent / "data" / "universes" / "world_top_stocks.csv"
    if data_path.exists():
        df = pd.read_csv(data_path)
        # Standardize column names
        if 'ticker' in df.columns:
            df = df.rename(columns={'ticker': 'Ticker', 'name': 'Name'})
        return df
    else:
        # Fallback to major world stocks
        return pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'UNH', 'JNJ'],
            'Name': ['Apple Inc', 'Microsoft Corporation', 'Alphabet Inc', 'Amazon.com Inc', 'NVIDIA Corporation',
                    'Tesla Inc', 'Meta Platforms Inc', 'Berkshire Hathaway Inc', 'UnitedHealth Group Inc',
                    'Johnson & Johnson']
        })


def load_custom_csv(path: str) -> pd.DataFrame:
    """Load custom ticker list from CSV file"""
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Error loading custom CSV: {e}")
        return pd.DataFrame()


def get_universe(universe_name: str) -> pd.DataFrame:
    """
    Get ticker universe by name
    
    Args:
        universe_name: Name of universe ('world_top_stocks', 'sp500', 'top_etfs', 'popular_stocks')
        
    Returns:
        DataFrame with Ticker and Name columns
    """
    if universe_name == "world_top_stocks":
        return load_world_top_stocks()
    elif universe_name == "sp500":
        return load_sp500()
    elif universe_name == "top_etfs":
        return load_top_etfs()
    elif universe_name == "popular_stocks":
        return load_popular_stocks()
    else:
        raise ValueError(f"Unknown universe: {universe_name}")


def get_available_universes() -> List[str]:
    """Get list of available universes"""
    return ["world_top_stocks", "sp500", "top_etfs", "popular_stocks"]
