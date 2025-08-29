#!/usr/bin/env python3
"""
Script to populate CSV files with yfinance data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import Database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Populate all CSV files with yfinance data"""
    print("🚀 Starting data population from yfinance...")
    
    # Initialize database
    db = Database()
    
    # Update all data
    print("📊 Calculating traditional factors (67% weight)...")
    print("🏢 Calculating reputation factors (33% weight)...")
    print("🎯 Computing composite scores...")
    
    rankings = db.update_all_data("world_top_stocks")
    
    print(f"✅ Successfully processed {len(rankings)} stocks!")
    print("\n📁 CSV files created:")
    print(f"   - {db.traditional_factors_file}")
    print(f"   - {db.reputation_factors_file}")
    print(f"   - {db.rankings_file}")
    
    # Show top 10 rankings
    print("\n🏆 Top 10 Stocks:")
    for i, stock in enumerate(rankings[:10], 1):
        print(f"   {i:2d}. {stock['ticker']:6s} - Score: {stock['composite_score']:.3f} "
              f"(Traditional: {stock['traditional_score']:.2f}, "
              f"Reputation: {stock['reputation_score']:.3f})")
    
    print(f"\n📈 Traditional Factors (67% weight):")
    print("   - Momentum (1M, 3M, 6M)")
    print("   - Volatility (30D, 60D)")
    print("   - Volume averages")
    print("   - Sharpe ratio")
    print("   - Beta vs SPY")
    
    print(f"\n🏢 Reputation Factors (33% weight):")
    print("   - Financial Health (Debt ratios, ROE, ROA)")
    print("   - Market Position (Market cap, P/B, P/S)")
    print("   - Growth & Stability (Revenue growth, margins, dividends)")
    
    print("\n🎯 Data is ready! You can now run the backend and frontend.")

if __name__ == "__main__":
    main()
