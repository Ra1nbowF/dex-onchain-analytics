-- Comprehensive DEX Onchain Analytics Database Schema for Railway
-- This script creates all tables needed for the DEX analytics platform

-- Drop existing tables to avoid conflicts (optional - remove if you want to preserve data)
DROP TABLE IF EXISTS moralis_swaps_enhanced CASCADE;
DROP TABLE IF EXISTS moralis_token_holder_stats CASCADE;
DROP TABLE IF EXISTS moralis_historical_holders_enhanced CASCADE;
DROP TABLE IF EXISTS moralis_pair_stats_enhanced CASCADE;
DROP TABLE IF EXISTS moralis_token_analytics_enhanced CASCADE;
DROP TABLE IF EXISTS moralis_snipers_enhanced CASCADE;
DROP TABLE IF EXISTS moralis_top_gainers CASCADE;
DROP TABLE IF EXISTS moralis_token_stats_simple CASCADE;
DROP TABLE IF EXISTS moralis_swaps_correct CASCADE;
DROP TABLE IF EXISTS moralis_token_analytics_correct CASCADE;
DROP TABLE IF EXISTS moralis_pair_stats_correct CASCADE;
DROP TABLE IF EXISTS moralis_holder_stats_correct CASCADE;
DROP TABLE IF EXISTS moralis_historical_holders_correct CASCADE;
DROP TABLE IF EXISTS moralis_snipers_correct CASCADE;
DROP TABLE IF EXISTS moralis_token_stats CASCADE;
DROP TABLE IF EXISTS moralis_holder_stats_complete CASCADE;
DROP TABLE IF EXISTS moralis_historical_holders CASCADE;
DROP TABLE IF EXISTS moralis_token_transfers CASCADE;
DROP TABLE IF EXISTS moralis_snipers_complete CASCADE;
DROP TABLE IF EXISTS moralis_liquidity_changes CASCADE;
DROP TABLE IF EXISTS moralis_holder_distribution CASCADE;
DROP TABLE IF EXISTS wash_trading_complete CASCADE;
DROP TABLE IF EXISTS moralis_metrics_summary CASCADE;
DROP TABLE IF EXISTS dex_trades CASCADE;
DROP TABLE IF EXISTS token_prices CASCADE;
DROP TABLE IF EXISTS liquidity_pools CASCADE;
DROP TABLE IF EXISTS wallet_activity CASCADE;
DROP TABLE IF EXISTS chain_stats CASCADE;
DROP TABLE IF EXISTS chains CASCADE;
DROP TABLE IF EXISTS dex_protocols CASCADE;
DROP TABLE IF EXISTS tokens CASCADE;
DROP TABLE IF EXISTS dex_pairs CASCADE;
DROP TABLE IF EXISTS swap_transactions CASCADE;
DROP TABLE IF EXISTS token_transfers CASCADE;
DROP TABLE IF EXISTS wallets CASCADE;
DROP TABLE IF EXISTS wallet_balances CASCADE;
DROP TABLE IF EXISTS liquidity_events CASCADE;
DROP TABLE IF EXISTS price_snapshots CASCADE;
DROP TABLE IF EXISTS arbitrage_opportunities CASCADE;
DROP TABLE IF EXISTS trading_metrics CASCADE;
DROP TABLE IF EXISTS smart_money_wallets CASCADE;

-- Schema.sql tables

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

-- Token transfers (from schema.sql)
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

