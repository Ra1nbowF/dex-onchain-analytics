"""Check LP activity and transfer data in local database"""

import asyncio
import asyncpg
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

async def check_lp_data():
    conn = None
    try:
        print("Checking LP Activity and Transfer Data in Local Database")
        print("=" * 70)
        conn = await asyncpg.connect(DATABASE_URL)

        now = datetime.utcnow()
        print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

        # 1. Check bsc_liquidity_events (for Add/Remove liquidity)
        print("1. Liquidity Pool Activity (bsc_liquidity_events):")
        print("-" * 50)
        count = await conn.fetchval("SELECT COUNT(*) FROM bsc_liquidity_events")
        print(f"   Total records: {count}")

        if count > 0:
            recent = await conn.fetch("""
                SELECT event_type, provider_address, btcb_amount, usdt_amount, timestamp
                FROM bsc_liquidity_events
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            print("   Recent events:")
            for r in recent:
                print(f"     {r['timestamp']}: {r['event_type']} - BTCB: {r['btcb_amount']:.4f}, USDT: {r['usdt_amount']:.0f}")
        else:
            print("   [NO DATA] - Table is empty")

        # 2. Check bsc_lp_token_transfers (LP token transfers)
        print("\n2. LP Token Transfers (bsc_lp_token_transfers):")
        print("-" * 50)
        count = await conn.fetchval("SELECT COUNT(*) FROM bsc_lp_token_transfers")
        print(f"   Total records: {count}")

        if count > 0:
            recent = await conn.fetch("""
                SELECT transfer_type, from_address, to_address, lp_amount, total_value_usd, timestamp
                FROM bsc_lp_token_transfers
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            print("   Recent transfers:")
            for r in recent:
                print(f"     {r['timestamp']}: {r['transfer_type']} - Amount: {r['lp_amount']:.6f}, Value: ${r['total_value_usd']:.0f}")
        else:
            print("   [NO DATA] - Table is empty")

        # 3. Check bsc_lp_holders (Top LP providers)
        print("\n3. Top Liquidity Providers (bsc_lp_holders):")
        print("-" * 50)
        count = await conn.fetchval("SELECT COUNT(*) FROM bsc_lp_holders")
        print(f"   Total records: {count}")

        if count > 0:
            top_holders = await conn.fetch("""
                SELECT wallet_address, lp_balance, pool_share_percent, total_value_usd
                FROM bsc_lp_holders
                ORDER BY lp_balance DESC
                LIMIT 5
            """)
            print("   Top holders:")
            for h in top_holders:
                print(f"     {h['wallet_address'][:10]}...: {h['lp_balance']:.4f} LP ({h['pool_share_percent']:.2f}%) - ${h['total_value_usd']:.0f}")
        else:
            print("   [NO DATA] - Table is empty")

        # 4. Check bsc_token_transfers (Token transfers)
        print("\n4. Recent Token Transfers (bsc_token_transfers):")
        print("-" * 50)
        count = await conn.fetchval("SELECT COUNT(*) FROM bsc_token_transfers")
        print(f"   Total records: {count}")

        if count > 0:
            recent = await conn.fetch("""
                SELECT token_symbol, from_address, to_address, amount, value_usd, transfer_type, timestamp
                FROM bsc_token_transfers
                WHERE is_pool_related = TRUE
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            print("   Recent pool-related transfers:")
            for r in recent:
                print(f"     {r['timestamp']}: {r['token_symbol']} {r['transfer_type']} - {r['amount']:.4f} (${r['value_usd']:.0f})")
        else:
            print("   [NO DATA] - Table is empty")

        # 5. Check bsc_trades (swap events)
        print("\n5. Swap Events (bsc_trades):")
        print("-" * 50)
        count = await conn.fetchval("SELECT COUNT(*) FROM bsc_trades")
        print(f"   Total records: {count}")

        if count > 0:
            recent = await conn.fetch("""
                SELECT trader_address, token_in, token_out, amount_in, amount_out, timestamp
                FROM bsc_trades
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            print("   Recent trades:")
            for r in recent:
                print(f"     {r['timestamp']}: {r['token_in'][:4]} -> {r['token_out'][:4]}")
        else:
            print("   [NO DATA] - Table is empty")

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY:")

        # Check which methods are being called
        print("\nChecking if BSC monitor methods are running...")

        # Get last bsc_pool_metrics update
        last_pool_update = await conn.fetchval("SELECT MAX(timestamp) FROM bsc_pool_metrics")
        if last_pool_update:
            age = (now - last_pool_update.replace(tzinfo=None)).total_seconds() / 60
            print(f"✅ Pool metrics updating (last: {age:.0f} min ago)")
        else:
            print("❌ Pool metrics not updating")

        print("\nData collection status:")
        tables_status = {
            "bsc_liquidity_events": await conn.fetchval("SELECT COUNT(*) FROM bsc_liquidity_events"),
            "bsc_lp_token_transfers": await conn.fetchval("SELECT COUNT(*) FROM bsc_lp_token_transfers"),
            "bsc_lp_holders": await conn.fetchval("SELECT COUNT(*) FROM bsc_lp_holders"),
            "bsc_token_transfers": await conn.fetchval("SELECT COUNT(*) FROM bsc_token_transfers"),
            "bsc_trades": await conn.fetchval("SELECT COUNT(*) FROM bsc_trades")
        }

        for table, count in tables_status.items():
            status = "❌ EMPTY" if count == 0 else f"✅ {count} records"
            print(f"  {table}: {status}")

        if all(count == 0 for count in tables_status.values()):
            print("\n[ISSUE] All LP/transfer tables are empty!")
            print("Possible causes:")
            print("1. The fetch methods for these events are not being called")
            print("2. The API endpoints for fetching events are failing")
            print("3. There's genuinely no activity (unlikely for a $10M pool)")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_lp_data())