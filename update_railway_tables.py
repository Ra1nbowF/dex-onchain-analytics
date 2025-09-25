"""Update Railway database with new tables for V3 and multi-pool monitoring"""

import asyncio
import asyncpg
import os

# Railway database URL
RAILWAY_DATABASE_URL = "postgresql://postgres:FnUBkBMahIeXCmmmuxBmwQrJfJjOVhHj@autorack.proxy.rlwy.net:21429/railway"

async def update_railway_db():
    conn = None
    try:
        print("Connecting to Railway database...")
        print("=" * 60)
        
        conn = await asyncpg.connect(RAILWAY_DATABASE_URL)
        print("[OK] Connected to Railway database")
        
        # 1. Create V3 liquidity events table
        print("\nCreating bsc_v3_liquidity_events table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bsc_v3_liquidity_events (
                id SERIAL PRIMARY KEY,
                tx_hash VARCHAR(66) NOT NULL,
                block_number BIGINT NOT NULL,
                event_type VARCHAR(20) NOT NULL,
                owner_address VARCHAR(42),
                position_id BIGINT,
                tick_lower INTEGER,
                tick_upper INTEGER,
                liquidity NUMERIC(40, 0),
                amount0 NUMERIC(40, 18),
                amount1 NUMERIC(40, 18),
                timestamp TIMESTAMP NOT NULL,
                UNIQUE(tx_hash, event_type, owner_address)
            )
        """)
        
        # Create indexes for V3 table
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_v3_liquidity_timestamp ON bsc_v3_liquidity_events(timestamp DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_v3_liquidity_owner ON bsc_v3_liquidity_events(owner_address)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_v3_liquidity_type ON bsc_v3_liquidity_events(event_type)")
        print("[OK] Created bsc_v3_liquidity_events table")
        
        # 2. Create multi-pool LP activity table
        print("\nCreating multi_pool_lp_activity table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS multi_pool_lp_activity (
                id SERIAL PRIMARY KEY,
                pool_address VARCHAR(42) NOT NULL,
                pool_name VARCHAR(50) NOT NULL,
                pool_version VARCHAR(10) NOT NULL,
                tx_hash VARCHAR(66) NOT NULL,
                block_number BIGINT NOT NULL,
                from_address VARCHAR(42),
                to_address VARCHAR(42),
                transfer_type VARCHAR(20) NOT NULL,
                lp_amount NUMERIC(40, 18),
                timestamp TIMESTAMP NOT NULL,
                UNIQUE(tx_hash, pool_address)
            )
        """)
        
        # Create indexes for multi-pool table
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_multi_pool_timestamp ON multi_pool_lp_activity(timestamp DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_multi_pool_address ON multi_pool_lp_activity(pool_address)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_multi_pool_type ON multi_pool_lp_activity(transfer_type)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_multi_pool_name ON multi_pool_lp_activity(pool_name)")
        print("[OK] Created multi_pool_lp_activity table")
        
        # 3. Create summary view for multi-pool data
        print("\nCreating multi_pool_lp_summary view...")
        await conn.execute("""
            CREATE OR REPLACE VIEW multi_pool_lp_summary AS
            SELECT 
                pool_name,
                pool_version,
                transfer_type,
                COUNT(*) as event_count,
                SUM(lp_amount) as total_lp_amount,
                MAX(timestamp) as last_activity
            FROM multi_pool_lp_activity
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY pool_name, pool_version, transfer_type
            ORDER BY pool_name, transfer_type
        """)
        print("[OK] Created multi_pool_lp_summary view")
        
        # 4. Check if all tables were created successfully
        print("\n" + "=" * 60)
        print("Verifying tables...")
        
        tables_to_check = [
            'bsc_v3_liquidity_events',
            'multi_pool_lp_activity',
            'bsc_liquidity_events',
            'bsc_lp_token_transfers',
            'bsc_lp_holders',
            'bsc_pool_metrics',
            'bsc_trades',
            'bsc_token_transfers'
        ]
        
        for table in tables_to_check:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            if exists:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"  [OK] {table}: {count} records")
            else:
                print(f"  [X] {table}: NOT FOUND")
        
        # 5. Check views
        print("\nVerifying views...")
        views = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            AND table_name LIKE '%pool%'
        """)
        
        for view in views:
            print(f"  [OK] {view['table_name']}")
        
        print("\n" + "=" * 60)
        print("Railway database update completed successfully!")
        print("\nSummary:")
        print("- Added V3 liquidity events tracking")
        print("- Added multi-pool LP activity tracking")
        print("- Created summary view for Grafana")
        print("- All indexes created for performance")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to update Railway database: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if conn:
            await conn.close()
            print("\nConnection closed")

if __name__ == "__main__":
    asyncio.run(update_railway_db())