#!/usr/bin/env python3
"""
Check if data is being populated in Railway database
"""

import psycopg2
from datetime import datetime, timedelta
import sys

# Railway connection details
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def check_railway_data():
    """Check data in Railway database"""
    try:
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()

        print("="*70)
        print("Railway Database Data Check")
        print("="*70)
        print(f"Timestamp: {datetime.now()}\n")

        # Tables to check with their timestamp columns
        tables_to_check = [
            ('dex_trades', 'timestamp'),
            ('liquidity_pools', 'timestamp'),
            ('token_prices', 'timestamp'),
            ('chain_stats', 'timestamp'),
            ('wallet_activity', 'timestamp'),
            ('wallet_pnl', 'timestamp'),
            ('bsc_trades', 'timestamp'),
            ('bsc_pool_metrics', 'timestamp'),
            ('bsc_liquidity_events', 'timestamp'),
            ('bsc_wallet_metrics', 'updated_at'),
            ('moralis_swaps', 'timestamp'),
            ('moralis_swaps_enhanced', 'timestamp'),
            ('moralis_holders', 'timestamp'),
            ('moralis_holder_distribution', 'timestamp'),
            ('moralis_token_analytics_enhanced', 'timestamp'),
            ('moralis_pair_stats_enhanced', 'timestamp'),
            ('market_manipulation_alerts', 'timestamp'),
            ('wash_trading_complete', 'timestamp'),
        ]

        print("TABLE DATA STATUS:")
        print("-" * 70)
        print(f"{'Table Name':<35} {'Row Count':>10} {'Latest Data':>25}")
        print("-" * 70)

        total_rows = 0
        tables_with_data = 0
        tables_with_recent_data = 0

        for table, timestamp_col in tables_to_check:
            try:
                # Get row count
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                total_rows += count

                # Get latest timestamp if table has data
                latest_str = "No data"
                if count > 0:
                    tables_with_data += 1
                    cur.execute(f"SELECT MAX({timestamp_col}) FROM {table}")
                    latest = cur.fetchone()[0]
                    if latest:
                        latest_str = latest.strftime("%Y-%m-%d %H:%M:%S")
                        # Check if data is recent (within last 24 hours)
                        if latest > datetime.now() - timedelta(days=1):
                            tables_with_recent_data += 1
                            latest_str += " *"

                print(f"{table:<35} {count:>10,} {latest_str:>25}")

            except Exception as e:
                print(f"{table:<35} {'ERROR':>10} {str(e)[:20]:>25}")

        print("-" * 70)
        print(f"{'TOTAL':.<35} {total_rows:>10,}")
        print()

        # Check specific high-volume tables
        print("\nDETAILED ANALYSIS:")
        print("-" * 70)

        # Check dex_trades details
        cur.execute("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(DISTINCT chain_id) as chains,
                COUNT(DISTINCT dex_name) as dexes,
                COUNT(DISTINCT DATE(timestamp)) as trading_days,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM dex_trades
        """)
        result = cur.fetchone()
        if result and result[0] > 0:
            print("\nDEX_TRADES Statistics:")
            print(f"  Total Trades: {result[0]:,}")
            print(f"  Unique Chains: {result[1]}")
            print(f"  Unique DEXes: {result[2]}")
            print(f"  Trading Days: {result[3]}")
            print(f"  Date Range: {result[4]} to {result[5]}")

            # Get recent activity
            cur.execute("""
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as trades,
                    SUM(value_usd) as volume
                FROM dex_trades
                WHERE timestamp > NOW() - INTERVAL '7 days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 7
            """)
            recent = cur.fetchall()
            if recent:
                print("\n  Last 7 Days Activity:")
                for date, trades, volume in recent:
                    volume_str = f"${volume:,.2f}" if volume else "$0"
                    print(f"    {date}: {trades:,} trades, {volume_str}")

        # Check moralis data
        cur.execute("""
            SELECT
                COUNT(*) as total_swaps,
                COUNT(DISTINCT wallet_address) as unique_wallets,
                MIN(block_timestamp) as earliest,
                MAX(block_timestamp) as latest
            FROM moralis_swaps_enhanced
        """)
        result = cur.fetchone()
        if result and result[0] > 0:
            print("\nMORALIS_SWAPS_ENHANCED Statistics:")
            print(f"  Total Swaps: {result[0]:,}")
            print(f"  Unique Wallets: {result[1]:,}")
            print(f"  Date Range: {result[2]} to {result[3]}")

        # Summary
        print("\n" + "="*70)
        print("SUMMARY:")
        print(f"  Tables with data: {tables_with_data}/{len(tables_to_check)}")
        print(f"  Tables with recent data (24h): {tables_with_recent_data}")
        print(f"  Total rows across all tables: {total_rows:,}")

        if tables_with_recent_data > 0:
            print("\n  STATUS: Data is actively flowing into Railway database!")
        elif tables_with_data > 0:
            print("\n  STATUS: Historical data present but no recent updates.")
        else:
            print("\n  STATUS: No data found. Database is empty.")

        print("="*70)

        # Check if collectors are configured for Railway
        print("\nCHECKING DATA COLLECTION CONFIGURATION:")
        print("-" * 70)

        # Note about configuration
        print("To enable data collection to Railway, ensure:")
        print("1. Update DATABASE_URL in docker-compose.yml or .env files")
        print("2. Restart data collectors with Railway connection string")
        print("3. Check collector logs for connection status")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error connecting to Railway: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_railway_data()