"""Verify and fix Railway database tables"""

import asyncio
import asyncpg
from datetime import datetime

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

async def verify_and_fix_tables():
    conn = None
    try:
        print("Checking Railway Database Tables...")
        print("=" * 60)
        conn = await asyncpg.connect(RAILWAY_URL)

        # Check if tables exist
        print("Checking which tables exist...")

        tables_to_check = [
            'moralis_holder_stats',
            'moralis_profitable_traders',
            'moralis_top_100_holders',
            'bsc_wallet_metrics'
        ]

        for table in tables_to_check:
            exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                )
            """)

            if exists:
                print(f"[EXISTS] {table}")

                # Check columns for bsc_wallet_metrics
                if table == 'bsc_wallet_metrics':
                    has_last_updated = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_name = 'bsc_wallet_metrics'
                            AND column_name = 'last_updated'
                        )
                    """)

                    if has_last_updated:
                        print(f"  - Column 'last_updated' exists")
                    else:
                        print(f"  - Column 'last_updated' MISSING")
            else:
                print(f"[MISSING] {table}")

        print("\n" + "=" * 60)
        print("Running the fix script that was already created...")
        print("This will create all missing tables and columns.")

        # Run the fix
        exec_result = await conn.execute(open('create_missing_moralis_tables.py').read())

        print("\nDone! Tables should now be created in Railway.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_and_fix_tables())