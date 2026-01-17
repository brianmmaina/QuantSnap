"""
Feature Engineering Module
Computes predictive features from raw OHLCV stock data.

This module creates 15 features including:
- Price/momentum features (5): returns, moving averages
- Volatility features (3): ATR, volatility, RSI
- Mean reversion features (2): price deviation, Bollinger position
- Volume features (2): volume ratios, volume trends
- Cross-asset features (3): SPY correlation, relative performance, market regime
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# PRICE/MOMENTUM FEATURES (Partner A)
# ============================================================================

def compute_price_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute price and momentum features.
    
    Features:
    1. return_1d: 1-day return
    2. return_5d: 5-day return  
    3. return_20d: 20-day return
    4. price_sma50_ratio: Price relative to 50-day moving average
    5. price_sma200_ratio: Price relative to 200-day moving average
    
    Args:
        df: DataFrame with Date, Close columns
    
    Returns:
        DataFrame with added momentum features
    """
    df = df.copy()
    
    # Calculate returns (percentage change)
    df['return_1d'] = df['Close'].pct_change(1) * 100  # 1-day return in %
    df['return_5d'] = df['Close'].pct_change(5) * 100  # 5-day return in %
    df['return_20d'] = df['Close'].pct_change(20) * 100  # 20-day return in %
    
    # Calculate moving averages
    df['sma_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
    df['sma_200'] = df['Close'].rolling(window=200, min_periods=1).mean()
    
    # Price ratios to moving averages (measures momentum/trend)
    df['price_sma50_ratio'] = (df['Close'] / df['sma_50']) - 1  # Deviation from 50-day MA
    df['price_sma200_ratio'] = (df['Close'] / df['sma_200']) - 1  # Deviation from 200-day MA
    
    # Drop intermediate columns
    df.drop(['sma_50', 'sma_200'], axis=1, inplace=True)
    
    return df


# ============================================================================
# VOLATILITY FEATURES (Partner A)
# ============================================================================

def compute_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute volatility and risk features.
    
    Features:
    1. atr_normalized: Average True Range normalized by price (14-day window)
    2. volatility_20d: 20-day rolling standard deviation of returns (annualized)
    3. rsi_14: Relative Strength Index (14-day window)
    
    Args:
        df: DataFrame with Date, Open, High, Low, Close columns
    
    Returns:
        DataFrame with added volatility features
    """
    df = df.copy()
    
    # Calculate returns for volatility
    returns = df['Close'].pct_change()
    
    # 1. Average True Range (ATR) - measures volatility
    # ATR = average of True Range over N periods
    # True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr_14'] = true_range.rolling(window=14, min_periods=1).mean()
    
    # Normalize ATR by price (makes it comparable across stocks)
    df['atr_normalized'] = (df['atr_14'] / df['Close']) * 100  # Percentage
    
    # 2. Volatility (standard deviation of returns, annualized)
    df['volatility_20d'] = returns.rolling(window=20, min_periods=1).std() * np.sqrt(252) * 100
    
    # 3. Relative Strength Index (RSI) - measures momentum/overbought/oversold
    # RSI = 100 - (100 / (1 + RS))
    # RS = Average Gain / Average Loss over N periods
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # Drop intermediate columns
    df.drop(['atr_14'], axis=1, inplace=True)
    
    return df


# ============================================================================
# MEAN REVERSION FEATURES (Partner A)
# ============================================================================

def compute_mean_reversion_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute mean reversion features.
    
    These features help identify oversold/overbought conditions:
    - When price deviates significantly from its average, it may revert
    
    Features:
    1. price_deviation_from_sma20: How far price is from 20-day moving average
    2. bollinger_position: Position within Bollinger Bands (-1 to +1 range)
    
    Args:
        df: DataFrame with Date, Close columns
    
    Returns:
        DataFrame with added mean reversion features
    """
    df = df.copy()
    
    # Calculate 20-day moving average
    df['sma_20'] = df['Close'].rolling(window=20, min_periods=1).mean()
    
    # Calculate 20-day standard deviation (for Bollinger Bands)
    df['std_20'] = df['Close'].rolling(window=20, min_periods=1).std()
    
    # 1. Price deviation from SMA20 (mean reversion indicator)
    # Positive = price above average (possibly overbought)
    # Negative = price below average (possibly oversold)
    df['price_deviation_from_sma20'] = ((df['Close'] - df['sma_20']) / df['sma_20']) * 100
    
    # 2. Bollinger Band Position
    # Bollinger Bands = SMA ± (2 × std)
    # Position tells us where price is within the bands:
    #   -1 = at lower band (oversold)
    #   0  = at middle (SMA20)
    #   +1 = at upper band (overbought)
    bollinger_upper = df['sma_20'] + (2 * df['std_20'])
    bollinger_lower = df['sma_20'] - (2 * df['std_20'])
    bollinger_width = bollinger_upper - bollinger_lower
    
    # Avoid division by zero
    df['bollinger_position'] = np.where(
        bollinger_width > 0,
        (df['Close'] - df['sma_20']) / (bollinger_width / 2),  # Normalized to -1 to +1
        0
    )
    
    # Drop intermediate columns
    df.drop(['sma_20', 'std_20'], axis=1, inplace=True)
    
    return df


# ============================================================================
# VOLUME FEATURES
# ============================================================================

def compute_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute volume features.
    
    Features:
    1. volume_ratio: Current volume / 20-day average volume
    2. volume_trend: Slope of 5-day volume (linear regression)
    
    Args:
        df: DataFrame with Date, Volume columns
    
    Returns:
        DataFrame with added volume features
    """
    df = df.copy()
    
    # 1. Volume ratio (volume relative to 20-day average)
    df['volume_avg_20d'] = df['Volume'].rolling(window=20, min_periods=1).mean()
    df['volume_ratio'] = df['Volume'] / df['volume_avg_20d']
    
    # 2. Volume trend (slope of 5-day volume)
    # Calculate the slope using linear regression over a rolling 5-day window
    def calculate_slope(series):
        if len(series) < 2 or series.isna().all():
            return np.nan
        x = np.arange(len(series))
        y = series.values
        # Remove NaN values
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            return np.nan
        x = x[mask]
        y = y[mask]
        # Calculate slope using least squares
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    df['volume_trend'] = df['Volume'].rolling(window=5, min_periods=2).apply(calculate_slope, raw=False)
    
    # Drop intermediate columns
    df.drop(['volume_avg_20d'], axis=1, inplace=True)
    
    return df


# ============================================================================
# CROSS-ASSET FEATURES
# ============================================================================

def compute_cross_asset_features(df: pd.DataFrame, spy_data: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cross-asset features using SPY (market benchmark).
    
    Features:
    1. correlation_spy_20d: 20-day rolling correlation with SPY
    2. relative_performance_spy_5d: Stock 5-day return minus SPY 5-day return
    3. spy_trend: Binary indicator if SPY is above its 200-day SMA (regime detection)
    
    Args:
        df: DataFrame with Date, Close columns (stock data)
        spy_data: DataFrame with Date, Close columns (SPY data)
    
    Returns:
        DataFrame with added cross-asset features
    """
    df = df.copy()
    spy_data = spy_data.copy()
    
    # Ensure both dataframes have Date as datetime
    df['Date'] = pd.to_datetime(df['Date'], utc=True)
    spy_data['Date'] = pd.to_datetime(spy_data['Date'], utc=True)
    
    # Merge SPY data on Date
    df_merged = df.merge(spy_data[['Date', 'Close']], on='Date', how='left', suffixes=('', '_spy'))
    
    # Calculate SPY returns
    df_merged['spy_return_1d'] = df_merged['Close_spy'].pct_change(1) * 100
    df_merged['spy_return_5d'] = df_merged['Close_spy'].pct_change(5) * 100
    
    # Calculate stock returns if not already present
    if 'return_1d' not in df_merged.columns:
        df_merged['return_1d'] = df_merged['Close'].pct_change(1) * 100
    if 'return_5d' not in df_merged.columns:
        df_merged['return_5d'] = df_merged['Close'].pct_change(5) * 100
    
    # 1. Correlation with SPY (20-day rolling)
    df_merged['correlation_spy_20d'] = df_merged['return_1d'].rolling(window=20, min_periods=10).corr(
        df_merged['spy_return_1d']
    )
    
    # 2. Relative performance vs SPY (5-day)
    df_merged['relative_performance_spy_5d'] = df_merged['return_5d'] - df_merged['spy_return_5d']
    
    # 3. SPY trend (regime detection): 1 if SPY > SMA200, 0 otherwise
    df_merged['spy_sma_200'] = df_merged['Close_spy'].rolling(window=200, min_periods=1).mean()
    df_merged['spy_trend'] = (df_merged['Close_spy'] > df_merged['spy_sma_200']).astype(int)
    
    # Drop intermediate columns
    drop_cols = ['Close_spy', 'spy_return_1d', 'spy_return_5d', 'spy_sma_200']
    df_merged.drop([col for col in drop_cols if col in df_merged.columns], axis=1, inplace=True)
    
    return df_merged


# ============================================================================
# MAIN FEATURE COMPUTATION FUNCTION
# ============================================================================

def compute_features(df: pd.DataFrame, spy_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Compute all features for a stock.
    
    This function combines all feature engineering steps (Partner A):
    1. Price/momentum features
    2. Volatility features
    3. Mean reversion features
    
    Partner B will add:
    4. Volume features
    5. Cross-asset features (requires spy_data)
    
    Args:
        df: DataFrame with OHLCV data (Date, Open, High, Low, Close, Volume)
        spy_data: Optional DataFrame with SPY data (for Partner B's cross-asset features)
    
    Returns:
        DataFrame with computed features
    """
    df = df.copy()
    
    # Ensure Date is datetime and sorted
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df = df.sort_values('Date').reset_index(drop=True)
    
    # Compute Partner A feature groups
    logger.debug("Computing price/momentum features...")
    df = compute_price_momentum_features(df)
    
    logger.debug("Computing volatility features...")
    df = compute_volatility_features(df)
    
    logger.debug("Computing mean reversion features...")
    df = compute_mean_reversion_features(df)
    
    # Compute volume features
    if 'Volume' in df.columns:
        logger.debug("Computing volume features...")
        df = compute_volume_features(df)
    else:
        logger.warning("Volume column not found, skipping volume features")
    
    # Compute cross-asset features if SPY data is provided
    if spy_data is not None:
        logger.debug("Computing cross-asset features...")
        df = compute_cross_asset_features(df, spy_data)
    else:
        logger.debug("No SPY data provided, skipping cross-asset features")
    
    return df


# ============================================================================
# FEATURE LIST
# ============================================================================

def get_feature_list() -> list:
    """
    Get list of all feature names.
    
    Returns:
        List of feature names
    """
    return [
        # Price/Momentum (5 features)
        'return_1d',
        'return_5d',
        'return_20d',
        'price_sma50_ratio',
        'price_sma200_ratio',
        
        # Volatility (3 features)
        'atr_normalized',
        'volatility_20d',
        'rsi_14',
        
        # Mean Reversion (2 features)
        'price_deviation_from_sma20',
        'bollinger_position',
        
        # Volume (2 features)
        'volume_ratio',
        'volume_trend',
        
        # Cross-Asset (3 features)
        'correlation_spy_20d',
        'relative_performance_spy_5d',
        'spy_trend',
    ]


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Test feature computation on a sample stock
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.append(str(project_root))
    
    # Load sample stock data
    data_file = project_root / "data" / "raw" / "stocks" / "AAPL.csv"
    spy_file = project_root / "data" / "raw" / "stocks" / "SPY.csv"
    
    if data_file.exists():
        print("Testing feature computation on AAPL...")
        df = pd.read_csv(data_file)
        
        # Load SPY data if available
        spy_data = None
        if spy_file.exists():
            print("Loading SPY data for cross-asset features...")
            spy_data = pd.read_csv(spy_file)
        else:
            print("Note: SPY.csv not found. Cross-asset features will be skipped.")
            print("You can download SPY data to enable cross-asset features.\n")
        
        # Compute all features
        df_features = compute_features(df, spy_data=spy_data)
        
        print(f"\nOriginal columns: {list(df.columns)}")
        print(f"\nTotal features: {len(get_feature_list())} features")
        print(f"\nFeature columns:")
        for feature in get_feature_list():
            if feature in df_features.columns:
                print(f"  ✓ {feature}")
            else:
                print(f"  ✗ {feature} (missing)")
        
        print(f"\nSample data (last 5 rows):")
        feature_cols = [col for col in get_feature_list() if col in df_features.columns]
        print(df_features[['Date', 'Close'] + feature_cols].tail())
        
        print(f"\nFeature statistics:")
        print(df_features[feature_cols].describe())
        
        # Check for missing values
        missing_counts = df_features[feature_cols].isna().sum()
        if missing_counts.any():
            print(f"\nMissing values per feature:")
            print(missing_counts[missing_counts > 0])
    else:
        print(f"Data file not found: {data_file}")
        print("Please run data collection script first.")
