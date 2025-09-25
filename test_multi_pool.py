"""Test multi-pool monitoring"""

import asyncio
import sys
sys.path.insert(0, '.')

from bsc_multi_pool_monitor import MultiPoolMonitor

async def test():
    monitor = MultiPoolMonitor()
    await monitor.initialize()
    
    print("Testing Multi-Pool LP Activity Monitoring")
    print("=" * 60)
    
    # Test each pool
    for pool_name, pool_config in monitor.pools.items():
        print(f"\n{pool_name}:")
        print(f"  Address: {pool_config['address']}")
        print(f"  Version: {pool_config['version']}")
        print(f"  Pair: {pool_config['token0_symbol']}/{pool_config['token1_symbol']}")
        
        if pool_config["version"] == "V2":
            transfers = await monitor.fetch_v2_lp_transfers(pool_config, hours=24)
            print(f"  Found {len(transfers)} LP transfers in 24 hours")
            
            if transfers:
                # Count types
                mints = sum(1 for t in transfers if t['transfer_type'] == 'mint')
                burns = sum(1 for t in transfers if t['transfer_type'] == 'burn')
                regular = sum(1 for t in transfers if t['transfer_type'] == 'transfer')
                
                print(f"    - Mints: {mints}")
                print(f"    - Burns: {burns}")
                print(f"    - Transfers: {regular}")
                
                # Show sample
                print(f"\n  Sample transfers (last 3):")
                for t in transfers[-3:]:
                    print(f"    {t['transfer_type'].upper()}: {t['tx_hash'][:10]}...")
        else:
            events = await monitor.fetch_v3_liquidity_events(pool_config, hours=24)
            print(f"  Found {len(events)} liquidity events in 24 hours")
            
            if events:
                mints = sum(1 for e in events if e['transfer_type'] == 'mint')
                burns = sum(1 for e in events if e['transfer_type'] == 'burn')
                
                print(f"    - Mints: {mints}")
                print(f"    - Burns: {burns}")
    
    # Check database
    print("\n" + "=" * 60)
    print("Checking database...")
    
    async with monitor.db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM multi_pool_lp_activity")
        print(f"Total records in multi_pool_lp_activity: {count}")
        
        if count > 0:
            recent = await conn.fetch("""
                SELECT pool_name, transfer_type, COUNT(*) as cnt
                FROM multi_pool_lp_activity
                WHERE timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY pool_name, transfer_type
                ORDER BY pool_name, transfer_type
            """)
            
            print("\nActivity summary (last 24 hours):")
            for row in recent:
                print(f"  {row['pool_name']} - {row['transfer_type']}: {row['cnt']}")
    
    await monitor.close()
    print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(test())