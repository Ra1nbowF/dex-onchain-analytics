-- DEX Onchain Analytics Database Schema
-- PostgreSQL database for storing blockchain and DEX data

-- Create database if not exists
-- CREATE DATABASE dex_analytics;

-- Chain information
CREATE TABLE IF NOT EXISTS chains (
    chain_id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    explorer_url VARCHAR(255),
    rpc_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DEX protocols
CREATE TABLE IF NOT EXISTS dex_protocols (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER REFERENCES chains(chain_id),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20),
    factory_address VARCHAR(42) NOT NULL,
    router_address VARCHAR(42),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chain_id, factory_address)
);

-- Token information
CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER REFERENCES chains(chain_id),
    address VARCHAR(42) NOT NULL,
    symbol VARCHAR(50),
    name VARCHAR(255),
    decimals INTEGER DEFAULT 18,
    total_supply NUMERIC(78, 0),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chain_id, address)
);

-- DEX pairs/pools
CREATE TABLE IF NOT EXISTS dex_pairs (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER REFERENCES chains(chain_id),
    dex_protocol_id INTEGER REFERENCES dex_protocols(id),
    pair_address VARCHAR(42) NOT NULL,
    token0_address VARCHAR(42) NOT NULL,
    token1_address VARCHAR(42) NOT NULL,
    token0_reserve NUMERIC(78, 0),
    token1_reserve NUMERIC(78, 0),
    total_liquidity NUMERIC(78, 0),
    creation_block BIGINT,
    creation_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chain_id, pair_address)
);

-- Swap transactions
CREATE TABLE IF NOT EXISTS swap_transactions (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER REFERENCES chains(chain_id),
    pair_id INTEGER REFERENCES dex_pairs(id),
    tx_hash VARCHAR(66) NOT NULL,
    block_number BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    sender_address VARCHAR(42),
    to_address VARCHAR(42),
    amount0_in NUMERIC(78, 0),
    amount1_in NUMERIC(78, 0),
    amount0_out NUMERIC(78, 0),
    amount1_out NUMERIC(78, 0),
    gas_used BIGINT,
    gas_price NUMERIC(78, 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chain_id, tx_hash)
);