-- Token transfers (from moralis_complete_monitor.py - different from schema.sql)
CREATE TABLE IF NOT EXISTS moralis_token_transfers (
    id SERIAL PRIMARY KEY,
    transaction_hash VARCHAR(66) UNIQUE,
    block_number BIGINT,
    block_timestamp TIMESTAMP,
    from_address VARCHAR(42),
    to_address VARCHAR(42),
    value DECIMAL(40, 18),
    value_usd DECIMAL(30, 2),
    token_address VARCHAR(42),
    token_symbol VARCHAR(20),
    transaction_index INTEGER,
    log_index INTEGER,
    is_spam BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Init.sql tables (for collector.py)

-- Chain statistics (simple)
CREATE TABLE IF NOT EXISTS chain_stats (
    id SERIAL PRIMARY KEY,
    chain_name VARCHAR(50) NOT NULL,
    chain_id INTEGER NOT NULL,
    total_volume_24h DECIMAL(30, 2),
    total_transactions INTEGER,
    active_wallets INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token prices (simple)
CREATE TABLE IF NOT EXISTS token_prices (
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
CREATE TABLE IF NOT EXISTS dex_trades (
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
CREATE TABLE IF NOT EXISTS liquidity_pools (
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
CREATE TABLE IF NOT EXISTS wallet_activity (
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

-- Enhanced Moralis Tables for Missing API Endpoints

-- Enhanced swaps table with new fields from API
CREATE TABLE IF NOT EXISTS moralis_swaps_enhanced (
    id SERIAL PRIMARY KEY,
    transaction_hash TEXT UNIQUE,
    transaction_index INT,
    transaction_type TEXT, -- buy/sell
    sub_category TEXT, -- accumulation, etc
    block_number BIGINT,
    block_timestamp TIMESTAMP,
    wallet_address TEXT,
    wallet_address_label TEXT,
    entity TEXT,
    entity_logo TEXT,
    pair_address TEXT,
    pair_label TEXT,
    exchange_address TEXT,
    exchange_name TEXT,
    exchange_logo TEXT,
    bought_address TEXT,
    bought_name TEXT,
    bought_symbol TEXT,
    bought_logo TEXT,
    bought_amount NUMERIC(40, 18),
    bought_usd_price NUMERIC(20, 8),
    bought_usd_amount NUMERIC(20, 2),
    sold_address TEXT,
    sold_name TEXT,
    sold_symbol TEXT,
    sold_logo TEXT,
    sold_amount NUMERIC(40, 18),
    sold_usd_price NUMERIC(20, 8),
    sold_usd_amount NUMERIC(20, 2),
    base_quote_price NUMERIC(40, 18),
    total_value_usd NUMERIC(20, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token holder stats with distribution categories
CREATE TABLE IF NOT EXISTS moralis_token_holder_stats (
    id SERIAL PRIMARY KEY,
    token_address TEXT,
    total_holders INT,
    holder_supply_top10 NUMERIC(40, 18),
    holder_supply_top10_percent NUMERIC(10, 6),
    holder_supply_top25 NUMERIC(40, 18),
    holder_supply_top25_percent NUMERIC(10, 6),
    holder_supply_top50 NUMERIC(40, 18),
    holder_supply_top50_percent NUMERIC(10, 6),
    holder_supply_top100 NUMERIC(40, 18),
    holder_supply_top100_percent NUMERIC(10, 6),
    holder_change_5min INT,
    holder_change_5min_percent NUMERIC(10, 6),
    holder_change_1h INT,
    holder_change_1h_percent NUMERIC(10, 6),
    holder_change_24h INT,
    holder_change_24h_percent NUMERIC(10, 6),
    holders_by_swap INT,
    holders_by_transfer INT,
    holders_by_airdrop INT,
    whales_count INT,
    sharks_count INT,
    dolphins_count INT,
    fish_count INT,
    octopus_count INT,
    crabs_count INT,
    shrimps_count INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_address, timestamp)
);

-- Historical holders timeseries
CREATE TABLE IF NOT EXISTS moralis_historical_holders_enhanced (
    id SERIAL PRIMARY KEY,
    token_address TEXT,
    timestamp TIMESTAMP,
    total_holders INT,
    net_holder_change INT,
    holder_percent_change NUMERIC(10, 6),
    new_holders_by_swap INT,
    new_holders_by_transfer INT,
    new_holders_by_airdrop INT,
    holders_in_whales INT,
    holders_in_sharks INT,
    holders_in_dolphins INT,
    holders_in_fish INT,
    holders_in_octopus INT,
    holders_in_crabs INT,
    holders_in_shrimps INT,
    holders_out_whales INT,
    holders_out_sharks INT,
    holders_out_dolphins INT,
    holders_out_fish INT,
    holders_out_octopus INT,
    holders_out_crabs INT,
    holders_out_shrimps INT,
    UNIQUE(token_address, timestamp)
);

-- Pair stats with comprehensive metrics
CREATE TABLE IF NOT EXISTS moralis_pair_stats_enhanced (
    id SERIAL PRIMARY KEY,
    pair_address TEXT,
    token_address TEXT,
    token_name TEXT,
    token_symbol TEXT,
    token_logo TEXT,
    pair_created TIMESTAMP,
    pair_label TEXT,
    exchange TEXT,
    exchange_address TEXT,
    exchange_logo TEXT,
    exchange_url TEXT,
    current_usd_price NUMERIC(20, 10),
    current_native_price NUMERIC(20, 10),
    total_liquidity_usd NUMERIC(20, 2),
    price_change_5min NUMERIC(10, 6),
    price_change_1h NUMERIC(10, 6),
    price_change_4h NUMERIC(10, 6),
    price_change_24h NUMERIC(10, 6),
    liquidity_change_5min NUMERIC(10, 6),
    liquidity_change_1h NUMERIC(10, 6),
    liquidity_change_4h NUMERIC(10, 6),
    liquidity_change_24h NUMERIC(10, 6),
    buys_5min INT,
    buys_1h INT,
    buys_4h INT,
    buys_24h INT,
    sells_5min INT,
    sells_1h INT,
    sells_4h INT,
    sells_24h INT,
    volume_5min NUMERIC(20, 2),
    volume_1h NUMERIC(20, 2),
    volume_4h NUMERIC(20, 2),
    volume_24h NUMERIC(20, 2),
    buy_volume_5min NUMERIC(20, 2),
    buy_volume_1h NUMERIC(20, 2),
    buy_volume_4h NUMERIC(20, 2),
    buy_volume_24h NUMERIC(20, 2),
    sell_volume_5min NUMERIC(20, 2),
    sell_volume_1h NUMERIC(20, 2),
    sell_volume_4h NUMERIC(20, 2),
    sell_volume_24h NUMERIC(20, 2),
    buyers_5min INT,
    buyers_1h INT,
    buyers_4h INT,
    buyers_24h INT,
    sellers_5min INT,
    sellers_1h INT,
    sellers_4h INT,
    sellers_24h INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pair_address, timestamp)
);

-- Token analytics with comprehensive time-based metrics
CREATE TABLE IF NOT EXISTS moralis_token_analytics_enhanced (
    id SERIAL PRIMARY KEY,
    token_address TEXT,
    category_id TEXT,
    buy_volume_5m NUMERIC(20, 2),
    buy_volume_1h NUMERIC(20, 2),
    buy_volume_6h NUMERIC(20, 2),
    buy_volume_24h NUMERIC(20, 2),
    sell_volume_5m NUMERIC(20, 2),
    sell_volume_1h NUMERIC(20, 2),
    sell_volume_6h NUMERIC(20, 2),
    sell_volume_24h NUMERIC(20, 2),
    buyers_5m INT,
    buyers_1h INT,
    buyers_6h INT,
    buyers_24h INT,
    sellers_5m INT,
    sellers_1h INT,
    sellers_6h INT,
    sellers_24h INT,
    buys_5m INT,
    buys_1h INT,
    buys_6h INT,
    buys_24h INT,
    sells_5m INT,
    sells_1h INT,
    sells_6h INT,
    sells_24h INT,
    liquidity_5m NUMERIC(20, 2),
    liquidity_1h NUMERIC(20, 2),
    liquidity_6h NUMERIC(20, 2),
    liquidity_24h NUMERIC(20, 2),
    fdv_5m NUMERIC(20, 2),
    fdv_1h NUMERIC(20, 2),
    fdv_6h NUMERIC(20, 2),
    fdv_24h NUMERIC(20, 2),
    price_change_5m NUMERIC(10, 6),
    price_change_1h NUMERIC(10, 6),
    price_change_6h NUMERIC(10, 6),
    price_change_24h NUMERIC(10, 6),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_address, timestamp)
);

-- Enhanced snipers table with PnL data
CREATE TABLE IF NOT EXISTS moralis_snipers_enhanced (
    id SERIAL PRIMARY KEY,
    pair_address TEXT,
    transaction_hash TEXT,
    block_timestamp TIMESTAMP,
    block_number BIGINT,
    wallet_address TEXT,
    total_tokens_sniped NUMERIC(40, 18),
    total_sniped_usd NUMERIC(20, 2),
    total_sniped_transactions INT,
    total_tokens_sold NUMERIC(40, 18),
    total_sold_usd NUMERIC(20, 2),
    total_sell_transactions INT,
    current_balance NUMERIC(40, 18),
    current_balance_usd_value NUMERIC(20, 2),
    realized_profit_percentage NUMERIC(10, 6),
    realized_profit_usd NUMERIC(20, 2),
    blocks_after_creation INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pair_address, wallet_address)
);

-- Top gainers/profitable wallets
CREATE TABLE IF NOT EXISTS moralis_top_gainers (
    id SERIAL PRIMARY KEY,
    token_address TEXT,
    wallet_address TEXT,
    avg_buy_price_usd NUMERIC(20, 8),
    avg_cost_of_quantity_sold NUMERIC(20, 8),
    avg_sell_price_usd NUMERIC(20, 8),
    count_of_trades INT,
    realized_profit_percentage NUMERIC(10, 6),
    realized_profit_usd NUMERIC(20, 2),
    total_sold_usd NUMERIC(20, 2),
    total_tokens_bought NUMERIC(40, 18),
    total_tokens_sold NUMERIC(40, 18),
    total_usd_invested NUMERIC(20, 2),
    timeframe TEXT, -- all, 7, 30 days
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_address, wallet_address, timeframe)
);

-- Token stats (simple endpoint)
CREATE TABLE IF NOT EXISTS moralis_token_stats_simple (
    id SERIAL PRIMARY KEY,
    token_address TEXT,
    total_transfers BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_address, timestamp)
);

-- Create tables from create_moralis_correct_tables.sql

-- SWAPS TABLE (from /erc20/{address}/swaps)
CREATE TABLE IF NOT EXISTS moralis_swaps_correct (
    transaction_hash TEXT PRIMARY KEY,
    transaction_index INTEGER,
    transaction_type TEXT,
    block_timestamp TIMESTAMP,
    block_number BIGINT,
    sub_category TEXT,
    wallet_address TEXT,
    wallet_address_label TEXT,
    entity TEXT,
    entity_logo TEXT,
    pair_address TEXT,
    pair_label TEXT,
    exchange_address TEXT,
    exchange_name TEXT,
    exchange_logo TEXT,
    bought_address TEXT,
    bought_name TEXT,
    bought_symbol TEXT,
    bought_logo TEXT,
    bought_amount NUMERIC(40,18),
    bought_usd_price NUMERIC(40,18),
    bought_usd_amount NUMERIC(40,18),
    sold_address TEXT,
    sold_name TEXT,
    sold_symbol TEXT,
    sold_logo TEXT,
    sold_amount NUMERIC(40,18),
    sold_usd_price NUMERIC(40,18),
    sold_usd_amount NUMERIC(40,18),
    base_quote_price TEXT,
    total_value_usd NUMERIC(40,18),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TOKEN ANALYTICS TABLE (from /tokens/{address}/analytics)
CREATE TABLE IF NOT EXISTS moralis_token_analytics_correct (
    id SERIAL PRIMARY KEY,
    token_address TEXT,
    category_id TEXT,
    -- Buy volumes
    total_buy_volume_5m NUMERIC(40,18),
    total_buy_volume_1h NUMERIC(40,18),
    total_buy_volume_6h NUMERIC(40,18),
    total_buy_volume_24h NUMERIC(40,18),
    -- Sell volumes
    total_sell_volume_5m NUMERIC(40,18),
    total_sell_volume_1h NUMERIC(40,18),
    total_sell_volume_6h NUMERIC(40,18),
    total_sell_volume_24h NUMERIC(40,18),
    -- Buyers
    total_buyers_5m INTEGER,
    total_buyers_1h INTEGER,
    total_buyers_6h INTEGER,
    total_buyers_24h INTEGER,
    -- Sellers
    total_sellers_5m INTEGER,
    total_sellers_1h INTEGER,
    total_sellers_6h INTEGER,
    total_sellers_24h INTEGER,
    -- Buy transactions
    total_buys_5m INTEGER,
    total_buys_1h INTEGER,
    total_buys_6h INTEGER,
    total_buys_24h INTEGER,
    -- Sell transactions
    total_sells_5m INTEGER,
    total_sells_1h INTEGER,
    total_sells_6h INTEGER,
    total_sells_24h INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_address, timestamp)
);

-- PAIR STATS TABLE (from /pairs/{address}/stats)
CREATE TABLE IF NOT EXISTS moralis_pair_stats_correct (
    id SERIAL PRIMARY KEY,
    pair_address TEXT,
    pair_label TEXT,
    pair_created TIMESTAMP,
    token_address TEXT,
    token_name TEXT,
    token_symbol TEXT,
    token_logo TEXT,
    exchange TEXT,
    exchange_address TEXT,
    exchange_logo TEXT,
    exchange_url TEXT,
    current_usd_price NUMERIC(40,18),
    current_native_price NUMERIC(40,18),
    total_liquidity_usd NUMERIC(40,18),
    -- Price changes
    price_change_5min NUMERIC(20,6),
    price_change_1h NUMERIC(20,6),
    price_change_4h NUMERIC(20,6),
    price_change_24h NUMERIC(20,6),
    -- Liquidity changes
    liquidity_change_5min NUMERIC(20,6),
    liquidity_change_1h NUMERIC(20,6),
    liquidity_change_4h NUMERIC(20,6),
    liquidity_change_24h NUMERIC(20,6),
    -- Transaction counts
    buys_5min INTEGER,
    buys_1h INTEGER,
    buys_4h INTEGER,
    buys_24h INTEGER,
    sells_5min INTEGER,
    sells_1h INTEGER,
    sells_4h INTEGER,
    sells_24h INTEGER,
    -- Volumes
    total_volume_5min NUMERIC(40,18),
    total_volume_1h NUMERIC(40,18),
    total_volume_4h NUMERIC(40,18),
    total_volume_24h NUMERIC(40,18),
    buy_volume_5min NUMERIC(40,18),
    buy_volume_1h NUMERIC(40,18),
    buy_volume_4h NUMERIC(40,18),
    buy_volume_24h NUMERIC(40,18),
    sell_volume_5min NUMERIC(40,18),
    sell_volume_1h NUMERIC(40,18),
    sell_volume_4h NUMERIC(40,18),
    sell_volume_24h NUMERIC(40,18),
    -- Traders
    buyers_5min INTEGER,
    buyers_1h INTEGER,
    buyers_4h INTEGER,
    buyers_24h INTEGER,
    sellers_5min INTEGER,
    sellers_1h INTEGER,
    sellers_4h INTEGER,
    sellers_24h INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pair_address, timestamp)
);

-- HOLDER STATS TABLE (from /erc20/{address}/holders)
CREATE TABLE IF NOT EXISTS moralis_holder_stats_correct (
    id SERIAL PRIMARY KEY,
    token_address TEXT,
    total_holders INTEGER,
    -- Holder supply concentrations
    top10_supply NUMERIC(40,18),
    top10_supply_percent NUMERIC(20,6),
    top25_supply NUMERIC(40,18),
    top25_supply_percent NUMERIC(20,6),
    top50_supply NUMERIC(40,18),
    top50_supply_percent NUMERIC(20,6),
    top100_supply NUMERIC(40,18),
    top100_supply_percent NUMERIC(20,6),
    top250_supply NUMERIC(40,18),
    top250_supply_percent NUMERIC(20,6),
    top500_supply NUMERIC(40,18),
    top500_supply_percent NUMERIC(20,6),
    -- Holder changes
    holder_change_5min INTEGER,
    holder_change_percent_5min NUMERIC(20,6),
    holder_change_1h INTEGER,
    holder_change_percent_1h NUMERIC(20,6),
    holder_change_6h INTEGER,
    holder_change_percent_6h NUMERIC(20,6),
    holder_change_24h INTEGER,
    holder_change_percent_24h NUMERIC(20,6),
    holder_change_3d INTEGER,
    holder_change_percent_3d NUMERIC(20,6),
    holder_change_7d INTEGER,
    holder_change_percent_7d NUMERIC(20,6),
    holder_change_30d INTEGER,
    holder_change_percent_30d NUMERIC(20,6),
    -- Holders by acquisition
    holders_by_swap INTEGER,
    holders_by_transfer INTEGER,
    holders_by_airdrop INTEGER,
    -- Holder distribution
    whales INTEGER,
    sharks INTEGER,
    dolphins INTEGER,
    fish INTEGER,
    octopus INTEGER,
    crabs INTEGER,
    shrimps INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_address, timestamp)
);

