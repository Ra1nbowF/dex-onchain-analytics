"""Simple DEX data collector that generates continuous data for Grafana"""

import asyncio
import asyncpg
import random
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/dex_analytics")

# DEX and token configurations
CHAINS = [
    {"id": 1, "name": "Ethereum"},
    {"id": 56, "name": "BSC"},
    {"id": 137, "name": "Polygon"},
    {"id": 42161, "name": "Arbitrum"},
    {"id": 10, "name": "Optimism"},
    {"id": 8453, "name": "Base"}
]

DEXES = ["Uniswap V3", "Uniswap V2", "SushiSwap", "PancakeSwap", "Curve", "Balancer"]

PAIRS = [
    "ETH/USDT", "ETH/USDC", "BTC/USDT", "BNB/USDT",
    "MATIC/USDT", "ARB/USDT", "OP/USDT", "LINK/ETH",
    "UNI/ETH", "AAVE/ETH", "SUSHI/ETH", "CRV/ETH"
]

TOKENS = {
    "ETH": {"price": 3800, "volatility": 0.02},
    "BTC": {"price": 70000, "volatility": 0.025},
    "USDT": {"price": 1, "volatility": 0.001},
    "USDC": {"price": 1, "volatility": 0.001},
    "BNB": {"price": 650, "volatility": 0.03},
    "MATIC": {"price": 1.5, "volatility": 0.04},
    "ARB": {"price": 2.0, "volatility": 0.05},
    "OP": {"price": 3.5, "volatility": 0.05},
    "LINK": {"price": 20, "volatility": 0.03},
    "UNI": {"price": 15, "volatility": 0.04},
    "AAVE": {"price": 150, "volatility": 0.04},
    "SUSHI": {"price": 2.5, "volatility": 0.05},
    "CRV": {"price": 1.2, "volatility": 0.04}
}


