#!/usr/bin/env python3
"""
Automated migration script to recreate Railway database with Docker database schema
"""

import psycopg2
from psycopg2 import sql
import sys
import os
from datetime import datetime

# Railway connection details
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def connect_to_railway():
    """Connect to Railway PostgreSQL database"""
    try:
        conn = psycopg2.connect(RAILWAY_URL)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"Error connecting to Railway database: {e}")
        sys.exit(1)

def backup_existing_tables(conn):
    """List existing tables in Railway database (for reference)"""
    print("\n=== Checking existing Railway database tables ===")
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()

        if tables:
            print(f"Found {len(tables)} existing tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("No existing tables found in Railway database")

        cur.close()
        return tables
    except Exception as e:
        print(f"Error checking existing tables: {e}")
        return []

def drop_all_objects(conn):
    """Drop all existing database objects"""
    print("\n=== Dropping all existing database objects ===")

    drop_statements = [
        # Drop materialized views first
        "DROP MATERIALIZED VIEW IF EXISTS hourly_dex_stats CASCADE",
        "DROP MATERIALIZED VIEW IF EXISTS top_pairs_24h CASCADE",

        # Drop all tables with CASCADE to handle any dependencies
        "DROP TABLE IF EXISTS bsc_liquidity_events CASCADE",
        "DROP TABLE IF EXISTS bsc_pool_metrics CASCADE",
        "DROP TABLE IF EXISTS bsc_trades CASCADE",
        "DROP TABLE IF EXISTS bsc_wallet_metrics CASCADE",
        "DROP TABLE IF EXISTS chain_stats CASCADE",
        "DROP TABLE IF EXISTS dex_trades CASCADE",
        "DROP TABLE IF EXISTS liquidity_pools CASCADE",
        "DROP TABLE IF EXISTS manipulation_alerts CASCADE",
        "DROP TABLE IF EXISTS market_manipulation_alerts CASCADE",
        "DROP TABLE IF EXISTS moralis_historical_holders CASCADE",
        "DROP TABLE IF EXISTS moralis_historical_holders_correct CASCADE",
        "DROP TABLE IF EXISTS moralis_historical_holders_enhanced CASCADE",
        "DROP TABLE IF EXISTS moralis_holder_distribution CASCADE",
        "DROP TABLE IF EXISTS moralis_holder_stats_complete CASCADE",
        "DROP TABLE IF EXISTS moralis_holder_stats_correct CASCADE",
        "DROP TABLE IF EXISTS moralis_holders CASCADE",
        "DROP TABLE IF EXISTS moralis_liquidity_changes CASCADE",
        "DROP TABLE IF EXISTS moralis_metrics_summary CASCADE",
        "DROP TABLE IF EXISTS moralis_pair_stats CASCADE",
        "DROP TABLE IF EXISTS moralis_pair_stats_correct CASCADE",
        "DROP TABLE IF EXISTS moralis_pair_stats_enhanced CASCADE",
        "DROP TABLE IF EXISTS moralis_snipers_complete CASCADE",
        "DROP TABLE IF EXISTS moralis_snipers_correct CASCADE",
        "DROP TABLE IF EXISTS moralis_snipers_enhanced CASCADE",
        "DROP TABLE IF EXISTS moralis_stats CASCADE",
        "DROP TABLE IF EXISTS moralis_swaps CASCADE",
        "DROP TABLE IF EXISTS moralis_swaps_correct CASCADE",
        "DROP TABLE IF EXISTS moralis_swaps_enhanced CASCADE",
        "DROP TABLE IF EXISTS moralis_token_analytics CASCADE",
        "DROP TABLE IF EXISTS moralis_token_analytics_correct CASCADE",
        "DROP TABLE IF EXISTS moralis_token_analytics_enhanced CASCADE",
        "DROP TABLE IF EXISTS moralis_token_holder_stats CASCADE",
        "DROP TABLE IF EXISTS moralis_token_stats CASCADE",
        "DROP TABLE IF EXISTS moralis_token_stats_simple CASCADE",
        "DROP TABLE IF EXISTS moralis_token_transfers CASCADE",
        "DROP TABLE IF EXISTS moralis_top_gainers CASCADE",
        "DROP TABLE IF EXISTS moralis_transfers CASCADE",
        "DROP TABLE IF EXISTS token_distribution CASCADE",
        "DROP TABLE IF EXISTS token_prices CASCADE",
        "DROP TABLE IF EXISTS wallet_activity CASCADE",
        "DROP TABLE IF EXISTS wallet_pnl CASCADE",
        "DROP TABLE IF EXISTS wash_trade_suspects CASCADE",
        "DROP TABLE IF EXISTS wash_trading_alerts CASCADE",
        "DROP TABLE IF EXISTS wash_trading_complete CASCADE",

        # Drop functions
        "DROP FUNCTION IF EXISTS refresh_materialized_views() CASCADE",
    ]

    try:
        cur = conn.cursor()
        for statement in drop_statements:
            print(f"  Executing: {statement[:50]}...")
            cur.execute(statement)

        conn.commit()
        print("Successfully dropped all existing objects")
        cur.close()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error dropping objects: {e}")
        return False

def execute_schema_file(conn, schema_file):
    """Execute the schema SQL file"""
    print(f"\n=== Executing schema from {schema_file} ===")

    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        cur = conn.cursor()
        cur.execute(schema_sql)
        conn.commit()
        print("Successfully executed schema file")
        cur.close()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error executing schema: {e}")
        print(f"Error details: {str(e)[:500]}")
        return False

def verify_tables_created(conn):
    """Verify that all tables were created successfully"""
    print("\n=== Verifying created tables ===")

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

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        created_tables = [row[0] for row in cur.fetchall()]

        print(f"\nCreated {len(created_tables)} tables:")
        for table in created_tables:
            print(f"  ✓ {table}")

        missing_tables = set(expected_tables) - set(created_tables)
        extra_tables = set(created_tables) - set(expected_tables)

        if missing_tables:
            print(f"\n⚠ WARNING: Missing tables: {missing_tables}")
        if extra_tables:
            print(f"\n⚠ Note: Additional tables found: {extra_tables}")

        if not missing_tables:
            print("\n✓ All expected tables created successfully!")

        # Check sequences
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.sequences
            WHERE sequence_schema = 'public'
        """)
        seq_count = cur.fetchone()[0]
        print(f"\n✓ Created {seq_count} sequences (expected ~43)")

        # Check indexes
        cur.execute("""
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE schemaname = 'public'
        """)
        idx_count = cur.fetchone()[0]
        print(f"✓ Created {idx_count} indexes")

        # Check constraints
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
        """)
        const_count = cur.fetchone()[0]
        print(f"✓ Created {const_count} constraints")

        cur.close()
        return len(missing_tables) == 0
    except Exception as e:
        print(f"Error verifying tables: {e}")
        return False

