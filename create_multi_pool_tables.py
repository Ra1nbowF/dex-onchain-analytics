"""Create tables for multi-pool monitoring"""

import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

async def create_tables():
    conn = None
    try:
        print("Creating multi-pool monitoring tables...")
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Create table for LP activity across multiple pools
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
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_multi_pool_timestamp ON multi_pool_lp_activity(timestamp DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_multi_pool_address ON multi_pool_lp_activity(pool_address)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_multi_pool_type ON multi_pool_lp_activity(transfer_type)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_multi_pool_name ON multi_pool_lp_activity(pool_name)")
        
        print("[OK] Table 'multi_pool_lp_activity' created successfully")
        
        # Create summary view for Grafana
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
        
        print("[OK] View 'multi_pool_lp_summary' created")
        
        # Check existing tables
        result = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%pool%' OR table_name LIKE '%lp%' OR table_name LIKE '%liquidity%')
            ORDER BY table_name
        """)
        
        print("\nExisting pool/LP related tables:")
        for row in result:
            print(f"  - {row['table_name']}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())