class DEXDataCollector:
    def __init__(self):
        self.db_pool = None
        self.token_prices = TOKENS.copy()

    async def initialize(self):
        """Initialize database connection"""
        self.db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        logger.info("Database connection established")

    async def cleanup(self):
        """Cleanup resources"""
        if self.db_pool:
            await self.db_pool.close()

    async def update_token_prices(self):
        """Simulate price movements"""
        for token, data in self.token_prices.items():
            change = random.gauss(0, data["volatility"])
            data["price"] *= (1 + change)

    async def generate_trade(self):
        """Generate a realistic DEX trade"""
        chain = random.choice(CHAINS)
        dex = random.choice(DEXES)
        pair = random.choice(PAIRS)
        tokens = pair.split("/")

        # Determine trade direction
        if random.random() > 0.5:
            token_in, token_out = tokens[0], tokens[1]
        else:
            token_in, token_out = tokens[1], tokens[0]

        # Calculate amounts
        amount_in = random.uniform(0.01, 100)
        price_in = self.token_prices.get(token_in, {"price": 1})["price"]
        price_out = self.token_prices.get(token_out, {"price": 1})["price"]
        amount_out = (amount_in * price_in) / price_out * random.uniform(0.997, 0.999)  # Include slippage
        value_usd = amount_in * price_in

        return {
            "chain_id": chain["id"],
            "chain_name": chain["name"],
            "dex_name": dex,
            "pair": pair,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "amount_out": amount_out,
            "price": price_in / price_out,
            "value_usd": value_usd,
            "trader_address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "tx_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            "gas_used": random.randint(50000, 300000)
        }

    async def insert_trade(self, trade):
        """Insert trade into database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO dex_trades (
                    chain_id, chain_name, dex_name, pair, token_in, token_out,
                    amount_in, amount_out, price, value_usd, trader_address,
                    tx_hash, gas_used, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
                trade["chain_id"], trade["chain_name"], trade["dex_name"],
                trade["pair"], trade["token_in"], trade["token_out"],
                trade["amount_in"], trade["amount_out"], trade["price"],
                trade["value_usd"], trade["trader_address"], trade["tx_hash"],
                trade["gas_used"], datetime.now()
            )

    async def update_token_price_table(self):
        """Update token prices in database"""
        async with self.db_pool.acquire() as conn:
            for token, data in self.token_prices.items():
                await conn.execute("""
                    INSERT INTO token_prices (
                        chain_id, token_symbol, price_usd, volume_24h,
                        price_change_24h, market_cap, timestamp
                    ) VALUES (1, $1, $2, $3, $4, $5, $6)
                """,
                    token, data["price"],
                    random.uniform(100000, 10000000),
                    random.uniform(-5, 5),
                    data["price"] * random.uniform(1000000, 1000000000),
                    datetime.now()
                )

    async def update_liquidity_pools(self):
        """Update liquidity pool data"""
        async with self.db_pool.acquire() as conn:
            for chain in CHAINS[:3]:  # Top 3 chains
                for dex in DEXES[:3]:  # Top 3 DEXes
                    for pair in PAIRS[:5]:  # Top 5 pairs
                        tokens = pair.split("/")
                        token0_price = self.token_prices.get(tokens[0], {"price": 1})["price"]
                        token1_price = self.token_prices.get(tokens[1], {"price": 1})["price"]

                        token0_reserve = random.uniform(1000, 1000000)
                        token1_reserve = token0_reserve * token0_price / token1_price
                        total_liquidity = token0_reserve * token0_price * 2

                        await conn.execute("""
                            INSERT INTO liquidity_pools (
                                chain_id, chain_name, dex_name, pool_address,
                                token0_symbol, token1_symbol, token0_reserve,
                                token1_reserve, total_liquidity_usd, volume_24h,
                                fees_24h, apy, timestamp
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        """,
                            chain["id"], chain["name"], dex,
                            f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                            tokens[0], tokens[1], token0_reserve, token1_reserve,
                            total_liquidity, total_liquidity * random.uniform(0.1, 2),
                            total_liquidity * random.uniform(0.0001, 0.001),
                            random.uniform(5, 50), datetime.now()
                        )

    async def update_chain_stats(self):
        """Update chain statistics"""
        async with self.db_pool.acquire() as conn:
            for chain in CHAINS:
                # Calculate from recent trades
                result = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as tx_count,
                        COALESCE(SUM(value_usd), 0) as volume,
                        COUNT(DISTINCT trader_address) as wallets
                    FROM dex_trades
                    WHERE chain_id = $1
                    AND timestamp > NOW() - INTERVAL '24 hours'
                """, chain["id"])

                await conn.execute("""
                    INSERT INTO chain_stats (
                        chain_name, chain_id, total_volume_24h,
                        total_transactions, active_wallets, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    chain["name"], chain["id"],
                    float(result["volume"]) if result else 0,
                    result["tx_count"] if result else 0,
                    result["wallets"] if result else 0,
                    datetime.now()
                )

    async def refresh_materialized_views(self):
        """Refresh materialized views for Grafana"""
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_dex_stats")
                await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY top_pairs_24h")
                logger.info("Materialized views refreshed")
            except Exception as e:
                logger.error(f"Error refreshing views: {e}")

    async def run_continuous(self):
        """Run continuous data collection"""
        logger.info("Starting continuous data collection...")

        trade_counter = 0
        while True:
            try:
                # Generate trades (high frequency)
                for _ in range(random.randint(1, 5)):
                    trade = await self.generate_trade()
                    await self.insert_trade(trade)
                    trade_counter += 1

                # Update prices every 10 trades
                if trade_counter % 10 == 0:
                    await self.update_token_prices()
                    await self.update_token_price_table()

                # Update pools every 50 trades
                if trade_counter % 50 == 0:
                    await self.update_liquidity_pools()

                # Update chain stats every 100 trades
                if trade_counter % 100 == 0:
                    await self.update_chain_stats()
                    await self.refresh_materialized_views()
                    logger.info(f"Processed {trade_counter} trades")

                # Sleep to simulate realistic rate
                await asyncio.sleep(random.uniform(0.5, 2))

            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(5)


async def main():
    collector = DEXDataCollector()
    try:
        await collector.initialize()
        await collector.run_continuous()
    finally:
        await collector.cleanup()


if __name__ == "__main__":
    asyncio.run(main())