"""Check BSC monitoring status in Railway database"""

import asyncio
import asyncpg
from datetime import datetime, timedelta

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

async def check_monitoring_status():
    conn = None
    try:
        print("Checking BSC Monitoring Status in Railway Database")
        print("=" * 60)
        conn = await asyncpg.connect(RAILWAY_URL)

        now = datetime.utcnow()
        print(f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current UTC+4:   {(now + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Check BSC pool metrics
        print("BSC Pool Metrics:")
        print("-" * 40)

        # Get latest records
        rows = await conn.fetch("""
            SELECT timestamp, token0_reserve, token1_reserve,
                   total_liquidity_usd, price_btcb_usdt
            FROM bsc_pool_metrics
            ORDER BY timestamp DESC
            LIMIT 10
        """)

        if rows:
            # Show latest
            latest = rows[0]
            time_diff = now - latest['timestamp'].replace(tzinfo=None)
            hours_ago = time_diff.total_seconds() / 3600
            mins_ago = time_diff.total_seconds() / 60

            print(f"Latest record: {latest['timestamp']}")
            print(f"Time since last update: {hours_ago:.1f} hours ({mins_ago:.0f} minutes)")
            print(f"BTCB Reserve: {latest['token0_reserve']:.6f}")
            print(f"USDT Reserve: {latest['token1_reserve']:,.2f}")
            print(f"Total Liquidity: ${latest['total_liquidity_usd']:,.0f}")
            print(f"BTCB/USDT Price: {latest['price_btcb_usdt']:,.2f}")

            # Show update frequency
            print(f"\nRecent updates (last 10):")
            prev_time = None
            for i, row in enumerate(rows):
                time_str = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                if prev_time:
                    gap = (prev_time - row['timestamp']).total_seconds() / 60
                    print(f"  {time_str} (gap: {gap:.0f} min)")
                else:
                    print(f"  {time_str} (latest)")
                prev_time = row['timestamp']

            # Analyze the outage
            print(f"\n[ANALYSIS]")
            stopped_at = rows[0]['timestamp'].replace(tzinfo=None)
            stopped_at_utc4 = stopped_at + timedelta(hours=4)

            print(f"Monitoring stopped at: {stopped_at} UTC")
            print(f"                       {stopped_at_utc4.strftime('%Y-%m-%d %H:%M:%S')} UTC+4")
            print(f"Downtime duration: {hours_ago:.1f} hours")

            if hours_ago > 1:
                print("\n[STATUS] BSC Monitor is DOWN")
                print("Expected fix: Should resume after Railway redeploys with web3 dependency")

                # Check if deployment might be in progress
                if mins_ago < 10:
                    print("[UPDATE] New data detected! Monitor may be recovering...")
                else:
                    print("[ACTION] Railway should auto-deploy the fix from GitHub")
                    print("         If not updating in 10 minutes, manual restart may be needed")
            else:
                print("\n[STATUS] BSC Monitor is RUNNING")

        else:
            print("No data found in bsc_pool_metrics table")

        # Count total records
        total = await conn.fetchval("SELECT COUNT(*) FROM bsc_pool_metrics")
        print(f"\nTotal records in database: {total}")

        # Check data gaps
        gaps = await conn.fetch("""
            WITH time_diffs AS (
                SELECT
                    timestamp,
                    LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp,
                    timestamp - LAG(timestamp) OVER (ORDER BY timestamp) as time_gap
                FROM bsc_pool_metrics
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            )
            SELECT timestamp, prev_timestamp, time_gap
            FROM time_diffs
            WHERE time_gap > INTERVAL '30 minutes'
            ORDER BY timestamp DESC
            LIMIT 5
        """)

        if gaps:
            print(f"\nRecent monitoring gaps (> 30 min):")
            for gap in gaps:
                gap_mins = gap['time_gap'].total_seconds() / 60
                print(f"  {gap['timestamp']} - Gap: {gap_mins:.0f} minutes")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_monitoring_status())