"""Run monitors directly to test"""

import os
import subprocess
import time
import sys
from datetime import datetime

# Use local database
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

print("=" * 60)
print("Running Monitors Test with Local Database")
print(f"Time: {datetime.now()}")
print("=" * 60)

# Start BSC monitor
print("\n[1] Starting BSC monitor...")
bsc_proc = subprocess.Popen(
    [sys.executable, "bsc_pool_monitor.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=os.environ.copy()
)

# Start Moralis monitor
print("[2] Starting Moralis monitor...")
moralis_proc = subprocess.Popen(
    [sys.executable, "main.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=os.environ.copy()
)

print("\nMonitors started. Collecting output for 20 seconds...")
print("-" * 60)

start_time = time.time()
timeout = 20  # seconds

# Collect output for timeout seconds
while time.time() - start_time < timeout:
    # Check BSC output (non-blocking)
    try:
        line = bsc_proc.stdout.readline()
        if line:
            print(f"[BSC] {line.strip()}")
    except:
        pass

    # Check Moralis output (non-blocking)
    try:
        line = moralis_proc.stdout.readline()
        if line:
            print(f"[MORALIS] {line.strip()}")
    except:
        pass

    time.sleep(0.1)

print("\n" + "-" * 60)
print("Terminating monitors...")

# Terminate processes
bsc_proc.terminate()
moralis_proc.terminate()

# Give them time to cleanup
time.sleep(2)

# Force kill if still running
if bsc_proc.poll() is None:
    bsc_proc.kill()
if moralis_proc.poll() is None:
    moralis_proc.kill()

print("\nChecking database for new data...")

import asyncio
import asyncpg

async def check_data():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])

    # Check BSC data
    bsc_latest = await conn.fetchrow("""
        SELECT timestamp, token0_reserve, token1_reserve, total_liquidity_usd
        FROM bsc_pool_metrics
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    if bsc_latest:
        age = (datetime.now() - bsc_latest['timestamp'].replace(tzinfo=None)).total_seconds()
        print(f"\n[BSC] Latest record: {bsc_latest['timestamp']}")
        print(f"      Age: {age:.0f} seconds")
        print(f"      BTCB: {bsc_latest['token0_reserve']:.6f}")
        print(f"      USDT: {bsc_latest['token1_reserve']:.0f}")
    else:
        print("\n[BSC] No data found")

    # Check Moralis data
    moralis_latest = await conn.fetchrow("""
        SELECT timestamp, liquidity_usd, total_volume_24h
        FROM moralis_pair_stats_correct
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    if moralis_latest:
        age = (datetime.now() - moralis_latest['timestamp'].replace(tzinfo=None)).total_seconds()
        print(f"\n[MORALIS] Latest record: {moralis_latest['timestamp']}")
        print(f"          Age: {age:.0f} seconds")
        print(f"          Liquidity: ${moralis_latest['liquidity_usd']:,.0f}")
        print(f"          Volume 24h: ${moralis_latest['total_volume_24h']:,.0f}")
    else:
        print("\n[MORALIS] No data found")

    await conn.close()

asyncio.run(check_data())

print("\nTest complete!")
print("=" * 60)