-- HISTORICAL HOLDERS TABLE (from /erc20/{address}/holders/historical)
CREATE TABLE IF NOT EXISTS moralis_historical_holders_correct (
    id SERIAL PRIMARY KEY,
    token_address TEXT,
    timestamp TIMESTAMP,
    total_holders INTEGER,
    net_holder_change INTEGER,
    holder_percent_change NUMERIC(20,6),
    -- New holders by acquisition
    new_holders_by_swap INTEGER,
    new_holders_by_transfer INTEGER,
    new_holders_by_airdrop INTEGER,
    -- Holders in (joining)
    holders_in_whales INTEGER,
    holders_in_sharks INTEGER,
    holders_in_dolphins INTEGER,
    holders_in_fish INTEGER,
    holders_in_octopus INTEGER,
    holders_in_crabs INTEGER,
    holders_in_shrimps INTEGER,
    -- Holders out (leaving)
    holders_out_whales INTEGER,
    holders_out_sharks INTEGER,
    holders_out_dolphins INTEGER,
    holders_out_fish INTEGER,
    holders_out_octopus INTEGER,
    holders_out_crabs INTEGER,
    holders_out_shrimps INTEGER,
    UNIQUE(token_address, timestamp)
);

-- SNIPERS TABLE (from /pairs/{address}/snipers)
CREATE TABLE IF NOT EXISTS moralis_snipers_correct (
    id SERIAL PRIMARY KEY,
    pair_address TEXT,
    wallet_address TEXT,
    total_tokens_sniped NUMERIC(40,18),
    total_sniped_usd NUMERIC(40,18),
    total_sniped_transactions INTEGER,
    total_tokens_sold NUMERIC(40,18),
    total_sold_usd NUMERIC(40,18),
    total_sell_transactions INTEGER,
    current_balance NUMERIC(40,18),
    current_balance_usd_value NUMERIC(40,18),
    realized_profit_percentage NUMERIC(20,6),
    realized_profit_usd NUMERIC(40,18),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pair_address, wallet_address, timestamp)
);

