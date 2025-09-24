#!/usr/bin/env python3
"""
Test script to verify Railway deployment will work correctly
"""

import os
import psycopg2
import sys

# Test with the Railway database URL
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def test_connection():
    """Test database connection and tables"""
    print("="*60)
    print("Railway Deployment Readiness Test")
    print("="*60)

    try:
        # Connect to Railway database
        print("\n1. Testing database connection...")
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()
        print("   [OK] Connected to Railway database")

        # Check PostgreSQL version
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"   [OK] PostgreSQL version: {version.split(',')[0]}")

        # Check required tables for monitors
        print("\n2. Checking required tables...")
        required_tables = [
            'bsc_pool_metrics',
            'bsc_trades',
            'bsc_liquidity_events',
            'bsc_wallet_metrics',
            'moralis_swaps_enhanced',
            'moralis_holder_distribution',
            'moralis_token_analytics_enhanced',
            'moralis_pair_stats_enhanced'
        ]

        missing_tables = []
        for table in required_tables:
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()[0]
            if exists:
                # Get row count
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"   [OK] {table}: {count} rows")
            else:
                missing_tables.append(table)
                print(f"   [MISSING] {table}: MISSING")

        # Test data insertion
        print("\n3. Testing data insertion...")
        try:
            # Test insert into bsc_pool_metrics
            cur.execute("""
                INSERT INTO bsc_pool_metrics (
                    pool_address, token0_reserve, token1_reserve,
                    total_liquidity_usd, tvl, price_btcb_usdt,
                    pool_ratio, lp_token_supply
                ) VALUES (
                    '0xtest', 1000, 2000, 3000, 3000, 100000,
                    0.5, 1500
                ) RETURNING id
            """)
            test_id = cur.fetchone()[0]
            print(f"   [OK] Can insert into bsc_pool_metrics (test id: {test_id})")

            # Rollback test insert
            conn.rollback()
            print("   [OK] Test insert rolled back")

        except Exception as e:
            print(f"   [MISSING] Insert test failed: {e}")
            conn.rollback()

        # Check current data status
        print("\n4. Current data status:")
        for table in ['bsc_pool_metrics', 'moralis_swaps_enhanced']:
            try:
                cur.execute(f"SELECT MAX(timestamp) FROM {table}")
                latest = cur.fetchone()[0]
                if latest:
                    print(f"   {table} latest: {latest}")
                else:
                    print(f"   {table}: No data yet")
            except:
                pass

        # Summary
        print("\n" + "="*60)
        if missing_tables:
            print("[WARNING] WARNING: Some tables are missing!")
            print("The deployment might fail. Run migration first.")
        else:
            print("[SUCCESS] Railway deployment ready!")
            print("\nTo deploy:")
            print("1. Commit changes: git add . && git commit -m 'message'")
            print("2. Push to GitHub: git push")
            print("3. Railway will auto-deploy from GitHub")

        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Cannot connect to Railway database!")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()