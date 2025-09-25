"""Check all monitoring data in Railway database"""

import asyncio
import asyncpg
from datetime import datetime, timedelta

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

async def check_all_monitors():
    conn = None
    try:
        print("Checking ALL Monitor Status in Railway Database")
        print("=" * 70)
        conn = await asyncpg.connect(RAILWAY_URL)

        now = datetime.utcnow()
        print(f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current UTC+4:   {(now + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Define all monitored tables
        monitor_tables = [
            # BSC Monitor tables
            ("bsc_pool_metrics", "timestamp", "BSC Pool Monitor"),
            ("bsc_trades", "timestamp", "BSC Trade Monitor"),
            ("bsc_wallet_metrics", "last_updated", "BSC Wallet Monitor"),
            ("bsc_liquidity_events", "timestamp", "BSC Liquidity Monitor"),

            # Moralis Monitor tables
            ("moralis_pair_stats_correct", "timestamp", "Moralis Pair Stats"),
            ("moralis_holder_stats", "timestamp", "Moralis Holder Stats"),
            ("moralis_profitable_traders", "timestamp", "Moralis Profitable Traders"),
            ("moralis_top_100_holders", "timestamp", "Moralis Top 100 Holders"),
        ]

        print("Monitor Status:")
        print("-" * 70)

        all_status = []

        for table_name, time_column, monitor_name in monitor_tables:
            try:
                # Get latest record
                query = f"SELECT MAX({time_column}) as latest FROM {table_name}"
                latest = await conn.fetchval(query)

                # Get record count
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count = await conn.fetchval(count_query)

                # Get count in last 24 hours
                recent_query = f"""
                    SELECT COUNT(*)
                    FROM {table_name}
                    WHERE {time_column} > NOW() - INTERVAL '24 hours'
                """
                recent_count = await conn.fetchval(recent_query)

                if latest:
                    time_diff = now - latest.replace(tzinfo=None)
                    hours_ago = time_diff.total_seconds() / 3600
                    mins_ago = time_diff.total_seconds() / 60

                    status = "[RUNNING]" if hours_ago < 1 else "[DELAYED]" if hours_ago < 6 else "[STOPPED]"

                    print(f"\n{monitor_name}:")
                    print(f"  Status: {status}")
                    print(f"  Latest: {latest.strftime('%Y-%m-%d %H:%M:%S')} ({hours_ago:.1f}h ago)")
                    print(f"  Total records: {count:,}")
                    print(f"  Last 24h: {recent_count:,} records")

                    all_status.append({
                        "monitor": monitor_name,
                        "status": status,
                        "hours_ago": hours_ago,
                        "latest": latest
                    })
                else:
                    print(f"\n{monitor_name}:")
                    print(f"  Status: [NO DATA]")
                    print(f"  Total records: {count:,}")

                    all_status.append({
                        "monitor": monitor_name,
                        "status": "[NO DATA]",
                        "hours_ago": 999,
                        "latest": None
                    })

            except Exception as e:
                print(f"\n{monitor_name}:")
                print(f"  Status: [ERROR] - {str(e)[:50]}")

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY:")
        print("-" * 70)

        # Group by status
        running = [s for s in all_status if "RUNNING" in s["status"]]
        delayed = [s for s in all_status if "DELAYED" in s["status"]]
        stopped = [s for s in all_status if "STOPPED" in s["status"] or "NO DATA" in s["status"]]

        print(f"[OK] Running: {len(running)} monitors")
        for s in running:
            print(f"   - {s['monitor']}")

        print(f"\n[WARNING] Delayed: {len(delayed)} monitors")
        for s in delayed:
            print(f"   - {s['monitor']} (last update {s['hours_ago']:.1f}h ago)")

        print(f"\n[FAILED] Stopped: {len(stopped)} monitors")
        for s in stopped:
            if s['latest']:
                print(f"   - {s['monitor']} (stopped {s['hours_ago']:.1f}h ago)")
            else:
                print(f"   - {s['monitor']} (no data)")

        # Timeline analysis
        print("\n" + "=" * 70)
        print("TIMELINE ANALYSIS:")
        print("-" * 70)

        # Sort by latest update time
        active_monitors = [s for s in all_status if s['latest']]
        active_monitors.sort(key=lambda x: x['latest'], reverse=True)

        print("\nLast updates (most recent first):")
        for s in active_monitors[:10]:
            time_str = s['latest'].strftime('%Y-%m-%d %H:%M:%S')
            utc4_time = (s['latest'] + timedelta(hours=4)).strftime('%H:%M:%S')
            print(f"  {time_str} UTC ({utc4_time} UTC+4) - {s['monitor']}")

        # Find when monitors stopped
        if stopped:
            print("\n[ALERT] Monitors that stopped:")
            for s in stopped:
                if s['latest']:
                    stop_time = s['latest']
                    utc4_stop = (stop_time + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {s['monitor']}: Stopped at {utc4_stop} UTC+4")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_all_monitors())