-- Complete Moralis Monitor tables

-- Token Stats (comprehensive token metrics)
CREATE TABLE IF NOT EXISTS moralis_token_stats (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(42),
    token_name VARCHAR(100),
    token_symbol VARCHAR(20),
    total_supply DECIMAL(40, 18),
    circulating_supply DECIMAL(40, 18),
    market_cap DECIMAL(30, 2),
    fdv DECIMAL(30, 2),
    transfers_total BIGINT,
    holders_count INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Complete Holder Stats with distribution
CREATE TABLE IF NOT EXISTS moralis_holder_stats_complete (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(42),
    total_holders INTEGER,
    holders_change_5m INTEGER,
    holders_change_1h INTEGER,
    holders_change_24h INTEGER,
    holders_change_7d INTEGER,
    holders_change_30d INTEGER,
    holders_change_pct_24h DECIMAL(10, 4),
    holders_by_swap INTEGER,
    holders_by_transfer INTEGER,
    holders_by_airdrop INTEGER,
    top_10_supply_pct DECIMAL(10, 4),
    top_25_supply_pct DECIMAL(10, 4),
    top_50_supply_pct DECIMAL(10, 4),
    top_100_supply_pct DECIMAL(10, 4),
    top_250_supply_pct DECIMAL(10, 4),
    top_500_supply_pct DECIMAL(10, 4),
    gini_coefficient DECIMAL(10, 6),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical Holder Data (time series)
CREATE TABLE IF NOT EXISTS moralis_historical_holders (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(42),
    holder_count INTEGER,
    unique_wallets INTEGER,
    data_timestamp TIMESTAMP,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Complete Snipers Data
CREATE TABLE IF NOT EXISTS moralis_snipers_complete (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42),
    pair_address VARCHAR(42),
    tokens_bought DECIMAL(40, 18),
    tokens_sold DECIMAL(40, 18),
    buy_tx_hash VARCHAR(66),
    sell_tx_hash VARCHAR(66),
    buy_timestamp TIMESTAMP,
    sell_timestamp TIMESTAMP,
    buy_block INTEGER,
    sell_block INTEGER,
    blocks_held INTEGER,
    time_held_seconds INTEGER,
    realized_profit DECIMAL(30, 2),
    realized_profit_pct DECIMAL(20, 4),
    current_balance DECIMAL(40, 18),
    is_sniper BOOLEAN DEFAULT TRUE,
    sniper_score DECIMAL(5, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Liquidity Changes tracking
CREATE TABLE IF NOT EXISTS moralis_liquidity_changes (
    id SERIAL PRIMARY KEY,
    pair_address VARCHAR(42),
    event_type VARCHAR(20), -- add/remove
    transaction_hash VARCHAR(66),
    block_timestamp TIMESTAMP,
    wallet_address VARCHAR(42),
    token0_amount DECIMAL(40, 18),
    token1_amount DECIMAL(40, 18),
    liquidity_change_usd DECIMAL(30, 2),
    total_liquidity_after DECIMAL(30, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Holder Distribution Analysis
CREATE TABLE IF NOT EXISTS moralis_holder_distribution (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(42),
    holder_address VARCHAR(42),
    balance DECIMAL(40, 18),
    balance_usd DECIMAL(30, 2),
    percentage_of_supply DECIMAL(10, 6),
    first_transaction TIMESTAMP,
    last_transaction TIMESTAMP,
    transaction_count INTEGER,
    is_whale BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    holder_type VARCHAR(50), -- whale/dolphin/fish/shrimp
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_address, holder_address)
);

-- Enhanced wash trading with more metrics
CREATE TABLE IF NOT EXISTS wash_trading_complete (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42),
    pair_address VARCHAR(42),
    detection_type VARCHAR(50),
    buy_count INTEGER,
    sell_count INTEGER,
    round_trips INTEGER,
    avg_hold_time_seconds INTEGER,
    total_volume DECIMAL(30, 2),
    net_pnl DECIMAL(30, 2),
    time_window_minutes INTEGER,
    confidence_score DECIMAL(5, 2),
    related_wallets TEXT[],
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token Metrics Summary
CREATE TABLE IF NOT EXISTS moralis_metrics_summary (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(42),
    metric_type VARCHAR(50),
    metric_value DECIMAL(30, 10),
    metric_json JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance

-- Schema.sql indexes
CREATE INDEX IF NOT EXISTS idx_swap_tx_timestamp ON swap_transactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_swap_tx_pair ON swap_transactions(pair_id);
CREATE INDEX IF NOT EXISTS idx_swap_tx_block ON swap_transactions(block_number DESC);
CREATE INDEX IF NOT EXISTS idx_token_transfers_token ON token_transfers(token_id);
CREATE INDEX IF NOT EXISTS idx_token_transfers_from ON token_transfers(from_address);
CREATE INDEX IF NOT EXISTS idx_token_transfers_to ON token_transfers(to_address);
CREATE INDEX IF NOT EXISTS idx_token_transfers_timestamp ON token_transfers(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_wallet_balances_wallet ON wallet_balances(wallet_id);
CREATE INDEX IF NOT EXISTS idx_wallet_balances_token ON wallet_balances(token_id);
CREATE INDEX IF NOT EXISTS idx_price_snapshots_pair ON price_snapshots(pair_id);
CREATE INDEX IF NOT EXISTS idx_price_snapshots_timestamp ON price_snapshots(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trading_metrics_token ON trading_metrics(token_id);
CREATE INDEX IF NOT EXISTS idx_trading_metrics_period ON trading_metrics(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_dex_pairs_tokens ON dex_pairs(token0_address, token1_address);
CREATE INDEX IF NOT EXISTS idx_liquidity_events_pair ON liquidity_events(pair_id);
CREATE INDEX IF NOT EXISTS idx_arbitrage_timestamp ON arbitrage_opportunities(timestamp DESC);

-- Init.sql indexes
CREATE INDEX IF NOT EXISTS idx_dex_trades_timestamp ON dex_trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dex_trades_chain ON dex_trades(chain_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dex_trades_dex ON dex_trades(dex_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dex_trades_pair ON dex_trades(pair);
CREATE INDEX IF NOT EXISTS idx_dex_trades_trader ON dex_trades(trader_address);

CREATE INDEX IF NOT EXISTS idx_token_prices_timestamp ON token_prices(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_token_prices_symbol ON token_prices(token_symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_liquidity_pools_timestamp ON liquidity_pools(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_liquidity_pools_dex ON liquidity_pools(dex_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_wallet_activity_timestamp ON wallet_activity(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_wallet_activity_volume ON wallet_activity(volume_24h DESC);

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
CREATE UNIQUE INDEX IF NOT EXISTS idx_hourly_dex_stats ON hourly_dex_stats (hour, chain_name, dex_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_top_pairs_24h ON top_pairs_24h (pair, chain_name, dex_name);

-- Enhanced tables indexes
CREATE INDEX IF NOT EXISTS idx_swaps_enhanced_wallet ON moralis_swaps_enhanced(wallet_address);
CREATE INDEX IF NOT EXISTS idx_swaps_enhanced_timestamp ON moralis_swaps_enhanced(block_timestamp);
CREATE INDEX IF NOT EXISTS idx_swaps_enhanced_type ON moralis_swaps_enhanced(transaction_type);
CREATE INDEX IF NOT EXISTS idx_holder_stats_token ON moralis_token_holder_stats(token_address);
CREATE INDEX IF NOT EXISTS idx_historical_holders_token ON moralis_historical_holders_enhanced(token_address, timestamp);
CREATE INDEX IF NOT EXISTS idx_pair_stats_pair ON moralis_pair_stats_enhanced(pair_address);
CREATE INDEX IF NOT EXISTS idx_token_analytics_token ON moralis_token_analytics_enhanced(token_address);
CREATE INDEX IF NOT EXISTS idx_snipers_pair ON moralis_snipers_enhanced(pair_address);
CREATE INDEX IF NOT EXISTS idx_snipers_wallet ON moralis_snipers_enhanced(wallet_address);
CREATE INDEX IF NOT EXISTS idx_top_gainers_token ON moralis_top_gainers(token_address);
CREATE INDEX IF NOT EXISTS idx_top_gainers_profit ON moralis_top_gainers(realized_profit_usd DESC);

-- Correct tables indexes
CREATE INDEX IF NOT EXISTS idx_swaps_timestamp ON moralis_swaps_correct(timestamp);
CREATE INDEX IF NOT EXISTS idx_swaps_wallet ON moralis_swaps_correct(wallet_address);
CREATE INDEX IF NOT EXISTS idx_swaps_type ON moralis_swaps_correct(transaction_type);

CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON moralis_token_analytics_correct(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_token ON moralis_token_analytics_correct(token_address);

CREATE INDEX IF NOT EXISTS idx_pair_stats_timestamp ON moralis_pair_stats_correct(timestamp);
CREATE INDEX IF NOT EXISTS idx_pair_stats_pair ON moralis_pair_stats_correct(pair_address);

CREATE INDEX IF NOT EXISTS idx_holder_stats_timestamp ON moralis_holder_stats_correct(timestamp);
CREATE INDEX IF NOT EXISTS idx_holder_stats_token ON moralis_holder_stats_correct(token_address);

CREATE INDEX IF NOT EXISTS idx_historical_holders_timestamp ON moralis_historical_holders_correct(timestamp);
CREATE INDEX IF NOT EXISTS idx_historical_holders_token ON moralis_historical_holders_correct(token_address);

CREATE INDEX IF NOT EXISTS idx_snipers_timestamp ON moralis_snipers_correct(timestamp);
CREATE INDEX IF NOT EXISTS idx_snipers_pair ON moralis_snipers_correct(pair_address);
CREATE INDEX IF NOT EXISTS idx_snipers_wallet ON moralis_snipers_correct(wallet_address);

-- Complete monitor tables indexes
CREATE INDEX IF NOT EXISTS idx_token_stats_timestamp ON moralis_token_stats(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_holder_stats_complete_timestamp ON moralis_holder_stats_complete(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_historical_holders_data ON moralis_historical_holders(data_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_moralis_transfers_block ON moralis_token_transfers(block_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_moralis_transfers_addresses ON moralis_token_transfers(from_address, to_address);
CREATE INDEX IF NOT EXISTS idx_moralis_snipers_wallet ON moralis_snipers_complete(wallet_address);
CREATE INDEX IF NOT EXISTS idx_moralis_snipers_profit ON moralis_snipers_complete(realized_profit_pct DESC);
CREATE INDEX IF NOT EXISTS idx_liquidity_changes_time ON moralis_liquidity_changes(block_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_holder_distribution_balance ON moralis_holder_distribution(balance_usd DESC);
CREATE INDEX IF NOT EXISTS idx_wash_trading_confidence ON wash_trading_complete(confidence_score DESC);

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