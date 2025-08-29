"""
Factor calculation functions for stock ranking
"""

import pandas as pd
import numpy as np
from typing import Union, Optional
from sklearn.linear_model import LinearRegression
import warnings

warnings.filterwarnings('ignore')


def pct_return(series: pd.Series, lookback: int) -> float:
    """
    Calculate percentage return over lookback period
    
    Args:
        series: Price series
        lookback: Number of days to look back
        
    Returns:
        Percentage return
    """
    if len(series) < lookback + 1:
        return np.nan
    
    current = series.iloc[-1]
    past = series.iloc[-lookback-1]
    
    if past == 0:
        return np.nan
    
    return (current / past) - 1


def slope_reg(prices: pd.Series, window: int = 50) -> float:
    """
    Calculate OLS slope of log prices over window
    
    Args:
        prices: Price series
        window: Number of days for regression
        
    Returns:
        Slope coefficient
    """
    if len(prices) < window:
        return np.nan
    
    # Use last 'window' days
    recent_prices = prices.tail(window)
    
    # Log transform
    log_prices = np.log(recent_prices)
    
    # Create time index
    X = np.arange(len(log_prices)).reshape(-1, 1)
    y = log_prices.values
    
    # Fit linear regression
    try:
        model = LinearRegression()
        model.fit(X, y)
        return model.coef_[0]
    except:
        return np.nan


def rolling_vol(returns: pd.Series, window: int = 30) -> float:
    """
    Calculate rolling volatility (standard deviation of returns)
    
    Args:
        returns: Return series
        window: Rolling window size
        
    Returns:
        Volatility (standard deviation)
    """
    if len(returns) < window:
        return np.nan
    
    return returns.tail(window).std()


def sharpe_approx(returns: pd.Series, window: int = 63, risk_free_rate: float = 0.02) -> float:
    """
    Calculate approximate Sharpe ratio
    
    Args:
        returns: Return series
        window: Rolling window size
        risk_free_rate: Annual risk-free rate
        
    Returns:
        Sharpe ratio
    """
    if len(returns) < window:
        return np.nan
    
    recent_returns = returns.tail(window)
    
    # Annualize
    mean_return = recent_returns.mean() * 252
    std_return = recent_returns.std() * np.sqrt(252)
    
    if std_return == 0:
        return np.nan
    
    return (mean_return - risk_free_rate) / std_return


def dollar_volume(close: pd.Series, volume: pd.Series, window: int = 20) -> float:
    """
    Calculate average dollar volume over window
    
    Args:
        close: Close price series
        volume: Volume series
        window: Rolling window size
        
    Returns:
        Average dollar volume
    """
    if len(close) < window or len(volume) < window:
        return np.nan
    
    # Calculate dollar volume
    dollar_vol = close * volume
    
    # Return average over window
    return dollar_vol.tail(window).mean()


