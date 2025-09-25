"""Create missing tables in Railway database"""

import psycopg2
import sys

# Railway database connection
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def create_missing_tables():
    """Create tables that monitors expect"""
    conn = psycopg2.connect(RAILWAY_URL)
    cur = conn.cursor()
    
    print("Creating missing tables in Railway database...")
    print("="*60)
    
    tables = [
        # BSC monitor tables
        (
            "bsc_dex_trades",
            """
            CREATE TABLE IF NOT EXISTS bsc_dex_trades (
                id SERIAL PRIMARY KEY,
                pool_address VARCHAR(66) NOT NULL,
                token0 VARCHAR(66),
                token1 VARCHAR(66),
                amount0_in DECIMAL(30, 18),
                amount1_in DECIMAL(30, 18),
                amount0_out DECIMAL(30, 18),
                amount1_out DECIMAL(30, 18),
                trader VARCHAR(66),
                tx_hash VARCHAR(66),
                block_number BIGINT,
                timestamp TIMESTAMP DEFAULT NOW(),
                INDEX idx_bsc_dex_trades_timestamp (timestamp),
                INDEX idx_bsc_dex_trades_pool (pool_address)
            )
            """
        ),
        (
            "bsc_pool_events",
            """
            CREATE TABLE IF NOT EXISTS bsc_pool_events (
                id SERIAL PRIMARY KEY,
                pool_address VARCHAR(66) NOT NULL,
                event_type VARCHAR(50),
                token0 VARCHAR(66),
                token1 VARCHAR(66),
                amount0 DECIMAL(30, 18),
                amount1 DECIMAL(30, 18),
                liquidity DECIMAL(30, 18),
                tx_hash VARCHAR(66),
                block_number BIGINT,
                timestamp TIMESTAMP DEFAULT NOW(),
                INDEX idx_bsc_pool_events_timestamp (timestamp),
                INDEX idx_bsc_pool_events_pool (pool_address)
            )
            """
        ),
        
        # Moralis _correct tables that dashboards expect
        (
            "moralis_liquidity_correct",
            """
            CREATE TABLE IF NOT EXISTS moralis_liquidity_correct (
                id SERIAL PRIMARY KEY,
                pool_address VARCHAR(66),
                token0_address VARCHAR(66),
                token1_address VARCHAR(66),
                token0_symbol VARCHAR(20),
                token1_symbol VARCHAR(20),
                reserve0 DECIMAL(30, 18),
                reserve1 DECIMAL(30, 18),
                total_liquidity_usd DECIMAL(20, 2),
                timestamp TIMESTAMP DEFAULT NOW()
            )
            """
        ),
        (
            "moralis_price_history_correct",
            """
            CREATE TABLE IF NOT EXISTS moralis_price_history_correct (
                id SERIAL PRIMARY KEY,
                token_address VARCHAR(66),
                token_symbol VARCHAR(20),
                price_usd DECIMAL(20, 8),
                volume_24h DECIMAL(20, 2),
                price_change_24h DECIMAL(10, 2),
                timestamp TIMESTAMP DEFAULT NOW()
            )
            """
        ),
        (
            "moralis_volume_metrics_correct",
            """
            CREATE TABLE IF NOT EXISTS moralis_volume_metrics_correct (
                id SERIAL PRIMARY KEY,
                pool_address VARCHAR(66),
                volume_24h DECIMAL(20, 2),
                volume_7d DECIMAL(20, 2),
                fees_24h DECIMAL(20, 2),
                trades_24h INTEGER,
                timestamp TIMESTAMP DEFAULT NOW()
            )
            """
        ),
        (
            "moralis_whale_activity_correct",
            """
            CREATE TABLE IF NOT EXISTS moralis_whale_activity_correct (
                id SERIAL PRIMARY KEY,
                wallet_address VARCHAR(66),
                transaction_hash VARCHAR(66),
                token_address VARCHAR(66),
                token_symbol VARCHAR(20),
                amount DECIMAL(30, 18),
                value_usd DECIMAL(20, 2),
                action VARCHAR(20),
                timestamp TIMESTAMP DEFAULT NOW()
            )
            """
        ),
        (
            "moralis_arbitrage_correct",
            """
            CREATE TABLE IF NOT EXISTS moralis_arbitrage_correct (
                id SERIAL PRIMARY KEY,
                wallet_address VARCHAR(66),
                from_pool VARCHAR(66),
                to_pool VARCHAR(66),
                token_in VARCHAR(66),
                token_out VARCHAR(66),
                amount_in DECIMAL(30, 18),
                amount_out DECIMAL(30, 18),
                profit_usd DECIMAL(20, 2),
                timestamp TIMESTAMP DEFAULT NOW()
            )
            """
        )
    ]
    
    # PostgreSQL doesn't support INDEX in CREATE TABLE, need to create separately
    for table_name, create_sql in tables:
        try:
            # Remove INDEX lines from CREATE TABLE
            clean_sql = "\n".join([line for line in create_sql.split("\n") 
                                   if not line.strip().startswith("INDEX")])
            clean_sql = clean_sql.replace(",\n            )", "\n            )")
            
            cur.execute(clean_sql)
            conn.commit()
            print(f"[OK] Created table: {table_name}")
            
            # Create indexes separately
            if "bsc_dex_trades" in table_name:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_pool ON {table_name}(pool_address)")
            elif "bsc_pool_events" in table_name:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_pool ON {table_name}(pool_address)")
            else:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp)")
            
            conn.commit()
            
        except Exception as e:
            if "already exists" in str(e):
                print(f"[EXISTS] Table already exists: {table_name}")
            else:
                print(f"[ERROR] Failed to create {table_name}: {e}")
            conn.rollback()
    
    # Check what tables we have now
    print("\n" + "="*60)
    print("Checking Moralis and BSC tables:")
    print("="*60)
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE 'moralis_%correct' OR table_name LIKE 'bsc_%')
        ORDER BY table_name
    """)
    
    tables = cur.fetchall()
    for table in tables:
        # Count rows
        cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cur.fetchone()[0]
        print(f"  {table[0]}: {count} rows")
    
    cur.close()
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    create_missing_tables()