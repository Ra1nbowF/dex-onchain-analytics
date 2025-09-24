-- Create tables for correct Moralis API endpoints

-- 1. SWAPS TABLE (from /erc20/{address}/swaps)
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

-- 2. TOKEN ANALYTICS TABLE (from /tokens/{address}/analytics)
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

-- 3. PAIR STATS TABLE (from /pairs/{address}/stats)
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

-- 4. HOLDER STATS TABLE (from /erc20/{address}/holders)
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

-- 5. HISTORICAL HOLDERS TABLE (from /erc20/{address}/holders/historical)
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

-- 6. SNIPERS TABLE (from /pairs/{address}/snipers)
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

-- Create indexes for better performance
CREATE INDEX idx_swaps_timestamp ON moralis_swaps_correct(timestamp);
CREATE INDEX idx_swaps_wallet ON moralis_swaps_correct(wallet_address);
CREATE INDEX idx_swaps_type ON moralis_swaps_correct(transaction_type);

CREATE INDEX idx_analytics_timestamp ON moralis_token_analytics_correct(timestamp);
CREATE INDEX idx_analytics_token ON moralis_token_analytics_correct(token_address);

CREATE INDEX idx_pair_stats_timestamp ON moralis_pair_stats_correct(timestamp);
CREATE INDEX idx_pair_stats_pair ON moralis_pair_stats_correct(pair_address);

CREATE INDEX idx_holder_stats_timestamp ON moralis_holder_stats_correct(timestamp);
CREATE INDEX idx_holder_stats_token ON moralis_holder_stats_correct(token_address);

CREATE INDEX idx_historical_holders_timestamp ON moralis_historical_holders_correct(timestamp);
CREATE INDEX idx_historical_holders_token ON moralis_historical_holders_correct(token_address);

CREATE INDEX idx_snipers_timestamp ON moralis_snipers_correct(timestamp);
CREATE INDEX idx_snipers_pair ON moralis_snipers_correct(pair_address);
CREATE INDEX idx_snipers_wallet ON moralis_snipers_correct(wallet_address);