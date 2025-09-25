"""Test Moralis monitor locally"""

import os
import sys
import asyncio

# Force local database
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

# Check which Moralis monitor to use
monitor_files = ["main.py", "moralis_final_monitor.py", "moralis_enhanced_monitor.py"]
monitor_module = None

for monitor in monitor_files:
    if os.path.exists(monitor):
        monitor_module = monitor.replace('.py', '')
        print(f"Using monitor: {monitor}")
        break

if not monitor_module:
    print("No Moralis monitor found!")
    sys.exit(1)

# Import the monitor
if monitor_module == "main":
    from main import MoralisFinalMonitor as MoralisMonitor
else:
    # Try to import from the specific file
    try:
        exec(f"from {monitor_module} import MoralisBSCMonitor as MoralisMonitor")
    except:
        exec(f"from {monitor_module} import MoralisFinalMonitor as MoralisMonitor")

async def test_moralis_monitor():
    """Test Moralis monitor with local database"""
    print("=" * 60)
    print("Testing Moralis Monitor with Local Database")
    print(f"Database: {os.environ['DATABASE_URL']}")
    print("=" * 60)

    monitor = MoralisMonitor()

    try:
        print("\nInitializing Moralis monitor...")
        await monitor.initialize()
        print("[OK] Initialized successfully")

        print("\nFetching pair stats...")
        pair_stats = await monitor.fetch_pair_stats()
        if pair_stats:
            print(f"[OK] Fetched pair stats:")
            print(f"  Liquidity: ${pair_stats.get('liquidity_usd', 0):,.0f}")
            print(f"  Volume 24h: ${pair_stats.get('total_volume_24h', 0):,.0f}")
            print(f"  Buy Volume: ${pair_stats.get('buy_volume_24h', 0):,.0f}")
            print(f"  Sell Volume: ${pair_stats.get('sell_volume_24h', 0):,.0f}")

            # Try to store it
            await monitor.store_pair_stats(pair_stats)
            print("[OK] Stored pair stats to database")
        else:
            print("[FAIL] Failed to fetch pair stats")

        print("\nChecking database for recent data...")
        async with monitor.db_pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM moralis_pair_stats_correct
                WHERE timestamp > NOW() - INTERVAL '1 minute'
            """)
            print(f"  Records in last minute: {count}")

            latest = await conn.fetchval("""
                SELECT MAX(timestamp)
                FROM moralis_pair_stats_correct
            """)
            if latest:
                print(f"  Latest record: {latest}")

        print("\n[SUCCESS] Moralis Monitor test completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Moralis Monitor test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await monitor.cleanup()
        print("\n[OK] Cleaned up connections")

if __name__ == "__main__":
    asyncio.run(test_moralis_monitor())