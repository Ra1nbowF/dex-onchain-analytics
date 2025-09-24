"""
Moralis-based BSC Pool Monitor with Advanced Analytics
Tracks BTCB/USDT pool with comprehensive metrics
"""

import asyncio
import aiohttp
import asyncpg
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import json

# Configuration
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

# BSC Addresses
BTCB_ADDRESS = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"  # BTCB on BSC
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"  # USDT on BSC
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"  # PancakeSwap BTCB/USDT

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@dex_postgres:5432/dex_analytics")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MoralisBSCMonitor:
    def __init__(self):
        self.session = None
        self.db_pool = None
        self.headers = {
            "X-API-Key": MORALIS_API_KEY,
            "accept": "application/json"
        }

    async def initialize(self):
        """Initialize connections and database tables"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        self.db_pool = await asyncpg.create_pool(DATABASE_URL)
        await self.create_tables()
        logger.info("Moralis BSC Monitor initialized")

    async def cleanup(self):
        """Cleanup connections"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()

    async def create_tables(self):
        """Create comprehensive monitoring tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                -- Token swaps table
                CREATE TABLE IF NOT EXISTS moralis_swaps (
                    id SERIAL PRIMARY KEY,
                    transaction_hash VARCHAR(66) UNIQUE,
                    block_number BIGINT,
                    block_timestamp TIMESTAMP,
                    transaction_type VARCHAR(10),  -- buy/sell
                    from_wallet VARCHAR(42),
                    to_wallet VARCHAR(42),
                    from_token VARCHAR(42),
                    to_token VARCHAR(42),
                    from_amount DECIMAL(40, 18),
                    to_amount DECIMAL(40, 18),
                    usd_value DECIMAL(30, 2),
                    exchange_name VARCHAR(100),
                    pair_address VARCHAR(42),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Token analytics table
                CREATE TABLE IF NOT EXISTS moralis_token_analytics (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    total_buy_volume_5m DECIMAL(30, 2),
                    total_sell_volume_5m DECIMAL(30, 2),
                    total_buy_volume_1h DECIMAL(30, 2),
                    total_sell_volume_1h DECIMAL(30, 2),
                    total_buy_volume_24h DECIMAL(30, 2),
                    total_sell_volume_24h DECIMAL(30, 2),
                    total_buyers_5m INTEGER,
                    total_sellers_5m INTEGER,
                    total_buyers_24h INTEGER,
                    total_sellers_24h INTEGER,
                    total_liquidity_usd DECIMAL(30, 2),
                    fdv DECIMAL(30, 2),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Token holder statistics
                CREATE TABLE IF NOT EXISTS moralis_holder_stats (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    total_holders INTEGER,
                    holders_change_24h INTEGER,
                    holders_change_pct_24h DECIMAL(10, 4),
                    top_10_supply_pct DECIMAL(10, 4),
                    top_25_supply_pct DECIMAL(10, 4),
                    top_50_supply_pct DECIMAL(10, 4),
                    top_100_supply_pct DECIMAL(10, 4),
                    gini_coefficient DECIMAL(10, 6),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Pair statistics
                CREATE TABLE IF NOT EXISTS moralis_pair_stats (
                    id SERIAL PRIMARY KEY,
                    pair_address VARCHAR(42),
                    token0_address VARCHAR(42),
                    token1_address VARCHAR(42),
                    exchange_name VARCHAR(100),
                    usd_price DECIMAL(30, 10),
                    liquidity_usd DECIMAL(30, 2),
                    price_change_5m DECIMAL(10, 4),
                    price_change_1h DECIMAL(10, 4),
                    price_change_24h DECIMAL(10, 4),
                    volume_24h DECIMAL(30, 2),
                    buy_txns_24h INTEGER,
                    sell_txns_24h INTEGER,
                    buyers_24h INTEGER,
                    sellers_24h INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Profitable wallets tracking
                CREATE TABLE IF NOT EXISTS moralis_profitable_wallets (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42),
                    token_address VARCHAR(42),
                    realized_profit_pct DECIMAL(20, 4),
                    total_trades INTEGER,
                    tokens_bought DECIMAL(40, 18),
                    tokens_sold DECIMAL(40, 18),
                    avg_buy_price DECIMAL(30, 10),
                    avg_sell_price DECIMAL(30, 10),
                    current_holdings DECIMAL(40, 18),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Sniper detection table
                CREATE TABLE IF NOT EXISTS moralis_snipers (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42),
                    pair_address VARCHAR(42),
                    tokens_bought DECIMAL(40, 18),
                    tokens_sold DECIMAL(40, 18),
                    buy_tx_hash VARCHAR(66),
                    sell_tx_hash VARCHAR(66),
                    realized_profit_pct DECIMAL(20, 4),
                    blocks_held INTEGER,
                    is_sniper BOOLEAN DEFAULT TRUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Historical holder data
                CREATE TABLE IF NOT EXISTS moralis_historical_holders (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    holder_count INTEGER,
                    data_point_timestamp TIMESTAMP,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_swaps_timestamp ON moralis_swaps(block_timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_swaps_wallet ON moralis_swaps(from_wallet, to_wallet);
                CREATE INDEX IF NOT EXISTS idx_swaps_type ON moralis_swaps(transaction_type);
                CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON moralis_token_analytics(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_holder_stats_timestamp ON moralis_holder_stats(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_pair_stats_timestamp ON moralis_pair_stats(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_profitable_wallets_profit ON moralis_profitable_wallets(realized_profit_pct DESC);
            """)

    async def fetch_token_swaps(self, hours_back: int = 1) -> List[Dict]:
        """Fetch recent swaps for BTCB"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/swaps"

            # Calculate from_date
            from_date = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat() + "Z"

            params = {
                "chain": "bsc",
                "limit": 100,
                "order": "DESC",
                "from_date": from_date
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    swaps = data.get("result", [])
                    logger.info(f"Fetched {len(swaps)} swaps for BTCB")
                    return swaps
                else:
                    logger.error(f"Failed to fetch swaps: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching swaps: {e}")
            return []

    async def fetch_token_analytics(self) -> Dict:
        """Fetch token analytics for BTCB"""
        try:
            url = f"{MORALIS_BASE_URL}/tokens/{BTCB_ADDRESS}/analytics"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched token analytics for BTCB")
                    return data
                else:
                    logger.error(f"Failed to fetch analytics: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            return {}

    async def fetch_holder_stats(self) -> Dict:
        """Fetch holder statistics for BTCB"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/holders"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched holder stats for BTCB")
                    return data
                else:
                    logger.error(f"Failed to fetch holder stats: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching holder stats: {e}")
            return {}

    async def fetch_pair_stats(self) -> Dict:
        """Fetch pair statistics for BTCB/USDT"""
        try:
            url = f"{MORALIS_BASE_URL}/pairs/{POOL_ADDRESS}/stats"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched pair stats for BTCB/USDT")
                    return data
                else:
                    logger.error(f"Failed to fetch pair stats: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching pair stats: {e}")
            return {}

    async def fetch_top_profitable_wallets(self) -> List[Dict]:
        """Fetch top profitable wallets for BTCB"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/top-gainers"
            params = {
                "chain": "bsc",
                "days": "7"  # Last 7 days
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    wallets = data.get("result", [])
                    logger.info(f"Fetched {len(wallets)} profitable wallets")
                    return wallets
                else:
                    logger.error(f"Failed to fetch profitable wallets: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching profitable wallets: {e}")
            return []

    async def fetch_snipers(self, blocks_after: int = 1000) -> List[Dict]:
        """Fetch snipers for BTCB/USDT pair"""
        try:
            url = f"{MORALIS_BASE_URL}/pairs/{POOL_ADDRESS}/snipers"
            params = {
                "chain": "bsc",
                "blocks_after_creation": blocks_after
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    snipers = data.get("result", [])
                    logger.info(f"Fetched {len(snipers)} potential snipers")
                    return snipers
                else:
                    logger.error(f"Failed to fetch snipers: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching snipers: {e}")
            return []

    async def store_swaps(self, swaps: List[Dict]):
        """Store swap data in database"""
        if not swaps:
            return

        async with self.db_pool.acquire() as conn:
            for swap in swaps:
                try:
                    await conn.execute("""
                        INSERT INTO moralis_swaps (
                            transaction_hash, block_number, block_timestamp,
                            transaction_type, from_wallet, to_wallet,
                            from_token, to_token, from_amount, to_amount,
                            usd_value, exchange_name, pair_address
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (transaction_hash) DO NOTHING
                    """,
                        swap.get("transaction_hash"),
                        int(swap.get("block_number", 0)),
                        datetime.fromisoformat(swap.get("block_timestamp", "").replace("Z", "")),
                        swap.get("transaction_type"),
                        swap.get("from_address"),
                        swap.get("to_address"),
                        swap.get("from_token_address"),
                        swap.get("to_token_address"),
                        Decimal(str(swap.get("from_amount", 0))),
                        Decimal(str(swap.get("to_amount", 0))),
                        Decimal(str(swap.get("usd_value", 0))),
                        swap.get("exchange_name"),
                        swap.get("pair_address")
                    )
                except Exception as e:
                    logger.error(f"Error storing swap: {e}")

    async def store_analytics(self, analytics: Dict):
        """Store token analytics in database"""
        if not analytics:
            return

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO moralis_token_analytics (
                    token_address, total_buy_volume_5m, total_sell_volume_5m,
                    total_buy_volume_1h, total_sell_volume_1h,
                    total_buy_volume_24h, total_sell_volume_24h,
                    total_buyers_5m, total_sellers_5m,
                    total_buyers_24h, total_sellers_24h,
                    total_liquidity_usd, fdv
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
                BTCB_ADDRESS,
                Decimal(str(analytics.get("totalBuyVolume5m", 0))),
                Decimal(str(analytics.get("totalSellVolume5m", 0))),
                Decimal(str(analytics.get("totalBuyVolume1h", 0))),
                Decimal(str(analytics.get("totalSellVolume1h", 0))),
                Decimal(str(analytics.get("totalBuyVolume24h", 0))),
                Decimal(str(analytics.get("totalSellVolume24h", 0))),
                analytics.get("totalBuyers5m", 0),
                analytics.get("totalSellers5m", 0),
                analytics.get("totalBuyers24h", 0),
                analytics.get("totalSellers24h", 0),
                Decimal(str(analytics.get("totalLiquidityUsd", 0))),
                Decimal(str(analytics.get("fdv", 0)))
            )

    async def store_holder_stats(self, stats: Dict):
        """Store holder statistics in database"""
        if not stats:
            return

        # Calculate Gini coefficient from holder distribution
        holder_supply = stats.get("holderSupply", {})
        gini = self.calculate_gini_from_distribution(holder_supply)

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO moralis_holder_stats (
                    token_address, total_holders,
                    holders_change_24h, holders_change_pct_24h,
                    top_10_supply_pct, top_25_supply_pct,
                    top_50_supply_pct, top_100_supply_pct,
                    gini_coefficient
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                BTCB_ADDRESS,
                stats.get("totalHolders", 0),
                stats.get("holderChange", {}).get("24h", {}).get("change", 0),
                Decimal(str(stats.get("holderChange", {}).get("24h", {}).get("percentage", 0))),
                Decimal(str(holder_supply.get("top10", 0))),
                Decimal(str(holder_supply.get("top25", 0))),
                Decimal(str(holder_supply.get("top50", 0))),
                Decimal(str(holder_supply.get("top100", 0))),
                Decimal(str(gini))
            )

    async def store_pair_stats(self, stats: Dict):
        """Store pair statistics in database"""
        if not stats:
            return

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO moralis_pair_stats (
                    pair_address, token0_address, token1_address,
                    exchange_name, usd_price, liquidity_usd,
                    price_change_5m, price_change_1h, price_change_24h,
                    volume_24h, buy_txns_24h, sell_txns_24h,
                    buyers_24h, sellers_24h
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
                POOL_ADDRESS,
                stats.get("token0Address", BTCB_ADDRESS),
                stats.get("token1Address", USDT_ADDRESS),
                stats.get("exchangeName", "PancakeSwap"),
                Decimal(str(stats.get("usdPrice", 0))),
                Decimal(str(stats.get("liquidityUsd", 0))),
                Decimal(str(stats.get("priceChange", {}).get("5m", 0))),
                Decimal(str(stats.get("priceChange", {}).get("1h", 0))),
                Decimal(str(stats.get("priceChange", {}).get("24h", 0))),
                Decimal(str(stats.get("volume24h", 0))),
                stats.get("txns", {}).get("24h", {}).get("buys", 0),
                stats.get("txns", {}).get("24h", {}).get("sells", 0),
                stats.get("buyers", {}).get("24h", 0),
                stats.get("sellers", {}).get("24h", 0)
            )

    async def store_profitable_wallets(self, wallets: List[Dict]):
        """Store profitable wallet data in database"""
        if not wallets:
            return

        async with self.db_pool.acquire() as conn:
            for wallet in wallets:
                await conn.execute("""
                    INSERT INTO moralis_profitable_wallets (
                        wallet_address, token_address,
                        realized_profit_pct, total_trades,
                        tokens_bought, tokens_sold,
                        avg_buy_price, avg_sell_price,
                        current_holdings
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    wallet.get("address"),
                    BTCB_ADDRESS,
                    Decimal(str(wallet.get("realizedProfitPercentage", 0))),
                    wallet.get("totalTrades", 0),
                    Decimal(str(wallet.get("tokensBought", 0))),
                    Decimal(str(wallet.get("tokensSold", 0))),
                    Decimal(str(wallet.get("avgBuyPrice", 0))),
                    Decimal(str(wallet.get("avgSellPrice", 0))),
                    Decimal(str(wallet.get("currentHoldings", 0)))
                )

    def calculate_gini_from_distribution(self, holder_supply: Dict) -> float:
        """Calculate approximate Gini coefficient from holder distribution"""
        # This is a simplified calculation based on top holder percentages
        # A more accurate Gini would require individual holder balances

        top_10 = float(holder_supply.get("top10", 0))
        top_25 = float(holder_supply.get("top25", 0))
        top_50 = float(holder_supply.get("top50", 0))
        top_100 = float(holder_supply.get("top100", 0))

        # Estimate Gini based on concentration levels
        if top_10 > 80:
            return 0.95
        elif top_10 > 60:
            return 0.85
        elif top_25 > 70:
            return 0.75
        elif top_50 > 80:
            return 0.65
        elif top_100 > 90:
            return 0.55
        else:
            return 0.45

    async def monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                logger.info("Starting Moralis monitoring cycle...")

                # Fetch all data types
                swaps = await self.fetch_token_swaps(hours_back=1)
                analytics = await self.fetch_token_analytics()
                holder_stats = await self.fetch_holder_stats()
                pair_stats = await self.fetch_pair_stats()
                profitable_wallets = await self.fetch_top_profitable_wallets()
                snipers = await self.fetch_snipers()

                # Store all data
                await self.store_swaps(swaps)
                await self.store_analytics(analytics)
                await self.store_holder_stats(holder_stats)
                await self.store_pair_stats(pair_stats)
                await self.store_profitable_wallets(profitable_wallets)

                # Log summary
                if pair_stats:
                    logger.info(f"Pair Stats - Price: ${pair_stats.get('usdPrice', 0):.2f}, "
                              f"Liquidity: ${pair_stats.get('liquidityUsd', 0):,.0f}, "
                              f"24h Volume: ${pair_stats.get('volume24h', 0):,.0f}")

                if holder_stats:
                    logger.info(f"Holder Stats - Total: {holder_stats.get('totalHolders', 0)}, "
                              f"Top 10: {holder_stats.get('holderSupply', {}).get('top10', 0):.2f}%")

                logger.info("Monitoring cycle complete")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Wait 60 seconds before next cycle
            await asyncio.sleep(60)

    async def run(self):
        """Run the monitor"""
        await self.initialize()
        try:
            await self.monitor_loop()
        finally:
            await self.cleanup()


async def main():
    monitor = MoralisBSCMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())