import asyncio
import asyncpg
from datetime import datetime
from decimal import Decimal

DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"

async def insert_test_data():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Insert holder stats test data
        await conn.execute("""
            INSERT INTO moralis_holder_stats_correct (
                token_address, total_holders,
                top10_supply, top10_supply_percent,
                whales, sharks, dolphins, fish, shrimps,
                holder_change_24h, holders_by_swap,
                timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (token_address, timestamp) DO UPDATE SET
                total_holders = EXCLUDED.total_holders
        """,
            "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c",  # token_address
            1325199,  # total_holders
            Decimal("51042.04"),  # top10_supply
            Decimal("78"),  # top10_supply_percent
            42,  # whales
            25,  # sharks
            353,  # dolphins
            1385,  # fish
            1309186,  # shrimps
            150,  # holder_change_24h
            850,  # holders_by_swap
            datetime.utcnow()  # timestamp
        )
        print("OK Holder stats inserted")

        # Insert pair stats test data
        await conn.execute("""
            INSERT INTO moralis_pair_stats_correct (
                pair_address, token_address,
                current_usd_price, total_liquidity_usd,
                price_change_24h, total_volume_24h,
                timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (pair_address, timestamp) DO UPDATE SET
                current_usd_price = EXCLUDED.current_usd_price
        """,
            "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4",  # pair_address
            "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c",  # token_address
            Decimal("113014.45"),  # current_usd_price
            Decimal("13467747.48"),  # total_liquidity_usd
            Decimal("0.124"),  # price_change_24h
            Decimal("17886674.16"),  # total_volume_24h
            datetime.utcnow()  # timestamp
        )
        print("OK Pair stats inserted")

        # Insert top gainers test data
        await conn.execute("""
            DELETE FROM moralis_top_gainers
        """)

        await conn.execute("""
            INSERT INTO moralis_top_gainers (
                wallet_address, avg_buy_price_usd, avg_sell_price_usd,
                total_tokens_bought, total_tokens_sold,
                total_usd_invested, total_sold_usd,
                realized_profit_usd, realized_profit_percentage,
                count_of_trades, timestamp
            ) VALUES
            ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11),
            ($12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22),
            ($23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33)
        """,
            # Trader 1
            "0x123...abc", Decimal("95000"), Decimal("113000"),
            Decimal("0.5"), Decimal("0.45"),
            Decimal("47500"), Decimal("50850"),
            Decimal("3350"), Decimal("7.05"),
            15, datetime.utcnow(),

            # Trader 2
            "0x456...def", Decimal("88000"), Decimal("112000"),
            Decimal("1.2"), Decimal("1.0"),
            Decimal("105600"), Decimal("112000"),
            Decimal("6400"), Decimal("6.06"),
            28, datetime.utcnow(),

            # Trader 3
            "0x789...ghi", Decimal("102000"), Decimal("114000"),
            Decimal("0.25"), Decimal("0.22"),
            Decimal("25500"), Decimal("25080"),
            Decimal("-420"), Decimal("-1.65"),
            8, datetime.utcnow()
        )
        print("OK Top gainers inserted")

        # Check data
        result = await conn.fetchval("SELECT COUNT(*) FROM moralis_holder_stats_correct")
        print(f"Holder stats count: {result}")

        result = await conn.fetchval("SELECT COUNT(*) FROM moralis_pair_stats_correct")
        print(f"Pair stats count: {result}")

        result = await conn.fetchval("SELECT COUNT(*) FROM moralis_top_gainers")
        print(f"Top gainers count: {result}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(insert_test_data())