"""Test if BSC monitor fixes work"""

import os
import asyncio
import sys

# Set local database
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

# Import the monitor
sys.path.insert(0, '.')
from bsc_pool_monitor import BSCPoolMonitor

async def test_fixes():
    """Test the BSC monitor fixes"""
    print("=" * 60)
    print("Testing BSC Monitor Fixes")
    print("=" * 60)

    monitor = BSCPoolMonitor()

    try:
        # Initialize
        print("\n1. Initializing monitor...")
        await monitor.initialize()
        print("   [OK] Initialized")

        # Test get_current_block (the main fix)
        print("\n2. Testing get_current_block() with new RPC method...")
        block_num = await monitor.get_current_block()
        if block_num and block_num > 0:
            print(f"   [OK] Got block number: {block_num}")
        else:
            print(f"   [FAIL] Failed to get block number: {block_num}")

        # Test fetch_pool_reserves (uses BSCScan API)
        print("\n3. Testing fetch_pool_reserves()...")
        reserves = await monitor.fetch_pool_reserves()
        if reserves:
            print(f"   [OK] Pool reserves fetched:")
            print(f"       BTCB: {reserves.get('btcb_reserve', 0):.6f}")
            print(f"       USDT: {reserves.get('usdt_reserve', 0):.2f}")
            print(f"       TVL: ${reserves.get('tvl', 0):,.0f}")
        else:
            print("   [FAIL] Failed to fetch reserves")

        # Test fetch_recent_trades
        print("\n4. Testing fetch_recent_trades()...")
        trades = await monitor.fetch_recent_trades(hours=1)
        if trades is not None:
            print(f"   [OK] Found {len(trades)} trades")
        else:
            print("   [FAIL] Failed to fetch trades")

        # Try to write to database
        print("\n5. Testing database write...")
        if reserves and block_num:
            async with monitor.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO bsc_pool_metrics
                    (pool_address, token0_reserve, token1_reserve, total_liquidity_usd, price_btcb_usdt, timestamp)
                    VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                """,
                    POOL_ADDRESS,
                    reserves.get('btcb_reserve', 0),
                    reserves.get('usdt_reserve', 0),
                    reserves.get('tvl', 0),
                    reserves.get('price', 0)
                )
                print("   [OK] Successfully wrote to database")

                # Check if it was written
                count = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM bsc_pool_metrics
                    WHERE timestamp > NOW() - INTERVAL '1 minute'
                """)
                print(f"   Records in last minute: {count}")

        print("\n" + "=" * 60)
        print("SUMMARY:")
        if block_num and reserves:
            print("[SUCCESS] BSC Monitor is working properly!")
            print("The fixes resolved the deprecated endpoint issues.")
        else:
            print("[PARTIAL] Some features working, but issues remain:")
            if not block_num:
                print("  - Block number fetch failed")
            if not reserves:
                print("  - Reserve fetch failed (might be API key issue)")

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await monitor.cleanup()
        print("\n[OK] Cleaned up connections")

# Import POOL_ADDRESS
from bsc_pool_monitor import POOL_ADDRESS

if __name__ == "__main__":
    asyncio.run(test_fixes())