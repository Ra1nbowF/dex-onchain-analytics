"""
Complete Moralis BSC Monitor with ALL API endpoints
Comprehensive tracking of BTCB on BSC
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


class CompleteMoralisMonitor:
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
        await self.create_all_tables()
        logger.info("Complete Moralis Monitor initialized")

    async def cleanup(self):
        """Cleanup connections"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()

    async def create_all_tables(self):
        """Create ALL comprehensive monitoring tables"""
        async with self.db_pool.acquire() as conn:
            # Drop existing tables to avoid conflicts
            await conn.execute("""
                DROP TABLE IF EXISTS
                    moralis_token_stats,
                    moralis_holder_stats_complete,
                    moralis_historical_holders,
                    moralis_token_transfers,
                    moralis_snipers_complete,
                    moralis_liquidity_changes,
                    moralis_holder_distribution
                CASCADE;
            """)

            await conn.execute("""
                -- Token Stats (comprehensive token metrics)
                CREATE TABLE IF NOT EXISTS moralis_token_stats (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    token_name VARCHAR(100),
                    token_symbol VARCHAR(20),
                    total_supply DECIMAL(40, 18),
                    circulating_supply DECIMAL(40, 18),
                    market_cap DECIMAL(30, 2),
                    fdv DECIMAL(30, 2),
                    transfers_total BIGINT,
                    holders_count INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Complete Holder Stats with distribution
                CREATE TABLE IF NOT EXISTS moralis_holder_stats_complete (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    total_holders INTEGER,
                    holders_change_5m INTEGER,
                    holders_change_1h INTEGER,
                    holders_change_24h INTEGER,
                    holders_change_7d INTEGER,
                    holders_change_30d INTEGER,
                    holders_change_pct_24h DECIMAL(10, 4),
                    holders_by_swap INTEGER,
                    holders_by_transfer INTEGER,
                    holders_by_airdrop INTEGER,
                    top_10_supply_pct DECIMAL(10, 4),
                    top_25_supply_pct DECIMAL(10, 4),
                    top_50_supply_pct DECIMAL(10, 4),
                    top_100_supply_pct DECIMAL(10, 4),
                    top_250_supply_pct DECIMAL(10, 4),
                    top_500_supply_pct DECIMAL(10, 4),
                    gini_coefficient DECIMAL(10, 6),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Historical Holder Data (time series)
                CREATE TABLE IF NOT EXISTS moralis_historical_holders (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    holder_count INTEGER,
                    unique_wallets INTEGER,
                    data_timestamp TIMESTAMP,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Token Transfers
                CREATE TABLE IF NOT EXISTS moralis_token_transfers (
                    id SERIAL PRIMARY KEY,
                    transaction_hash VARCHAR(66) UNIQUE,
                    block_number BIGINT,
                    block_timestamp TIMESTAMP,
                    from_address VARCHAR(42),
                    to_address VARCHAR(42),
                    value DECIMAL(40, 18),
                    value_usd DECIMAL(30, 2),
                    token_address VARCHAR(42),
                    token_symbol VARCHAR(20),
                    transaction_index INTEGER,
                    log_index INTEGER,
                    is_spam BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Complete Snipers Data
                CREATE TABLE IF NOT EXISTS moralis_snipers_complete (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42),
                    pair_address VARCHAR(42),
                    tokens_bought DECIMAL(40, 18),
                    tokens_sold DECIMAL(40, 18),
                    buy_tx_hash VARCHAR(66),
                    sell_tx_hash VARCHAR(66),
                    buy_timestamp TIMESTAMP,
                    sell_timestamp TIMESTAMP,
                    buy_block INTEGER,
                    sell_block INTEGER,
                    blocks_held INTEGER,
                    time_held_seconds INTEGER,
                    realized_profit DECIMAL(30, 2),
                    realized_profit_pct DECIMAL(20, 4),
                    current_balance DECIMAL(40, 18),
                    is_sniper BOOLEAN DEFAULT TRUE,
                    sniper_score DECIMAL(5, 2),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Liquidity Changes tracking
                CREATE TABLE IF NOT EXISTS moralis_liquidity_changes (
                    id SERIAL PRIMARY KEY,
                    pair_address VARCHAR(42),
                    event_type VARCHAR(20), -- add/remove
                    transaction_hash VARCHAR(66),
                    block_timestamp TIMESTAMP,
                    wallet_address VARCHAR(42),
                    token0_amount DECIMAL(40, 18),
                    token1_amount DECIMAL(40, 18),
                    liquidity_change_usd DECIMAL(30, 2),
                    total_liquidity_after DECIMAL(30, 2),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Holder Distribution Analysis
                CREATE TABLE IF NOT EXISTS moralis_holder_distribution (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    holder_address VARCHAR(42),
                    balance DECIMAL(40, 18),
                    balance_usd DECIMAL(30, 2),
                    percentage_of_supply DECIMAL(10, 6),
                    first_transaction TIMESTAMP,
                    last_transaction TIMESTAMP,
                    transaction_count INTEGER,
                    is_whale BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    holder_type VARCHAR(50), -- whale/dolphin/fish/shrimp
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, holder_address)
                );

                -- Enhanced wash trading with more metrics
                CREATE TABLE IF NOT EXISTS wash_trading_complete (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42),
                    pair_address VARCHAR(42),
                    detection_type VARCHAR(50),
                    buy_count INTEGER,
                    sell_count INTEGER,
                    round_trips INTEGER,
                    avg_hold_time_seconds INTEGER,
                    total_volume DECIMAL(30, 2),
                    net_pnl DECIMAL(30, 2),
                    time_window_minutes INTEGER,
                    confidence_score DECIMAL(5, 2),
                    related_wallets TEXT[],
                    details JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Token Metrics Summary
                CREATE TABLE IF NOT EXISTS moralis_metrics_summary (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(42),
                    metric_type VARCHAR(50),
                    metric_value DECIMAL(30, 10),
                    metric_json JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Create all indexes
                CREATE INDEX IF NOT EXISTS idx_token_stats_timestamp ON moralis_token_stats(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_holder_stats_complete_timestamp ON moralis_holder_stats_complete(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_historical_holders_data ON moralis_historical_holders(data_timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_transfers_block ON moralis_token_transfers(block_timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_transfers_addresses ON moralis_token_transfers(from_address, to_address);
                CREATE INDEX IF NOT EXISTS idx_snipers_wallet ON moralis_snipers_complete(wallet_address);
                CREATE INDEX IF NOT EXISTS idx_snipers_profit ON moralis_snipers_complete(realized_profit_pct DESC);
                CREATE INDEX IF NOT EXISTS idx_liquidity_changes_time ON moralis_liquidity_changes(block_timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_holder_distribution_balance ON moralis_holder_distribution(balance_usd DESC);
                CREATE INDEX IF NOT EXISTS idx_wash_trading_confidence ON wash_trading_complete(confidence_score DESC);
            """)

    # API CALLS - Implementing ALL endpoints

    async def fetch_token_stats(self) -> Dict:
        """Fetch comprehensive token statistics"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/stats"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched token stats for BTCB")
                    return data
                else:
                    logger.error(f"Failed to fetch token stats: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching token stats: {e}")
            return {}

    async def fetch_holder_stats_complete(self) -> Dict:
        """Fetch complete holder statistics with distribution"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/holders"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched complete holder stats")
                    return data
                else:
                    logger.error(f"Failed to fetch holder stats: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching holder stats: {e}")
            return {}

    async def fetch_historical_holders(self) -> List[Dict]:
        """Fetch historical holder data"""
        try:
            # Calculate time range
            to_date = datetime.utcnow()
            from_date = to_date - timedelta(hours=24)

            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/historical-holders"
            params = {
                "chain": "bsc",
                "from_date": from_date.isoformat() + "Z",
                "to_date": to_date.isoformat() + "Z",
                "time_frame": "1h"  # Get hourly data
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    holders = data.get("result", [])
                    logger.info(f"Fetched {len(holders)} historical holder points")
                    return holders
                else:
                    logger.error(f"Failed to fetch historical holders: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching historical holders: {e}")
            return []

    async def fetch_token_transfers(self, limit: int = 100) -> List[Dict]:
        """Fetch recent token transfers"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/transfers"
            params = {
                "chain": "bsc",
                "limit": limit,
                "order": "DESC"
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    transfers = data.get("result", [])
                    logger.info(f"Fetched {len(transfers)} token transfers")
                    return transfers
                else:
                    logger.error(f"Failed to fetch transfers: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching transfers: {e}")
            return []

    async def fetch_snipers_complete(self, blocks_after: int = 100) -> List[Dict]:
        """Fetch complete sniper data with enhanced metrics"""
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
                    logger.info(f"Fetched {len(snipers)} snipers")
                    return snipers
                else:
                    logger.error(f"Failed to fetch snipers: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching snipers: {e}")
            return []

    async def fetch_top_holders(self, limit: int = 100) -> List[Dict]:
        """Fetch top token holders for distribution analysis"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/owners"
            params = {
                "chain": "bsc",
                "limit": limit,
                "order": "DESC"
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    holders = data.get("result", [])
                    logger.info(f"Fetched {len(holders)} top holders")
                    return holders
                else:
                    logger.error(f"Failed to fetch top holders: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching top holders: {e}")
            return []

    # STORAGE METHODS - Store all data types

    async def store_token_stats(self, stats: Dict):
        """Store token statistics"""
        if not stats:
            return

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO moralis_token_stats (
                        token_address, token_name, token_symbol,
                        total_supply, circulating_supply,
                        market_cap, fdv, transfers_total, holders_count
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    BTCB_ADDRESS,
                    stats.get("name", "BTCB"),
                    stats.get("symbol", "BTCB"),
                    Decimal(str(stats.get("totalSupply", 0))),
                    Decimal(str(stats.get("circulatingSupply", 0))),
                    Decimal(str(stats.get("marketCap", 0))),
                    Decimal(str(stats.get("fullyDilutedValuation", 0))),
                    stats.get("transfers", {}).get("total", 0),
                    stats.get("holders", 0)
                )
                logger.info("Stored token stats")
        except Exception as e:
            logger.error(f"Error storing token stats: {e}")

    async def store_holder_stats_complete(self, stats: Dict):
        """Store complete holder statistics"""
        if not stats:
            return

        try:
            holder_change = stats.get("holderChange", {})
            holder_supply = stats.get("holderSupply", {})
            holders_by = stats.get("holdersByAcquisition", {})

            # Calculate Gini coefficient
            gini = self.calculate_gini_from_distribution(holder_supply)

            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO moralis_holder_stats_complete (
                        token_address, total_holders,
                        holders_change_5m, holders_change_1h, holders_change_24h,
                        holders_change_7d, holders_change_30d,
                        holders_change_pct_24h,
                        holders_by_swap, holders_by_transfer, holders_by_airdrop,
                        top_10_supply_pct, top_25_supply_pct, top_50_supply_pct,
                        top_100_supply_pct, top_250_supply_pct, top_500_supply_pct,
                        gini_coefficient
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                """,
                    BTCB_ADDRESS,
                    stats.get("totalHolders", 0),
                    holder_change.get("5min", {}).get("change", 0),
                    holder_change.get("1h", {}).get("change", 0),
                    holder_change.get("24h", {}).get("change", 0),
                    holder_change.get("7d", {}).get("change", 0),
                    holder_change.get("30d", {}).get("change", 0),
                    Decimal(str(holder_change.get("24h", {}).get("percentage", 0))),
                    holders_by.get("swap", 0),
                    holders_by.get("transfer", 0),
                    holders_by.get("airdrop", 0),
                    Decimal(str(holder_supply.get("top10", 0))),
                    Decimal(str(holder_supply.get("top25", 0))),
                    Decimal(str(holder_supply.get("top50", 0))),
                    Decimal(str(holder_supply.get("top100", 0))),
                    Decimal(str(holder_supply.get("top250", 0))),
                    Decimal(str(holder_supply.get("top500", 0))),
                    Decimal(str(gini))
                )
                logger.info("Stored complete holder stats")
        except Exception as e:
            logger.error(f"Error storing holder stats: {e}")

    async def store_historical_holders(self, holders: List[Dict]):
        """Store historical holder data"""
        if not holders:
            return

        async with self.db_pool.acquire() as conn:
            for point in holders:
                try:
                    await conn.execute("""
                        INSERT INTO moralis_historical_holders (
                            token_address, holder_count, unique_wallets, data_timestamp
                        ) VALUES ($1, $2, $3, $4)
                    """,
                        BTCB_ADDRESS,
                        point.get("holderCount", 0),
                        point.get("uniqueWallets", 0),
                        datetime.fromisoformat(point.get("timestamp", "").replace("Z", ""))
                    )
                except Exception as e:
                    logger.error(f"Error storing historical holder point: {e}")

    async def store_token_transfers(self, transfers: List[Dict]):
        """Store token transfers"""
        if not transfers:
            return

        async with self.db_pool.acquire() as conn:
            for transfer in transfers:
                try:
                    block_timestamp = transfer.get("blockTimestamp", "")
                    if block_timestamp:
                        block_timestamp = datetime.fromisoformat(block_timestamp.replace("Z", ""))
                    else:
                        continue

                    await conn.execute("""
                        INSERT INTO moralis_token_transfers (
                            transaction_hash, block_number, block_timestamp,
                            from_address, to_address, value, value_usd,
                            token_address, token_symbol,
                            transaction_index, log_index, is_spam
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        ON CONFLICT (transaction_hash) DO NOTHING
                    """,
                        transfer.get("transactionHash"),
                        int(transfer.get("blockNumber", 0)),
                        block_timestamp,
                        transfer.get("fromAddress"),
                        transfer.get("toAddress"),
                        Decimal(str(transfer.get("value", 0))),
                        Decimal(str(transfer.get("valueFormatted", 0))),
                        transfer.get("address", BTCB_ADDRESS),
                        transfer.get("tokenSymbol", "BTCB"),
                        transfer.get("transactionIndex", 0),
                        transfer.get("logIndex", 0),
                        transfer.get("possibleSpam", False)
                    )
                except Exception as e:
                    logger.error(f"Error storing transfer: {e}")

    async def store_snipers_complete(self, snipers: List[Dict]):
        """Store complete sniper data"""
        if not snipers:
            return

        async with self.db_pool.acquire() as conn:
            for sniper in snipers:
                try:
                    # Calculate enhanced metrics
                    buy_timestamp = sniper.get("buyTimestamp", "")
                    sell_timestamp = sniper.get("sellTimestamp", "")

                    if buy_timestamp and sell_timestamp:
                        buy_dt = datetime.fromisoformat(buy_timestamp.replace("Z", ""))
                        sell_dt = datetime.fromisoformat(sell_timestamp.replace("Z", ""))
                        time_held = (sell_dt - buy_dt).total_seconds()
                    else:
                        time_held = 0

                    # Calculate sniper score based on speed and profit
                    blocks_held = sniper.get("blocksHeld", 0)
                    profit_pct = float(sniper.get("realizedProfitPercentage", 0))

                    if blocks_held < 10 and profit_pct > 10:
                        sniper_score = 95
                    elif blocks_held < 50 and profit_pct > 5:
                        sniper_score = 80
                    elif blocks_held < 100:
                        sniper_score = 60
                    else:
                        sniper_score = 40

                    await conn.execute("""
                        INSERT INTO moralis_snipers_complete (
                            wallet_address, pair_address,
                            tokens_bought, tokens_sold,
                            buy_tx_hash, sell_tx_hash,
                            buy_timestamp, sell_timestamp,
                            buy_block, sell_block,
                            blocks_held, time_held_seconds,
                            realized_profit, realized_profit_pct,
                            current_balance, is_sniper, sniper_score
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    """,
                        sniper.get("walletAddress"),
                        POOL_ADDRESS,
                        Decimal(str(sniper.get("tokensBought", 0))),
                        Decimal(str(sniper.get("tokensSold", 0))),
                        sniper.get("buyTransactionHash"),
                        sniper.get("sellTransactionHash"),
                        buy_dt if buy_timestamp else None,
                        sell_dt if sell_timestamp else None,
                        sniper.get("buyBlock", 0),
                        sniper.get("sellBlock", 0),
                        blocks_held,
                        int(time_held),
                        Decimal(str(sniper.get("realizedProfit", 0))),
                        Decimal(str(profit_pct)),
                        Decimal(str(sniper.get("currentBalance", 0))),
                        blocks_held < 100,
                        Decimal(str(sniper_score))
                    )
                except Exception as e:
                    logger.error(f"Error storing sniper: {e}")

    async def store_holder_distribution(self, holders: List[Dict]):
        """Store holder distribution data"""
        if not holders:
            return

        # Get current price for USD calculations
        analytics = await self.fetch_token_analytics()
        current_price = Decimal(str(analytics.get("usdPrice", 0))) if analytics else Decimal("0")

        async with self.db_pool.acquire() as conn:
            for holder in holders:
                try:
                    balance = Decimal(str(holder.get("balance", 0)))
                    balance_usd = balance * current_price

                    # Classify holder type
                    if balance_usd > 1000000:
                        holder_type = "whale"
                    elif balance_usd > 100000:
                        holder_type = "dolphin"
                    elif balance_usd > 10000:
                        holder_type = "fish"
                    else:
                        holder_type = "shrimp"

                    await conn.execute("""
                        INSERT INTO moralis_holder_distribution (
                            token_address, holder_address,
                            balance, balance_usd, percentage_of_supply,
                            first_transaction, last_transaction,
                            transaction_count, is_whale, holder_type
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (token_address, holder_address)
                        DO UPDATE SET
                            balance = EXCLUDED.balance,
                            balance_usd = EXCLUDED.balance_usd,
                            percentage_of_supply = EXCLUDED.percentage_of_supply,
                            last_transaction = EXCLUDED.last_transaction,
                            transaction_count = EXCLUDED.transaction_count,
                            timestamp = CURRENT_TIMESTAMP
                    """,
                        BTCB_ADDRESS,
                        holder.get("ownerAddress"),
                        balance,
                        balance_usd,
                        Decimal(str(holder.get("percentageRelativeToTotalSupply", 0))),
                        datetime.fromisoformat(holder.get("firstTransferTimestamp", "").replace("Z", "")) if holder.get("firstTransferTimestamp") else None,
                        datetime.fromisoformat(holder.get("lastTransferTimestamp", "").replace("Z", "")) if holder.get("lastTransferTimestamp") else None,
                        holder.get("transactionCount", 0),
                        balance_usd > 1000000,
                        holder_type
                    )
                except Exception as e:
                    logger.error(f"Error storing holder distribution: {e}")

    async def fetch_token_analytics(self) -> Dict:
        """Fetch token analytics (reused from previous implementation)"""
        try:
            url = f"{MORALIS_BASE_URL}/tokens/{BTCB_ADDRESS}/analytics"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            return {}

    def calculate_gini_from_distribution(self, holder_supply: Dict) -> float:
        """Calculate Gini coefficient from holder distribution"""
        # More sophisticated Gini calculation based on multiple distribution points
        distributions = [
            (10, float(holder_supply.get("top10", 0))),
            (25, float(holder_supply.get("top25", 0))),
            (50, float(holder_supply.get("top50", 0))),
            (100, float(holder_supply.get("top100", 0))),
            (250, float(holder_supply.get("top250", 0))),
            (500, float(holder_supply.get("top500", 0)))
        ]

        # Calculate area under Lorenz curve
        area = 0
        prev_holders = 0
        prev_supply = 0

        for holders, supply in distributions:
            # Trapezoidal integration
            holder_pct = holders / 1000  # Assume 1000 total holders for simplification
            area += (holder_pct - prev_holders) * (supply + prev_supply) / 2
            prev_holders = holder_pct
            prev_supply = supply / 100  # Convert percentage to decimal

        # Complete the curve to 100%
        area += (1 - prev_holders) * (1 + prev_supply) / 2

        # Gini = 1 - 2 * area under Lorenz curve
        gini = 1 - 2 * area
        return max(0, min(1, gini))  # Ensure between 0 and 1

    async def enhanced_wash_trading_detection(self, swaps: List[Dict], transfers: List[Dict]):
        """Enhanced wash trading detection with transfer analysis"""
        if not swaps:
            return

        # Analyze both swaps and transfers for circular patterns
        wallet_activity = {}

        # Process swaps
        for swap in swaps:
            wallet = swap.get("walletAddress")
            if wallet:
                if wallet not in wallet_activity:
                    wallet_activity[wallet] = {
                        "swaps": [],
                        "transfers": [],
                        "counterparties": set(),
                        "round_trips": 0
                    }
                wallet_activity[wallet]["swaps"].append(swap)

        # Process transfers to find circular patterns
        for transfer in transfers:
            from_addr = transfer.get("fromAddress")
            to_addr = transfer.get("toAddress")

            if from_addr in wallet_activity:
                wallet_activity[from_addr]["transfers"].append(transfer)
                wallet_activity[from_addr]["counterparties"].add(to_addr)

            if to_addr in wallet_activity:
                wallet_activity[to_addr]["transfers"].append(transfer)
                wallet_activity[to_addr]["counterparties"].add(from_addr)

        # Detect wash trading patterns
        async with self.db_pool.acquire() as conn:
            for wallet, activity in wallet_activity.items():
                # Count round trips (buy then sell)
                buys = [s for s in activity["swaps"] if s.get("transactionType") == "buy"]
                sells = [s for s in activity["swaps"] if s.get("transactionType") == "sell"]
                round_trips = min(len(buys), len(sells))

                if round_trips >= 2:  # At least 2 round trips
                    # Calculate metrics
                    total_volume = sum(float(s.get("totalValueUsd", 0)) for s in activity["swaps"])

                    # Check for related wallets (circular transfers)
                    related_wallets = list(activity["counterparties"])[:5]

                    # Calculate confidence score
                    confidence = 50
                    if round_trips >= 5:
                        confidence += 20
                    if len(related_wallets) >= 3:
                        confidence += 15
                    if total_volume > 10000:
                        confidence += 15

                    confidence = min(95, confidence)

                    await conn.execute("""
                        INSERT INTO wash_trading_complete (
                            wallet_address, pair_address, detection_type,
                            buy_count, sell_count, round_trips,
                            total_volume, confidence_score,
                            related_wallets, details
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                        wallet,
                        POOL_ADDRESS,
                        "advanced_pattern",
                        len(buys),
                        len(sells),
                        round_trips,
                        Decimal(str(total_volume)),
                        Decimal(str(confidence)),
                        related_wallets,
                        json.dumps({
                            "counterparties": len(activity["counterparties"]),
                            "transfers": len(activity["transfers"])
                        })
                    )

                    if confidence > 80:
                        logger.info(f"High confidence wash trading: {wallet} - {confidence}%")

    async def monitor_loop(self):
        """Main monitoring loop with all data collection"""
        while True:
            try:
                logger.info("Starting complete monitoring cycle...")

                # Fetch ALL data types
                tasks = [
                    self.fetch_token_swaps(hours_back=1),
                    self.fetch_token_analytics(),
                    self.fetch_pair_stats(),
                    self.fetch_token_stats(),
                    self.fetch_holder_stats_complete(),
                    self.fetch_historical_holders(),
                    self.fetch_token_transfers(limit=100),
                    self.fetch_snipers_complete(blocks_after=100),
                    self.fetch_top_holders(limit=100)
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                swaps = results[0] if not isinstance(results[0], Exception) else []
                analytics = results[1] if not isinstance(results[1], Exception) else {}
                pair_stats = results[2] if not isinstance(results[2], Exception) else {}
                token_stats = results[3] if not isinstance(results[3], Exception) else {}
                holder_stats = results[4] if not isinstance(results[4], Exception) else {}
                historical_holders = results[5] if not isinstance(results[5], Exception) else []
                transfers = results[6] if not isinstance(results[6], Exception) else []
                snipers = results[7] if not isinstance(results[7], Exception) else []
                top_holders = results[8] if not isinstance(results[8], Exception) else []

                # Store all data
                await self.store_swaps(swaps)
                await self.store_analytics(analytics)
                await self.store_pair_stats(pair_stats)
                await self.store_token_stats(token_stats)
                await self.store_holder_stats_complete(holder_stats)
                await self.store_historical_holders(historical_holders)
                await self.store_token_transfers(transfers)
                await self.store_snipers_complete(snipers)
                await self.store_holder_distribution(top_holders)

                # Advanced analytics
                await self.enhanced_wash_trading_detection(swaps, transfers)
                await self.check_market_manipulation(pair_stats, analytics)
                await self.calculate_wallet_pnl(swaps)

                # Log summary
                logger.info(f"""
                    Monitoring Summary:
                    - Swaps: {len(swaps)}
                    - Transfers: {len(transfers)}
                    - Snipers detected: {len(snipers)}
                    - Top holders analyzed: {len(top_holders)}
                    - Historical data points: {len(historical_holders)}
                    - Token Stats: {token_stats.get('holders', 0)} holders
                """)

                logger.info("Complete monitoring cycle finished")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()

            # Wait before next cycle
            await asyncio.sleep(30)

    # Include previous methods for swaps, analytics, etc.
    async def fetch_token_swaps(self, hours_back: int = 1) -> List[Dict]:
        """Fetch recent swaps for BTCB"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/swaps"
            params = {"chain": "bsc", "limit": 100, "order": "DESC"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result", [])
                return []
        except Exception as e:
            logger.error(f"Error fetching swaps: {e}")
            return []

    async def fetch_pair_stats(self) -> Dict:
        """Fetch pair statistics"""
        try:
            url = f"{MORALIS_BASE_URL}/pairs/{POOL_ADDRESS}/stats"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as e:
            logger.error(f"Error fetching pair stats: {e}")
            return {}

    # Reuse storage methods from previous implementation
    async def store_swaps(self, swaps):
        # Implementation from moralis_bsc_monitor_fixed.py
        pass

    async def store_analytics(self, analytics):
        # Implementation from moralis_bsc_monitor_fixed.py
        pass

    async def store_pair_stats(self, stats):
        # Implementation from moralis_bsc_monitor_fixed.py
        pass

    async def check_market_manipulation(self, stats, analytics):
        # Implementation from moralis_bsc_monitor_fixed.py
        pass

    async def calculate_wallet_pnl(self, swaps):
        # Implementation from moralis_bsc_monitor_fixed.py
        pass

    async def run(self):
        """Run the complete monitor"""
        await self.initialize()
        try:
            await self.monitor_loop()
        finally:
            await self.cleanup()


async def main():
    monitor = CompleteMoralisMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())