#!/usr/bin/env python3
"""
Data Validation Script
Validates collected stock data against quality standards.

Usage:
    python scripts/validate_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data" / "raw" / "stocks"
REQUIRED_COLUMNS = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
MIN_VOLUME_THRESHOLD = 100000  # Minimum average daily volume for liquid stocks
MIN_ROWS_EXPECTED = 700  # Minimum rows expected for 3 years (accounting for holidays)


class DataValidator:
    """Validates stock data quality."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.results = {}
        
    def validate_file(self, ticker: str) -> Dict:
        """
        Validate a single stock CSV file.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with validation results
        """
        file_path = self.data_dir / f"{ticker}.csv"
        
        result = {
            'ticker': ticker,
            'file_exists': False,
            'readable': False,
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        # Check if file exists
        if not file_path.exists():
            result['errors'].append(f"File does not exist: {file_path}")
            return result
        
        result['file_exists'] = True
        
        try:
            # Try to read the file
            df = pd.read_csv(file_path)
            result['readable'] = True
            result['rows'] = len(df)
            result['columns'] = list(df.columns)
            
            # Check columns
            missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                result['errors'].append(f"Missing columns: {missing_cols}")
            else:
                result['checks']['has_all_columns'] = True
            
            # Check number of rows
            if len(df) < MIN_ROWS_EXPECTED:
                result['warnings'].append(
                    f"Fewer rows than expected: {len(df)} (expected >= {MIN_ROWS_EXPECTED})"
                )
            else:
                result['checks']['sufficient_rows'] = True
            
            # Check for empty file
            if len(df) == 0:
                result['errors'].append("File is empty")
                return result
            
            # Convert Date to datetime
            try:
                df['Date'] = pd.to_datetime(df['Date'], utc=True)
                result['checks']['dates_parseable'] = True
            except Exception as e:
                result['errors'].append(f"Date parsing failed: {str(e)}")
                return result
            
            # Validate dates
            date_checks = self._validate_dates(df)
            result['checks'].update(date_checks)
            if date_checks.get('dates_ordered', False):
                # If dates are ordered, check for duplicates
                if not df['Date'].duplicated().any():
                    result['checks']['no_duplicate_dates'] = True
                else:
                    result['errors'].append("Duplicate dates found")
            
            # Validate prices
            price_checks = self._validate_prices(df)
            result['checks'].update(price_checks)
            
            # Validate volume
            volume_checks = self._validate_volume(df)
            result['checks'].update(volume_checks)
            
            # Check for missing values
            missing_checks = self._check_missing_values(df)
            result['checks'].update(missing_checks)
            
        except Exception as e:
            result['errors'].append(f"Error reading file: {str(e)}")
            return result
        
        return result
    
    def _validate_dates(self, df: pd.DataFrame) -> Dict:
        """Validate date column."""
        checks = {}
        
        # Check if dates are in order
        if df['Date'].is_monotonic_increasing:
            checks['dates_ordered'] = True
        else:
            checks['dates_ordered'] = False
        
        # Check date range (should be within last 3-4 years)
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        checks['date_range'] = {'min': str(min_date), 'max': str(max_date)}
        
        return checks
    
    def _validate_prices(self, df: pd.DataFrame) -> Dict:
        """Validate price data."""
        checks = {}
        errors = []
        
        # Check for negative prices
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if (df[col] < 0).any():
                errors.append(f"Negative values found in {col}")
        
        if not errors:
            checks['all_prices_positive'] = True
        
        # Check price relationships
        if not (df['High'] >= df['Low']).all():
            errors.append("High < Low found")
        else:
            checks['high_ge_low'] = True
        
        if not (df['High'] >= df['Open']).all():
            errors.append("High < Open found")
        else:
            checks['high_ge_open'] = True
        
        if not (df['High'] >= df['Close']).all():
            errors.append("High < Close found")
        else:
            checks['high_ge_close'] = True
        
        if not (df['Low'] <= df['Open']).all():
            errors.append("Low > Open found")
        else:
            checks['low_le_open'] = True
        
        if not (df['Low'] <= df['Close']).all():
            errors.append("Low > Close found")
        else:
            checks['low_le_close'] = True
        
        # Check for missing values
        for col in price_cols:
            if df[col].isna().any():
                errors.append(f"Missing values in {col}")
        
        if not any('Missing values' in e for e in errors):
            checks['no_missing_prices'] = True
        
        if errors:
            checks['price_errors'] = errors
        
        return checks
    
    def _validate_volume(self, df: pd.DataFrame) -> Dict:
        """Validate volume data."""
        checks = {}
        
        # Check for negative volume
        if (df['Volume'] < 0).any():
            checks['volume_negative'] = True
        else:
            checks['volume_non_negative'] = True
        
        # Check average volume
        avg_volume = df['Volume'].mean()
        checks['avg_volume'] = avg_volume
        
        if avg_volume >= MIN_VOLUME_THRESHOLD:
            checks['meets_volume_threshold'] = True
        else:
            checks['meets_volume_threshold'] = False
        
        # Check for missing values
        if df['Volume'].isna().any():
            checks['missing_volume'] = True
        else:
            checks['no_missing_volume'] = True
        
        return checks
    
    def _check_missing_values(self, df: pd.DataFrame) -> Dict:
        """Check for missing values across all columns."""
        checks = {}
        
        missing_counts = df.isna().sum()
        total_missing = missing_counts.sum()
        
        checks['total_missing_values'] = int(total_missing)
        checks['missing_by_column'] = missing_counts.to_dict()
        
        if total_missing == 0:
            checks['no_missing_values'] = True
        else:
            checks['no_missing_values'] = False
        
        return checks
    
    def validate_all(self, tickers: List[str]) -> Dict:
        """
        Validate all stock files.
        
        Args:
            tickers: List of ticker symbols to validate
        
        Returns:
            Dictionary with validation results for all stocks
        """
        logger.info(f"Validating {len(tickers)} stock files...")
        
        all_results = {}
        passed = 0
        failed = 0
        
        for ticker in tickers:
            result = self.validate_file(ticker)
            all_results[ticker] = result
            
            if result['errors']:
                failed += 1
                logger.warning(f"{ticker}: {len(result['errors'])} errors found")
            else:
                passed += 1
                logger.debug(f"{ticker}: All checks passed")
        
        summary = {
            'total': len(tickers),
            'passed': passed,
            'failed': failed,
            'results': all_results
        }
        
        return summary
    
    def print_summary(self, summary: Dict):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("Data Validation Summary")
        print("=" * 60)
        print(f"Total stocks: {summary['total']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print("=" * 60)
        
        # Print errors for failed stocks
        failed_stocks = [
            ticker for ticker, result in summary['results'].items()
            if result['errors']
        ]
        
        if failed_stocks:
            print("\nFailed Stocks:")
            for ticker in failed_stocks:
                result = summary['results'][ticker]
                print(f"\n{ticker}:")
                for error in result['errors']:
                    print(f"  ❌ {error}")
                for warning in result['warnings']:
                    print(f"  ⚠️  {warning}")
        else:
            print("\n✅ All stocks passed validation!")
        
        # Print warnings for passed stocks with warnings
        stocks_with_warnings = [
            ticker for ticker, result in summary['results'].items()
            if result['warnings'] and not result['errors']
        ]
        
        if stocks_with_warnings:
            print("\nStocks with Warnings:")
            for ticker in stocks_with_warnings:
                result = summary['results'][ticker]
                print(f"\n{ticker}:")
                for warning in result['warnings']:
                    print(f"  ⚠️  {warning}")


def main():
    """Main function to run validation."""
    print("=" * 60)
    print("Stock Data Validation Script")
    print("=" * 60)
    
    # Get list of CSV files in data directory
    csv_files = list(DATA_DIR.glob("*.csv"))
    tickers = [f.stem for f in csv_files]
    
    if not tickers:
        print(f"No CSV files found in {DATA_DIR}")
        return
    
    print(f"Found {len(tickers)} stock files to validate")
    
    # Create validator and run validation
    validator = DataValidator(DATA_DIR)
    summary = validator.validate_all(tickers)
    
    # Print summary
    validator.print_summary(summary)
    
    # Exit with appropriate code
    if summary['failed'] > 0:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
