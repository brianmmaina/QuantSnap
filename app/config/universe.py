"""
Stock Universe Configuration

This module defines the stock universe for backtesting and live trading.
The universe consists of highly liquid stocks with strong fundamentals.

Selection Criteria:
- S&P 500 constituent (preferred)
- Minimum average daily volume: 500,000 shares
- Market cap: Large-cap preferred (>$10B)
- Sector diversity: Balanced representation across major sectors
- Data availability: Consistent historical data for backtesting
- Liquidity: Tight bid-ask spreads for efficient execution

Universe Review: Monthly or when S&P 500 composition changes
"""

from typing import List, Dict
from datetime import datetime


# ============================================================================
# STOCK UNIVERSE
# ============================================================================

STOCK_UNIVERSE: List[str] = [
    # Technology (15 stocks)
    "AAPL",   # Apple Inc. - Consumer Electronics
    "MSFT",   # Microsoft Corp. - Software
    "GOOGL",  # Alphabet Inc. - Internet Services
    "AMZN",   # Amazon.com Inc. - E-commerce/Cloud
    "NVDA",   # NVIDIA Corp. - Semiconductors
    "META",   # Meta Platforms Inc. - Social Media
    "TSLA",   # Tesla Inc. - Electric Vehicles
    "AVGO",   # Broadcom Inc. - Semiconductors
    "ORCL",   # Oracle Corp. - Enterprise Software
    "CRM",    # Salesforce Inc. - Cloud Software
    "CSCO",   # Cisco Systems - Networking
    "ADBE",   # Adobe Inc. - Creative Software
    "INTC",   # Intel Corp. - Semiconductors
    "AMD",    # Advanced Micro Devices - Semiconductors
    "QCOM",   # Qualcomm Inc. - Semiconductors
    
    # Healthcare (7 stocks)
    "UNH",    # UnitedHealth Group - Health Insurance
    "JNJ",    # Johnson & Johnson - Pharmaceuticals
    "LLY",    # Eli Lilly - Pharmaceuticals
    "ABBV",   # AbbVie Inc. - Biopharmaceuticals
    "PFE",    # Pfizer Inc. - Pharmaceuticals
    "TMO",    # Thermo Fisher Scientific - Lab Equipment
    "MRK",    # Merck & Co. - Pharmaceuticals
    
    # Financials (8 stocks)
    "JPM",    # JPMorgan Chase - Banking
    "V",      # Visa Inc. - Payment Processing
    "MA",     # Mastercard Inc. - Payment Processing
    "BAC",    # Bank of America - Banking
    "WFC",    # Wells Fargo - Banking
    "GS",     # Goldman Sachs - Investment Banking
    "MS",     # Morgan Stanley - Investment Banking
    "BLK",    # BlackRock Inc. - Asset Management
    
    # Consumer Discretionary (6 stocks)
    "HD",     # Home Depot - Home Improvement Retail
    "MCD",    # McDonald's - Fast Food
    "NKE",    # Nike Inc. - Apparel
    "SBUX",   # Starbucks - Coffee Retail
    "TGT",    # Target Corp. - Retail
    "LOW",    # Lowe's Companies - Home Improvement
    
    # Communication Services (3 stocks)
    "DIS",    # Walt Disney - Entertainment
    "NFLX",   # Netflix Inc. - Streaming
    "CMCSA",  # Comcast Corp. - Telecom/Media
    
    # Industrials (4 stocks)
    "BA",     # Boeing - Aerospace
    "UPS",    # United Parcel Service - Logistics
    "CAT",    # Caterpillar - Heavy Equipment
    "HON",    # Honeywell - Diversified Industrial
    
    # Energy (3 stocks)
    "XOM",    # Exxon Mobil - Oil & Gas
    "CVX",    # Chevron Corp. - Oil & Gas
    "COP",    # ConocoPhillips - Oil & Gas
    
    # Consumer Staples (2 stocks)
    "PG",     # Procter & Gamble - Consumer Goods
    "KO",     # Coca-Cola - Beverages
    
    # Utilities (1 stock)
    "NEE",    # NextEra Energy - Electric Utility
    
    # Real Estate (1 stock)
    "PLD",    # Prologis Inc. - Industrial REITs
]


# ============================================================================
# BENCHMARK TICKERS
# ============================================================================

BENCHMARK_TICKERS: List[str] = [
    "SPY",  # S&P 500 ETF - Market benchmark for cross-asset features
]


# ============================================================================
# ALL TICKERS (Stocks + Benchmarks)
# ============================================================================

ALL_TICKERS = STOCK_UNIVERSE + BENCHMARK_TICKERS

UNIVERSE_METADATA: Dict = {
    "total_stocks": len(STOCK_UNIVERSE),
    "benchmark_tickers": len(BENCHMARK_TICKERS),
    "total_tickers": len(ALL_TICKERS),
    "last_updated": "2026-01-17",
    "review_frequency": "monthly",
    "min_daily_volume": 500_000,  # shares
    "min_market_cap": 10_000_000_000,  # $10B USD
    "index_source": "S&P 500",
}


SECTOR_ALLOCATION: Dict[str, int] = {
    "Technology": 15,
    "Healthcare": 7,
    "Financials": 8,
    "Consumer Discretionary": 6,
    "Communication Services": 3,
    "Industrials": 4,
    "Energy": 3,
    "Consumer Staples": 2,
    "Utilities": 1,
    "Real Estate": 1,
}


