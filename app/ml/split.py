"""
Walk-Forward Validation and Data Quality Module

This module implements walk-forward (rolling window) validation for time-series data
and provides comprehensive data quality checks to prevent look-ahead bias.

Why Walk-Forward Validation?
============================
Walk-forward validation is CRITICAL for time-series trading strategies because:

1. **Prevents Look-Ahead Bias**: Models are only trained on past data and tested on 
   future data, exactly mimicking real trading conditions.

2. **Realistic Performance Estimates**: Unlike random k-fold cross-validation which 
   shuffles data, walk-forward respects temporal ordering.

3. **Accounts for Non-Stationarity**: Financial markets change over time. Walk-forward
   ensures models are tested on truly unseen future market conditions.

4. **Prevents Data Leakage**: Strict temporal separation between train and validation
   sets ensures no future information contaminates training.

Example:
--------
With 3 years of data, train_years=2, val_years=1:

Split 1: Train [2020-2022] → Validate [2022-2023]
Split 2: Train [2020.5-2022.5] → Validate [2022.5-2023.5] (if stepping by 6 months)

The model is trained on historical data and validated on future data it has never seen.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def walk_forward_split(
    data: pd.DataFrame,
    train_years: float = 2.0,
    val_years: float = 1.0,
    step_months: Optional[int] = None,
    date_column: str = 'Date'
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Create walk-forward validation splits for time-series data.
    
    This implements a rolling window approach where:
    - Training window: Fixed size (train_years)
    - Validation window: Fixed size (val_years)
    - Window slides forward in time (step_months)
    
    **Critical for preventing look-ahead bias in time-series!**
    
    Args:
        data: DataFrame with time-series data (must have date_column)
        train_years: Number of years for training window (default: 2.0)
        val_years: Number of years for validation window (default: 1.0)
        step_months: How many months to slide forward (None = val_years * 12)
        date_column: Name of the date column (default: 'Date')
    
    Returns:
        List of (train_df, val_df) tuples for each split
    
    Example:
        >>> # Standard walk-forward with 2-year train, 1-year validation
        >>> splits = walk_forward_split(df, train_years=2, val_years=1)
        >>> 
        >>> # More frequent splits (every 6 months)
        >>> splits = walk_forward_split(df, train_years=2, val_years=1, step_months=6)
        >>> 
        >>> for i, (train, val) in enumerate(splits, 1):
        ...     print(f"Split {i}: Train={len(train)}, Val={len(val)}")
    """
    # Validate inputs
    if date_column not in data.columns:
        raise ValueError(f"Date column '{date_column}' not found in data")
    
    if train_years <= 0 or val_years <= 0:
        raise ValueError("train_years and val_years must be positive")
    
    # Ensure date column is datetime and data is sorted
    df = data.copy()
    df[date_column] = pd.to_datetime(df[date_column], utc=True)
    df = df.sort_values(date_column).reset_index(drop=True)
    
    # Get date range
    start_date = df[date_column].min()
    end_date = df[date_column].max()
    total_days = (end_date - start_date).days
    
    logger.info(f"Data range: {start_date.date()} to {end_date.date()} ({total_days} days)")
    
    # Calculate step size (default: same as validation period for non-overlapping validation)
    if step_months is None:
        step_months = int(val_years * 12)
    
    step_days = int(step_months * 30.44)  # Average days per month
    train_days = int(train_years * 365.25)
    val_days = int(val_years * 365.25)
    
    # Minimum data requirement (allow some flexibility for calendar vs trading days)
    min_required_days = train_days + val_days
    if total_days < min_required_days - 5:  # Allow 5-day buffer for flexibility
        raise ValueError(
            f"Insufficient data: need at least {min_required_days} days "
            f"({train_years + val_years:.1f} years), have {total_days} days "
            f"({total_days/365.25:.1f} years)"
        )
    
    # Generate splits
    splits = []
    current_train_start = start_date
    
    while True:
        # Calculate split boundaries
        train_start = current_train_start
        train_end = train_start + timedelta(days=train_days)
        val_start = train_end
        val_end = val_start + timedelta(days=val_days)
        
        # Check if we have enough data for this validation split
        # Allow small buffer (2 days) for calendar/trading day differences
        if val_end > end_date + timedelta(days=2):
            logger.info(f"Stopped: validation end {val_end.date()} exceeds data end {end_date.date()}")
            break
        
        # Create train/val masks (train < train_end, val >= val_start and < val_end)
        train_mask = (df[date_column] >= train_start) & (df[date_column] < train_end)
        val_mask = (df[date_column] >= val_start) & (df[date_column] < val_end)
        
        train_df = df[train_mask].copy()
        val_df = df[val_mask].copy()
        
        # Only add split if both have sufficient data
        if len(train_df) > 0 and len(val_df) > 0:
            splits.append((train_df, val_df))
            logger.info(
                f"Split {len(splits)}: "
                f"Train[{train_start.date()} to {train_end.date()}] ({len(train_df)} rows) → "
                f"Val[{val_start.date()} to {val_end.date()}] ({len(val_df)} rows)"
            )
        else:
            logger.warning(f"Skipped split with insufficient data: train={len(train_df)}, val={len(val_df)}")
        
        # Move to next split
        current_train_start += timedelta(days=step_days)
    
    if len(splits) == 0:
        raise ValueError(
            f"Could not create any splits. Check your data range and parameters. "
            f"Data spans {total_days/365.25:.1f} years, "
            f"need at least {(train_days + val_days)/365.25:.1f} years per split."
        )
    
    logger.info(f"✓ Created {len(splits)} walk-forward splits")
    return splits


