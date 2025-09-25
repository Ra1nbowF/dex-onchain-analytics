"""Fix missing constraints in Railway database"""

import psycopg2
import sys

# Railway database connection
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def fix_constraints():
    """Add missing unique constraints to tables"""
    conn = psycopg2.connect(RAILWAY_URL)
    cur = conn.cursor()

    print("Fixing missing constraints in Railway database...")
    print("="*60)

    constraints = [
        # Moralis tables
        ("moralis_transfers", "transaction_hash", "moralis_transfers_tx_hash_unique"),
        ("moralis_swaps_correct", "transaction_hash", "moralis_swaps_correct_tx_unique"),
        ("moralis_token_analytics_correct", "token_address", "moralis_token_analytics_correct_token_unique"),
        ("moralis_historical_holders_correct", "wallet_address, token_address", "moralis_holders_correct_wallet_token_unique"),

        # BSC tables
        ("bsc_pool_metrics", "pool_address, timestamp", "bsc_pool_metrics_pool_time_unique"),
        ("bsc_dex_trades", "tx_hash", "bsc_dex_trades_tx_unique"),
        ("bsc_pool_events", "tx_hash", "bsc_pool_events_tx_unique"),
    ]

    for table, columns, constraint_name in constraints:
        try:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table,))

            if not cur.fetchone()[0]:
                print(f"[SKIP] Table {table} does not exist")
                continue

            # Check if constraint already exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_constraint
                    WHERE conname = %s
                )
            """, (constraint_name,))

            if cur.fetchone()[0]:
                print(f"[EXISTS] Constraint {constraint_name} already exists")
                continue

            # Add the constraint
            sql = f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} UNIQUE ({columns})"
            cur.execute(sql)
            conn.commit()
            print(f"[OK] Added constraint {constraint_name} on {table}({columns})")

        except Exception as e:
            conn.rollback()
            if "already exists" in str(e):
                print(f"[EXISTS] Constraint on {table}({columns}) already exists")
            else:
                print(f"[ERROR] Failed to add constraint on {table}: {str(e)[:100]}")

    # Add indexes for performance
    print("\nAdding performance indexes...")
    print("="*60)

    indexes = [
        ("moralis_swaps_correct", "timestamp", "idx_moralis_swaps_correct_timestamp"),
        ("moralis_swaps_correct", "wallet_address", "idx_moralis_swaps_correct_wallet"),
        ("moralis_transfers", "from_address", "idx_moralis_transfers_from"),
        ("moralis_transfers", "to_address", "idx_moralis_transfers_to"),
        ("moralis_transfers", "timestamp", "idx_moralis_transfers_timestamp"),
        ("bsc_pool_metrics", "pool_address", "idx_bsc_pool_metrics_pool"),
    ]

    for table, column, index_name in indexes:
        try:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table,))

            if not cur.fetchone()[0]:
                print(f"[SKIP] Table {table} does not exist")
                continue

            # Check if index already exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = %s
                )
            """, (index_name,))

            if cur.fetchone()[0]:
                print(f"[EXISTS] Index {index_name} already exists")
                continue

            # Create the index
            sql = f"CREATE INDEX {index_name} ON {table}({column})"
            cur.execute(sql)
            conn.commit()
            print(f"[OK] Created index {index_name} on {table}({column})")

        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Failed to create index {index_name}: {str(e)[:100]}")

    print("\n" + "="*60)
    print("Constraint and index fixes complete!")

    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_constraints()