def main():
    print("="*60)
    print("Railway Database Migration Script (Automated)")
    print("="*60)
    print(f"Target: {RAILWAY_URL.split('@')[1]}")  # Show host without password
    print(f"Time: {datetime.now()}")

    # Check if schema file exists
    schema_file = 'docker_schema_clean.sql'
    if not os.path.exists(schema_file):
        print(f"\nERROR: {schema_file} not found!")
        print("Please ensure the schema dump file exists.")
        sys.exit(1)

    print("\n" + "="*60)
    print("Starting automatic migration...")
    print("="*60)

    # Connect to Railway
    conn = connect_to_railway()

    try:
        # Show existing tables
        existing_tables = backup_existing_tables(conn)

        # Drop all objects
        if not drop_all_objects(conn):
            print("\n❌ Failed to drop existing objects. Aborting.")
            sys.exit(1)

        # Execute new schema
        if not execute_schema_file(conn, schema_file):
            print("\n❌ Failed to create new schema. Aborting.")
            sys.exit(1)

        # Verify creation
        if verify_tables_created(conn):
            print("\n" + "="*60)
            print("✅ SUCCESS: Railway database recreated with Docker schema!")
            print("="*60)
        else:
            print("\n⚠ Warning: Some tables may be missing. Please verify manually.")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()