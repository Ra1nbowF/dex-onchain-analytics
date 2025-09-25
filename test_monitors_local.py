"""Test monitors locally with local database"""

import os
import sys
import asyncio
import subprocess
import threading
import time
from datetime import datetime

# Use local database
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

def run_bsc_monitor():
    """Run BSC monitor for testing"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting BSC monitor...")
    try:
        process = subprocess.Popen(
            [sys.executable, "bsc_pool_monitor.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )

        # Read output
        for line in process.stdout:
            if line.strip():
                print(f"[BSC] {line.strip()}")

        # Check for errors
        stderr = process.stderr.read()
        if stderr:
            print(f"[BSC ERROR] {stderr}")

    except Exception as e:
        print(f"[BSC EXCEPTION] {e}")

def run_moralis_monitor():
    """Run Moralis monitor for testing"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Moralis monitor...")

    # Check which monitor file exists
    monitor_files = ["main.py", "moralis_final_monitor.py", "moralis_enhanced_monitor.py"]
    monitor_to_use = None

    for monitor in monitor_files:
        if os.path.exists(monitor):
            monitor_to_use = monitor
            break

    if not monitor_to_use:
        print("[MORALIS] No monitor file found!")
        return

    print(f"[MORALIS] Using {monitor_to_use}")

    try:
        process = subprocess.Popen(
            [sys.executable, monitor_to_use],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )

        # Read output
        for line in process.stdout:
            if line.strip():
                print(f"[MORALIS] {line.strip()}")

        # Check for errors
        stderr = process.stderr.read()
        if stderr:
            print(f"[MORALIS ERROR] {stderr}")

    except Exception as e:
        print(f"[MORALIS EXCEPTION] {e}")

def check_database_data():
    """Check if data is being written"""
    import asyncpg

    async def check():
        conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5433/dex_analytics")

        # Check BSC data
        bsc_count = await conn.fetchval("SELECT COUNT(*) FROM bsc_pool_metrics WHERE timestamp > NOW() - INTERVAL '5 minutes'")
        print(f"\n[DB CHECK] BSC pool metrics (last 5 min): {bsc_count} records")

        # Check Moralis data
        moralis_count = await conn.fetchval("SELECT COUNT(*) FROM moralis_pair_stats_correct WHERE timestamp > NOW() - INTERVAL '5 minutes'")
        print(f"[DB CHECK] Moralis pair stats (last 5 min): {moralis_count} records")

        # Get latest timestamps
        bsc_latest = await conn.fetchval("SELECT MAX(timestamp) FROM bsc_pool_metrics")
        if bsc_latest:
            print(f"[DB CHECK] BSC latest: {bsc_latest}")

        moralis_latest = await conn.fetchval("SELECT MAX(timestamp) FROM moralis_pair_stats_correct")
        if moralis_latest:
            print(f"[DB CHECK] Moralis latest: {moralis_latest}")

        await conn.close()

    asyncio.run(check())

def main():
    print("=" * 60)
    print("Testing Monitors Locally")
    print(f"Database: {os.environ['DATABASE_URL']}")
    print("=" * 60)

    # Create threads for monitors
    bsc_thread = threading.Thread(target=run_bsc_monitor, daemon=True)
    moralis_thread = threading.Thread(target=run_moralis_monitor, daemon=True)

    # Start monitors
    bsc_thread.start()
    moralis_thread.start()

    # Let them run for a bit
    print("\nMonitors started. Waiting 30 seconds for data collection...")
    time.sleep(30)

    # Check database
    print("\nChecking database for new data...")
    check_database_data()

    print("\nTest complete. Press Ctrl+C to exit.")

    try:
        # Keep running
        while True:
            time.sleep(60)
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking data again...")
            check_database_data()
    except KeyboardInterrupt:
        print("\nStopping test...")

if __name__ == "__main__":
    main()