"""Create missing Moralis tables in Railway database"""

import asyncio
import asyncpg

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

async def create_moralis_tables():
    conn = None
    try:
        print("Creating missing Moralis tables in Railway database...")
        conn = await asyncpg.connect(RAILWAY_URL)

        # Create moralis_holder_stats table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS moralis_holder_stats (
                id SERIAL PRIMARY KEY,
                wallet_address VARCHAR(42),
                balance_btcb DECIMAL(40, 18),
                balance_usdt DECIMAL(40, 18),
                total_value_usd DECIMAL(30, 2),
                percentage_of_supply DECIMAL(10, 6),
                holder_rank INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(wallet_address, timestamp)
            )
        """)
        print("[OK] Created moralis_holder_stats table")

        # Create moralis_profitable_traders table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS moralis_profitable_traders (
                id SERIAL PRIMARY KEY,
                wallet_address VARCHAR(42),
                total_trades INTEGER,
                profitable_trades INTEGER,
                win_rate DECIMAL(5, 2),
                total_profit_usd DECIMAL(30, 2),
                avg_profit_per_trade DECIMAL(30, 2),
                best_trade_profit DECIMAL(30, 2),
                worst_trade_loss DECIMAL(30, 2),
                last_trade_date TIMESTAMP,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(wallet_address, timestamp)
            )
        """)
        print("[OK] Created moralis_profitable_traders table")

        # Create moralis_top_100_holders table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS moralis_top_100_holders (
                id SERIAL PRIMARY KEY,
                rank INTEGER,
                wallet_address VARCHAR(42),
                token_symbol VARCHAR(10),
                balance DECIMAL(40, 18),
                value_usd DECIMAL(30, 2),
                percentage_of_supply DECIMAL(10, 6),
                first_seen TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(wallet_address, token_symbol, last_updated)
            )
        """)
        print("[OK] Created moralis_top_100_holders table")

        # Create indexes
        print("\nCreating indexes...")

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holder_stats_timestamp
            ON moralis_holder_stats(timestamp DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_profitable_traders_timestamp
            ON moralis_profitable_traders(timestamp DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_profitable_traders_profit
            ON moralis_profitable_traders(total_profit_usd DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_top_100_holders_updated
            ON moralis_top_100_holders(last_updated DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_top_100_holders_rank
            ON moralis_top_100_holders(rank)
        """)

        print("[OK] Created all indexes")

        # Fix BSC wallet_metrics column name issue
        print("\nFixing BSC wallet_metrics column...")

        # Check if column exists
        col_exists = await conn.fetchval("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'bsc_wallet_metrics'
            AND column_name = 'last_updated'
        """)

        if col_exists == 0:
            # Add the missing column
            await conn.execute("""
                ALTER TABLE bsc_wallet_metrics
                ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            print("[OK] Added last_updated column to bsc_wallet_metrics")

        # Verify all tables
        print("\nVerifying all tables...")
        tables = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN (
                'moralis_holder_stats',
                'moralis_profitable_traders',
                'moralis_top_100_holders',
                'moralis_pair_stats_correct'
            )
            ORDER BY tablename
        """)

        print("\nMoralis tables in database:")
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['tablename']}")
            print(f"  - {table['tablename']}: {count} records")

        print("\n[SUCCESS] All missing tables created!")

    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(create_moralis_tables())