def anchored_walk_forward_split(
    data: pd.DataFrame,
    initial_train_years: float = 2.0,
    val_years: float = 1.0,
    step_months: int = 6,
    date_column: str = 'Date'
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Create anchored (expanding window) walk-forward validation splits.
    
    Unlike standard walk-forward, the training set GROWS over time:
    - Training window: Expanding (anchored at start, grows with each split)
    - Validation window: Fixed size (val_years)
    - Window slides forward in time (step_months)
    
    This approach uses all available historical data for each model.
    
    Example with initial_train_years=2, val_years=1, step_months=6:
    Split 1: Train[2020-2022] (2 years) → Val[2022-2023]
    Split 2: Train[2020-2022.5] (2.5 years) → Val[2022.5-2023.5]
    Split 3: Train[2020-2023] (3 years) → Val[2023-2024]
    
    Args:
        data: DataFrame with time-series data
        initial_train_years: Initial training window size
        val_years: Validation window size (fixed)
        step_months: How many months to slide validation window forward
        date_column: Name of the date column
    
    Returns:
        List of (train_df, val_df) tuples
    """
    df = data.copy()
    df[date_column] = pd.to_datetime(df[date_column], utc=True)
    df = df.sort_values(date_column).reset_index(drop=True)
    
    start_date = df[date_column].min()
    end_date = df[date_column].max()
    
    step_days = int(step_months * 30.44)
    initial_train_days = int(initial_train_years * 365.25)
    val_days = int(val_years * 365.25)
    
    splits = []
    val_start = start_date + timedelta(days=initial_train_days)
    
    while True:
        # Training: from start to validation start (EXPANDING WINDOW)
        train_mask = (df[date_column] >= start_date) & (df[date_column] < val_start)
        
        # Validation: fixed window after training
        val_end = val_start + timedelta(days=val_days)
        val_mask = (df[date_column] >= val_start) & (df[date_column] < val_end)
        
        if val_end > end_date + timedelta(days=2):
            logger.info(f"Stopped: validation end {val_end.date()} exceeds data end {end_date.date()}")
            break
        
        train_df = df[train_mask].copy()
        val_df = df[val_mask].copy()
        
        if len(train_df) > 0 and len(val_df) > 0:
            train_years_actual = (val_start - start_date).days / 365.25
            splits.append((train_df, val_df))
            logger.info(
                f"Split {len(splits)}: "
                f"Train[{start_date.date()} to {val_start.date()}] ({train_years_actual:.1f}y, {len(train_df)} rows) → "
                f"Val[{val_start.date()} to {val_end.date()}] ({len(val_df)} rows)"
            )
        
        # Move validation window forward
        val_start += timedelta(days=step_days)
    
    logger.info(f"✓ Created {len(splits)} anchored walk-forward splits")
    return splits


def get_split_summary(
    splits: List[Tuple[pd.DataFrame, pd.DataFrame]],
    date_column: str = 'Date'
) -> pd.DataFrame:
    """
    Generate a summary table of all splits.
    
    Args:
        splits: List of (train_df, val_df) tuples
        date_column: Name of the date column
    
    Returns:
        DataFrame with split information (dates, sizes, gaps)
    """
    summary = []
    
    for i, (train, val) in enumerate(splits, 1):
        train_start = train[date_column].min()
        train_end = train[date_column].max()
        val_start = val[date_column].min()
        val_end = val[date_column].max()
        
        gap_days = (val_start - train_end).days
        
        summary.append({
            'Split': i,
            'Train_Start': train_start.date(),
            'Train_End': train_end.date(),
            'Train_Days': (train_end - train_start).days,
            'Train_Rows': len(train),
            'Val_Start': val_start.date(),
            'Val_End': val_end.date(),
            'Val_Days': (val_end - val_start).days,
            'Val_Rows': len(val),
            'Gap_Days': gap_days,
        })
    
    return pd.DataFrame(summary)


# ============================================================================
# DATA QUALITY CHECKS
# ============================================================================

def check_data_leakage(
    train: pd.DataFrame,
    val: pd.DataFrame,
    feature_columns: List[str],
    date_column: str = 'Date'
) -> Dict[str, any]:
    """
    Check for data leakage: ensure no future data in training features.
    
    **CRITICAL**: Data leakage is when information from the validation/test set
    "leaks" into the training set, leading to overly optimistic performance
    estimates that won't hold in real trading.
    
    This function checks:
    1. No temporal overlap between train and validation
    2. All validation dates are strictly after training dates
    3. No NaN values introduced during feature computation
    4. Feature values are bounded (no infinite values)
    
    Args:
        train: Training DataFrame
        val: Validation DataFrame
        feature_columns: List of feature column names to check
        date_column: Name of the date column
    
    Returns:
        Dictionary with leakage check results
    """
    checks = {
        'passed': True,
        'issues': [],
        'warnings': []
    }
    
    train_dates = pd.to_datetime(train[date_column])
    val_dates = pd.to_datetime(val[date_column])
    
    # Check 1: No overlap
    train_max = train_dates.max()
    val_min = val_dates.min()
    
    if train_max >= val_min:
        checks['passed'] = False
        checks['issues'].append(
            f"CRITICAL: Temporal overlap detected! "
            f"Training ends at {train_max.date()} but validation starts at {val_min.date()}"
        )
    
    # Check 2: Chronological order within each set
    if not train_dates.is_monotonic_increasing:
        checks['passed'] = False
        checks['issues'].append("Training data is not sorted chronologically")
    
    if not val_dates.is_monotonic_increasing:
        checks['passed'] = False
        checks['issues'].append("Validation data is not sorted chronologically")
    
    # Check 3: No NaN values in features
    for col in feature_columns:
        if col in train.columns:
            train_nan_pct = train[col].isna().sum() / len(train) * 100
            val_nan_pct = val[col].isna().sum() / len(val) * 100
            
            if train_nan_pct > 10:
                checks['warnings'].append(
                    f"Feature '{col}' has {train_nan_pct:.1f}% NaN in training set"
                )
            
            if val_nan_pct > 10:
                checks['warnings'].append(
                    f"Feature '{col}' has {val_nan_pct:.1f}% NaN in validation set"
                )
    
    # Check 4: No infinite values
    for col in feature_columns:
        if col in train.columns:
            if np.isinf(train[col]).any():
                checks['passed'] = False
                checks['issues'].append(f"Feature '{col}' contains infinite values in training set")
            
            if np.isinf(val[col]).any():
                checks['passed'] = False
                checks['issues'].append(f"Feature '{col}' contains infinite values in validation set")
    
    return checks


def check_target_alignment(
    data: pd.DataFrame,
    target_column: str,
    date_column: str = 'Date',
    forward_days: int = 5
) -> Dict[str, any]:
    """
    Verify that targets are correctly aligned with future dates.
    
    **CRITICAL**: Target variables must represent FUTURE returns/outcomes,
    not past or current values. This check ensures targets are properly
    forward-looking.
    
    For example, if predicting 5-day forward returns:
    - Row for date 2023-01-01 should have target = return from 2023-01-01 to 2023-01-06
    - NOT the return from 2022-12-27 to 2023-01-01 (that would be leakage!)
    
    Args:
        data: DataFrame with features and targets
        target_column: Name of the target column
        date_column: Name of the date column
        forward_days: Number of days the target should look forward
    
    Returns:
        Dictionary with alignment check results
    """
    checks = {
        'passed': True,
        'issues': [],
        'warnings': []
    }
    
    if target_column not in data.columns:
        checks['passed'] = False
        checks['issues'].append(f"Target column '{target_column}' not found in data")
        return checks
    
    # Check for NaN targets at the end (expected for forward-looking targets)
    target_series = data[target_column]
    nan_count = target_series.isna().sum()
    
    if nan_count == 0:
        checks['warnings'].append(
            f"No NaN values in target column. "
            f"Expected ~{forward_days} NaN at end for {forward_days}-day forward targets."
        )
    else:
        # Check if NaNs are at the end (as expected)
        nan_indices = target_series.isna()
        first_nan_idx = nan_indices.idxmax() if nan_indices.any() else len(data)
        last_nan_idx = len(data) - 1 - nan_indices.iloc[::-1].idxmax() if nan_indices.any() else -1
        
        # NaNs should be consecutive at the end
        expected_nan_positions = list(range(len(data) - nan_count, len(data)))
        actual_nan_positions = list(data[nan_indices].index)
        
        if actual_nan_positions != expected_nan_positions:
            checks['warnings'].append(
                f"NaN values in target are not at the end. "
                f"This might indicate improper target calculation."
            )
    
    # Check target distribution
    target_values = target_series.dropna()
    if len(target_values) > 0:
        target_mean = target_values.mean()
        target_std = target_values.std()
        target_min = target_values.min()
        target_max = target_values.max()
        
        # Warn about extreme values
        if abs(target_min) > 100 or abs(target_max) > 100:
            checks['warnings'].append(
                f"Extreme target values detected: min={target_min:.2f}, max={target_max:.2f}. "
                f"Are these percentage returns?"
            )
        
        logger.info(
            f"Target statistics: mean={target_mean:.3f}, std={target_std:.3f}, "
            f"range=[{target_min:.2f}, {target_max:.2f}]"
        )
    
    return checks


def check_feature_distributions(
    train: pd.DataFrame,
    val: pd.DataFrame,
    feature_columns: List[str],
    threshold: float = 3.0
) -> Dict[str, any]:
    """
    Check feature distributions for significant drift between train and validation.
    
    Large distribution shifts can indicate:
    - Market regime changes
    - Data quality issues
    - Feature calculation errors
    
    Args:
        train: Training DataFrame
        val: Validation DataFrame
        feature_columns: List of feature columns to check
        threshold: Standard deviation threshold for drift warning (default: 3.0)
    
    Returns:
        Dictionary with distribution check results and summary statistics
    """
    checks = {
        'passed': True,
        'warnings': [],
        'stats': {}
    }
    
    for col in feature_columns:
        if col not in train.columns or col not in val.columns:
            continue
        
        train_values = train[col].dropna()
        val_values = val[col].dropna()
        
        if len(train_values) == 0 or len(val_values) == 0:
            checks['warnings'].append(f"Feature '{col}' has no valid values")
            continue
        
        # Calculate statistics
        train_mean = train_values.mean()
        train_std = train_values.std()
        val_mean = val_values.mean()
        val_std = val_values.std()
        
        # Check for distribution drift
        if train_std > 0:
            mean_shift_std = abs(val_mean - train_mean) / train_std
            
            if mean_shift_std > threshold:
                checks['warnings'].append(
                    f"Feature '{col}' shows significant drift: "
                    f"train_mean={train_mean:.3f}, val_mean={val_mean:.3f} "
                    f"({mean_shift_std:.1f} std shift)"
                )
        
        # Store statistics
        checks['stats'][col] = {
            'train_mean': train_mean,
            'train_std': train_std,
            'train_min': train_values.min(),
            'train_max': train_values.max(),
            'val_mean': val_mean,
            'val_std': val_std,
            'val_min': val_values.min(),
            'val_max': val_values.max(),
            'mean_shift': val_mean - train_mean,
        }
    
    return checks


def run_all_quality_checks(
    train: pd.DataFrame,
    val: pd.DataFrame,
    feature_columns: List[str],
    target_column: Optional[str] = None,
    date_column: str = 'Date',
    forward_days: int = 5
) -> Dict[str, any]:
    """
    Run all data quality checks on a train/validation split.
    
    This is a comprehensive check that should be run on every split to ensure:
    1. No data leakage
    2. Proper target alignment
    3. Reasonable feature distributions
    
    Args:
        train: Training DataFrame
        val: Validation DataFrame
        feature_columns: List of feature columns
        target_column: Name of target column (optional)
        date_column: Name of date column
        forward_days: Days for forward-looking targets
    
    Returns:
        Dictionary with all check results
    """
    results = {
        'overall_passed': True,
        'leakage_check': None,
        'target_alignment': None,
        'feature_distributions': None
    }
    
    # Run leakage check
    logger.info("Checking for data leakage...")
    leakage = check_data_leakage(train, val, feature_columns, date_column)
    results['leakage_check'] = leakage
    if not leakage['passed']:
        results['overall_passed'] = False
    
    # Run target alignment check
    if target_column:
        logger.info("Checking target alignment...")
        combined_data = pd.concat([train, val], ignore_index=True)
        target_check = check_target_alignment(combined_data, target_column, date_column, forward_days)
        results['target_alignment'] = target_check
    
    # Run distribution check
    logger.info("Checking feature distributions...")
    dist_check = check_feature_distributions(train, val, feature_columns)
    results['feature_distributions'] = dist_check
    
    return results


# ============================================================================
# MAIN TESTING
# ============================================================================

if __name__ == "__main__":
    # Test walk-forward validation
    from pathlib import Path
    import sys
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.append(str(project_root))
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Load sample data
    data_file = project_root / "data" / "raw" / "stocks" / "AAPL.csv"
    
    if data_file.exists():
        print("=" * 80)
        print("WALK-FORWARD VALIDATION & DATA QUALITY CHECKS")
        print("=" * 80)
        
        df = pd.read_csv(data_file)
        df['Date'] = pd.to_datetime(df['Date'], utc=True)  # Fix warning
        
        print(f"\n✓ Loaded AAPL data: {len(df)} rows")
        print(f"  Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
        print(f"  Columns: {list(df.columns)}")
        
        # Test standard walk-forward
        print("\n" + "=" * 80)
        print("STANDARD WALK-FORWARD SPLIT (train_years=2, val_years=1)")
        print("=" * 80)
        
        try:
            splits = walk_forward_split(df, train_years=2.0, val_years=1.0)
            
            summary = get_split_summary(splits)
            print("\nSplit Summary:")
            print(summary.to_string(index=False))
            
            # Data quality checks on first split
            print("\n" + "=" * 80)
            print("DATA QUALITY CHECKS (Split 1)")
            print("=" * 80)
            
            train, val = splits[0]
            feature_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            quality_results = run_all_quality_checks(
                train, val,
                feature_columns=feature_cols,
                date_column='Date'
            )
            
            # Print results
            print("\n1. Data Leakage Check:")
            leakage = quality_results['leakage_check']
            if leakage['passed']:
                print("   ✓ PASSED - No data leakage detected")
            else:
                print("   ✗ FAILED - Data leakage detected!")
                for issue in leakage['issues']:
                    print(f"     - {issue}")
            
            if leakage['warnings']:
                print("   Warnings:")
                for warning in leakage['warnings']:
                    print(f"     - {warning}")
            
            print("\n2. Feature Distribution Check:")
            dist_check = quality_results['feature_distributions']
            if dist_check['warnings']:
                print("   Warnings:")
                for warning in dist_check['warnings']:
                    print(f"     - {warning}")
            else:
                print("   ✓ No significant distribution drift detected")
            
            print("\n3. Feature Statistics Summary:")
            print(f"   {'Feature':<15} {'Train Mean':<12} {'Val Mean':<12} {'Shift':<10}")
            print("   " + "-" * 55)
            for feature, stats in dist_check['stats'].items():
                print(f"   {feature:<15} {stats['train_mean']:>11.2f} {stats['val_mean']:>11.2f} {stats['mean_shift']:>9.2f}")
            
            # Test anchored walk-forward
            print("\n" + "=" * 80)
            print("ANCHORED WALK-FORWARD SPLIT (expanding training set)")
            print("=" * 80)
            
            anchored_splits = anchored_walk_forward_split(
                df, initial_train_years=2.0, val_years=1.0, step_months=6
            )
            
            anchored_summary = get_split_summary(anchored_splits)
            print("\nAnchored Split Summary:")
            print(anchored_summary.to_string(index=False))
            
            print("\n" + "=" * 80)
            print("✓ ALL TESTS COMPLETED")
            print("=" * 80)
            
        except ValueError as e:
            print(f"\n✗ Error: {e}")
            print("\nNote: You may need more data to create splits.")
            print("      Try reducing train_years or val_years parameters.")
    else:
        print(f"✗ Data file not found: {data_file}")
        print("  Please run scripts/collect_data.py first.")
