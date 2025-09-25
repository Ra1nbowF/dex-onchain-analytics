"""Check BSC table structure and data in Railway database"""

import asyncio
import asyncpg
from datetime import datetime

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

async def check_bsc_tables():
    conn = None
    try:
        print("Connecting to Railway database...")
        conn = await asyncpg.connect(RAILWAY_URL)

        # List all BSC-related tables
        print("\nBSC-related tables:")
        tables = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE 'bsc_%'
            ORDER BY tablename
        """)

        for table in tables:
            table_name = table['tablename']
            print(f"\n[{table_name}]")

            # Get column information
            columns = await conn.fetch(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
                LIMIT 10
            """)

            print("  Columns:")
            for col in columns:
                print(f"    - {col['column_name']}: {col['data_type']}")

            # Get record count and latest timestamp
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"  Records: {count}")

            # Try to find timestamp column and get latest
            timestamp_cols = ['timestamp', 'last_updated', 'created_at']
            for ts_col in timestamp_cols:
                try:
                    latest = await conn.fetchval(f"SELECT MAX({ts_col}) FROM {table_name}")
                    if latest:
                        now = datetime.utcnow()
                        time_diff = now - latest.replace(tzinfo=None)
                        hours_ago = time_diff.total_seconds() / 3600
                        print(f"  Latest {ts_col}: {latest} ({hours_ago:.1f}h ago)")
                        break
                except:
                    continue

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()

asyncio.run(check_bsc_tables())