"""Railway-optimized DEX data collector"""

import asyncio
import asyncpg
import random
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway automatically provides DATABASE_URL for PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback for local development
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"
    logger.warning("DATABASE_URL not set, using local development database")
else:
    logger.info(f"Connected to Railway database")

# If Railway provides a private URL, use it
DATABASE_URL_PRIVATE = os.getenv("DATABASE_PRIVATE_URL")
if DATABASE_URL_PRIVATE:
    DATABASE_URL = DATABASE_URL_PRIVATE
    logger.info("Using private database URL for better performance")

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

# Track wallet addresses
WALLETS = [f"0x{i:040x}" for i in range(1, 101)]

class DexDataGenerator:
    def __init__(self):
        self.token_prices = TOKENS.copy()
        self.pool_liquidity = {}
        self.wallet_balances = {}

    def update_prices(self):
        """Update token prices with random walk"""
        for token, data in self.token_prices.items():
            change = random.gauss(0, data["volatility"])
            data["price"] *= (1 + change)
            data["price"] = max(0.01, data["price"])  # Prevent negative prices

    def generate_trade(self):
        """Generate a random trade"""
        chain = random.choice(CHAINS)
        dex = random.choice(DEXES)
        pair = random.choice(PAIRS)
        token_in, token_out = pair.split("/")

        # Generate trade amounts
        amount_in = random.uniform(0.1, 1000)
        price_in = self.token_prices.get(token_in, {"price": 1})["price"]
        price_out = self.token_prices.get(token_out, {"price": 1})["price"]
        amount_out = (amount_in * price_in) / price_out * random.uniform(0.997, 1.003)  # Slippage

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
            "trader_address": random.choice(WALLETS),
            "tx_hash": f"0x{random.getrandbits(256):064x}",
            "gas_used": random.randint(100000, 500000),
            "timestamp": datetime.now()
        }

    def generate_liquidity_pool(self):
        """Generate liquidity pool data"""
        chain = random.choice(CHAINS)
        dex = random.choice(DEXES)
        pair = random.choice(PAIRS)
        token0, token1 = pair.split("/")

        # Generate reserves
        token0_reserve = random.uniform(1000, 1000000)
        token1_reserve = random.uniform(1000, 1000000)

        price0 = self.token_prices.get(token0, {"price": 1})["price"]
        price1 = self.token_prices.get(token1, {"price": 1})["price"]

        total_liquidity_usd = (token0_reserve * price0) + (token1_reserve * price1)

        return {
            "chain_id": chain["id"],
            "chain_name": chain["name"],
            "dex_name": dex,
            "pool_address": f"0x{random.getrandbits(160):040x}",
            "token0_symbol": token0,
            "token1_symbol": token1,
            "token0_reserve": token0_reserve,
            "token1_reserve": token1_reserve,
            "total_liquidity_usd": total_liquidity_usd,
            "volume_24h": total_liquidity_usd * random.uniform(0.1, 2.0),
            "fees_24h": total_liquidity_usd * random.uniform(0.001, 0.01),
            "apy": random.uniform(1, 50),
            "timestamp": datetime.now()
        }

async def store_trade(conn, trade):
    """Store trade in database"""
    await conn.execute("""
        INSERT INTO dex_trades (
            chain_id, chain_name, dex_name, pair, token_in, token_out,
            amount_in, amount_out, price, value_usd, trader_address,
            tx_hash, gas_used, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    """, *trade.values())

async def store_liquidity_pool(conn, pool):
    """Store liquidity pool data"""
    await conn.execute("""
        INSERT INTO liquidity_pools (
            chain_id, chain_name, dex_name, pool_address,
            token0_symbol, token1_symbol, token0_reserve, token1_reserve,
            total_liquidity_usd, volume_24h, fees_24h, apy, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """, *pool.values())

async def store_token_price(conn, token, price):
    """Store token price"""
    await conn.execute("""
        INSERT INTO token_prices (
            chain_id, token_symbol, price_usd, volume_24h,
            price_change_24h, market_cap, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, 1, token, price,
    random.uniform(1000000, 100000000),
    random.uniform(-20, 20),
    price * random.uniform(1000000, 1000000000),
    datetime.now())

async def update_chain_stats(conn):
    """Update chain statistics"""
    for chain in CHAINS:
        await conn.execute("""
            INSERT INTO chain_stats (
                chain_name, chain_id, total_volume_24h,
                total_transactions, active_wallets, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, chain["name"], chain["id"],
        random.uniform(1000000, 100000000),
        random.randint(1000, 100000),
        random.randint(100, 10000),
        datetime.now())

async def main():
    """Main data generation loop"""
    logger.info("Starting Railway DEX data collector...")
    logger.info(f"Database URL: {DATABASE_URL[:50]}...")

    # Connect to database
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("Successfully connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return

    generator = DexDataGenerator()

    try:
        # Test database connection
        version = await conn.fetchval("SELECT version()")
        logger.info(f"Database version: {version[:50]}...")

        # Initial chain stats
        await update_chain_stats(conn)

        iteration = 0
        while True:
            iteration += 1

            # Update prices every iteration
            generator.update_prices()

            # Generate multiple trades per iteration
            for _ in range(random.randint(5, 15)):
                trade = generator.generate_trade()
                await store_trade(conn, trade)

            # Update liquidity pools less frequently
            if iteration % 10 == 0:
                for _ in range(random.randint(2, 5)):
                    pool = generator.generate_liquidity_pool()
                    await store_liquidity_pool(conn, pool)

            # Update token prices
            if iteration % 5 == 0:
                for token, data in generator.token_prices.items():
                    await store_token_price(conn, token, data["price"])

            # Update chain stats every 20 iterations
            if iteration % 20 == 0:
                await update_chain_stats(conn)
                logger.info(f"Iteration {iteration}: Updated chain stats")

            if iteration % 10 == 0:
                logger.info(f"Iteration {iteration}: Generated data successfully")

            # Sleep for a short time
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())