#!/usr/bin/env python3
"""
Verify Railway database structure matches Docker database
"""

import psycopg2
import sys

# Railway connection details
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def verify_railway_database():
    """Verify Railway database structure"""
    try:
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()

        print("="*60)
        print("Railway Database Verification")
        print("="*60)

        # Get table count
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        table_count = cur.fetchone()[0]
        print(f"\nTotal Tables: {table_count}")

        # Get all tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()

        expected_tables = [
            'bsc_liquidity_events', 'bsc_pool_metrics', 'bsc_trades', 'bsc_wallet_metrics',
            'chain_stats', 'dex_trades', 'liquidity_pools', 'manipulation_alerts',
            'market_manipulation_alerts', 'moralis_historical_holders',
            'moralis_historical_holders_correct', 'moralis_historical_holders_enhanced',
            'moralis_holder_distribution', 'moralis_holder_stats_complete',
            'moralis_holder_stats_correct', 'moralis_holders', 'moralis_liquidity_changes',
            'moralis_metrics_summary', 'moralis_pair_stats', 'moralis_pair_stats_correct',
            'moralis_pair_stats_enhanced', 'moralis_snipers_complete', 'moralis_snipers_correct',
            'moralis_snipers_enhanced', 'moralis_stats', 'moralis_swaps', 'moralis_swaps_correct',
            'moralis_swaps_enhanced', 'moralis_token_analytics', 'moralis_token_analytics_correct',
            'moralis_token_analytics_enhanced', 'moralis_token_holder_stats', 'moralis_token_stats',
            'moralis_token_stats_simple', 'moralis_token_transfers', 'moralis_top_gainers',
            'moralis_transfers', 'token_distribution', 'token_prices', 'wallet_activity',
            'wallet_pnl', 'wash_trade_suspects', 'wash_trading_alerts', 'wash_trading_complete'
        ]

        actual_tables = [t[0] for t in tables]

        print("\n--- Core Tables Status ---")
        for table in expected_tables:
            if table in actual_tables:
                print(f"[OK] {table}")
            else:
                print(f"[MISSING] {table}")

        # Check for extra tables
        extra_tables = set(actual_tables) - set(expected_tables)
        if extra_tables:
            print(f"\n--- Additional Tables Found ---")
            for table in extra_tables:
                print(f"  + {table}")

        # Get sequence count
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.sequences
            WHERE sequence_schema = 'public'
        """)
        seq_count = cur.fetchone()[0]
        print(f"\nSequences: {seq_count} (expected 43)")

        # Get index count
        cur.execute("""
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE schemaname = 'public'
        """)
        idx_count = cur.fetchone()[0]
        print(f"Indexes: {idx_count}")

        # Get constraint count
        cur.execute("""
            SELECT constraint_type, COUNT(*)
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
            GROUP BY constraint_type
            ORDER BY constraint_type
        """)
        constraints = cur.fetchall()
        print("\nConstraints:")
        for constraint_type, count in constraints:
            print(f"  {constraint_type}: {count}")

        # Check materialized views
        cur.execute("""
            SELECT matviewname
            FROM pg_matviews
            WHERE schemaname = 'public'
        """)
        matviews = cur.fetchall()
        if matviews:
            print("\nMaterialized Views:")
            for mv in matviews:
                print(f"  - {mv[0]}")
        else:
            print("\nMaterialized Views: None")

        # Sample table structure check
        print("\n--- Sample Table Structure Check ---")
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'dex_trades'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        print("\ndex_trades table columns:")
        for col in columns:
            col_name, data_type, char_max, num_prec, num_scale = col
            if data_type == 'character varying':
                print(f"  {col_name}: VARCHAR({char_max})")
            elif data_type == 'numeric':
                print(f"  {col_name}: DECIMAL({num_prec},{num_scale})")
            else:
                print(f"  {col_name}: {data_type.upper()}")

        # Final status
        missing_count = len(set(expected_tables) - set(actual_tables))
        if missing_count == 0:
            print("\n" + "="*60)
            print("SUCCESS: All expected tables are present!")
            print("Railway database matches Docker database schema")
            print("="*60)
        else:
            print("\n" + "="*60)
            print(f"WARNING: {missing_count} expected tables are missing")
            print("="*60)

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_railway_database()