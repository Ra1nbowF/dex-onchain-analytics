"""Create LP token tables in Railway database"""

import asyncio
import asyncpg
import os
from datetime import datetime

# Use Railway database
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"
DATABASE_URL = os.getenv("DATABASE_URL", RAILWAY_URL)

async def create_lp_tables():
    """Create LP token related tables in Railway database"""

    conn = None
    try:
        print(f"Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)

        print("Creating LP token tables...")

        # Create LP token transfers table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bsc_lp_token_transfers (
                id SERIAL PRIMARY KEY,
                tx_hash VARCHAR(66),
                block_number BIGINT,
                from_address VARCHAR(42),
                to_address VARCHAR(42),
                lp_amount DECIMAL(40, 18),
                btcb_amount DECIMAL(40, 18),
                usdt_amount DECIMAL(40, 18),
                total_value_usd DECIMAL(30, 2),
                transfer_type VARCHAR(20), -- 'mint', 'burn', 'transfer'
                pool_share_percent DECIMAL(10, 6),
                timestamp TIMESTAMP,
                UNIQUE(tx_hash, from_address, to_address)
            )
        """)
        print("[OK] Created bsc_lp_token_transfers table")

        # Create LP holders table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bsc_lp_holders (
                id SERIAL PRIMARY KEY,
                wallet_address VARCHAR(42) UNIQUE,
                lp_balance DECIMAL(40, 18),
                pool_share_percent DECIMAL(10, 6),
                btcb_value DECIMAL(40, 18),
                usdt_value DECIMAL(40, 18),
                total_value_usd DECIMAL(30, 2),
                first_provided TIMESTAMP,
                last_updated TIMESTAMP,
                total_deposits INTEGER DEFAULT 0,
                total_withdrawals INTEGER DEFAULT 0
            )
        """)
        print("[OK] Created bsc_lp_holders table")

        # Create indexes for better performance
        print("\nCreating indexes...")

        # Index for LP transfers
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lp_transfers_timestamp
            ON bsc_lp_token_transfers(timestamp DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lp_transfers_type
            ON bsc_lp_token_transfers(transfer_type)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lp_transfers_addresses
            ON bsc_lp_token_transfers(from_address, to_address)
        """)
        print("[OK] Created indexes for bsc_lp_token_transfers")

        # Index for LP holders
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lp_holders_balance
            ON bsc_lp_holders(lp_balance DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lp_holders_value
            ON bsc_lp_holders(total_value_usd DESC)
        """)
        print("[OK] Created indexes for bsc_lp_holders")

        # Verify tables exist
        print("\nVerifying tables...")

        result = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN ('bsc_lp_token_transfers', 'bsc_lp_holders')
            ORDER BY tablename
        """)

        print("\nCreated tables:")
        for row in result:
            print(f"  - {row['tablename']}")

        # Check if tables are empty or have data
        for table_name in ['bsc_lp_token_transfers', 'bsc_lp_holders']:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"\n{table_name}: {count} records")

        print("\n[SUCCESS] All LP token tables created successfully!")
        print(f"\nDatabase: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")

    except Exception as e:
        print(f"\n[ERROR] Error creating tables: {e}")
        return False
    finally:
        if conn:
            await conn.close()

    return True

if __name__ == "__main__":
    success = asyncio.run(create_lp_tables())
    exit(0 if success else 1)