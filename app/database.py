#!/usr/bin/env python3
"""
Database management for QuantSnap with separate factor files
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import yfinance as yf
import numpy as np

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Separate CSV files for different data types
        self.stocks_file = self.data_dir / "stocks.csv"
        self.traditional_factors_file = self.data_dir / "traditional_factors.csv"
        self.reputation_factors_file = self.data_dir / "reputation_factors.csv"
        self.rankings_file = self.data_dir / "rankings.csv"
        self.indicators_file = self.data_dir / "indicators.csv"
        
    def get_stock_universe(self, universe_name: str = "world_top_stocks") -> List[str]:
        """Get stock tickers for a universe"""
        universe_file = self.data_dir / "universes" / f"{universe_name}.csv"
        
        if universe_file.exists():
            try:
                df = pd.read_csv(universe_file)
                return df['Ticker'].tolist()
            except Exception as e:
                logger.error(f"Error reading universe {universe_name}: {e}")
        
        # Fallback to hardcoded list
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "JNJ",
            "JPM", "V", "PG", "HD", "MA", "DIS", "PYPL", "ADBE", "CRM", "NFLX", "ABT", "PFE",
            "KO", "PEP", "AVGO", "TMO", "COST", "ABBV", "WMT", "ACN", "DHR", "NEE", "LLY",
            "TXN", "HON", "UNP", "LOW", "SPGI", "ISRG", "GILD", "BMY", "RTX", "QCOM", "AMAT",
            "ADI", "MDLZ", "BKNG", "REGN", "CMCSA", "KLAC", "VRTX", "PANW", "SNPS", "CDNS",
            "MU", "ORCL", "CSCO", "INTC", "IBM", "GE", "CAT", "DE", "BA", "GS", "MS", "BLK",
            "AXP", "C", "WFC", "BAC", "USB", "PNC", "T", "VZ", "CME", "ICE", "AMD", "ZM",
            "SHOP", "SQ", "ROKU", "SPOT", "UBER", "LYFT", "SNAP", "TWTR", "PLTR", "SNOW",
            "CRWD", "ZS", "OKTA", "TEAM", "DOCU", "DDOG", "NET", "MDB", "ESTC", "PATH",
            "RBLX", "COIN", "HOOD", "DASH", "PTON", "BYND", "NIO", "XPEV", "LI", "LCID",
            "RIVN", "BABA", "JD", "PDD", "TCEHY", "NTES", "BILI", "TME", "DIDI"
        ]
    
    def calculate_traditional_factors(self, ticker: str) -> Optional[Dict]:
        """Calculate traditional quantitative factors (67% weight)"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if hist.empty or len(hist) < 30:
                return None
            
            current_price = hist['Close'].iloc[-1]
            returns = hist['Close'].pct_change().dropna()
            
            # Momentum factors
            momentum_1m = ((current_price / hist['Close'].iloc[-22]) - 1) * 100 if len(hist) >= 21 else 0
            momentum_3m = ((current_price / hist['Close'].iloc[-64]) - 1) * 100 if len(hist) >= 63 else 0
            momentum_6m = ((current_price / hist['Close'].iloc[-126]) - 1) * 100 if len(hist) >= 126 else 0
            
            # Volatility factors
            volatility_30d = returns.tail(30).std() * 100 if len(returns) >= 30 else returns.std() * 100
            volatility_60d = returns.tail(60).std() * 100 if len(returns) >= 60 else returns.std() * 100
            
            # Volume factors
            volume_avg_20d = hist['Volume'].tail(20).mean() if len(hist) >= 20 else hist['Volume'].mean()
            volume_avg_60d = hist['Volume'].tail(60).mean() if len(hist) >= 60 else hist['Volume'].mean()
            
            # Price factors
            price_change_1d = hist['Close'].pct_change().iloc[-1] * 100
            price_change_5d = hist['Close'].pct_change(5).iloc[-1] * 100 if len(hist) >= 5 else 0
            
            # Sharpe ratio
            if len(returns) >= 63:
                returns_3m = returns.tail(63)
                sharpe_ratio = (returns_3m.mean() / returns_3m.std()) * np.sqrt(252) if returns_3m.std() > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Beta calculation (vs SPY)
            try:
                spy_data = yf.download('SPY', period="1y", progress=False, auto_adjust=True)
                if not spy_data.empty and len(spy_data) >= 30:
                    spy_returns = spy_data['Close'].pct_change().dropna()
                    stock_returns = hist['Close'].pct_change().dropna()
                    
                    # Align the data
                    common_dates = stock_returns.index.intersection(spy_returns.index)
                    if len(common_dates) >= 30:
                        stock_aligned = stock_returns.loc[common_dates]
                        spy_aligned = spy_returns.loc[common_dates]
                        
                        covariance = np.cov(stock_aligned, spy_aligned)[0, 1]
                        spy_variance = np.var(spy_aligned)
                        beta = covariance / spy_variance if spy_variance > 0 else 1.0
                    else:
                        beta = 1.0
                else:
                    beta = 1.0
            except:
                beta = 1.0
            
            return {
                'ticker': ticker,
                'momentum_1m': round(momentum_1m, 2),
                'momentum_3m': round(momentum_3m, 2),
                'momentum_6m': round(momentum_6m, 2),
                'volatility_30d': round(volatility_30d, 2),
                'volatility_60d': round(volatility_60d, 2),
                'volume_avg_20d': round(volume_avg_20d, 0),
                'volume_avg_60d': round(volume_avg_60d, 0),
                'price_change_1d': round(price_change_1d, 2),
                'price_change_5d': round(price_change_5d, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'beta': round(beta, 2),
                'current_price': round(current_price, 2),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error calculating traditional factors for {ticker}: {e}")
            return None
    
    def calculate_reputation_factors(self, ticker: str) -> Optional[Dict]:
        """Calculate reputation factors (33% weight)"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Financial health indicators
            debt_to_equity = info.get('debtToEquity', 0)
            current_ratio = info.get('currentRatio', 0)
            quick_ratio = info.get('quickRatio', 0)
            roe = info.get('returnOnEquity', 0)
            roa = info.get('returnOnAssets', 0)
            
            # Market position indicators
            market_cap = info.get('marketCap', 0)
            enterprise_value = info.get('enterpriseValue', 0)
            price_to_book = info.get('priceToBook', 0)
            price_to_sales = info.get('priceToSales', 0)
            
            # Growth indicators
            revenue_growth = info.get('revenueGrowth', 0)
            earnings_growth = info.get('earningsGrowth', 0)
            profit_margins = info.get('profitMargins', 0)
            
            # Stability indicators
            dividend_yield = info.get('dividendYield', 0)
            payout_ratio = info.get('payoutRatio', 0)
            
            # Calculate composite scores
            financial_health_score = self._calculate_financial_health_score(
                debt_to_equity, current_ratio, quick_ratio, roe, roa
            )
            
            market_position_score = self._calculate_market_position_score(
                market_cap, enterprise_value, price_to_book, price_to_sales
            )
            
            growth_stability_score = self._calculate_growth_stability_score(
                revenue_growth, earnings_growth, profit_margins, dividend_yield, payout_ratio
            )
            
            return {
                'ticker': ticker,
                'debt_to_equity': round(debt_to_equity, 2),
                'current_ratio': round(current_ratio, 2),
                'quick_ratio': round(quick_ratio, 2),
                'roe': round(roe, 4),
                'roa': round(roa, 4),
                'market_cap': market_cap,
                'enterprise_value': enterprise_value,
                'price_to_book': round(price_to_book, 2),
                'price_to_sales': round(price_to_sales, 2),
                'revenue_growth': round(revenue_growth, 4) if revenue_growth else 0,
                'earnings_growth': round(earnings_growth, 4) if earnings_growth else 0,
                'profit_margins': round(profit_margins, 4) if profit_margins else 0,
                'dividend_yield': round(dividend_yield, 4) if dividend_yield else 0,
                'payout_ratio': round(payout_ratio, 4) if payout_ratio else 0,
                'financial_health_score': round(financial_health_score, 3),
                'market_position_score': round(market_position_score, 3),
                'growth_stability_score': round(growth_stability_score, 3),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error calculating reputation factors for {ticker}: {e}")
            return None
    
    def _calculate_financial_health_score(self, debt_to_equity, current_ratio, quick_ratio, roe, roa):
        """Calculate financial health composite score"""
        scores = []
        
        # Debt to equity (lower is better)
        if debt_to_equity and debt_to_equity > 0:
            if debt_to_equity < 0.5:
                scores.append(1.0)
            elif debt_to_equity < 1.0:
                scores.append(0.8)
            elif debt_to_equity < 2.0:
                scores.append(0.6)
            else:
                scores.append(0.3)
        
        # Current ratio (higher is better)
        if current_ratio and current_ratio > 0:
            if current_ratio > 2.0:
                scores.append(1.0)
            elif current_ratio > 1.5:
                scores.append(0.8)
            elif current_ratio > 1.0:
                scores.append(0.6)
            else:
                scores.append(0.3)
        
        # ROE (higher is better)
        if roe and roe > 0:
            if roe > 0.15:
                scores.append(1.0)
            elif roe > 0.10:
                scores.append(0.8)
            elif roe > 0.05:
                scores.append(0.6)
            else:
                scores.append(0.3)
        
        return np.mean(scores) if scores else 0.5
    
    def _calculate_market_position_score(self, market_cap, enterprise_value, price_to_book, price_to_sales):
        """Calculate market position composite score"""
        scores = []
        
        # Market cap (higher is better for stability)
        if market_cap and market_cap > 0:
            if market_cap > 100e9:  # > $100B
                scores.append(1.0)
            elif market_cap > 10e9:  # > $10B
                scores.append(0.8)
            elif market_cap > 1e9:   # > $1B
                scores.append(0.6)
            else:
                scores.append(0.4)
        
        # Price to book (lower is better)
        if price_to_book and price_to_book > 0:
            if price_to_book < 1.0:
                scores.append(1.0)
            elif price_to_book < 2.0:
                scores.append(0.8)
            elif price_to_book < 5.0:
                scores.append(0.6)
            else:
                scores.append(0.3)
        
        return np.mean(scores) if scores else 0.5
    
    def _calculate_growth_stability_score(self, revenue_growth, earnings_growth, profit_margins, dividend_yield, payout_ratio):
        """Calculate growth and stability composite score"""
        scores = []
        
        # Revenue growth (higher is better)
        if revenue_growth and revenue_growth > 0:
            if revenue_growth > 0.20:
                scores.append(1.0)
            elif revenue_growth > 0.10:
                scores.append(0.8)
            elif revenue_growth > 0.05:
                scores.append(0.6)
            else:
                scores.append(0.4)
        
        # Profit margins (higher is better)
        if profit_margins and profit_margins > 0:
            if profit_margins > 0.20:
                scores.append(1.0)
            elif profit_margins > 0.10:
                scores.append(0.8)
            elif profit_margins > 0.05:
                scores.append(0.6)
            else:
                scores.append(0.3)
        
        # Dividend yield (moderate is good)
        if dividend_yield and dividend_yield > 0:
            if 0.02 < dividend_yield < 0.06:
                scores.append(1.0)
            elif 0.01 < dividend_yield < 0.08:
                scores.append(0.8)
            else:
                scores.append(0.5)
        
        return np.mean(scores) if scores else 0.5
    
    def calculate_composite_score(self, traditional_factors: Dict, reputation_factors: Dict) -> float:
        """Calculate 67/33 composite score"""
        # Traditional factors score (67% weight)
        traditional_score = (
            traditional_factors.get('momentum_1m', 0) * 0.2 +
            traditional_factors.get('momentum_3m', 0) * 0.15 +
            traditional_factors.get('sharpe_ratio', 0) * 0.25 +
            (traditional_factors.get('volume_avg_20d', 0) / 1000000) * 0.1 +
            (1 / (1 + traditional_factors.get('volatility_30d', 1))) * 0.1
        ) * 0.67
        
        # Reputation factors score (33% weight)
        reputation_score = (
            reputation_factors.get('financial_health_score', 0) * 0.4 +
            reputation_factors.get('market_position_score', 0) * 0.3 +
            reputation_factors.get('growth_stability_score', 0) * 0.3
        ) * 0.33
        
        return traditional_score + reputation_score
    
    def update_all_data(self, universe_name: str = "world_top_stocks") -> List[Dict]:
        """Update all data files"""
        logger.info(f"Updating all data for universe: {universe_name}")
        
        tickers = self.get_stock_universe(universe_name)
        traditional_data = []
        reputation_data = []
        rankings_data = []
        
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"Processing {ticker} ({i}/{len(tickers)})")
            
            # Calculate traditional factors
            trad_factors = self.calculate_traditional_factors(ticker)
            if trad_factors:
                traditional_data.append(trad_factors)
            
            # Calculate reputation factors
            rep_factors = self.calculate_reputation_factors(ticker)
            if rep_factors:
                reputation_data.append(rep_factors)
            
            # Calculate composite score if both factors available
            if trad_factors and rep_factors:
                composite_score = self.calculate_composite_score(trad_factors, rep_factors)
                
                ranking_entry = {
                    'ticker': ticker,
                    'name': rep_factors.get('name', ticker),
                    'sector': rep_factors.get('sector', 'Unknown'),
                    'price': trad_factors.get('current_price', 0),
                    'traditional_score': trad_factors.get('sharpe_ratio', 0),
                    'reputation_score': rep_factors.get('financial_health_score', 0),
                    'score': round(composite_score, 3),
                    'momentum_1m': trad_factors.get('momentum_1m', 0),
                    'momentum_3m': trad_factors.get('momentum_3m', 0),
                    'sharpe_ratio': trad_factors.get('sharpe_ratio', 0),
                    'volatility': trad_factors.get('volatility_30d', 0),
                    'volume_avg': trad_factors.get('volume_avg_20d', 0),
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                rankings_data.append(ranking_entry)
        
        # Save to separate CSV files
        if traditional_data:
            trad_df = pd.DataFrame(traditional_data)
            trad_df.to_csv(self.traditional_factors_file, index=False)
            logger.info(f"Saved {len(traditional_data)} traditional factors")
        
        if reputation_data:
            rep_df = pd.DataFrame(reputation_data)
            rep_df.to_csv(self.reputation_factors_file, index=False)
            logger.info(f"Saved {len(reputation_data)} reputation factors")
        
        if rankings_data:
            # Sort by score
            rankings_df = pd.DataFrame(rankings_data)
            rankings_df = rankings_df.sort_values('score', ascending=False).reset_index(drop=True)
            rankings_df['rank'] = range(1, len(rankings_df) + 1)
            rankings_df.to_csv(self.rankings_file, index=False)
            logger.info(f"Saved {len(rankings_data)} rankings")
        
        return rankings_data
    
    def get_rankings(self, universe_name: str = "world_top_stocks", limit: int = 10) -> List[Dict]:
        """Get current rankings"""
        if not self.rankings_file.exists():
            logger.info("No rankings file found, updating...")
            return self.update_all_data(universe_name)[:limit]
        
        try:
            df = pd.read_csv(self.rankings_file)
            return df.head(limit).to_dict('records')
        except Exception as e:
            logger.error(f"Error reading rankings: {e}")
            return self.update_all_data(universe_name)[:limit]
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive stock data"""
        try:
            # Get traditional factors
            trad_factors = self.calculate_traditional_factors(ticker)
            if not trad_factors:
                return None
            
            # Get reputation factors
            rep_factors = self.calculate_reputation_factors(ticker)
            if not rep_factors:
                return None
            
            # Calculate composite score
            composite_score = self.calculate_composite_score(trad_factors, rep_factors)
            
            # Combine data
            stock_data = {
                'ticker': ticker,
                'name': rep_factors.get('name', ticker),
                'sector': rep_factors.get('sector', 'Unknown'),
                'market_cap': rep_factors.get('market_cap', 0),
                'price': trad_factors.get('current_price', 0),
                'momentum_1m': trad_factors.get('momentum_1m', 0),
                'momentum_3m': trad_factors.get('momentum_3m', 0),
                'volatility': trad_factors.get('volatility_30d', 0),
                'volume_avg': trad_factors.get('volume_avg_20d', 0),
                'sharpe_ratio': trad_factors.get('sharpe_ratio', 0),
                'score': round(composite_score, 3),
                'traditional_score': trad_factors.get('sharpe_ratio', 0),
                'reputation_score': rep_factors.get('financial_health_score', 0),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error getting stock data for {ticker}: {e}")
            return None
    
    def get_all_universes(self) -> List[str]:
        """Get list of available universes"""
        universe_dir = self.data_dir / "universes"
        if universe_dir.exists():
            return [f.stem for f in universe_dir.glob("*.csv")]
        return ["world_top_stocks"]