def calculate_reputation_factors(ticker: str, close: pd.Series, volume: pd.Series) -> dict:
    """
    Calculate reputation factors for a ticker
    
    Args:
        ticker: Ticker symbol
        close: Close price series
        volume: Volume series
        
    Returns:
        Dictionary with reputation factor values
    """
    factors = {}
    
    try:
        import yfinance as yf
        
        # Get company info
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        # 1. ESG & Sustainability Metrics
        factors['ESG_Score'] = info.get('esgScores', {}).get('totalEsg', {}).get('raw', 0) / 100 if info.get('esgScores') else 0
        factors['Environmental_Score'] = info.get('esgScores', {}).get('environmentalScore', {}).get('raw', 0) / 100 if info.get('esgScores') else 0
        factors['Social_Score'] = info.get('esgScores', {}).get('socialScore', {}).get('raw', 0) / 100 if info.get('esgScores') else 0
        factors['Governance_Score'] = info.get('esgScores', {}).get('governanceScore', {}).get('raw', 0) / 100 if info.get('esgScores') else 0
        
        # 2. Financial Health Indicators
        factors['Debt_to_Equity'] = info.get('debtToEquity', 0) if info.get('debtToEquity') else 0
        factors['Current_Ratio'] = info.get('currentRatio', 0) if info.get('currentRatio') else 0
        factors['Quick_Ratio'] = info.get('quickRatio', 0) if info.get('quickRatio') else 0
        factors['ROE'] = info.get('returnOnEquity', 0) if info.get('returnOnEquity') else 0
        factors['ROA'] = info.get('returnOnAssets', 0) if info.get('returnOnAssets') else 0
        
        # 3. Market Position & Innovation
        factors['Market_Cap'] = info.get('marketCap', 0) if info.get('marketCap') else 0
        factors['Enterprise_Value'] = info.get('enterpriseValue', 0) if info.get('enterpriseValue') else 0
        factors['R&D_Spending'] = info.get('researchAndDevelopment', 0) if info.get('researchAndDevelopment') else 0
        
        # 4. Dividend & Stability
        factors['Dividend_Yield'] = info.get('dividendYield', 0) if info.get('dividendYield') else 0
        factors['Payout_Ratio'] = info.get('payoutRatio', 0) if info.get('payoutRatio') else 0
        factors['Beta'] = info.get('beta', 1) if info.get('beta') else 1
        
        # 5. Growth & Efficiency
        factors['Revenue_Growth'] = info.get('revenueGrowth', 0) if info.get('revenueGrowth') else 0
        factors['Earnings_Growth'] = info.get('earningsGrowth', 0) if info.get('earningsGrowth') else 0
        factors['Profit_Margins'] = info.get('profitMargins', 0) if info.get('profitMargins') else 0
        
        # 6. Liquidity & Trading
        factors['Volume_Avg'] = volume.mean() if len(volume) > 0 else 0
        factors['Price_Stability'] = 1 / (close.pct_change().std() + 0.001)  # Inverse of volatility
        
        # 7. Composite Reputation Score
        reputation_score = calculate_composite_reputation_score(factors)
        factors['Reputation_Score'] = reputation_score
        
    except Exception as e:
        # Set default values if data unavailable
        factors.update({
            'ESG_Score': 0, 'Environmental_Score': 0, 'Social_Score': 0, 'Governance_Score': 0,
            'Debt_to_Equity': 0, 'Current_Ratio': 0, 'Quick_Ratio': 0, 'ROE': 0, 'ROA': 0,
            'Market_Cap': 0, 'Enterprise_Value': 0, 'R&D_Spending': 0,
            'Dividend_Yield': 0, 'Payout_Ratio': 0, 'Beta': 1,
            'Revenue_Growth': 0, 'Earnings_Growth': 0, 'Profit_Margins': 0,
            'Volume_Avg': 0, 'Price_Stability': 0, 'Reputation_Score': 0
        })
    
    return factors


def calculate_composite_reputation_score(factors: dict) -> float:
    """
    Calculate composite reputation score from individual factors
    
    Args:
        factors: Dictionary of reputation factors
        
    Returns:
        Composite reputation score (0-1)
    """
    score = 0
    weights = {
        # ESG (20%)
        'ESG_Score': 0.20,
        'Environmental_Score': 0.05,
        'Social_Score': 0.05,
        'Governance_Score': 0.05,
        
        # Financial Health (25%)
        'Debt_to_Equity': 0.05,  # Lower is better
        'Current_Ratio': 0.05,
        'Quick_Ratio': 0.05,
        'ROE': 0.05,
        'ROA': 0.05,
        
        # Market Position (20%)
        'Market_Cap': 0.10,  # Log scale
        'R&D_Spending': 0.05,
        'Revenue_Growth': 0.05,
        
        # Stability (20%)
        'Dividend_Yield': 0.05,
        'Beta': 0.05,  # Lower is better
        'Price_Stability': 0.05,
        'Profit_Margins': 0.05,
        
        # Growth (15%)
        'Earnings_Growth': 0.10,
        'Volume_Avg': 0.05  # Log scale
    }
    
    for factor, weight in weights.items():
        if factor in factors:
            value = factors[factor]
            
            # Normalize different metrics
            if factor == 'Debt_to_Equity':
                # Lower debt is better
                normalized = max(0, 1 - min(value / 2, 1))  # Cap at 200% debt
            elif factor == 'Beta':
                # Lower beta is better
                normalized = max(0, 1 - min(value - 1, 1))  # 1 is market average
            elif factor in ['Market_Cap', 'Volume_Avg', 'R&D_Spending']:
                # Log scale for large numbers
                normalized = min(1, np.log10(max(value, 1)) / 10)
            elif factor in ['ESG_Score', 'Environmental_Score', 'Social_Score', 'Governance_Score']:
                # Already 0-1 scale
                normalized = value
            elif factor in ['Current_Ratio', 'Quick_Ratio']:
                # Higher is better, cap at 3
                normalized = min(1, value / 3)
            elif factor in ['ROE', 'ROA', 'Revenue_Growth', 'Earnings_Growth', 'Profit_Margins']:
                # Higher is better, cap at reasonable levels
                normalized = min(1, max(0, value))
            elif factor == 'Dividend_Yield':
                # Higher is better, cap at 10%
                normalized = min(1, value / 0.10)
            elif factor == 'Price_Stability':
                # Already normalized
                normalized = min(1, value)
            else:
                normalized = min(1, max(0, value))
            
            score += normalized * weight
    
    return min(1, max(0, score))  # Ensure 0-1 range