-- Token transfers
CREATE TABLE IF NOT EXISTS token_transfers (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER REFERENCES chains(chain_id),
    token_id INTEGER REFERENCES tokens(id),
    tx_hash VARCHAR(66) NOT NULL,
    block_number BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    value NUMERIC(78, 0) NOT NULL,
    gas_used BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wallet tracking
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    address VARCHAR(42) UNIQUE NOT NULL,
    label VARCHAR(255),
    is_contract BOOLEAN DEFAULT FALSE,
    is_dex_trader BOOLEAN DEFAULT FALSE,
    is_whale BOOLEAN DEFAULT FALSE,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wallet balances (snapshot)
CREATE TABLE IF NOT EXISTS wallet_balances (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES wallets(id),
    chain_id INTEGER REFERENCES chains(chain_id),
    token_id INTEGER REFERENCES tokens(id),
    balance NUMERIC(78, 0) NOT NULL,
    usd_value DECIMAL(20, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    block_number BIGINT
);

-- Liquidity events (add/remove)
CREATE TABLE IF NOT EXISTS liquidity_events (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER REFERENCES chains(chain_id),
    pair_id INTEGER REFERENCES dex_pairs(id),
    tx_hash VARCHAR(66) NOT NULL,
    event_type VARCHAR(20) NOT NULL, -- 'ADD' or 'REMOVE'
    provider_address VARCHAR(42),
    amount0 NUMERIC(78, 0),
    amount1 NUMERIC(78, 0),
    liquidity_tokens NUMERIC(78, 0),
    timestamp TIMESTAMP NOT NULL,
    block_number BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price snapshots
CREATE TABLE IF NOT EXISTS price_snapshots (
    id SERIAL PRIMARY KEY,
    pair_id INTEGER REFERENCES dex_pairs(id),
    token0_price DECIMAL(40, 18),
    token1_price DECIMAL(40, 18),
    volume_24h NUMERIC(78, 0),
    liquidity_usd DECIMAL(20, 2),
    price_change_24h DECIMAL(10, 4),
    timestamp TIMESTAMP NOT NULL,
    block_number BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Arbitrage opportunities
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER REFERENCES chains(chain_id),
    token_address VARCHAR(42),
    buy_dex VARCHAR(100),
    sell_dex VARCHAR(100),
    buy_price DECIMAL(40, 18),
    sell_price DECIMAL(40, 18),
    spread_percentage DECIMAL(10, 4),
    potential_profit_usd DECIMAL(20, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE
);

-- Trading metrics (aggregated)
CREATE TABLE IF NOT EXISTS trading_metrics (
    id SERIAL PRIMARY KEY,
    chain_id INTEGER REFERENCES chains(chain_id),
    token_id INTEGER REFERENCES tokens(id),
    period_type VARCHAR(20), -- 'HOURLY', 'DAILY', 'WEEKLY'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_trades INTEGER,
    unique_traders INTEGER,
    buy_count INTEGER,
    sell_count INTEGER,
    total_volume NUMERIC(78, 0),
    avg_trade_size NUMERIC(78, 0),
    price_high DECIMAL(40, 18),
    price_low DECIMAL(40, 18),
    price_open DECIMAL(40, 18),
    price_close DECIMAL(40, 18),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Smart money wallets
CREATE TABLE IF NOT EXISTS smart_money_wallets (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES wallets(id),
    chain_id INTEGER REFERENCES chains(chain_id),
    total_profit_usd DECIMAL(20, 2),
    win_rate DECIMAL(5, 2),
    avg_holding_time_hours DECIMAL(10, 2),
    total_trades INTEGER,
    profitable_trades INTEGER,
    ranking_score DECIMAL(10, 4),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX idx_swap_tx_timestamp ON swap_transactions(timestamp DESC);
CREATE INDEX idx_swap_tx_pair ON swap_transactions(pair_id);
CREATE INDEX idx_swap_tx_block ON swap_transactions(block_number DESC);
CREATE INDEX idx_token_transfers_token ON token_transfers(token_id);
CREATE INDEX idx_token_transfers_from ON token_transfers(from_address);
CREATE INDEX idx_token_transfers_to ON token_transfers(to_address);
CREATE INDEX idx_token_transfers_timestamp ON token_transfers(timestamp DESC);
CREATE INDEX idx_wallet_balances_wallet ON wallet_balances(wallet_id);
CREATE INDEX idx_wallet_balances_token ON wallet_balances(token_id);
CREATE INDEX idx_price_snapshots_pair ON price_snapshots(pair_id);
CREATE INDEX idx_price_snapshots_timestamp ON price_snapshots(timestamp DESC);
CREATE INDEX idx_trading_metrics_token ON trading_metrics(token_id);
CREATE INDEX idx_trading_metrics_period ON trading_metrics(period_start, period_end);
CREATE INDEX idx_dex_pairs_tokens ON dex_pairs(token0_address, token1_address);
CREATE INDEX idx_liquidity_events_pair ON liquidity_events(pair_id);
CREATE INDEX idx_arbitrage_timestamp ON arbitrage_opportunities(timestamp DESC);

-- Functions for data management
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-updating timestamps
CREATE TRIGGER update_tokens_modtime BEFORE UPDATE ON tokens
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_dex_pairs_modtime BEFORE UPDATE ON dex_pairs
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_wallets_modtime BEFORE UPDATE ON wallets
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Insert initial chain data
INSERT INTO chains (chain_id, name, symbol, explorer_url) VALUES
    (1, 'Ethereum', 'ETH', 'https://etherscan.io'),
    (56, 'BSC', 'BNB', 'https://bscscan.com'),
    (137, 'Polygon', 'MATIC', 'https://polygonscan.com'),
    (42161, 'Arbitrum', 'ETH', 'https://arbiscan.io'),
    (10, 'Optimism', 'ETH', 'https://optimistic.etherscan.io'),
    (8453, 'Base', 'ETH', 'https://basescan.org'),
    (43114, 'Avalanche', 'AVAX', 'https://snowtrace.io')
ON CONFLICT (chain_id) DO NOTHING;