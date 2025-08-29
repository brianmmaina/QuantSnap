-- PostgreSQL Schema for AI Daily Draft
-- Clean, normalized data structure for stock analysis

-- Companies table (normalized)
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    enterprise_value BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily price data (time series)
CREATE TABLE IF NOT EXISTS daily_prices (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES companies(ticker),
    date DATE NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4),
    adj_close DECIMAL(10,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

-- Calculated factors (daily snapshots)
CREATE TABLE IF NOT EXISTS daily_factors (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES companies(ticker),
    date DATE NOT NULL,
    -- Traditional factors
    mom_1m DECIMAL(8,6),      -- 1-month momentum
    mom_3m DECIMAL(8,6),      -- 3-month momentum
    slope_50d DECIMAL(8,6),   -- 50-day slope
    vol_30d DECIMAL(8,6),     -- 30-day volatility
    sharpe_3m DECIMAL(8,6),   -- 3-month Sharpe ratio
    dollar_vol_20d BIGINT,    -- 20-day dollar volume
    
    -- Reputation factors
    esg_score DECIMAL(5,4),   -- ESG score (0-1)
    env_score DECIMAL(5,4),   -- Environmental score
    social_score DECIMAL(5,4), -- Social score
    gov_score DECIMAL(5,4),   -- Governance score
    
    -- Financial health
    debt_to_equity DECIMAL(8,4),
    current_ratio DECIMAL(8,4),
    quick_ratio DECIMAL(8,4),
    roe DECIMAL(8,4),         -- Return on equity
    roa DECIMAL(8,4),         -- Return on assets
    
    -- Market position
    r_d_spending BIGINT,      -- R&D spending
    revenue_growth DECIMAL(8,4),
    earnings_growth DECIMAL(8,4),
    profit_margins DECIMAL(8,4),
    
    -- Stability metrics
    dividend_yield DECIMAL(8,4),
    payout_ratio DECIMAL(8,4),
    beta DECIMAL(8,4),
    price_stability DECIMAL(8,4),
    
    -- Composite scores
    reputation_score DECIMAL(5,4),
    financial_health_score DECIMAL(5,4),
    market_position_score DECIMAL(5,4),
    growth_stability_score DECIMAL(5,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

-- Rankings table (daily snapshots)
CREATE TABLE IF NOT EXISTS daily_rankings (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES companies(ticker),
    date DATE NOT NULL,
    universe VARCHAR(50) NOT NULL, -- 'sp500', 'world_top_stocks', etc.
    rank INTEGER NOT NULL,
    score DECIMAL(8,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date, universe)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker_date ON daily_prices(ticker, date);
CREATE INDEX IF NOT EXISTS idx_daily_factors_ticker_date ON daily_factors(ticker, date);
CREATE INDEX IF NOT EXISTS idx_daily_rankings_date_universe ON daily_rankings(date, universe);
CREATE INDEX IF NOT EXISTS idx_daily_rankings_ticker ON daily_rankings(ticker);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_companies_updated_at') THEN
        CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
