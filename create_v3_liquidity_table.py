"""Create table for PancakeSwap V3 liquidity events"""

import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

async def create_table():
    conn = None
    try:
        print("Creating V3 liquidity events table...")
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Create table for V3 liquidity events
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bsc_v3_liquidity_events (
                id SERIAL PRIMARY KEY,
                tx_hash VARCHAR(66) NOT NULL,
                block_number BIGINT NOT NULL,
                event_type VARCHAR(20) NOT NULL, -- 'mint', 'burn', 'collect'
                owner_address VARCHAR(42),
                position_id BIGINT,  -- NFT token ID for the position
                tick_lower INTEGER,  -- Price range lower bound
                tick_upper INTEGER,  -- Price range upper bound
                liquidity NUMERIC(40, 0),  -- Liquidity amount
                amount0 NUMERIC(40, 18),  -- Token0 amount (BTCB)
                amount1 NUMERIC(40, 18),  -- Token1 amount (USDT)
                timestamp TIMESTAMP NOT NULL,
                UNIQUE(tx_hash, event_type, owner_address)
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_v3_liquidity_timestamp ON bsc_v3_liquidity_events(timestamp DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_v3_liquidity_owner ON bsc_v3_liquidity_events(owner_address)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_v3_liquidity_type ON bsc_v3_liquidity_events(event_type)")
        
        print("[OK] Table 'bsc_v3_liquidity_events' created successfully")
        
        # Check existing liquidity tables
        result = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%liquidity%'
            ORDER BY table_name
        """)
        
        print("\nExisting liquidity-related tables:")
        for row in result:
            print(f"  - {row['table_name']}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(create_table())