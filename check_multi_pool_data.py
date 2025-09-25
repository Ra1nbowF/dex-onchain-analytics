"""Check multi-pool LP activity data"""

import asyncio
import asyncpg
from datetime import datetime

DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

async def check_data():
    conn = None
    try:
        print("Multi-Pool LP Activity Status")
        print("=" * 60)
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Check multi_pool_lp_activity
        count = await conn.fetchval("SELECT COUNT(*) FROM multi_pool_lp_activity")
        print(f"Total records in multi_pool_lp_activity: {count}")
        
        if count > 0:
            # Get summary by pool
            summary = await conn.fetch("""
                SELECT 
                    pool_name,
                    pool_version,
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN transfer_type = 'mint' THEN 1 END) as mints,
                    COUNT(CASE WHEN transfer_type = 'burn' THEN 1 END) as burns,
                    COUNT(CASE WHEN transfer_type = 'transfer' THEN 1 END) as transfers,
                    MIN(timestamp) as first_event,
                    MAX(timestamp) as last_event
                FROM multi_pool_lp_activity
                GROUP BY pool_name, pool_version
                ORDER BY pool_name
            """)
            
            print("\nLP Activity by Pool:")
            for row in summary:
                print(f"\n{row['pool_name']} ({row['pool_version']}):")
                print(f"  Total Events: {row['total_events']}")
                print(f"  - Mints: {row['mints']}")
                print(f"  - Burns: {row['burns']}")
                print(f"  - Transfers: {row['transfers']}")
                print(f"  First Event: {row['first_event']}")
                print(f"  Last Event: {row['last_event']}")
            
            # Get recent events
            recent = await conn.fetch("""
                SELECT pool_name, transfer_type, tx_hash, timestamp
                FROM multi_pool_lp_activity
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            print("\nRecent LP Activity (last 10):")
            for row in recent:
                print(f"  {row['timestamp']}: {row['pool_name']} - {row['transfer_type']} - {row['tx_hash'][:10]}...")
        else:
            print("\n[NO DATA] No LP activity recorded yet")
            print("\nTrying manual insert to test...")
            
            # Insert test data
            await conn.execute("""
                INSERT INTO multi_pool_lp_activity (
                    pool_address, pool_name, pool_version,
                    tx_hash, block_number, from_address, to_address,
                    transfer_type, lp_amount, timestamp
                ) VALUES (
                    '0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae',
                    'WBNB/USDT', 'V2',
                    '0xtest123', 12345678,
                    '0x0000000000000000000000000000000000000000',
                    '0x1234567890123456789012345678901234567890',
                    'mint', 1.5, NOW()
                )
                ON CONFLICT (tx_hash, pool_address) DO NOTHING
            """)
            
            count = await conn.fetchval("SELECT COUNT(*) FROM multi_pool_lp_activity")
            print(f"After test insert: {count} records")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_data())