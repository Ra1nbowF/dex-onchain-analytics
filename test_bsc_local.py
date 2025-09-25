"""Test BSC monitor locally"""

import os
import asyncio
import sys

# Force local database
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

# Import after setting env var
sys.path.insert(0, '.')
from bsc_pool_monitor import BSCPoolMonitor

async def test_bsc_monitor():
    """Test BSC monitor with local database"""
    print("=" * 60)
    print("Testing BSC Monitor with Local Database")
    print(f"Database: {os.environ['DATABASE_URL']}")
    print("=" * 60)

    monitor = BSCPoolMonitor()

    try:
        print("\nInitializing BSC monitor...")
        await monitor.initialize()
        print("[OK] Initialized successfully")

        print("\nFetching pool reserves...")
        reserves = await monitor.fetch_pool_reserves()
        if reserves:
            print(f"[OK] Pool reserves fetched:")
            print(f"  BTCB: {reserves['btcb_reserve']:.6f}")
            print(f"  USDT: {reserves['usdt_reserve']:.2f}")
            print(f"  Liquidity: ${reserves['total_liquidity']:.0f}")
        else:
            print("[FAIL] Failed to fetch reserves")

        print("\nFetching recent trades...")
        trades = await monitor.fetch_recent_trades()
        print(f"[OK] Found {len(trades)} recent trades")

        if trades:
            print(f"  Latest trade: {trades[0].get('swap_type', 'N/A')}")

        print("\nTesting database write...")
        # Try to write one pool metric
        if reserves:
            async with monitor.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO bsc_pool_metrics
                    (pool_address, token0_reserve, token1_reserve, total_liquidity_usd, price_btcb_usdt, timestamp)
                    VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                """,
                    "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4",
                    reserves['btcb_reserve'],
                    reserves['usdt_reserve'],
                    reserves['total_liquidity'],
                    reserves['btcb_price'],
                )
                print("[OK] Successfully wrote to database")

                # Check if it was written
                count = await conn.fetchval("SELECT COUNT(*) FROM bsc_pool_metrics WHERE timestamp > NOW() - INTERVAL '1 minute'")
                print(f"  Records in last minute: {count}")

        print("\n[SUCCESS] BSC Monitor test completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] BSC Monitor test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await monitor.cleanup()
        print("\n[OK] Cleaned up connections")

if __name__ == "__main__":
    asyncio.run(test_bsc_monitor())