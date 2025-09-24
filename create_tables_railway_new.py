"""
Script to create all tables in Railway PostgreSQL database
This script will drop all existing tables and recreate them with the exact same structure as the running database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database connection parameters - UPDATE WITH YOUR RAILWAY DATABASE CREDENTIALS
DATABASE_URL = os.environ.get("RAILWAY_DATABASE_URL", "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway").strip()

def drop_all_tables_and_objects():
    """
    Drop all existing tables, views, and sequences in Railway database
    """
    # SQL to drop all tables, views, and sequences in the correct order (with CASCADE)
    drop_script = """
    -- Drop all materialized views first
    DROP MATERIALIZED VIEW IF EXISTS hourly_dex_stats CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS top_pairs_24h CASCADE;

    -- Drop all tables in reverse dependency order (child tables before parent tables)
    -- BSC Monitoring Tables
    DROP TABLE IF EXISTS bsc_liquidity_events CASCADE;
    DROP TABLE IF EXISTS bsc_wallet_metrics CASCADE;
    DROP TABLE IF EXISTS bsc_trades CASCADE;
    DROP TABLE IF EXISTS bsc_pool_metrics CASCADE;
    
    -- Moralis Complete Monitor Tables
    DROP TABLE IF EXISTS wash_trading_complete CASCADE;
    DROP TABLE IF EXISTS moralis_metrics_summary CASCADE;
    DROP TABLE IF EXISTS moralis_holder_distribution CASCADE;
    DROP TABLE IF EXISTS moralis_snipers_complete CASCADE;
    DROP TABLE IF EXISTS moralis_historical_holders CASCADE;
    DROP TABLE IF EXISTS moralis_holder_stats_complete CASCADE;
    DROP TABLE IF EXISTS moralis_token_stats CASCADE;
    DROP TABLE IF EXISTS moralis_token_transfers CASCADE;
    
    -- Moralis Correct Tables
    DROP TABLE IF EXISTS moralis_snipers_correct CASCADE;
    DROP TABLE IF EXISTS moralis_historical_holders_correct CASCADE;
    DROP TABLE IF EXISTS moralis_holder_stats_correct CASCADE;
    DROP TABLE IF EXISTS moralis_pair_stats_correct CASCADE;
    DROP TABLE IF EXISTS moralis_token_analytics_correct CASCADE;
    DROP TABLE IF EXISTS moralis_swaps_correct CASCADE;
    
    -- Moralis Enhanced Tables
    DROP TABLE IF EXISTS moralis_snipers_enhanced CASCADE;
    DROP TABLE IF EXISTS moralis_pair_stats_enhanced CASCADE;
    DROP TABLE IF EXISTS moralis_token_analytics_enhanced CASCADE;
    DROP TABLE IF EXISTS moralis_historical_holders_enhanced CASCADE;
    DROP TABLE IF EXISTS moralis_token_holder_stats CASCADE;
    DROP TABLE IF EXISTS moralis_swaps_enhanced CASCADE;
    
    -- Moralis Basic Tables
    DROP TABLE IF EXISTS moralis_top_gainers CASCADE;
    DROP TABLE IF EXISTS moralis_token_stats_simple CASCADE;
    DROP TABLE IF EXISTS moralis_liquidity_changes CASCADE;
    DROP TABLE IF EXISTS moralis_transfers CASCADE;
    DROP TABLE IF EXISTS moralis_holders CASCADE;
    DROP TABLE IF EXISTS moralis_stats CASCADE;
    DROP TABLE IF EXISTS moralis_token_analytics CASCADE;
    DROP TABLE IF EXISTS moralis_pair_stats CASCADE;
    DROP TABLE IF EXISTS moralis_swaps CASCADE;
    
    -- Alert and Manipulation Tables
    DROP TABLE IF EXISTS manipulation_alerts CASCADE;
    DROP TABLE IF EXISTS market_manipulation_alerts CASCADE;
    DROP TABLE IF EXISTS wash_trade_suspects CASCADE;
    DROP TABLE IF EXISTS wash_trading_alerts CASCADE;
    DROP TABLE IF EXISTS wallet_pnl CASCADE;
    
    -- Standard DEX Analytics Tables
    DROP TABLE IF EXISTS token_distribution CASCADE;
    DROP TABLE IF EXISTS wallet_activity CASCADE;
    DROP TABLE IF EXISTS dex_trades CASCADE;
    DROP TABLE IF EXISTS token_prices CASCADE;
    DROP TABLE IF EXISTS liquidity_pools CASCADE;
    DROP TABLE IF EXISTS chain_stats CASCADE;

    -- Schema.sql related tables (with foreign key dependencies)
    DROP TABLE IF EXISTS smart_money_wallets CASCADE;
    DROP TABLE IF EXISTS wallet_balances CASCADE;
    DROP TABLE IF EXISTS liquidity_events CASCADE;
    DROP TABLE IF EXISTS price_snapshots CASCADE;
    DROP TABLE IF EXISTS arbitrage_opportunities CASCADE;
    DROP TABLE IF EXISTS trading_metrics CASCADE;
    DROP TABLE IF EXISTS swap_transactions CASCADE;
    DROP TABLE IF EXISTS token_transfers CASCADE;
    DROP TABLE IF EXISTS dex_pairs CASCADE;
    DROP TABLE IF EXISTS tokens CASCADE;
    DROP TABLE IF EXISTS dex_protocols CASCADE;
    DROP TABLE IF EXISTS wallets CASCADE;
    DROP TABLE IF EXISTS chains CASCADE;

    -- Remove triggers if they exist
    DROP TRIGGER IF EXISTS update_tokens_modtime ON tokens CASCADE;
    DROP TRIGGER IF EXISTS update_dex_pairs_modtime ON dex_pairs CASCADE;
    DROP TRIGGER IF EXISTS update_wallets_modtime ON wallets CASCADE;
    
    -- Remove functions if they exist
    DROP FUNCTION IF EXISTS update_modified_column() CASCADE;
    DROP FUNCTION IF EXISTS refresh_materialized_views() CASCADE;
    
    -- Drop any remaining sequences that might not be tied to tables
    DO $$ 
    DECLARE
        seq_name text;
    BEGIN
        FOR seq_name IN 
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        LOOP
            EXECUTE 'DROP SEQUENCE IF EXISTS ' || seq_name || ' CASCADE;';
        END LOOP;
    END $$;
    """
    
    # Connect to the database
    conn = None
    cur = None
    try:
        print("Connecting to Railway database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Dropping all existing tables, views and objects...")
        # Execute the drop script
        cur.execute(drop_script)
        
        # Commit the changes
        conn.commit()
        
        print("All tables, views, and objects dropped successfully!")
        
    except psycopg2.Error as e:
        print(f"Database error during drop: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Error during drop: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Database connection closed after dropping objects.")

def create_all_tables():
    """
    Execute the complete table creation script with all tables from the current running database
    """
    # SQL script to recreate all tables with exact structure from running database
    create_script = """
    -- BSC Monitoring Tables with exact structure from running database
    
    CREATE TABLE bsc_pool_metrics (
        id SERIAL PRIMARY KEY,
        pool_address VARCHAR(42),
        token0_reserve NUMERIC,
        token1_reserve NUMERIC,
        total_liquidity_usd NUMERIC,
        tvl NUMERIC,
        price_btcb_usdt NUMERIC,
        pool_ratio NUMERIC,
        lp_token_supply NUMERIC,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE bsc_trades (
        id SERIAL PRIMARY KEY,
        tx_hash VARCHAR(66),
        block_number BIGINT,
        trader_address VARCHAR(42),
        token_in VARCHAR(20),
        token_out VARCHAR(20),
        amount_in NUMERIC,
        amount_out NUMERIC,
        price NUMERIC,
        value_usd NUMERIC,
        gas_used BIGINT,
        slippage NUMERIC,
        is_buy BOOLEAN,
        timestamp TIMESTAMP
    );

    CREATE TABLE bsc_wallet_metrics (
        id SERIAL PRIMARY KEY,
        wallet_address VARCHAR(42),
        btcb_balance NUMERIC,
        usdt_balance NUMERIC,
        lp_token_balance NUMERIC,
        total_trades INTEGER DEFAULT 0,
        total_volume_usd NUMERIC DEFAULT 0,
        realized_pnl NUMERIC DEFAULT 0,
        unrealized_pnl NUMERIC,
        win_rate NUMERIC,
        avg_trade_size NUMERIC,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        is_mm_suspect BOOLEAN DEFAULT FALSE,
        is_insider_suspect BOOLEAN DEFAULT FALSE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE bsc_liquidity_events (
        id SERIAL PRIMARY KEY,
        tx_hash VARCHAR(66),
        event_type VARCHAR(20),
        provider_address VARCHAR(42),
        btcb_amount NUMERIC,
        usdt_amount NUMERIC,
        lp_tokens NUMERIC,
        share_of_pool NUMERIC,
        timestamp TIMESTAMP
    );

    -- Moralis Data Tables with exact structure from running database
    
    CREATE TABLE moralis_swaps (
        id SERIAL PRIMARY KEY,
        transaction_hash VARCHAR(66),
        block_number BIGINT,
        block_timestamp TIMESTAMP,
        transaction_type VARCHAR(20),
        wallet_address VARCHAR(42),
        bought_token VARCHAR(20),
        bought_amount NUMERIC,
        bought_usd NUMERIC,
        sold_token VARCHAR(20),
        sold_amount NUMERIC,
        sold_usd NUMERIC,
        total_usd NUMERIC,
        exchange_name VARCHAR(50),
        pair_address VARCHAR(42),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_swaps_correct (
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
        bought_amount NUMERIC,
        bought_usd_price NUMERIC,
        bought_usd_amount NUMERIC,
        sold_address TEXT,
        sold_name TEXT,
        sold_symbol TEXT,
        sold_logo TEXT,
        sold_amount NUMERIC,
        sold_usd_price NUMERIC,
        sold_usd_amount NUMERIC,
        base_quote_price TEXT,
        total_value_usd NUMERIC,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_swaps_enhanced (
        id SERIAL PRIMARY KEY,
        transaction_hash TEXT,
        transaction_index INTEGER,
        transaction_type TEXT,
        sub_category TEXT,
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
        bought_amount NUMERIC,
        bought_usd_price NUMERIC,
        bought_usd_amount NUMERIC,
        sold_address TEXT,
        sold_name TEXT,
        sold_symbol TEXT,
        sold_logo TEXT,
        sold_amount NUMERIC,
        sold_usd_price NUMERIC,
        sold_usd_amount NUMERIC,
        base_quote_price NUMERIC,
        total_value_usd NUMERIC,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_token_analytics (
        id SERIAL PRIMARY KEY,
        token_address VARCHAR(42),
        buy_volume_5m NUMERIC,
        sell_volume_5m NUMERIC,
        buy_volume_1h NUMERIC,
        sell_volume_1h NUMERIC,
        buy_volume_24h NUMERIC,
        sell_volume_24h NUMERIC,
        buyers_5m INTEGER,
        sellers_5m INTEGER,
        buyers_24h INTEGER,
        sellers_24h INTEGER,
        buys_24h INTEGER,
        sells_24h INTEGER,
        liquidity_usd NUMERIC,
        fdv NUMERIC,
        usd_price NUMERIC,
        price_change_24h NUMERIC,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_token_analytics_correct (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        category_id TEXT,
        total_buy_volume_5m NUMERIC,
        total_buy_volume_1h NUMERIC,
        total_buy_volume_6h NUMERIC,
        total_buy_volume_24h NUMERIC,
        total_sell_volume_5m NUMERIC,
        total_sell_volume_1h NUMERIC,
        total_sell_volume_6h NUMERIC,
        total_sell_volume_24h NUMERIC,
        total_buyers_5m INTEGER,
        total_buyers_1h INTEGER,
        total_buyers_6h INTEGER,
        total_buyers_24h INTEGER,
        total_sellers_5m INTEGER,
        total_sellers_1h INTEGER,
        total_sellers_6h INTEGER,
        total_sellers_24h INTEGER,
        total_buys_5m INTEGER,
        total_buys_1h INTEGER,
        total_buys_6h INTEGER,
        total_buys_24h INTEGER,
        total_sells_5m INTEGER,
        total_sells_1h INTEGER,
        total_sells_6h INTEGER,
        total_sells_24h INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(token_address, timestamp)
    );

    CREATE TABLE moralis_token_analytics_enhanced (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        category_id TEXT,
        buy_volume_5m NUMERIC,
        buy_volume_1h NUMERIC,
        buy_volume_6h NUMERIC,
        buy_volume_24h NUMERIC,
        sell_volume_5m NUMERIC,
        sell_volume_1h NUMERIC,
        sell_volume_6h NUMERIC,
        sell_volume_24h NUMERIC,
        buyers_5m INTEGER,
        buyers_1h INTEGER,
        buyers_6h INTEGER,
        buyers_24h INTEGER,
        sellers_5m INTEGER,
        sellers_1h INTEGER,
        sellers_6h INTEGER,
        sellers_24h INTEGER,
        buys_5m INTEGER,
        buys_1h INTEGER,
        buys_6h INTEGER,
        buys_24h INTEGER,
        sells_5m INTEGER,
        sells_1h INTEGER,
        sells_6h INTEGER,
        sells_24h INTEGER,
        liquidity_5m NUMERIC,
        liquidity_1h NUMERIC,
        liquidity_6h NUMERIC,
        liquidity_24h NUMERIC,
        fdv_5m NUMERIC,
        fdv_1h NUMERIC,
        fdv_6h NUMERIC,
        fdv_24h NUMERIC,
        price_change_5m NUMERIC,
        price_change_1h NUMERIC,
        price_change_6h NUMERIC,
        price_change_24h NUMERIC,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(token_address, timestamp)
    );

    CREATE TABLE moralis_pair_stats (
        id SERIAL PRIMARY KEY,
        pair_address VARCHAR(42),
        token_address VARCHAR(42),
        exchange_address VARCHAR(42),
        usd_price NUMERIC,
        liquidity_usd NUMERIC,
        price_change_5m NUMERIC,
        price_change_1h NUMERIC,
        price_change_24h NUMERIC,
        liquidity_change_24h NUMERIC,
        volume_24h NUMERIC,
        buys_5m INTEGER,
        sells_5m INTEGER,
        buys_1h INTEGER,
        sells_1h INTEGER,
        buys_24h INTEGER,
        sells_24h INTEGER,
        buyers_1h INTEGER,
        sellers_1h INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_pair_stats_correct (
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
        current_usd_price NUMERIC,
        current_native_price NUMERIC,
        total_liquidity_usd NUMERIC,
        price_change_5min NUMERIC,
        price_change_1h NUMERIC,
        price_change_4h NUMERIC,
        price_change_24h NUMERIC,
        liquidity_change_5min NUMERIC,
        liquidity_change_1h NUMERIC,
        liquidity_change_4h NUMERIC,
        liquidity_change_24h NUMERIC,
        buys_5min INTEGER,
        buys_1h INTEGER,
        buys_4h INTEGER,
        buys_24h INTEGER,
        sells_5min INTEGER,
        sells_1h INTEGER,
        sells_4h INTEGER,
        sells_24h INTEGER,
        total_volume_5min NUMERIC,
        total_volume_1h NUMERIC,
        total_volume_4h NUMERIC,
        total_volume_24h NUMERIC,
        buy_volume_5min NUMERIC,
        buy_volume_1h NUMERIC,
        buy_volume_4h NUMERIC,
        buy_volume_24h NUMERIC,
        sell_volume_5min NUMERIC,
        sell_volume_1h NUMERIC,
        sell_volume_4h NUMERIC,
        sell_volume_24h NUMERIC,
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

    CREATE TABLE moralis_pair_stats_enhanced (
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
        current_usd_price NUMERIC,
        current_native_price NUMERIC,
        total_liquidity_usd NUMERIC,
        price_change_5min NUMERIC,
        price_change_1h NUMERIC,
        price_change_4h NUMERIC,
        price_change_24h NUMERIC,
        liquidity_change_5min NUMERIC,
        liquidity_change_1h NUMERIC,
        liquidity_change_4h NUMERIC,
        liquidity_change_24h NUMERIC,
        buys_5min INTEGER,
        buys_1h INTEGER,
        buys_4h INTEGER,
        buys_24h INTEGER,
        sells_5min INTEGER,
        sells_1h INTEGER,
        sells_4h INTEGER,
        sells_24h INTEGER,
        volume_5min NUMERIC,
        volume_1h NUMERIC,
        volume_4h NUMERIC,
        volume_24h NUMERIC,
        buy_volume_5min NUMERIC,
        buy_volume_1h NUMERIC,
        buy_volume_4h NUMERIC,
        buy_volume_24h NUMERIC,
        sell_volume_5min NUMERIC,
        sell_volume_1h NUMERIC,
        sell_volume_4h NUMERIC,
        sell_volume_24h NUMERIC,
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

    CREATE TABLE moralis_holder_stats_correct (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        total_holders INTEGER,
        top10_supply NUMERIC,
        top10_supply_percent NUMERIC,
        top25_supply NUMERIC,
        top25_supply_percent NUMERIC,
        top50_supply NUMERIC,
        top50_supply_percent NUMERIC,
        top100_supply NUMERIC,
        top100_supply_percent NUMERIC,
        top250_supply NUMERIC,
        top250_supply_percent NUMERIC,
        top500_supply NUMERIC,
        top500_supply_percent NUMERIC,
        holder_change_5min INTEGER,
        holder_change_percent_5min NUMERIC,
        holder_change_1h INTEGER,
        holder_change_percent_1h NUMERIC,
        holder_change_6h INTEGER,
        holder_change_percent_6h NUMERIC,
        holder_change_24h INTEGER,
        holder_change_percent_24h NUMERIC,
        holder_change_3d INTEGER,
        holder_change_percent_3d NUMERIC,
        holder_change_7d INTEGER,
        holder_change_percent_7d NUMERIC,
        holder_change_30d INTEGER,
        holder_change_percent_30d NUMERIC,
        holders_by_swap INTEGER,
        holders_by_transfer INTEGER,
        holders_by_airdrop INTEGER,
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

    CREATE TABLE moralis_historical_holders_correct (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        timestamp TIMESTAMP,
        total_holders INTEGER,
        net_holder_change INTEGER,
        holder_percent_change NUMERIC,
        new_holders_by_swap INTEGER,
        new_holders_by_transfer INTEGER,
        new_holders_by_airdrop INTEGER,
        holders_in_whales INTEGER,
        holders_in_sharks INTEGER,
        holders_in_dolphins INTEGER,
        holders_in_fish INTEGER,
        holders_in_octopus INTEGER,
        holders_in_crabs INTEGER,
        holders_in_shrimps INTEGER,
        holders_out_whales INTEGER,
        holders_out_sharks INTEGER,
        holders_out_dolphins INTEGER,
        holders_out_fish INTEGER,
        holders_out_octopus INTEGER,
        holders_out_crabs INTEGER,
        holders_out_shrimps INTEGER,
        UNIQUE(token_address, timestamp)
    );

    CREATE TABLE moralis_historical_holders_enhanced (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        timestamp TIMESTAMP,
        total_holders INTEGER,
        net_holder_change INTEGER,
        holder_percent_change NUMERIC,
        new_holders_by_swap INTEGER,
        new_holders_by_transfer INTEGER,
        new_holders_by_airdrop INTEGER,
        holders_in_whales INTEGER,
        holders_in_sharks INTEGER,
        holders_in_dolphins INTEGER,
        holders_in_fish INTEGER,
        holders_in_octopus INTEGER,
        holders_in_crabs INTEGER,
        holders_in_shrimps INTEGER,
        holders_out_whales INTEGER,
        holders_out_sharks INTEGER,
        holders_out_dolphins INTEGER,
        holders_out_fish INTEGER,
        holders_out_octopus INTEGER,
        holders_out_crabs INTEGER,
        holders_out_shrimps INTEGER,
        UNIQUE(token_address, timestamp)
    );

    CREATE TABLE moralis_snipers_correct (
        id SERIAL PRIMARY KEY,
        pair_address TEXT,
        wallet_address TEXT,
        total_tokens_sniped NUMERIC,
        total_sniped_usd NUMERIC,
        total_sniped_transactions INTEGER,
        total_tokens_sold NUMERIC,
        total_sold_usd NUMERIC,
        total_sell_transactions INTEGER,
        current_balance NUMERIC,
        current_balance_usd_value NUMERIC,
        realized_profit_percentage NUMERIC,
        realized_profit_usd NUMERIC,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(pair_address, wallet_address, timestamp)
    );

    CREATE TABLE moralis_snipers_enhanced (
        id SERIAL PRIMARY KEY,
        pair_address TEXT,
        transaction_hash TEXT,
        block_timestamp TIMESTAMP,
        block_number BIGINT,
        wallet_address TEXT,
        total_tokens_sniped NUMERIC,
        total_sniped_usd NUMERIC,
        total_sniped_transactions INTEGER,
        total_tokens_sold NUMERIC,
        total_sold_usd NUMERIC,
        total_sell_transactions INTEGER,
        current_balance NUMERIC,
        current_balance_usd_value NUMERIC,
        realized_profit_percentage NUMERIC,
        realized_profit_usd NUMERIC,
        blocks_after_creation INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_snipers_complete (
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

    CREATE TABLE moralis_holders (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        holder_address TEXT,
        balance NUMERIC,
        balance_formatted NUMERIC,
        percentage_of_supply NUMERIC,
        holder_type TEXT,
        timestamp TIMESTAMP
    );

    CREATE TABLE moralis_stats (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_holders INTEGER,
        unique_wallets INTEGER,
        total_volume_24h NUMERIC,
        total_transactions_24h INTEGER,
        buy_volume_24h NUMERIC,
        sell_volume_24h NUMERIC,
        unique_buyers_24h INTEGER,
        unique_sellers_24h INTEGER,
        price_usd NUMERIC,
        market_cap NUMERIC,
        fully_diluted_valuation NUMERIC,
        total_supply NUMERIC,
        circulating_supply NUMERIC,
        gini_coefficient NUMERIC,
        top10_concentration NUMERIC,
        top100_concentration NUMERIC,
        whale_count INTEGER,
        dolphin_count INTEGER,
        fish_count INTEGER,
        shrimp_count INTEGER
    );

    CREATE TABLE moralis_token_stats (
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

    CREATE TABLE moralis_holder_stats_complete (
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

    CREATE TABLE moralis_historical_holders (
        id SERIAL PRIMARY KEY,
        token_address VARCHAR(42),
        holder_count INTEGER,
        unique_wallets INTEGER,
        data_timestamp TIMESTAMP,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_token_transfers (
        id SERIAL PRIMARY KEY,
        transaction_hash VARCHAR(66),
        block_number BIGINT,
        block_timestamp TIMESTAMP,
        from_address VARCHAR(42),
        to_address VARCHAR(42),
        value NUMERIC,
        value_usd NUMERIC,
        token_address VARCHAR(42),
        token_symbol VARCHAR(20),
        transaction_index INTEGER,
        log_index INTEGER,
        is_spam BOOLEAN DEFAULT FALSE,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_transfers (
        id SERIAL PRIMARY KEY,
        transaction_hash TEXT,
        block_number BIGINT,
        block_timestamp TIMESTAMP,
        from_address TEXT,
        to_address TEXT,
        value NUMERIC,
        value_decimal NUMERIC,
        token_address TEXT,
        token_name TEXT,
        token_symbol TEXT,
        token_decimals INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_token_holder_stats (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        total_holders INTEGER,
        holder_supply_top10 NUMERIC,
        holder_supply_top10_percent NUMERIC,
        holder_supply_top25 NUMERIC,
        holder_supply_top25_percent NUMERIC,
        holder_supply_top50 NUMERIC,
        holder_supply_top50_percent NUMERIC,
        holder_supply_top100 NUMERIC,
        holder_supply_top100_percent NUMERIC,
        holder_change_5min INTEGER,
        holder_change_5min_percent NUMERIC,
        holder_change_1h INTEGER,
        holder_change_1h_percent NUMERIC,
        holder_change_24h INTEGER,
        holder_change_24h_percent NUMERIC,
        holders_by_swap INTEGER,
        holders_by_transfer INTEGER,
        holders_by_airdrop INTEGER,
        whales_count INTEGER,
        sharks_count INTEGER,
        dolphins_count INTEGER,
        fish_count INTEGER,
        octopus_count INTEGER,
        crabs_count INTEGER,
        shrimps_count INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(token_address, timestamp)
    );

    CREATE TABLE moralis_token_stats_simple (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        total_transfers BIGINT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(token_address, timestamp)
    );

    CREATE TABLE moralis_top_gainers (
        id SERIAL PRIMARY KEY,
        token_address TEXT,
        wallet_address TEXT,
        avg_buy_price_usd NUMERIC,
        avg_cost_of_quantity_sold NUMERIC,
        avg_sell_price_usd NUMERIC,
        count_of_trades INTEGER,
        realized_profit_percentage NUMERIC,
        realized_profit_usd NUMERIC,
        total_sold_usd NUMERIC,
        total_tokens_bought NUMERIC,
        total_tokens_sold NUMERIC,
        total_usd_invested NUMERIC,
        timeframe TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(token_address, wallet_address, timeframe)
    );

    CREATE TABLE moralis_liquidity_changes (
        id SERIAL PRIMARY KEY,
        pair_address VARCHAR(42),
        event_type VARCHAR(20),
        transaction_hash VARCHAR(66),
        block_timestamp TIMESTAMP,
        wallet_address VARCHAR(42),
        token0_amount DECIMAL(40, 18),
        token1_amount DECIMAL(40, 18),
        liquidity_change_usd DECIMAL(30, 2),
        total_liquidity_after DECIMAL(30, 2),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE moralis_holder_distribution (
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
        holder_type VARCHAR(50),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(token_address, holder_address)
    );

    CREATE TABLE wash_trading_complete (
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

    CREATE TABLE moralis_metrics_summary (
        id SERIAL PRIMARY KEY,
        token_address VARCHAR(42),
        metric_type VARCHAR(50),
        metric_value DECIMAL(30, 10),
        metric_json JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Alert and Manipulation Tables
    CREATE TABLE manipulation_alerts (
        id SERIAL PRIMARY KEY,
        alert_type VARCHAR(50),
        severity VARCHAR(20),
        description TEXT,
        evidence JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE market_manipulation_alerts (
        id SERIAL PRIMARY KEY,
        alert_type VARCHAR(50),
        severity VARCHAR(20),
        pair_address VARCHAR(42),
        description TEXT,
        metrics JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE wash_trade_suspects (
        id SERIAL PRIMARY KEY,
        wallet_address VARCHAR(42),
        related_wallets VARCHAR(42)[],
        suspicious_tx_count INTEGER,
        circular_volume NUMERIC,
        detection_score NUMERIC,
        evidence JSONB,
        detected_at TIMESTAMP
    );

    CREATE TABLE wash_trading_alerts (
        id SERIAL PRIMARY KEY,
        wallet_address VARCHAR(42),
        pair_address VARCHAR(42),
        detection_type VARCHAR(50),
        buy_count INTEGER,
        sell_count INTEGER,
        total_volume NUMERIC,
        time_window_minutes INTEGER,
        confidence_score NUMERIC,
        details JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE wallet_pnl (
        id SERIAL PRIMARY KEY,
        wallet_address VARCHAR(42),
        token_address VARCHAR(42),
        total_bought NUMERIC,
        total_sold NUMERIC,
        avg_buy_price NUMERIC,
        avg_sell_price NUMERIC,
        realized_pnl NUMERIC,
        unrealized_pnl NUMERIC,
        trade_count INTEGER,
        first_trade TIMESTAMP,
        last_trade TIMESTAMP,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Standard DEX Analytics Tables
    CREATE TABLE chain_stats (
        id SERIAL PRIMARY KEY,
        chain_name VARCHAR(50) NOT NULL,
        chain_id INTEGER NOT NULL,
        total_volume_24h DECIMAL(30, 2),
        total_transactions INTEGER,
        active_wallets INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

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

    CREATE TABLE token_distribution (
        id SERIAL PRIMARY KEY,
        top_10_concentration NUMERIC,
        top_50_concentration NUMERIC,
        top_100_concentration NUMERIC,
        gini_coefficient NUMERIC,
        unique_holders INTEGER,
        new_holders_24h INTEGER,
        whale_count INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Schema.sql related tables
    CREATE TABLE chains (
        chain_id INTEGER PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        symbol VARCHAR(10) NOT NULL,
        explorer_url VARCHAR(255),
        rpc_url VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE dex_protocols (
        id SERIAL PRIMARY KEY,
        chain_id INTEGER REFERENCES chains(chain_id),
        name VARCHAR(100) NOT NULL,
        version VARCHAR(20),
        factory_address VARCHAR(42) NOT NULL,
        router_address VARCHAR(42),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(chain_id, factory_address)
    );

    CREATE TABLE tokens (
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

    CREATE TABLE dex_pairs (
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

    CREATE TABLE swap_transactions (
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

    CREATE TABLE token_transfers (
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

    CREATE TABLE wallets (
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

    CREATE TABLE wallet_balances (
        id SERIAL PRIMARY KEY,
        wallet_id INTEGER REFERENCES wallets(id),
        chain_id INTEGER REFERENCES chains(chain_id),
        token_id INTEGER REFERENCES tokens(id),
        balance NUMERIC(78, 0) NOT NULL,
        usd_value DECIMAL(20, 2),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        block_number BIGINT
    );

    CREATE TABLE liquidity_events (
        id SERIAL PRIMARY KEY,
        chain_id INTEGER REFERENCES chains(chain_id),
        pair_id INTEGER REFERENCES dex_pairs(id),
        tx_hash VARCHAR(66) NOT NULL,
        event_type VARCHAR(20) NOT NULL,
        provider_address VARCHAR(42),
        amount0 NUMERIC(78, 0),
        amount1 NUMERIC(78, 0),
        liquidity_tokens NUMERIC(78, 0),
        timestamp TIMESTAMP NOT NULL,
        block_number BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE price_snapshots (
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

    CREATE TABLE arbitrage_opportunities (
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

    CREATE TABLE trading_metrics (
        id SERIAL PRIMARY KEY,
        chain_id INTEGER REFERENCES chains(chain_id),
        token_id INTEGER REFERENCES tokens(id),
        period_type VARCHAR(20),
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

    CREATE TABLE smart_money_wallets (
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

    -- Create indexes for better query performance
    -- BSC indexes
    CREATE INDEX IF NOT EXISTS idx_bsc_pool_metrics_timestamp ON bsc_pool_metrics(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_bsc_trades_timestamp ON bsc_trades(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_bsc_trades_block_number ON bsc_trades(block_number DESC);
    CREATE INDEX IF NOT EXISTS idx_bsc_wallet_metrics_address ON bsc_wallet_metrics(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_bsc_wallet_metrics_updated_at ON bsc_wallet_metrics(updated_at DESC);
    CREATE INDEX IF NOT EXISTS idx_bsc_liquidity_events_timestamp ON bsc_liquidity_events(timestamp DESC);

    -- Moralis indexes
    CREATE INDEX IF NOT EXISTS idx_moralis_swaps_timestamp ON moralis_swaps(block_timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_swaps_wallet ON moralis_swaps(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_swaps_pair ON moralis_swaps(pair_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_swaps_correct_timestamp ON moralis_swaps_correct(block_timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_swaps_correct_wallet ON moralis_swaps_correct(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_swaps_correct_type ON moralis_swaps_correct(transaction_type);
    CREATE INDEX IF NOT EXISTS idx_moralis_swaps_enhanced_wallet ON moralis_swaps_enhanced(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_swaps_enhanced_timestamp ON moralis_swaps_enhanced(block_timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_analytics_timestamp ON moralis_token_analytics(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_analytics_token ON moralis_token_analytics(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_analytics_correct_timestamp ON moralis_token_analytics_correct(timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_analytics_correct_token ON moralis_token_analytics_correct(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_analytics_enhanced_timestamp ON moralis_token_analytics_enhanced(timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_analytics_enhanced_token ON moralis_token_analytics_enhanced(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_pair_stats_timestamp ON moralis_pair_stats(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_pair_stats_token ON moralis_pair_stats(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_pair_stats_correct_timestamp ON moralis_pair_stats_correct(timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_pair_stats_correct_pair ON moralis_pair_stats_correct(pair_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_pair_stats_enhanced_timestamp ON moralis_pair_stats_enhanced(timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_pair_stats_enhanced_pair ON moralis_pair_stats_enhanced(pair_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_holders_token ON moralis_holders(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_holders_address ON moralis_holders(holder_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_transfers_timestamp ON moralis_transfers(block_timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_transfers_addresses ON moralis_transfers(from_address, to_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_transfers_block ON moralis_token_transfers(block_timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_transfers_addresses ON moralis_token_transfers(from_address, to_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_holder_stats_token ON moralis_token_holder_stats(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_historical_holders_token ON moralis_historical_holders(token_address, data_timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_historical_holders_correct_timestamp ON moralis_historical_holders_correct(timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_historical_holders_correct_token ON moralis_historical_holders_correct(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_historical_holders_enhanced_timestamp ON moralis_historical_holders_enhanced(timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_historical_holders_enhanced_token ON moralis_historical_holders_enhanced(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_holder_stats_correct_timestamp ON moralis_holder_stats_correct(timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_holder_stats_correct_token ON moralis_holder_stats_correct(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_snipers_correct_timestamp ON moralis_snipers_correct(timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_snipers_correct_pair ON moralis_snipers_correct(pair_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_snipers_correct_wallet ON moralis_snipers_correct(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_snipers_enhanced_timestamp ON moralis_snipers_enhanced(block_timestamp);
    CREATE INDEX IF NOT EXISTS idx_moralis_snipers_enhanced_pair ON moralis_snipers_enhanced(pair_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_snipers_enhanced_wallet ON moralis_snipers_enhanced(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_snipers_complete_wallet ON moralis_snipers_complete(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_snipers_complete_pair ON moralis_snipers_complete(pair_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_top_gainers_token ON moralis_top_gainers(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_top_gainers_wallet ON moralis_top_gainers(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_liquidity_changes_time ON moralis_liquidity_changes(block_timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_holder_distribution_balance ON moralis_holder_distribution(balance_usd DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_holder_distribution_token ON moralis_holder_distribution(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_metrics_summary_token ON moralis_metrics_summary(token_address);
    CREATE INDEX IF NOT EXISTS idx_moralis_token_stats_timestamp ON moralis_token_stats(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_moralis_holder_stats_complete_timestamp ON moralis_holder_stats_complete(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_wash_trading_complete_confidence ON wash_trading_complete(confidence_score DESC);

    -- Analytics indexes
    CREATE INDEX IF NOT EXISTS idx_dex_trades_timestamp ON dex_trades(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_dex_trades_chain ON dex_trades(chain_id, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_dex_trades_dex ON dex_trades(dex_name, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_dex_trades_pair ON dex_trades(pair);
    CREATE INDEX IF NOT EXISTS idx_dex_trades_trader ON dex_trades(trader_address);
    CREATE INDEX IF NOT EXISTS idx_dex_trades_tx_hash ON dex_trades(tx_hash);

    CREATE INDEX IF NOT EXISTS idx_token_prices_timestamp ON token_prices(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_token_prices_symbol ON token_prices(token_symbol, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_token_prices_chain ON token_prices(chain_id, timestamp DESC);

    CREATE INDEX IF NOT EXISTS idx_liquidity_pools_timestamp ON liquidity_pools(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_liquidity_pools_dex ON liquidity_pools(dex_name, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_liquidity_pools_chain ON liquidity_pools(chain_id, timestamp DESC);

    CREATE INDEX IF NOT EXISTS idx_chain_stats_timestamp ON chain_stats(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_chain_stats_chain ON chain_stats(chain_id, timestamp DESC);

    CREATE INDEX IF NOT EXISTS idx_wallet_activity_timestamp ON wallet_activity(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_wallet_activity_chain ON wallet_activity(chain_id, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_wallet_activity_address ON wallet_activity(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_wallet_activity_volume ON wallet_activity(volume_24h DESC);

    CREATE INDEX IF NOT EXISTS idx_token_distribution_timestamp ON token_distribution(timestamp DESC);

    CREATE INDEX IF NOT EXISTS idx_wallet_pnl_wallet ON wallet_pnl(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_wallet_pnl_token ON wallet_pnl(token_address);
    CREATE INDEX IF NOT EXISTS idx_wallet_pnl_timestamp ON wallet_pnl(timestamp DESC);

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

    -- Functions for data management
    CREATE OR REPLACE FUNCTION update_modified_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

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
    """

    # Connect to the database
    conn = None
    cur = None
    try:
        print("Connecting to Railway database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Creating all tables...")
        # Execute the creation script
        cur.execute(create_script)
        
        # Commit the changes
        conn.commit()
        
        print("All tables created successfully!")
        
    except psycopg2.Error as e:
        print(f"Database error during creation: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Error during creation: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Database connection closed after creating tables.")

def main():
    """
    Main function to drop old tables and create new ones
    """
    print("Starting Railway database reset and update process...")
    print("This will DROP ALL existing data and recreate the database structure!")
    print("Ensure you have proper backups if needed.")
    
    # First, drop all existing objects
    drop_all_tables_and_objects()
    
    # Then, create all new tables with exact structure
    create_all_tables()
    
    print("Railway database update completed successfully!")
    print("All tables, sequences, indexes, views, and functions have been recreated with the exact structure from the running database.")

if __name__ == "__main__":
    main()