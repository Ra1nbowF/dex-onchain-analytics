-- Enhanced Moralis Tables for Missing API Endpoints
-- Run this script in the dex_analytics database

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

-- Create indexes for better query performance
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