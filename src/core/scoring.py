"""
Scoring and normalization functions for factor ranking
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


# Factors where lower values are better (should be inverted)
LOWER_IS_BETTER = {
    "Vol_30d",           # Lower volatility is better
    "Debt_to_Equity",    # Lower debt is better
    "Beta",              # Lower beta is better (less volatile than market)
    "Payout_Ratio"       # Lower payout ratio is better (more sustainable)
}


def winsorize_zscore(series: pd.Series, clip: float = 3.0) -> pd.Series:
    """
    Winsorize and z-score normalize a series
    
    Args:
        series: Input series
        clip: Number of standard deviations to clip at
        
    Returns:
        Normalized series
    """
    # Handle infinite values
    series = series.replace([np.inf, -np.inf], np.nan)
    
    # Calculate mean and standard deviation
    mean_val = series.mean()
    std_val = series.std()
    
    # Handle edge cases
    if std_val == 0 or pd.isna(std_val):
        return pd.Series(np.zeros(len(series)), index=series.index)
    
    # Calculate z-scores
    z_scores = (series - mean_val) / std_val
    
    # Winsorize (clip extreme values)
    z_scores = z_scores.clip(-clip, clip)
    
    return z_scores


def compose_scores(factors_df: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    """
    Compose final scores from normalized factors
    
    Args:
        factors_df: DataFrame with factor columns
        weights: Dictionary of factor weights (should sum to 1)
        
    Returns:
        Series with composite scores, sorted descending
    """
    # Normalize all factors
    normalized = factors_df.apply(winsorize_zscore)
    
    # Invert factors where lower is better
    for col in factors_df.columns:
        if col in LOWER_IS_BETTER:
            normalized[col] = -normalized[col]
    
    # Create weight series, filling missing factors with 0
    weight_series = pd.Series(weights).reindex(factors_df.columns).fillna(0.0)
    
    # Calculate weighted composite score
    composite_scores = (normalized * weight_series).sum(axis=1)
    
    # Sort by score (descending)
    return composite_scores.sort_values(ascending=False)


def get_default_weights() -> Dict[str, float]:
    """
    Get default factor weights with 67/33 split (traditional/reputation)
    
    Returns:
        Dictionary of default weights
    """
    weights = {
        # Traditional factors (67%)
        'MOM_1M': 0.20,
        'MOM_3M': 0.20,
        'Slope_50d': 0.10,
        'Vol_30d': 0.12,  # Will be inverted in scoring
        'Sharpe_3M': 0.15,
        'DollarVol_20d': 0.08,
        
        # Reputation factors (33%)
        'Reputation_Score': 0.15,
        'ESG_Score': 0.03,
        'Financial_Health': 0.03,  # Composite of financial metrics
        'Market_Position': 0.03,   # Composite of market metrics
        'Growth_Stability': 0.03   # Composite of growth metrics
    }
    
    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    normalized_weights = {k: v / total_weight for k, v in weights.items()}
    
    return normalized_weights


def create_composite_reputation_factors(factors_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create composite reputation factors from individual metrics
    
    Args:
        factors_df: DataFrame with individual reputation factors
        
    Returns:
        DataFrame with additional composite factors
    """
    df = factors_df.copy()
    
    # Financial Health Composite (average of financial ratios)
    financial_cols = ['Current_Ratio', 'Quick_Ratio', 'ROE', 'ROA']
    available_financial = [col for col in financial_cols if col in df.columns]
    if available_financial:
        df['Financial_Health'] = df[available_financial].mean(axis=1)
    else:
        df['Financial_Health'] = 0
    
    # Market Position Composite (market cap + R&D normalized)
    market_cols = ['Market_Cap', 'R&D_Spending']
    available_market = [col for col in market_cols if col in df.columns]
    if available_market:
        df['Market_Position'] = df[available_market].mean(axis=1)
    else:
        df['Market_Position'] = 0
    
    # Growth Stability Composite (growth + stability metrics)
    growth_cols = ['Revenue_Growth', 'Earnings_Growth', 'Profit_Margins', 'Price_Stability']
    available_growth = [col for col in growth_cols if col in df.columns]
    if available_growth:
        df['Growth_Stability'] = df[available_growth].mean(axis=1)
    else:
        df['Growth_Stability'] = 0
    
    return df


def validate_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that weights sum to approximately 1
    
    Args:
        weights: Dictionary of weights
        
    Returns:
        True if weights are valid
    """
    total = sum(weights.values())
    return abs(total - 1.0) < 0.01


def rank_tickers(
    factors_df: pd.DataFrame, 
    weights: Optional[Dict[str, float]] = None,
    top_n: Optional[int] = None
) -> pd.DataFrame:
    """
    Rank tickers based on factors and weights including reputation factors
    
    Args:
        factors_df: DataFrame with factor columns
        weights: Dictionary of factor weights (uses defaults if None)
        top_n: Number of top tickers to return (None for all)
        
    Returns:
        DataFrame with scores and rankings
    """
    if weights is None:
        weights = get_default_weights()
    
    if not validate_weights(weights):
        raise ValueError("Weights must sum to 1.0")
    
    # Create composite reputation factors
    factors_df = create_composite_reputation_factors(factors_df)
    
    # Calculate composite scores
    scores = compose_scores(factors_df, weights)
    
    # Create result DataFrame
    result = pd.DataFrame({
        'Score': scores,
        'Rank': range(1, len(scores) + 1)
    })
    
    # Add factor columns
    for col in factors_df.columns:
        result[col] = factors_df.loc[scores.index, col]
    
    # Return top N if specified
    if top_n is not None:
        result = result.head(top_n)
    
    return result