# ============================================================================
# SELECTION CRITERIA DOCUMENTATION
# ============================================================================

SELECTION_CRITERIA: Dict = {
    "liquidity": {
        "description": "High trading volume ensures efficient order execution",
        "min_daily_volume": 500_000,
        "typical_volume": "1M-10M+ shares/day",
        "bid_ask_spread": "Tight (typically < 0.1%)",
        "importance": "Critical for minimizing slippage and market impact",
    },
    
    "market_cap": {
        "description": "Large-cap stocks for stability and liquidity",
        "min_market_cap": 10_000_000_000,  # $10B
        "typical_range": "$10B - $3T",
        "importance": "Reduces volatility and ensures institutional participation",
    },
    
    "sector_diversity": {
        "description": "Balanced exposure across major economic sectors",
        "sectors": list(SECTOR_ALLOCATION.keys()),
        "allocation": SECTOR_ALLOCATION,
        "importance": "Reduces concentration risk and sector-specific exposure",
    },
    
    "index_membership": {
        "description": "S&P 500 constituent preferred",
        "index": "S&P 500",
        "benefit": "Institutional coverage, analyst research, stable fundamentals",
        "importance": "Ensures quality and reduces delisting risk",
    },
    
    "data_quality": {
        "description": "Consistent historical data availability",
        "min_history": "3 years",
        "data_source": "Yahoo Finance / Alpha Vantage",
        "validation": "Daily price/volume checks, gap detection",
        "importance": "Essential for accurate backtesting and model training",
    },
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_universe() -> List[str]:
    """
    Get the current stock universe.
    
    Returns:
        List of ticker symbols
    """
    return STOCK_UNIVERSE.copy()


def get_benchmark_tickers() -> List[str]:
    """
    Get benchmark tickers (used for cross-asset features).
    
    Returns:
        List of benchmark ticker symbols
    """
    return BENCHMARK_TICKERS.copy()


def get_all_tickers() -> List[str]:
    """
    Get all tickers (stocks + benchmarks).
    
    Returns:
        List of all ticker symbols
    """
    return ALL_TICKERS.copy()


def get_universe_size() -> int:
    """
    Get the number of stocks in the universe.
    
    Returns:
        Number of stocks
    """
    return len(STOCK_UNIVERSE)


def is_in_universe(ticker: str) -> bool:
    """
    Check if a ticker is in the universe.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        True if ticker is in universe, False otherwise
    """
    return ticker.upper() in STOCK_UNIVERSE


def get_sector_allocation() -> Dict[str, int]:
    """
    Get sector allocation breakdown.
    
    Returns:
        Dictionary mapping sector names to number of stocks
    """
    return SECTOR_ALLOCATION.copy()


def get_metadata() -> Dict:
    """
    Get universe metadata.
    
    Returns:
        Dictionary with universe configuration details
    """
    return UNIVERSE_METADATA.copy()


def get_selection_criteria() -> Dict:
    """
    Get detailed selection criteria documentation.
    
    Returns:
        Dictionary with selection criteria details
    """
    return SELECTION_CRITERIA.copy()


def validate_universe() -> Dict:
    """
    Validate universe configuration.
    
    Returns:
        Dictionary with validation results
    """
    checks = {
        "total_stocks": len(STOCK_UNIVERSE),
        "expected_stocks": 50,
        "has_duplicates": len(STOCK_UNIVERSE) != len(set(STOCK_UNIVERSE)),
        "sector_total": sum(SECTOR_ALLOCATION.values()),
    }
    
    checks["valid"] = (
        checks["total_stocks"] == checks["expected_stocks"] and
        not checks["has_duplicates"] and
        checks["sector_total"] == checks["total_stocks"]
    )
    
    return checks


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("QUANTSNAP STOCK UNIVERSE")
    print("=" * 70)
    
    validation = validate_universe()
    print(f"\nTotal Stocks: {validation['total_stocks']}")
    print(f"Benchmark Tickers: {len(BENCHMARK_TICKERS)}")
    print(f"Total Tickers: {len(ALL_TICKERS)}")
    print(f"Valid Configuration: {'✓' if validation['valid'] else '✗'}")
    
    print(f"\nBenchmark Tickers:")
    print("-" * 50)
    for ticker in BENCHMARK_TICKERS:
        print(f"  {ticker:<10} (Market benchmark for cross-asset features)")
    
    print(f"\nSector Allocation:")
    print("-" * 50)
    for sector, count in SECTOR_ALLOCATION.items():
        pct = (count / len(STOCK_UNIVERSE)) * 100
        print(f"  {sector:<25} {count:>2} ({pct:>5.1f}%)")
    
    print(f"\nSelection Criteria:")
    print("-" * 50)
    print(f"  Min Daily Volume:  {UNIVERSE_METADATA['min_daily_volume']:,} shares")
    print(f"  Min Market Cap:    ${UNIVERSE_METADATA['min_market_cap'] / 1e9:.0f}B")
    print(f"  Index Source:      {UNIVERSE_METADATA['index_source']}")
    print(f"  Last Updated:      {UNIVERSE_METADATA['last_updated']}")
    
    print(f"\nStocks in Universe:")
    print("-" * 50)
    for i, ticker in enumerate(STOCK_UNIVERSE, 1):
        print(f"  {ticker}", end="  ")
        if i % 10 == 0:
            print()
    print("\n")
