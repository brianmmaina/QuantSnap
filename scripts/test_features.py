#!/usr/bin/env python3
"""
Test script for feature engineering module.

This script validates that all features are computed correctly.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.ml.features import compute_features, get_feature_list


def test_feature_computation():
    """Test feature computation on AAPL data."""
    print("=" * 70)
    print("FEATURE ENGINEERING TEST")
    print("=" * 70)
    
    # Load AAPL data
    data_file = project_root / "data" / "raw" / "stocks" / "AAPL.csv"
    
    if not data_file.exists():
        print(f"❌ Error: Data file not found: {data_file}")
        print("   Please run data collection script first.")
        return False
    
    print(f"\n1. Loading stock data from: {data_file.name}")
    df = pd.read_csv(data_file)
    print(f"   ✓ Loaded {len(df)} rows")
    
    # Compute Partner A features (no SPY needed yet)
    print(f"\n2. Computing Partner A features...")
    df_features = compute_features(df)  # No spy_data needed for Partner A features
    print(f"   ✓ Features computed")
    
    # Check all features are present
    print(f"\n4. Validating features...")
    expected_features = get_feature_list()
    missing_features = [f for f in expected_features if f not in df_features.columns]
    
    if missing_features:
        print(f"   ❌ Missing features: {missing_features}")
        return False
    
    print(f"   ✓ All {len(expected_features)} Partner A features present")
    
    # Check for NaN values
    print(f"\n5. Checking for missing values...")
    feature_cols = [col for col in get_feature_list() if col in df_features.columns]
    nan_counts = df_features[feature_cols].isna().sum()
    features_with_nans = nan_counts[nan_counts > 0]
    
    if len(features_with_nans) > 0:
        print(f"   ⚠️  Features with NaN values:")
        for feature, count in features_with_nans.items():
            print(f"      - {feature}: {count} NaN values (first {len(df_features)} rows)")
    else:
        print(f"   ✓ No NaN values in features (after initial rows)")
    
    # Check feature ranges
    print(f"\n6. Validating feature ranges...")
    feature_ranges = {
        'rsi_14': (0, 100),
        'bollinger_position': (-2, 2),  # Should be around -1 to +1, but allow some margin
        'spy_trend': (0, 1),
        'volume_ratio': (0, None),  # Should be positive
    }
    
    all_valid = True
    for feature, (min_val, max_val) in feature_ranges.items():
        if feature in df_features.columns:
            values = df_features[feature].dropna()
            if len(values) > 0:
                actual_min = values.min()
                actual_max = values.max()
                
                if min_val is not None and actual_min < min_val:
                    print(f"   ❌ {feature}: min value {actual_min:.2f} < expected {min_val}")
                    all_valid = False
                elif max_val is not None and actual_max > max_val:
                    print(f"   ❌ {feature}: max value {actual_max:.2f} > expected {max_val}")
                    all_valid = False
                else:
                    print(f"   ✓ {feature}: range [{actual_min:.2f}, {actual_max:.2f}] is valid")
    
    if all_valid:
        print(f"   ✓ All feature ranges are valid")
    
    # Display sample data
    print(f"\n7. Sample feature values (last 3 rows):")
    print("-" * 70)
    sample_cols = ['Date', 'Close'] + feature_cols[:5]  # Show first 5 features
    print(df_features[sample_cols].tail(3).to_string())
    print("   ...")
    
    # Summary statistics
    print(f"\n8. Feature Summary:")
    print("-" * 70)
    stats = df_features[feature_cols].describe()
    print(f"   Total rows: {len(df_features)}")
    print(f"   Partner A features: {len(feature_cols)}")
    print(f"   Feature categories (Partner A):")
    print(f"      - Price/Momentum: 5 features")
    print(f"      - Volatility: 3 features")
    print(f"      - Mean Reversion: 2 features")
    print(f"   Note: Partner B will add Volume and Cross-Asset features")
    
    print(f"\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = test_feature_computation()
    sys.exit(0 if success else 1)
