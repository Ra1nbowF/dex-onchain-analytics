import asyncio
import asyncpg
from datetime import datetime, timedelta
from decimal import Decimal
import random

DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

async def add_timeseries_data():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Add 7 days of token analytics data (hourly)
        base_time = datetime.utcnow() - timedelta(days=7)

        for i in range(168):  # 7 days * 24 hours
            timestamp = base_time + timedelta(hours=i)

            # Generate realistic trending data
            base_buyers = 8000 + random.randint(-500, 1500)
            base_sellers = 8200 + random.randint(-500, 1500)

            await conn.execute("""
                INSERT INTO moralis_token_analytics_correct (
                    token_address,
                    total_buy_volume_24h, total_sell_volume_24h,
                    total_buyers_24h, total_sellers_24h,
                    total_buys_24h, total_sells_24h,
                    timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (token_address, timestamp) DO UPDATE SET
                    total_buyers_24h = EXCLUDED.total_buyers_24h
            """,
                "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c",
                Decimal(str(55000000 + random.randint(-5000000, 10000000))),  # buy volume
                Decimal(str(56000000 + random.randint(-5000000, 10000000))),  # sell volume
                base_buyers,  # buyers
                base_sellers,  # sellers
                base_buyers * 3,  # buy transactions
                base_sellers * 3,  # sell transactions
                timestamp
            )

            if i % 24 == 0:
                print(f"Added data for day {i // 24 + 1}")

        print("OK Added 7 days of analytics data")

        # Verify
        result = await conn.fetchval("SELECT COUNT(*) FROM moralis_token_analytics_correct")
        print(f"Total analytics records: {result}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_timeseries_data())