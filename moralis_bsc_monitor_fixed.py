"""
Fixed Moralis-based BSC Pool Monitor with Advanced Analytics
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
                -- Token swaps table (fixed)
                CREATE TABLE IF NOT EXISTS moralis_swaps (
                    id SERIAL PRIMARY KEY,
                    transaction_hash VARCHAR(66) UNIQUE,
                    block_number BIGINT,
                    block_timestamp TIMESTAMP,
                    transaction_type VARCHAR(10),
                    wallet_address VARCHAR(42),
                    bought_token VARCHAR(42),
                    bought_amount DECIMAL(40, 18),
                    bought_usd DECIMAL(30, 2),
                    sold_token VARCHAR(42),
                    sold_amount DECIMAL(40, 18),
                    sold_usd DECIMAL(30, 2),
                    total_usd DECIMAL(30, 2),
                    exchange_name VARCHAR(100),
                    pair_address VARCHAR(42),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Token analytics table (fixed)
                CREATE TABLE IF NOT EXISTS moralis_token_analytics (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    buy_volume_5m DECIMAL(30, 2),
                    sell_volume_5m DECIMAL(30, 2),
                    buy_volume_1h DECIMAL(30, 2),
                    sell_volume_1h DECIMAL(30, 2),
                    buy_volume_24h DECIMAL(30, 2),
                    sell_volume_24h DECIMAL(30, 2),
                    buyers_5m INTEGER,
                    sellers_5m INTEGER,
                    buyers_24h INTEGER,
                    sellers_24h INTEGER,
                    buys_24h INTEGER,
                    sells_24h INTEGER,
                    liquidity_usd DECIMAL(30, 2),
                    fdv DECIMAL(30, 2),
                    usd_price DECIMAL(30, 10),
                    price_change_24h DECIMAL(10, 4),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Pair statistics (fixed)
                CREATE TABLE IF NOT EXISTS moralis_pair_stats (
                    id SERIAL PRIMARY KEY,
                    pair_address VARCHAR(42),
                    token_address VARCHAR(42),
                    exchange_address VARCHAR(42),
                    usd_price DECIMAL(30, 10),
                    liquidity_usd DECIMAL(30, 2),
                    price_change_5m DECIMAL(10, 4),
                    price_change_1h DECIMAL(10, 4),
                    price_change_24h DECIMAL(10, 4),
                    liquidity_change_24h DECIMAL(10, 4),
                    volume_24h DECIMAL(30, 2),
                    buys_5m INTEGER,
                    sells_5m INTEGER,
                    buys_1h INTEGER,
                    sells_1h INTEGER,
                    buys_24h INTEGER,
                    sells_24h INTEGER,
                    buyers_1h INTEGER,
                    sellers_1h INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Wash trading detection
                CREATE TABLE IF NOT EXISTS wash_trading_alerts (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42),
                    pair_address VARCHAR(42),
                    detection_type VARCHAR(50),
                    buy_count INTEGER,
                    sell_count INTEGER,
                    total_volume DECIMAL(30, 2),
                    time_window_minutes INTEGER,
                    confidence_score DECIMAL(5, 2),
                    details JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Market manipulation alerts
                CREATE TABLE IF NOT EXISTS market_manipulation_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_type VARCHAR(50),
                    severity VARCHAR(20),
                    pair_address VARCHAR(42),
                    description TEXT,
                    metrics JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Wallet PnL tracking
                CREATE TABLE IF NOT EXISTS wallet_pnl (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42),
                    token_address VARCHAR(42),
                    total_bought DECIMAL(40, 18),
                    total_sold DECIMAL(40, 18),
                    avg_buy_price DECIMAL(30, 10),
                    avg_sell_price DECIMAL(30, 10),
                    realized_pnl DECIMAL(30, 2),
                    unrealized_pnl DECIMAL(30, 2),
                    trade_count INTEGER,
                    first_trade TIMESTAMP,
                    last_trade TIMESTAMP,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(wallet_address, token_address)
                );

                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_swaps_wallet ON moralis_swaps(wallet_address);
                CREATE INDEX IF NOT EXISTS idx_swaps_timestamp ON moralis_swaps(block_timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_wash_trading_wallet ON wash_trading_alerts(wallet_address);
                CREATE INDEX IF NOT EXISTS idx_manipulation_timestamp ON market_manipulation_alerts(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_pnl_profit ON wallet_pnl(realized_pnl DESC);
            """)

    async def fetch_token_swaps(self, hours_back: int = 1) -> List[Dict]:
        """Fetch recent swaps for BTCB"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/swaps"

            from_date = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat() + "Z"
            params = {
                "chain": "bsc",
                "limit": 100,
                "order": "DESC"
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

    async def store_swaps(self, swaps: List[Dict]):
        """Store swap data in database (fixed)"""
        if not swaps:
            return

        async with self.db_pool.acquire() as conn:
            for swap in swaps:
                try:
                    # Parse the correct fields from Moralis response
                    block_timestamp = swap.get("blockTimestamp", "")
                    if block_timestamp:
                        block_timestamp = datetime.fromisoformat(block_timestamp.replace("Z", ""))
                    else:
                        continue

                    bought = swap.get("bought", {})
                    sold = swap.get("sold", {})

                    await conn.execute("""
                        INSERT INTO moralis_swaps (
                            transaction_hash, block_number, block_timestamp,
                            transaction_type, wallet_address,
                            bought_token, bought_amount, bought_usd,
                            sold_token, sold_amount, sold_usd,
                            total_usd, exchange_name, pair_address
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                        ON CONFLICT (transaction_hash) DO NOTHING
                    """,
                        swap.get("transactionHash"),
                        int(swap.get("blockNumber", 0)),
                        block_timestamp,
                        swap.get("transactionType"),
                        swap.get("walletAddress"),
                        bought.get("address"),
                        Decimal(str(bought.get("amount", 0))),
                        Decimal(str(bought.get("usdAmount", 0))),
                        sold.get("address"),
                        Decimal(str(abs(float(sold.get("amount", 0))))),
                        Decimal(str(abs(float(sold.get("usdAmount", 0))))),
                        Decimal(str(swap.get("totalValueUsd", 0))),
                        swap.get("exchangeName"),
                        swap.get("pairAddress")
                    )
                except Exception as e:
                    logger.error(f"Error storing swap: {e}")

    async def store_analytics(self, analytics: Dict):
        """Store token analytics in database (fixed)"""
        if not analytics:
            return

        try:
            async with self.db_pool.acquire() as conn:
                # Extract nested values correctly
                buy_volume = analytics.get("totalBuyVolume", {})
                sell_volume = analytics.get("totalSellVolume", {})
                buyers = analytics.get("totalBuyers", {})
                sellers = analytics.get("totalSellers", {})
                buys = analytics.get("totalBuys", {})
                sells = analytics.get("totalSells", {})
                price_change = analytics.get("pricePercentChange", {})

                await conn.execute("""
                    INSERT INTO moralis_token_analytics (
                        token_address, buy_volume_5m, sell_volume_5m,
                        buy_volume_1h, sell_volume_1h, buy_volume_24h, sell_volume_24h,
                        buyers_5m, sellers_5m, buyers_24h, sellers_24h,
                        buys_24h, sells_24h, liquidity_usd, fdv,
                        usd_price, price_change_24h
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                """,
                    BTCB_ADDRESS,
                    Decimal(str(buy_volume.get("5m", 0))),
                    Decimal(str(sell_volume.get("5m", 0))),
                    Decimal(str(buy_volume.get("1h", 0))),
                    Decimal(str(sell_volume.get("1h", 0))),
                    Decimal(str(buy_volume.get("24h", 0))),
                    Decimal(str(sell_volume.get("24h", 0))),
                    buyers.get("5m", 0),
                    sellers.get("5m", 0),
                    buyers.get("24h", 0),
                    sellers.get("24h", 0),
                    buys.get("24h", 0),
                    sells.get("24h", 0),
                    Decimal(str(analytics.get("totalLiquidityUsd", 0))),
                    Decimal(str(analytics.get("totalFullyDilutedValuation", 0))),
                    Decimal(str(analytics.get("usdPrice", 0))),
                    Decimal(str(price_change.get("24h", 0)))
                )
                logger.info("Stored token analytics")
        except Exception as e:
            logger.error(f"Error storing analytics: {e}")

    async def store_pair_stats(self, stats: Dict):
        """Store pair statistics in database (fixed)"""
        if not stats:
            return

        try:
            async with self.db_pool.acquire() as conn:
                price_change = stats.get("pricePercentChange", {})
                liquidity_change = stats.get("liquidityPercentChange", {})
                buys = stats.get("buys", {})
                sells = stats.get("sells", {})
                buyers = stats.get("buyers", {})
                sellers = stats.get("sellers", {})
                volume = stats.get("volume", {})

                await conn.execute("""
                    INSERT INTO moralis_pair_stats (
                        pair_address, token_address, exchange_address,
                        usd_price, liquidity_usd,
                        price_change_5m, price_change_1h, price_change_24h,
                        liquidity_change_24h, volume_24h,
                        buys_5m, sells_5m, buys_1h, sells_1h,
                        buys_24h, sells_24h, buyers_1h, sellers_1h
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                """,
                    stats.get("pairAddress", POOL_ADDRESS),
                    stats.get("tokenAddress", BTCB_ADDRESS),
                    stats.get("exchangeAddress"),
                    Decimal(str(stats.get("currentUsdPrice", 0))),
                    Decimal(str(stats.get("totalLiquidityUsd", 0))),
                    Decimal(str(price_change.get("5min", 0))),
                    Decimal(str(price_change.get("1h", 0))),
                    Decimal(str(price_change.get("24h", 0))),
                    Decimal(str(liquidity_change.get("24h", 0))),
                    Decimal(str(volume.get("24h", 0) if isinstance(volume.get("24h"), (int, float, str)) else 0)),
                    buys.get("5min", 0),
                    sells.get("5min", 0),
                    buys.get("1h", 0),
                    sells.get("1h", 0),
                    buys.get("24h", 0),
                    sells.get("24h", 0),
                    buyers.get("1h", 0),
                    sellers.get("1h", 0)
                )
                logger.info("Stored pair stats")
        except Exception as e:
            logger.error(f"Error storing pair stats: {e}")

    async def detect_wash_trading(self, swaps: List[Dict]):
        """Detect potential wash trading patterns"""
        if not swaps:
            return

        # Group swaps by wallet
        wallet_trades = {}
        for swap in swaps:
            wallet = swap.get("walletAddress")
            if wallet:
                if wallet not in wallet_trades:
                    wallet_trades[wallet] = {"buys": [], "sells": [], "volume": 0}

                if swap.get("transactionType") == "buy":
                    wallet_trades[wallet]["buys"].append(swap)
                else:
                    wallet_trades[wallet]["sells"].append(swap)

                wallet_trades[wallet]["volume"] += float(swap.get("totalValueUsd", 0))

        # Analyze for wash trading patterns
        async with self.db_pool.acquire() as conn:
            for wallet, trades in wallet_trades.items():
                buy_count = len(trades["buys"])
                sell_count = len(trades["sells"])
                total_volume = trades["volume"]

                # Detection criteria
                if buy_count >= 3 and sell_count >= 3:  # Multiple round trips
                    if abs(buy_count - sell_count) <= 2:  # Similar buy/sell counts
                        confidence = min(95, 50 + (buy_count + sell_count) * 5)

                        await conn.execute("""
                            INSERT INTO wash_trading_alerts (
                                wallet_address, pair_address, detection_type,
                                buy_count, sell_count, total_volume,
                                time_window_minutes, confidence_score, details
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        """,
                            wallet,
                            POOL_ADDRESS,
                            "high_frequency_round_trips",
                            buy_count,
                            sell_count,
                            Decimal(str(total_volume)),
                            60,  # 1 hour window
                            Decimal(str(confidence)),
                            json.dumps({"pattern": "balanced_trading"})
                        )
                        logger.info(f"Wash trading alert: {wallet} - {confidence}% confidence")

    async def check_market_manipulation(self, stats: Dict, analytics: Dict):
        """Check for various market manipulation patterns"""
        if not stats or not analytics:
            return

        alerts = []

        # Check for extreme price movements
        price_change = stats.get("pricePercentChange", {})
        if abs(price_change.get("5min", 0)) > 5:
            alerts.append({
                "type": "extreme_price_movement",
                "severity": "HIGH",
                "description": f"Price changed {price_change.get('5min', 0):.2f}% in 5 minutes",
                "metrics": {"price_change_5m": price_change.get("5min", 0)}
            })

        # Check for volume anomalies
        buy_volume = analytics.get("totalBuyVolume", {})
        sell_volume = analytics.get("totalSellVolume", {})

        if buy_volume.get("5m", 0) > 0 and sell_volume.get("5m", 0) > 0:
            ratio = buy_volume.get("5m", 0) / sell_volume.get("5m", 0)
            if ratio > 3 or ratio < 0.33:
                alerts.append({
                    "type": "volume_imbalance",
                    "severity": "MEDIUM",
                    "description": f"Extreme buy/sell volume ratio: {ratio:.2f}",
                    "metrics": {
                        "buy_volume_5m": buy_volume.get("5m", 0),
                        "sell_volume_5m": sell_volume.get("5m", 0)
                    }
                })

        # Store alerts
        async with self.db_pool.acquire() as conn:
            for alert in alerts:
                await conn.execute("""
                    INSERT INTO market_manipulation_alerts (
                        alert_type, severity, pair_address, description, metrics
                    ) VALUES ($1, $2, $3, $4, $5)
                """,
                    alert["type"],
                    alert["severity"],
                    POOL_ADDRESS,
                    alert["description"],
                    json.dumps(alert["metrics"])
                )

    async def calculate_wallet_pnl(self, swaps: List[Dict]):
        """Calculate PnL for active wallets"""
        if not swaps:
            return

        wallet_data = {}
        current_price = Decimal("0")

        # Get current price from latest swap
        if swaps:
            latest = swaps[0]
            if latest.get("bought", {}).get("symbol") == "BTCB":
                current_price = Decimal(str(latest.get("bought", {}).get("usdPrice", 0)))

        # Group by wallet
        for swap in swaps:
            wallet = swap.get("walletAddress")
            if not wallet:
                continue

            if wallet not in wallet_data:
                wallet_data[wallet] = {
                    "bought": Decimal("0"),
                    "sold": Decimal("0"),
                    "buy_value": Decimal("0"),
                    "sell_value": Decimal("0"),
                    "trades": 0,
                    "first_trade": swap.get("blockTimestamp"),
                    "last_trade": swap.get("blockTimestamp")
                }

            if swap.get("transactionType") == "buy":
                amount = Decimal(str(swap.get("bought", {}).get("amount", 0)))
                value = Decimal(str(swap.get("totalValueUsd", 0)))
                wallet_data[wallet]["bought"] += amount
                wallet_data[wallet]["buy_value"] += value
            else:
                amount = Decimal(str(abs(float(swap.get("sold", {}).get("amount", 0)))))
                value = Decimal(str(swap.get("totalValueUsd", 0)))
                wallet_data[wallet]["sold"] += amount
                wallet_data[wallet]["sell_value"] += value

            wallet_data[wallet]["trades"] += 1

        # Calculate and store PnL
        async with self.db_pool.acquire() as conn:
            for wallet, data in wallet_data.items():
                if data["bought"] > 0:
                    avg_buy = data["buy_value"] / data["bought"]
                else:
                    avg_buy = Decimal("0")

                if data["sold"] > 0:
                    avg_sell = data["sell_value"] / data["sold"]
                else:
                    avg_sell = Decimal("0")

                realized_pnl = data["sell_value"] - (data["sold"] * avg_buy if data["bought"] > 0 else 0)
                holdings = data["bought"] - data["sold"]
                unrealized_pnl = holdings * current_price - holdings * avg_buy if holdings > 0 else 0

                await conn.execute("""
                    INSERT INTO wallet_pnl (
                        wallet_address, token_address,
                        total_bought, total_sold,
                        avg_buy_price, avg_sell_price,
                        realized_pnl, unrealized_pnl,
                        trade_count, first_trade, last_trade
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (wallet_address, token_address)
                    DO UPDATE SET
                        total_bought = EXCLUDED.total_bought,
                        total_sold = EXCLUDED.total_sold,
                        avg_buy_price = EXCLUDED.avg_buy_price,
                        avg_sell_price = EXCLUDED.avg_sell_price,
                        realized_pnl = EXCLUDED.realized_pnl,
                        unrealized_pnl = EXCLUDED.unrealized_pnl,
                        trade_count = EXCLUDED.trade_count,
                        last_trade = EXCLUDED.last_trade,
                        timestamp = CURRENT_TIMESTAMP
                """,
                    wallet,
                    BTCB_ADDRESS,
                    data["bought"],
                    data["sold"],
                    avg_buy,
                    avg_sell,
                    realized_pnl,
                    unrealized_pnl,
                    data["trades"],
                    datetime.fromisoformat(data["first_trade"].replace("Z", "")) if data["first_trade"] else None,
                    datetime.fromisoformat(data["last_trade"].replace("Z", "")) if data["last_trade"] else None
                )

    async def monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                logger.info("Starting Moralis monitoring cycle...")

                # Fetch all data types
                swaps = await self.fetch_token_swaps(hours_back=1)
                analytics = await self.fetch_token_analytics()
                pair_stats = await self.fetch_pair_stats()

                # Store all data
                await self.store_swaps(swaps)
                await self.store_analytics(analytics)
                await self.store_pair_stats(pair_stats)

                # Advanced analytics
                await self.detect_wash_trading(swaps)
                await self.check_market_manipulation(pair_stats, analytics)
                await self.calculate_wallet_pnl(swaps)

                # Log summary
                if pair_stats:
                    logger.info(f"Pair Stats - Price: ${pair_stats.get('currentUsdPrice', 0):.2f}, "
                              f"Liquidity: ${pair_stats.get('totalLiquidityUsd', 0):,.0f}")

                if analytics:
                    buy_vol = analytics.get("totalBuyVolume", {}).get("24h", 0)
                    sell_vol = analytics.get("totalSellVolume", {}).get("24h", 0)
                    logger.info(f"24h Volume - Buy: ${buy_vol:,.0f}, Sell: ${sell_vol:,.0f}")

                logger.info("Monitoring cycle complete")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Wait 30 seconds before next cycle
            await asyncio.sleep(30)

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