def calculate_all_factors(
    close: pd.Series, 
    volume: pd.Series, 
    returns: pd.Series,
    ticker: str = None
) -> dict:
    """
    Calculate all factors for a single ticker
    
    Args:
        close: Close price series
        volume: Volume series
        returns: Return series
        ticker: Ticker symbol for reputation data
        
    Returns:
        Dictionary with all factor values
    """
    factors = {}
    
    # Momentum factors
    factors['MOM_1M'] = pct_return(close, 21)
    factors['MOM_3M'] = pct_return(close, 63)
    
    # Trend factor
    factors['Slope_50d'] = slope_reg(close, 50)
    
    # Volatility factor
    factors['Vol_30d'] = rolling_vol(returns, 30)
    
    # Risk-adjusted return
    factors['Sharpe_3M'] = sharpe_approx(returns, 63)
    
    # Liquidity factor
    factors['DollarVol_20d'] = dollar_volume(close, volume, 20)
    
    # Reputation factors (if ticker provided)
    if ticker:
        reputation_factors = calculate_reputation_factors(ticker, close, volume)
        factors.update(reputation_factors)
    
    return factors


def calculate_universe_factors(
    prices: pd.DataFrame,
    min_data_points: int = 65
) -> pd.DataFrame:
    """
    Calculate factors for all tickers in universe
    
    Args:
        prices: MultiIndex DataFrame with price data
        min_data_points: Minimum data points required
        
    Returns:
        DataFrame with factors for each ticker
    """
    # Handle different data structures from yfinance
    if isinstance(prices.columns, pd.MultiIndex):
        # Multi-index case (multiple tickers)
        # Check if we have 'Adj Close' or 'Close'
        if ('Adj Close',) in prices.columns.get_level_values(1):
            adj_close = prices.xs('Adj Close', axis=1, level=1)
        else:
            # Use 'Close' if 'Adj Close' not available
            adj_close = prices.xs('Close', axis=1, level=1)
        
        volume = prices.xs('Volume', axis=1, level=1)
    else:
        # Single ticker case
        if 'Adj Close' in prices.columns:
            adj_close = prices['Adj Close']
        else:
            adj_close = prices['Close']
        volume = prices['Volume']
        # Convert to DataFrame with single column
        adj_close = pd.DataFrame(adj_close)
        volume = pd.DataFrame(volume)
    
    # Calculate returns
    returns = adj_close.pct_change()
    
    # Calculate factors for each ticker
    factor_data = {}
    
    for ticker in adj_close.columns:
        close_series = adj_close[ticker].dropna()
        volume_series = volume[ticker].dropna()
        returns_series = returns[ticker].dropna()
        
        # Skip if insufficient data
        if len(close_series) < min_data_points:
            continue
            
        try:
            factors = calculate_all_factors(close_series, volume_series, returns_series, ticker)
            factor_data[ticker] = factors
        except Exception as e:
            print(f"Error calculating factors for {ticker}: {e}")
            continue
    
    return pd.DataFrame.from_dict(factor_data, orient='index')
