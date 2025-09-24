-- Sample data for DEX Analytics

-- Insert chain stats
INSERT INTO chain_stats (chain_name, chain_id, total_volume_24h, total_transactions, active_wallets, timestamp)
SELECT
    chain,
    chain_id,
    RANDOM() * 10000000 + 1000000,
    FLOOR(RANDOM() * 50000 + 10000)::INTEGER,
    FLOOR(RANDOM() * 5000 + 1000)::INTEGER,
    NOW() - (interval '1 hour' * generate_series)
FROM (
    VALUES
    ('Ethereum', 1),
    ('BSC', 56),
    ('Polygon', 137),
    ('Arbitrum', 42161),
    ('Optimism', 10),
    ('Base', 8453)
) AS chains(chain, chain_id)
CROSS JOIN generate_series(0, 23);

-- Insert token prices with realistic values
INSERT INTO token_prices (chain_id, token_symbol, token_address, price_usd, volume_24h, price_change_24h, market_cap, timestamp)
SELECT
    1,
    token,
    '0x' || substr(md5(token || generate_series::text), 1, 40),
    base_price * (1 + (RANDOM() - 0.5) * 0.1),
    RANDOM() * 1000000 + 100000,
    (RANDOM() - 0.5) * 20,
    base_price * market_cap_mult,
    NOW() - (interval '1 hour' * generate_series)
FROM (
    VALUES
    ('ETH', 3800.0::DECIMAL, 300000000000::DECIMAL),
    ('USDT', 1.0::DECIMAL, 95000000000::DECIMAL),
    ('USDC', 1.0::DECIMAL, 42000000000::DECIMAL),
    ('BNB', 650.0::DECIMAL, 100000000000::DECIMAL),
    ('MATIC', 1.5::DECIMAL, 13000000000::DECIMAL),
    ('UNI', 15.0::DECIMAL, 11000000000::DECIMAL),
    ('LINK', 20.0::DECIMAL, 12000000000::DECIMAL),
    ('AAVE', 150.0::DECIMAL, 2000000000::DECIMAL),
    ('SUSHI', 2.5::DECIMAL, 500000000::DECIMAL),
    ('CRV', 1.2::DECIMAL, 1500000000::DECIMAL)
) AS tokens(token, base_price, market_cap_mult)
CROSS JOIN generate_series(0, 47);

-- Insert DEX trades with realistic patterns
INSERT INTO dex_trades (chain_id, chain_name, dex_name, pair, token_in, token_out, amount_in, amount_out, price, value_usd, trader_address, tx_hash, gas_used, timestamp)
SELECT
    chain_id,
    chain_name,
    dex_name,
    pair,
    CASE WHEN RANDOM() > 0.5 THEN split_part(pair, '/', 1) ELSE split_part(pair, '/', 2) END,
    CASE WHEN RANDOM() > 0.5 THEN split_part(pair, '/', 2) ELSE split_part(pair, '/', 1) END,
    RANDOM() * 10 + 0.1,
    RANDOM() * 10000 + 100,
    3800 * (1 + (RANDOM() - 0.5) * 0.02),
    RANDOM() * 50000 + 100,
    '0x' || substr(md5(random()::text), 1, 40),
    '0x' || substr(md5(random()::text || generate_series), 1, 64),
    FLOOR(RANDOM() * 200000 + 50000)::INTEGER,
    NOW() - (interval '1 minute' * generate_series)
FROM (
    SELECT
        c.chain_id,
        c.chain_name,
        d.dex_name,
        p.pair
    FROM (VALUES (1, 'Ethereum'), (56, 'BSC'), (137, 'Polygon'), (42161, 'Arbitrum')) AS c(chain_id, chain_name)
    CROSS JOIN (VALUES ('Uniswap V3'), ('Uniswap V2'), ('SushiSwap'), ('PancakeSwap'), ('QuickSwap')) AS d(dex_name)
    CROSS JOIN (VALUES ('ETH/USDT'), ('ETH/USDC'), ('BNB/USDT'), ('MATIC/USDT'), ('UNI/ETH'), ('LINK/ETH'), ('AAVE/ETH'), ('SUSHI/ETH')) AS p(pair)
) AS combinations
CROSS JOIN generate_series(0, 500)
WHERE RANDOM() > 0.7;  -- Random sampling for realistic distribution

-- Insert liquidity pools
INSERT INTO liquidity_pools (chain_id, chain_name, dex_name, pool_address, token0_symbol, token1_symbol, token0_reserve, token1_reserve, total_liquidity_usd, volume_24h, fees_24h, apy, timestamp)
SELECT
    chain_id,
    chain_name,
    dex_name,
    '0x' || substr(md5(dex_name || pair || chain_name), 1, 40),
    split_part(pair, '/', 1),
    split_part(pair, '/', 2),
    RANDOM() * 1000000 + 100000,
    RANDOM() * 1000000 + 100000,
    RANDOM() * 10000000 + 1000000,
    RANDOM() * 5000000 + 100000,
    RANDOM() * 10000 + 100,
    RANDOM() * 50 + 5,
    NOW() - (interval '1 hour' * generate_series(0, 23))
FROM (
    SELECT DISTINCT
        c.chain_id,
        c.chain_name,
        d.dex_name,
        p.pair
    FROM (VALUES (1, 'Ethereum'), (56, 'BSC'), (137, 'Polygon')) AS c(chain_id, chain_name)
    CROSS JOIN (VALUES ('Uniswap V3'), ('Uniswap V2'), ('SushiSwap'), ('PancakeSwap')) AS d(dex_name)
    CROSS JOIN (VALUES ('ETH/USDT'), ('ETH/USDC'), ('BNB/USDT'), ('MATIC/USDT'), ('UNI/ETH')) AS p(pair)
) AS pools;

-- Insert wallet activity (whales and regular traders)
INSERT INTO wallet_activity (chain_id, wallet_address, wallet_label, total_trades, volume_24h, profit_loss, win_rate, tokens_traded, last_trade_time)
SELECT
    1,
    '0x' || substr(md5('wallet' || n::text), 1, 40),
    CASE
        WHEN n <= 5 THEN 'Whale #' || n
        WHEN n <= 10 THEN 'Smart Money #' || n
        WHEN n <= 20 THEN 'Active Trader #' || n
        ELSE NULL
    END,
    FLOOR(RANDOM() * 500 + CASE WHEN n <= 5 THEN 1000 ELSE 50 END)::INTEGER,
    RANDOM() * CASE WHEN n <= 5 THEN 10000000 ELSE 100000 END + 10000,
    (RANDOM() - 0.3) * CASE WHEN n <= 10 THEN 100000 ELSE 10000 END,
    CASE WHEN n <= 10 THEN 60 + RANDOM() * 30 ELSE 30 + RANDOM() * 40 END,
    FLOOR(RANDOM() * 50 + 5)::INTEGER,
    NOW() - (interval '1 minute' * FLOOR(RANDOM() * 60))
FROM generate_series(1, 100) AS n;

-- Refresh materialized views
REFRESH MATERIALIZED VIEW hourly_dex_stats;
REFRESH MATERIALIZED VIEW top_pairs_24h;