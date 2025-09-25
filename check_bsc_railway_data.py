"""Check recent BSC monitor data in Railway database"""

import asyncio
import asyncpg
from datetime import datetime, timedelta

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

async def check_bsc_data():
    """Check recent BSC monitor data in Railway"""

    conn = None
    try:
        print("Connecting to Railway database...")
        conn = await asyncpg.connect(RAILWAY_URL)

        # Get current time
        now = datetime.utcnow()
        print(f"\nCurrent UTC time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Check BSC pool metrics
        print("\n1. BSC Pool Metrics (last 5 records):")
        rows = await conn.fetch("""
            SELECT timestamp, btcb_reserve, usdt_reserve, total_liquidity_usd,
                   volume_24h, price_btcb_usdt
            FROM bsc_pool_metrics
            ORDER BY timestamp DESC
            LIMIT 5
        """)

        if rows:
            for row in rows:
                time_diff = now - row['timestamp'].replace(tzinfo=None)
                hours_ago = time_diff.total_seconds() / 3600
                print(f"  {row['timestamp']} ({hours_ago:.1f}h ago)")
                print(f"    Liquidity: ${row['total_liquidity_usd']:,.0f}")
                print(f"    Volume 24h: ${row['volume_24h']:,.0f}")
                print(f"    BTCB: {row['btcb_reserve']:.4f}, USDT: {row['usdt_reserve']:,.0f}")
        else:
            print("  No data found")

        # Check BSC transactions
        print("\n2. BSC Transactions (last 5):")
        rows = await conn.fetch("""
            SELECT timestamp, tx_hash, swap_type, amount_in, amount_out,
                   price_impact, total_value_usd
            FROM bsc_transactions
            ORDER BY timestamp DESC
            LIMIT 5
        """)

        if rows:
            for row in rows:
                time_diff = now - row['timestamp'].replace(tzinfo=None)
                mins_ago = time_diff.total_seconds() / 60
                print(f"  {row['timestamp']} ({mins_ago:.0f}m ago)")
                print(f"    TX: {row['tx_hash'][:10]}...")
                print(f"    Type: {row['swap_type']}, Value: ${row['total_value_usd']:,.0f}")
        else:
            print("  No data found")

        # Check BSC wallet metrics
        print("\n3. BSC Wallet Metrics (count by type):")
        rows = await conn.fetch("""
            SELECT wallet_type, COUNT(*) as count, MAX(last_updated) as latest
            FROM bsc_wallet_metrics
            GROUP BY wallet_type
        """)

        if rows:
            for row in rows:
                if row['latest']:
                    time_diff = now - row['latest'].replace(tzinfo=None)
                    hours_ago = time_diff.total_seconds() / 3600
                    print(f"  {row['wallet_type']}: {row['count']} wallets (latest: {hours_ago:.1f}h ago)")
                else:
                    print(f"  {row['wallet_type']}: {row['count']} wallets")
        else:
            print("  No data found")

        # Check LP token tables (new)
        print("\n4. LP Token Transfers (last 5):")
        rows = await conn.fetch("""
            SELECT timestamp, transfer_type, lp_amount, total_value_usd
            FROM bsc_lp_token_transfers
            ORDER BY timestamp DESC
            LIMIT 5
        """)

        if rows:
            for row in rows:
                time_diff = now - row['timestamp'].replace(tzinfo=None)
                hours_ago = time_diff.total_seconds() / 3600
                print(f"  {row['timestamp']} ({hours_ago:.1f}h ago)")
                print(f"    Type: {row['transfer_type']}, Amount: {row['lp_amount']:.6f}")
                print(f"    Value: ${row['total_value_usd']:,.0f}")
        else:
            print("  No LP token transfers found")

        # Check last successful run
        print("\n5. Latest Data Summary:")

        # Get last pool metrics update
        last_pool = await conn.fetchval("""
            SELECT MAX(timestamp) FROM bsc_pool_metrics
        """)

        # Get last transaction
        last_tx = await conn.fetchval("""
            SELECT MAX(timestamp) FROM bsc_transactions
        """)

        # Get last wallet update
        last_wallet = await conn.fetchval("""
            SELECT MAX(last_updated) FROM bsc_wallet_metrics
        """)

        if last_pool:
            time_diff = now - last_pool.replace(tzinfo=None)
            hours_ago = time_diff.total_seconds() / 3600
            print(f"  Last pool metrics: {last_pool} ({hours_ago:.1f} hours ago)")
            if hours_ago > 1:
                print(f"    [WARNING] No updates for {hours_ago:.1f} hours!")

        if last_tx:
            time_diff = now - last_tx.replace(tzinfo=None)
            mins_ago = time_diff.total_seconds() / 60
            print(f"  Last transaction: {last_tx} ({mins_ago:.0f} minutes ago)")

        if last_wallet:
            time_diff = now - last_wallet.replace(tzinfo=None)
            hours_ago = time_diff.total_seconds() / 3600
            print(f"  Last wallet update: {last_wallet} ({hours_ago:.1f} hours ago)")

        # Check if monitoring is working
        print("\n6. Monitoring Status:")
        if last_pool:
            time_since_update = (now - last_pool.replace(tzinfo=None)).total_seconds() / 3600
            if time_since_update < 0.5:
                print("  [OK] BSC monitoring is ACTIVE and updating")
            elif time_since_update < 2:
                print("  [WARNING] BSC monitoring may be delayed")
            else:
                print(f"  [ERROR] BSC monitoring appears to be STOPPED ({time_since_update:.1f} hours since last update)")
                print("  The fix should restore monitoring within a few minutes...")
        else:
            print("  [ERROR] No BSC monitoring data found")

    except Exception as e:
        print(f"\n[ERROR] Failed to check database: {e}")

    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_bsc_data())