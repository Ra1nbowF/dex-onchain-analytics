"""Quick check of Railway database tables"""

import asyncio
import asyncpg

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

async def quick_check():
    conn = None
    try:
        conn = await asyncpg.connect(RAILWAY_URL)
        print("Connected to Railway database")
        print("-" * 40)

        # List all tables starting with 'moralis' or 'bsc'
        tables = await conn.fetch("""
            SELECT tablename,
                   (SELECT COUNT(*) FROM pg_tables WHERE tablename = t.tablename) as exists
            FROM pg_tables t
            WHERE schemaname = 'public'
            AND (tablename LIKE 'moralis_%' OR tablename LIKE 'bsc_%')
            ORDER BY tablename
        """)

        print("\nTables in Railway database:")
        for table in tables:
            # Get record count
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['tablename']}")
                print(f"  {table['tablename']}: {count} records")
            except Exception as e:
                print(f"  {table['tablename']}: ERROR - {str(e)[:30]}")

        # Specifically check for the missing tables
        print("\nChecking specifically for reported missing tables:")

        missing_tables = [
            'moralis_holder_stats',
            'moralis_profitable_traders',
            'moralis_top_100_holders'
        ]

        for table_name in missing_tables:
            exists = await conn.fetchval(f"""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
            """)

            if exists > 0:
                print(f"  {table_name}: EXISTS")
            else:
                print(f"  {table_name}: DOES NOT EXIST")

        # Check bsc_wallet_metrics columns
        print("\nChecking bsc_wallet_metrics columns:")
        columns = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'bsc_wallet_metrics'
            ORDER BY ordinal_position
        """)

        if columns:
            for col in columns:
                print(f"  - {col['column_name']}")
        else:
            print("  Table doesn't exist or has no columns")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

asyncio.run(quick_check())