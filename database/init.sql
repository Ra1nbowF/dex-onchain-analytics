-- Simplified DEX Analytics Schema for Grafana Visualization

-- Drop existing tables if they exist
DROP TABLE IF EXISTS dex_trades CASCADE;
DROP TABLE IF EXISTS token_prices CASCADE;
DROP TABLE IF EXISTS liquidity_pools CASCADE;
DROP TABLE IF EXISTS wallet_activity CASCADE;
DROP TABLE IF EXISTS chain_stats CASCADE;

-- Chain statistics (simple)
CREATE TABLE chain_stats (
    id SERIAL PRIMARY KEY,
    chain_name VARCHAR(50) NOT NULL,
    chain_id INTEGER NOT NULL,
    total_volume_24h DECIMAL(30, 2),
    total_transactions INTEGER,
    active_wallets INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token prices (simple)
CREATE TABLE token_prices (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER NOT NULL,
    token_symbol VARCHAR(20) NOT NULL,
    token_address VARCHAR(42),
    price_usd DECIMAL(20, 8),
    volume_24h DECIMAL(30, 2),
    price_change_24h DECIMAL(10, 4),
    market_cap DECIMAL(30, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DEX trades (raw data)
CREATE TABLE dex_trades (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER NOT NULL,
    chain_name VARCHAR(50),
    dex_name VARCHAR(50) NOT NULL,
    pair VARCHAR(50) NOT NULL,
    token_in VARCHAR(20),
    token_out VARCHAR(20),
    amount_in DECIMAL(30, 8),
    amount_out DECIMAL(30, 8),
    price DECIMAL(20, 8),
    value_usd DECIMAL(30, 2),
    trader_address VARCHAR(42),
    tx_hash VARCHAR(66),
    gas_used INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Liquidity pools
CREATE TABLE liquidity_pools (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER NOT NULL,
    chain_name VARCHAR(50),
    dex_name VARCHAR(50) NOT NULL,
    pool_address VARCHAR(42),
    token0_symbol VARCHAR(20),
    token1_symbol VARCHAR(20),
    token0_reserve DECIMAL(30, 8),
    token1_reserve DECIMAL(30, 8),
    total_liquidity_usd DECIMAL(30, 2),
    volume_24h DECIMAL(30, 2),
    fees_24h DECIMAL(20, 2),
    apy DECIMAL(10, 4),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wallet activity
CREATE TABLE wallet_activity (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER NOT NULL,
    wallet_address VARCHAR(42) NOT NULL,
    wallet_label VARCHAR(100),
    total_trades INTEGER DEFAULT 0,
    volume_24h DECIMAL(30, 2),
    profit_loss DECIMAL(20, 2),
    win_rate DECIMAL(5, 2),
    tokens_traded INTEGER,
    last_trade_time TIMESTAMP,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_dex_trades_timestamp ON dex_trades(timestamp DESC);
CREATE INDEX idx_dex_trades_chain ON dex_trades(chain_id, timestamp DESC);
CREATE INDEX idx_dex_trades_dex ON dex_trades(dex_name, timestamp DESC);
CREATE INDEX idx_dex_trades_pair ON dex_trades(pair);
CREATE INDEX idx_dex_trades_trader ON dex_trades(trader_address);

CREATE INDEX idx_token_prices_timestamp ON token_prices(timestamp DESC);
CREATE INDEX idx_token_prices_symbol ON token_prices(token_symbol, timestamp DESC);

CREATE INDEX idx_liquidity_pools_timestamp ON liquidity_pools(timestamp DESC);
CREATE INDEX idx_liquidity_pools_dex ON liquidity_pools(dex_name, timestamp DESC);

CREATE INDEX idx_wallet_activity_timestamp ON wallet_activity(timestamp DESC);
CREATE INDEX idx_wallet_activity_volume ON wallet_activity(volume_24h DESC);

-- Create materialized views for Grafana
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_dex_stats AS
SELECT
    date_trunc('hour', timestamp) as hour,
    chain_name,
    dex_name,
    COUNT(*) as trade_count,
    SUM(value_usd) as volume_usd,
    AVG(gas_used) as avg_gas,
    COUNT(DISTINCT trader_address) as unique_traders
FROM dex_trades
GROUP BY date_trunc('hour', timestamp), chain_name, dex_name
ORDER BY hour DESC;

CREATE MATERIALIZED VIEW IF NOT EXISTS top_pairs_24h AS
SELECT
    pair,
    chain_name,
    dex_name,
    COUNT(*) as trade_count,
    SUM(value_usd) as volume_usd,
    AVG(price) as avg_price,
    MAX(timestamp) as last_trade
FROM dex_trades
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY pair, chain_name, dex_name
ORDER BY volume_usd DESC
LIMIT 100;

-- Create refresh function
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_dex_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY top_pairs_24h;
END;
$$ LANGUAGE plpgsql;

-- Create unique indexes for CONCURRENTLY refresh
CREATE UNIQUE INDEX ON hourly_dex_stats (hour, chain_name, dex_name);
CREATE UNIQUE INDEX ON top_pairs_24h (pair, chain_name, dex_name);