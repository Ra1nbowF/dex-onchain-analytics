"""Fix Railway database table issues"""

import psycopg2
import sys

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def fix_tables():
    """Fix table structures and constraints"""
    conn = psycopg2.connect(RAILWAY_URL)
    cur = conn.cursor()

    print("Fixing Railway database tables...")
    print("="*60)

    # 1. Fix moralis_transfers constraint
    try:
        # First check if constraint exists
        cur.execute("""
            SELECT conname FROM pg_constraint
            WHERE conname = 'moralis_transfers_tx_hash_unique'
        """)
        if cur.fetchone():
            print("[EXISTS] moralis_transfers unique constraint")
        else:
            # Remove duplicates first
            cur.execute("""
                DELETE FROM moralis_transfers
                WHERE ctid NOT IN (
                    SELECT MIN(ctid)
                    FROM moralis_transfers
                    GROUP BY transaction_hash
                )
            """)
            deleted = cur.rowcount
            print(f"[CLEAN] Removed {deleted} duplicate transfers")

            # Add constraint
            cur.execute("""
                ALTER TABLE moralis_transfers
                ADD CONSTRAINT moralis_transfers_tx_hash_unique
                UNIQUE (transaction_hash)
            """)
            conn.commit()
            print("[OK] Added moralis_transfers unique constraint")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] moralis_transfers: {str(e)[:100]}")

    # 2. Check and fix moralis_pair_stats_correct structure
    try:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'moralis_pair_stats_correct'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cur.fetchall()]

        if not columns:
            # Create the table with correct structure
            cur.execute("""
                CREATE TABLE IF NOT EXISTS moralis_pair_stats_correct (
                    id SERIAL PRIMARY KEY,
                    pair_address VARCHAR(66),
                    pair_label VARCHAR(100),
                    pair_created TIMESTAMP,
                    token_address VARCHAR(66),
                    token_name VARCHAR(100),
                    token_symbol VARCHAR(20),
                    token_logo TEXT,
                    exchange VARCHAR(50),
                    exchange_address VARCHAR(66),
                    exchange_logo TEXT,
                    exchange_url TEXT,
                    current_usd_price DECIMAL(20, 8),
                    current_native_price DECIMAL(20, 8),
                    total_liquidity_usd DECIMAL(20, 2),
                    price_change_5min DECIMAL(10, 2),
                    price_change_1h DECIMAL(10, 2),
                    price_change_4h DECIMAL(10, 2),
                    price_change_24h DECIMAL(10, 2),
                    liquidity_change_5min DECIMAL(10, 2),
                    liquidity_change_1h DECIMAL(10, 2),
                    liquidity_change_4h DECIMAL(10, 2),
                    liquidity_change_24h DECIMAL(10, 2),
                    buys_5min INTEGER,
                    buys_1h INTEGER,
                    buys_4h INTEGER,
                    buys_24h INTEGER,
                    sells_5min INTEGER,
                    sells_1h INTEGER,
                    sells_4h INTEGER,
                    sells_24h INTEGER,
                    total_volume_5min DECIMAL(20, 2),
                    total_volume_1h DECIMAL(20, 2),
                    total_volume_4h DECIMAL(20, 2),
                    total_volume_24h DECIMAL(20, 2),
                    buy_volume_5min DECIMAL(20, 2),
                    buy_volume_1h DECIMAL(20, 2),
                    buy_volume_4h DECIMAL(20, 2),
                    buy_volume_24h DECIMAL(20, 2),
                    sell_volume_5min DECIMAL(20, 2),
                    sell_volume_1h DECIMAL(20, 2),
                    sell_volume_4h DECIMAL(20, 2),
                    sell_volume_24h DECIMAL(20, 2),
                    buyers_5min INTEGER,
                    buyers_1h INTEGER,
                    buyers_4h INTEGER,
                    buyers_24h INTEGER,
                    sellers_5min INTEGER,
                    sellers_1h INTEGER,
                    sellers_4h INTEGER,
                    sellers_24h INTEGER,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    UNIQUE(pair_address, timestamp)
                )
            """)
            conn.commit()
            print("[OK] Created moralis_pair_stats_correct table")
        else:
            print(f"[INFO] moralis_pair_stats_correct has {len(columns)} columns")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] pair_stats: {str(e)[:100]}")

    # 3. Fix moralis_holder_stats_correct structure
    try:
        # Drop and recreate with correct structure
        cur.execute("DROP TABLE IF EXISTS moralis_holder_stats_correct CASCADE")
        cur.execute("""
            CREATE TABLE moralis_holder_stats_correct (
                id SERIAL PRIMARY KEY,
                token_address VARCHAR(66),
                total_holders INTEGER,
                top10_supply DECIMAL(30, 18),
                top10_supply_percent DECIMAL(10, 2),
                top25_supply DECIMAL(30, 18),
                top25_supply_percent DECIMAL(10, 2),
                top50_supply DECIMAL(30, 18),
                top50_supply_percent DECIMAL(10, 2),
                top100_supply DECIMAL(30, 18),
                top100_supply_percent DECIMAL(10, 2),
                top250_supply DECIMAL(30, 18),
                top250_supply_percent DECIMAL(10, 2),
                top500_supply DECIMAL(30, 18),
                top500_supply_percent DECIMAL(10, 2),
                holder_change_5min INTEGER,
                holder_change_percent_5min DECIMAL(10, 2),
                holder_change_1h INTEGER,
                holder_change_percent_1h DECIMAL(10, 2),
                holder_change_6h INTEGER,
                holder_change_percent_6h DECIMAL(10, 2),
                holder_change_24h INTEGER,
                holder_change_percent_24h DECIMAL(10, 2),
                holder_change_3d INTEGER,
                holder_change_percent_3d DECIMAL(10, 2),
                holder_change_7d INTEGER,
                holder_change_percent_7d DECIMAL(10, 2),
                holder_change_30d INTEGER,
                holder_change_percent_30d DECIMAL(10, 2),
                holders_by_swap INTEGER,
                holders_by_transfer INTEGER,
                holders_by_airdrop INTEGER,
                whales INTEGER,
                sharks INTEGER,
                dolphins INTEGER,
                fish INTEGER,
                octopus INTEGER,
                crabs INTEGER,
                shrimps INTEGER,
                timestamp TIMESTAMP DEFAULT NOW(),
                UNIQUE(token_address, timestamp)
            )
        """)
        conn.commit()
        print("[OK] Recreated moralis_holder_stats_correct table")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] holder_stats: {str(e)[:100]}")

    # 4. Fix moralis_token_analytics_correct duplicates
    try:
        # Remove duplicates
        cur.execute("""
            DELETE FROM moralis_token_analytics_correct
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM moralis_token_analytics_correct
                GROUP BY token_address
            )
        """)
        deleted = cur.rowcount
        if deleted > 0:
            print(f"[CLEAN] Removed {deleted} duplicate token analytics")

        # Try to add constraint
        cur.execute("""
            ALTER TABLE moralis_token_analytics_correct
            ADD CONSTRAINT moralis_token_analytics_correct_unique
            UNIQUE (token_address)
        """)
        conn.commit()
        print("[OK] Added token_analytics unique constraint")
    except Exception as e:
        conn.rollback()
        if "already exists" in str(e):
            print("[EXISTS] token_analytics constraint")
        else:
            print(f"[INFO] token_analytics: {str(e)[:50]}")

    print("\n" + "="*60)
    print("Table fixes complete!")

    # Show current status
    print("\nCurrent table row counts:")
    for table in ['moralis_transfers', 'moralis_swaps_correct',
                  'moralis_pair_stats_correct', 'moralis_holder_stats_correct',
                  'moralis_token_analytics_correct']:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count} rows")
        except:
            print(f"  {table}: ERROR or missing")

    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_tables()