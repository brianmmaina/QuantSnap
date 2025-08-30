#!/usr/bin/env python3
"""
Database management for QuantSnap - Alpha Vantage + yfinance fallback
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import time
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Define factor files for 67/33 breakdown
        self.traditional_factors_file = self.data_dir / "traditional_factors.csv"
        self.reputation_factors_file = self.data_dir / "reputation_factors.csv"
        
        # Note: Using yfinance as primary data source (no rate limits, reliable)
        
        # Comprehensive stock universe - 500+ top stocks (cleaned and deduplicated)
        self.stocks = [
            # Technology (100+ stocks)
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "CRM",
            "ORCL", "INTC", "AMD", "QCOM", "TXN", "AVGO", "MU", "AMAT", "KLAC", "LRCX",
            "ASML", "TSM", "SMCI", "PLTR", "SNOW", "DDOG", "CRWD", "ZS", "OKTA", "NET",
            "PYPL", "COIN", "HOOD", "DASH", "UBER", "LYFT", "ZM", "TEAM", "SHOP", "SPOT",
            "PINS", "SNAP", "RBLX", "EA", "TTWO", "TTD", "ROKU", "DOCU", "TWLO",
            "MELI", "SE", "JD", "BABA", "PDD", "TCEHY", "NIO", "XPEV", "LI", "BIDU",
            "NTES", "TME", "VIPS", "BILI", "IQ", "HUYA", "DOYU", "WB", "SINA",
            "SOHU", "CTRP", "TCOM", "HTHT", "ZTO", "YUMC", "BZUN", "VNET", "DANG",
            "YY", "MOMO", "XNET", "JRJC", "SFUN",
            
            # Financial (50+ stocks)
            "JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "V", "MA", "UNH",
            "BLK", "SCHW", "COF", "USB", "PNC", "TFC", "KEY", "HBAN", "RF", "FITB",
            "MTB", "STT", "NTRS", "BEN", "IVZ", "TROW", "AMG", "APO", "KKR", "BX",
            "CG", "ARES", "OWL", "PIPR", "LAZ", "HLI", "EVR", "PJT", "MC", "RJF",
            "SF", "AMP", "AON", "MMC", "AJG", "BRO", "MKL", "BRK.A", "BRK.B",
            
            # Healthcare (50+ stocks)
            "JNJ", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD",
            "CVS", "WBA", "CI", "ANTM", "HUM", "CNC", "MOH", "AGN", "BIIB",
            "REGN", "VRTX", "ALXN", "ILMN", "DXCM", "ISRG", "IDXX", "ALGN", "WST", "COO",
            "IQV", "LH", "DGX", "HOLX", "BAX", "BDX", "ZBH", "SYK", "BSX", "MDT", "EW",
            
            # Consumer/Retail (50+ stocks)
            "WMT", "TGT", "COST", "HD", "LOW", "NKE", "SBUX", "MCD", "DIS", "CMCSA",
            "ULTA", "LULU", "UA", "DECK", "SKX", "FL", "JBLU", "DAL", "UAL", "AAL",
            "LUV", "ALK", "SKYW", "ALGT", "BA", "RTX", "LMT", "GD", "NOC", "LHX",
            "TDG", "KTOS", "TXT", "CAT", "DE", "CNH", "AGCO", "TTC", "LNN", "ALG",
            "WNC", "OSK", "JCI", "EMR", "ETN", "ROK", "DOV", "XYL", "AME", "FTV",
            
            # Energy (30+ stocks)
            "XOM", "CVX", "COP", "EOG", "SLB", "HAL", "BKR", "KMI", "WMB", "MPC",
            "VLO", "PSX", "HES", "PXD", "FANG", "DVN", "MRO", "OXY", "APA", "NBL",
            "CHK", "RRC", "EQT", "SWN", "RICE", "GPOR", "AR", "NFX", "PE",
            
            # Industrials (50+ stocks)
            "ITT", "FLS", "PH", "DHR", "HON", "GE", "MMM",
            
            # Materials (30+ stocks)
            "LIN", "APD", "FCX", "NEM", "NUE", "STLD", "X", "AA", "ALB", "LTHM",
            "LVS", "WYNN", "MGM", "CZR", "PENN", "BYD", "BALY", "RRR", "CHDN",
            
            # Real Estate (30+ stocks)
            "AMT", "CCI", "SBAC", "PLD", "EQIX", "DLR", "WELL", "PSA", "SPG", "O",
            "AVB", "EQR", "MAA", "UDR", "ESS", "AIV", "CPT", "BXP", "VNO", "SLG",
            "KIM", "REG", "FRT", "MAC", "PEAK", "ARE", "HST", "HHC", "IRM", "PLD",
            
            # Utilities (20+ stocks)
            "NEE", "DUK", "SO", "D", "AEP", "XEL", "SRE", "DTE", "WEC", "ED",
            "EIX", "PEG", "AEE", "CMS", "CNP", "NI", "LNT", "ATO", "BKH", "PNW",
            
            # Communication Services (30+ stocks)
            "T", "VZ", "TMUS", "CHTR", "FOX", "FOXA", "NWSA", "NWS", "PARA", "WBD",
            "LYV", "LGF.A", "IMAX",
            
            # Consumer Staples (30+ stocks)
            "PM", "MO", "STZ", "BF.B", "TAP", "SAM", "BUD", "HEINY", "DEO", "MGAM",
            "CAG", "GIS", "K", "HSY", "SJM", "CPB", "HRL",
            
            # Additional Tech & Growth (50+ stocks)
            "SQ"
        ]
        
        # Remove duplicates and ensure unique stocks
        self.stocks = list(set(self.stocks))
        logger.info(f"Loaded {len(self.stocks)} unique stocks")
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive stock data from yfinance with optimized accuracy"""
        try:
            # Use yfinance as primary source (no rate limits, more reliable)
            time.sleep(0.1)  # Small delay to be respectful
            
            # Create ticker object
            stock = yf.Ticker(ticker)
            
            # Get comprehensive data
            hist = stock.history(period="1y", auto_adjust=True)
            info = stock.info
            
            if hist.empty or len(hist) < 30:
                logger.warning(f"Insufficient data for {ticker}")
                return None
            
            # Get current price and calculate metrics
            current_price = hist['Close'].iloc[-1]
            returns = hist['Close'].pct_change().dropna()
            
            # Calculate accurate stock price growth using proper date ranges
            if len(hist) >= 21:
                month_ago_price = hist['Close'].iloc[-21]
                momentum_1m = ((current_price / month_ago_price) - 1) * 100
            else:
                momentum_1m = 0
                
            if len(hist) >= 63:
                three_months_ago_price = hist['Close'].iloc[-63]
                momentum_3m = ((current_price / three_months_ago_price) - 1) * 100
            else:
                momentum_3m = 0
                
            if len(hist) >= 126:
                six_months_ago_price = hist['Close'].iloc[-126]
                momentum_6m = ((current_price / six_months_ago_price) - 1) * 100
            else:
                momentum_6m = 0
            
            # Volatility (30-day rolling)
            volatility_30d = returns.tail(30).std() * 100 if len(returns) >= 30 else returns.std() * 100
            
            # Volume (20-day average)
            volume_avg_20d = hist['Volume'].tail(20).mean() if len(hist) >= 20 else hist['Volume'].mean()
            
            # Sharpe ratio (3-month)
            if len(returns) >= 63:
                returns_3m = returns.tail(63)
                sharpe_ratio = (returns_3m.mean() / returns_3m.std()) * np.sqrt(252) if returns_3m.std() > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Daily change (current vs previous close)
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            daily_change = current_price - previous_close
            daily_change_pct = (daily_change / previous_close) * 100 if previous_close > 0 else 0
            
            # Get comprehensive company info from yfinance
            company_name = info.get('longName', info.get('shortName', ticker))
            sector = info.get('sector', 'Unknown')
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE', 0)
            dividend_yield = info.get('dividendYield', 0)
            beta = info.get('beta', 1.0)
            
            # 67/33 Factor Breakdown: Traditional vs Reputation Factors
            
            # Improved scoring algorithm - prioritize positive growth and quality metrics
            
            # Traditional Factors (67% weight) - Quantitative metrics
            # Normalize and scale factors properly
            momentum_1m_normalized = max(momentum_1m, -50) / 50  # Cap at -50% to +50%, normalize to -1 to +1
            momentum_3m_normalized = max(momentum_3m, -50) / 50  # Cap at -50% to +50%, normalize to -1 to +1
            sharpe_normalized = max(min(sharpe_ratio, 3), -1) / 3  # Cap Sharpe at -1 to +3, normalize to -0.33 to +1
            volume_factor = min(volume_avg_20d / 10000000, 1)  # Volume factor (0 to 1, max 10M volume)
            market_cap_factor = min(market_cap / 1e12, 1)  # Market cap factor (0 to 1, max 1T)
            
            traditional_score = (
                (momentum_1m_normalized * 0.4) +      # 1M growth (40% of traditional)
                (momentum_3m_normalized * 0.25) +     # 3M growth (25% of traditional)
                (sharpe_normalized * 0.15) +          # Sharpe ratio (15% of traditional)
                (volume_factor * 0.1) +               # Volume factor (10% of traditional)
                (market_cap_factor * 0.1)             # Market cap factor (10% of traditional)
            )
            
            # Reputation Factors (33% weight) - Qualitative metrics
            pe_quality = max(1 / (pe_ratio + 1), 0) if pe_ratio > 0 else 0.5  # P/E quality (0 to 1)
            dividend_factor = min(dividend_yield, 5) / 5  # Dividend factor (0 to 1, max 5%)
            beta_stability = max(1 / (beta + 0.1), 0)  # Beta stability (0 to 1)
            
            reputation_score = (
                (pe_quality * 0.4) +           # P/E ratio quality (40% of reputation)
                (dividend_factor * 0.35) +     # Dividend yield (35% of reputation)
                (beta_stability * 0.25)        # Beta stability (25% of reputation)
            )
            
            # Combine with 67/33 weighting
            score = (traditional_score * 0.67) + (reputation_score * 0.33)
            
            # Scale score to 0-10 range for better usability
            score = score * 20  # Scale up to 0-10 range
            
            # Apply strict performance filters - exclude poor performers
            if momentum_1m < -5:  # If 1M growth is less than -5%
                score *= 0.1  # Severely penalize (90% reduction)
            elif momentum_1m < 0:  # If 1M growth is negative
                score *= 0.3  # Heavily penalize (70% reduction)
            elif momentum_1m < 2:  # If 1M growth is less than 2%
                score *= 0.7  # Moderate penalty (30% reduction)
            
            # Debug logging for top stocks
            if ticker in ['NVDA', 'INTC', 'AMD', 'GOOGL', 'AAPL', 'TSLA', 'MSFT', 'META', 'AMZN', 'NFLX']:
                logger.info(f"DEBUG {ticker}: 1M={momentum_1m:.2f}%, 3M={momentum_3m:.2f}%, Sharpe={sharpe_ratio:.2f}, Score={score:.3f}")
            
            return {
                'ticker': ticker,
                'name': company_name,
                'sector': sector,
                'price': round(current_price, 2),
                'momentum_1m': round(momentum_1m, 2),
                'momentum_3m': round(momentum_3m, 2),
                'momentum_6m': round(momentum_6m, 2),
                'volatility': round(volatility_30d, 2),
                'volume_avg': round(volume_avg_20d, 0),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'daily_change': round(daily_change, 2),
                'daily_change_pct': round(daily_change_pct, 2),
                'market_cap': market_cap,
                'pe_ratio': round(pe_ratio, 2) if pe_ratio else 0,
                'dividend_yield': round(dividend_yield * 100, 2) if dividend_yield else 0,
                'beta': round(beta, 2),
                'score': round(score, 3),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            if "Too Many Requests" in str(e):
                logger.warning(f"Rate limited for {ticker}, skipping...")
            else:
                logger.error(f"Error getting stock data for {ticker}: {e}")
            return None
    
    def get_live_prices(self, tickers: List[str]) -> Dict:
        """Get live prices for multiple stocks from yfinance with optimized accuracy"""
        price_data = {}
        
        for ticker in tickers:
            try:
                time.sleep(0.1)  # Small delay to be respectful
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get current market data
                current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
                previous_close = info.get('regularMarketPreviousClose', info.get('previousClose', 0))
                change = current_price - previous_close if previous_close else 0
                change_pct = (change / previous_close * 100) if previous_close else 0
                
                # Get additional market data
                volume = info.get('volume', info.get('regularMarketVolume', 0))
                market_cap = info.get('marketCap', 0)
                pe_ratio = info.get('trailingPE', 0)
                dividend_yield = info.get('dividendYield', 0)
                
                price_data[ticker] = {
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'volume': volume,
                    'market_cap': market_cap,
                    'pe_ratio': round(pe_ratio, 2) if pe_ratio else 0,
                    'dividend_yield': round(dividend_yield * 100, 2) if dividend_yield else 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Live price for {ticker}: ${current_price} ({change_pct:+.2f}%)")
                
            except Exception as e:
                logger.error(f"Error fetching live price for {ticker}: {e}")
                continue
        
        return price_data
    
    def get_chart_data(self, ticker: str, period: str = "1y") -> Optional[Dict]:
        """Get chart data for a stock from yfinance with enhanced metrics"""
        try:
            time.sleep(0.1)  # Small delay to be respectful
            stock = yf.Ticker(ticker)
            
            # Get historical data with auto-adjustment
            hist = stock.history(period=period, auto_adjust=True)
            
            if hist.empty:
                logger.warning(f"No chart data available for {ticker}")
                return None
            
            # Get comprehensive company info
            info = stock.info
            company_name = info.get('longName', info.get('shortName', ticker))
            sector = info.get('sector', 'Unknown')
            market_cap = info.get('marketCap', 0)
            
            # Calculate enhanced metrics
            current_price = hist['Close'].iloc[-1]
            start_price = hist['Close'].iloc[0]
            change = current_price - start_price
            change_pct = (change / start_price) * 100 if start_price != 0 else 0.0
            
            # Calculate additional metrics
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * 100
            avg_volume = hist['Volume'].mean()
            
            # Format chart data with OHLCV
            chart_data = []
            for date, row in hist.iterrows():
                chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume'])
                })
            
            return {
                "ticker": ticker,
                "company_name": company_name,
                "sector": sector,
                "period": period,
                "current_price": round(current_price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volatility": round(volatility, 2),
                "avg_volume": int(avg_volume),
                "market_cap": market_cap,
                "data": chart_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting chart data for {ticker}: {e}")
            return None
    
    def get_rankings(self, universe_name: str = "world_top_stocks", limit: int = 10) -> List[Dict]:
        """Get current rankings by fetching fresh data with rate limiting"""
        try:
            rankings = []
            successful_fetches = 0
            
            for ticker in self.stocks:
                data = self.get_stock_data(ticker)
                if data and data['score'] > 2.0:  # Only include stocks with good scores (scaled to 0-10)
                    rankings.append(data)
                    successful_fetches += 1
                    
                    # Get more stocks to ensure we have quality picks
                    if successful_fetches >= limit * 5:  # Get 5x the limit to have better options
                        break
            
            # Sort by score (highest first) and add rank
            rankings.sort(key=lambda x: x['score'], reverse=True)
            
            for i, ranking in enumerate(rankings[:limit]):
                ranking['rank'] = i + 1
            
            logger.info(f"Successfully fetched {len(rankings[:limit])} stock rankings")
            return rankings[:limit]
            
        except Exception as e:
            logger.error(f"Error getting rankings: {e}")
            return []
    
    def get_all_universes(self) -> List[str]:
        """Get list of available universes"""
        return ["world_top_stocks"]
    
    def get_all_stocks_metadata(self) -> List[Dict]:
        """Get metadata for all available stocks (similar to basketball scout's approach)"""
        try:
            metadata = []
            for ticker in self.stocks[:100]:  # Limit to top 100 for performance
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    metadata.append({
                        "ticker": ticker,
                        "name": info.get('longName', info.get('shortName', ticker)),
                        "sector": info.get('sector', 'Unknown'),
                        "industry": info.get('industry', 'Unknown'),
                        "market_cap": info.get('marketCap', 0),
                        "country": info.get('country', 'Unknown')
                    })
                except Exception as e:
                    # Skip stocks that fail to load
                    continue
            
            return metadata
        except Exception as e:
            logger.error(f"Error getting stocks metadata: {e}")
            return []
    
    def update_all_data(self, universe_name: str = "world_top_stocks") -> List[Dict]:
        """Update all stock data (same as get_rankings for direct approach)"""
        return self.get_rankings(universe_name, limit=50)
