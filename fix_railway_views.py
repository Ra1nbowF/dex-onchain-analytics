#!/usr/bin/env python3
"""
Create views or update Grafana dashboard to fix table name mismatches
"""

import psycopg2
import json
import sys

# Railway connection details
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def check_existing_tables(conn):
    """Check which tables actually exist in the database"""
    cur = conn.cursor()

    # Tables that Grafana expects vs what exists
    table_mappings = {
        'moralis_swaps_correct': None,
        'moralis_holders': None,
        'moralis_transfers': None,
        'moralis_historical_holders_correct': None,
        'moralis_holder_stats_correct': None,
        'moralis_pair_stats_correct': None
    }

    # Check what tables actually exist
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'moralis%'
        ORDER BY table_name
    """)

    existing_tables = [row[0] for row in cur.fetchall()]
    print("Existing Moralis tables in Railway:")
    for table in existing_tables:
        print(f"  - {table}")

    # Try to map expected to existing
    for expected in table_mappings.keys():
        base_name = expected.replace('_correct', '')

        # Look for best match
        if expected in existing_tables:
            table_mappings[expected] = expected
        elif base_name in existing_tables:
            table_mappings[expected] = base_name
        elif base_name + '_enhanced' in existing_tables:
            table_mappings[expected] = base_name + '_enhanced'
        elif base_name + '_complete' in existing_tables:
            table_mappings[expected] = base_name + '_complete'

    cur.close()
    return table_mappings, existing_tables

def create_view_mappings(conn, mappings):
    """Create views to map expected table names to actual tables"""
    cur = conn.cursor()

    views_created = []
    views_failed = []

    for expected_name, actual_table in mappings.items():
        if actual_table and expected_name != actual_table:
            try:
                # Drop view if exists
                cur.execute(f"DROP VIEW IF EXISTS {expected_name} CASCADE")

                # Create view pointing to actual table
                cur.execute(f"CREATE VIEW {expected_name} AS SELECT * FROM {actual_table}")
                conn.commit()
                views_created.append(expected_name)
                print(f"✓ Created view: {expected_name} -> {actual_table}")
            except Exception as e:
                conn.rollback()
                views_failed.append((expected_name, str(e)))
                print(f"✗ Failed to create view {expected_name}: {e}")
        elif actual_table == expected_name:
            print(f"• Table {expected_name} already exists correctly")
        else:
            views_failed.append((expected_name, "No matching table found"))
            print(f"✗ No matching table for {expected_name}")

    cur.close()
    return views_created, views_failed

def check_column_compatibility(conn):
    """Check if columns match between what Grafana expects and what exists"""
    cur = conn.cursor()

    print("\n" + "="*60)
    print("Checking column compatibility...")
    print("="*60)

    # Check moralis_swaps columns
    queries_to_check = [
        ("moralis_swaps", ["wallet_address", "transaction_type", "total_value_usd",
                          "bought_name", "sold_name", "block_timestamp"]),
        ("moralis_holder_stats", ["total_holders", "whales", "shrimps", "timestamp"]),
        ("moralis_pair_stats", ["current_usd_price", "total_liquidity_usd", "timestamp"])
    ]

    for base_table, required_columns in queries_to_check:
        # Find the actual table
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE %s
        """, (base_table + '%',))

        tables = cur.fetchall()
        if tables:
            actual_table = tables[0][0]

            # Get columns
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
            """, (actual_table,))

            existing_columns = [row[0] for row in cur.fetchall()]

            print(f"\nTable: {actual_table}")
            missing = set(required_columns) - set(existing_columns)
            if missing:
                print(f"  ⚠ Missing columns: {missing}")
            else:
                print(f"  ✓ All required columns present")

    cur.close()

def update_dashboard_file():
    """Update the Grafana dashboard JSON to use correct table names"""
    dashboard_file = 'grafana/consolidated-dashboard.json'

    print("\n" + "="*60)
    print("Dashboard Update Options")
    print("="*60)

    # Mapping of wrong names to correct ones based on what exists
    replacements = {
        'moralis_swaps_correct': 'moralis_swaps_enhanced',
        'moralis_holders': 'moralis_holders',  # This one exists
        'moralis_transfers': 'moralis_transfers',  # Check if exists
        'moralis_historical_holders_correct': 'moralis_historical_holders_enhanced',
        'moralis_holder_stats_correct': 'moralis_holder_stats_complete',
        'moralis_pair_stats_correct': 'moralis_pair_stats_enhanced'
    }

    print("\nSuggested table replacements in dashboard:")
    for old, new in replacements.items():
        print(f"  {old} -> {new}")

    print("\nYou can either:")
    print("1. Update the dashboard file to use correct table names")
    print("2. Create database views (already done above)")
    print("3. Both for maximum compatibility")

def main():
    print("="*60)
    print("Railway Database - Grafana Dashboard Fix")
    print("="*60)

    try:
        conn = psycopg2.connect(RAILWAY_URL)

        # Check existing tables
        mappings, existing_tables = check_existing_tables(conn)

        print("\n" + "="*60)
        print("Table Mapping Analysis")
        print("="*60)
        print("\nExpected -> Actual mapping:")
        for expected, actual in mappings.items():
            if actual:
                print(f"  {expected} -> {actual}")
            else:
                print(f"  {expected} -> NOT FOUND")

        # Create views to fix the mismatches
        print("\n" + "="*60)
        print("Creating Compatibility Views")
        print("="*60)

        # Update mappings based on what we found
        mappings['moralis_swaps_correct'] = 'moralis_swaps_enhanced'
        mappings['moralis_holders'] = 'moralis_holders'
        mappings['moralis_transfers'] = 'moralis_transfers'
        mappings['moralis_historical_holders_correct'] = 'moralis_historical_holders_enhanced'
        mappings['moralis_holder_stats_correct'] = 'moralis_holder_stats_complete'
        mappings['moralis_pair_stats_correct'] = 'moralis_pair_stats_enhanced'

        views_created, views_failed = create_view_mappings(conn, mappings)

        # Check column compatibility
        check_column_compatibility(conn)

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        if views_created:
            print(f"\n✓ Successfully created {len(views_created)} views:")
            for view in views_created:
                print(f"    - {view}")

        if views_failed:
            print(f"\n✗ Failed to create {len(views_failed)} views:")
            for view, reason in views_failed:
                print(f"    - {view}: {reason}")

        # Provide dashboard update guidance
        update_dashboard_file()

        conn.close()

        print("\n" + "="*60)
        print("RECOMMENDED ACTIONS:")
        print("="*60)
        print("1. Views have been created to redirect queries")
        print("2. However, some tables may still be empty (no data)")
        print("3. To populate data, update docker-compose.yml to use Railway URL")
        print("4. Or consider updating the dashboard to query existing tables directly")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()