import os
import asyncio
import aiohttp
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/dex_analytics")
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

# BSC BTCB Token and Pool addresses
BTCB_ADDRESS = "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

class EnhancedMoralisMonitor:
    def __init__(self):
        self.db_pool = None
        self.session = None
        self.headers = {
            "accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }

    async def init_db(self):
        """Initialize database connection pool and tables"""
        try:
            self.db_pool = await asyncpg.create_pool(DATABASE_URL)
            await self.create_enhanced_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def create_enhanced_tables(self):
        """Create all enhanced tables including new ones for missing endpoints"""
        async with self.db_pool.acquire() as conn:
            # Enhanced swaps table with new fields from API
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moralis_swaps_enhanced (
                    id SERIAL PRIMARY KEY,
                    transaction_hash TEXT UNIQUE,
                    transaction_index INT,
                    transaction_type TEXT, -- buy/sell
                    sub_category TEXT, -- accumulation, etc
                    block_number BIGINT,
                    block_timestamp TIMESTAMP,
                    wallet_address TEXT,
                    wallet_address_label TEXT,
                    entity TEXT,
                    entity_logo TEXT,
                    pair_address TEXT,
                    pair_label TEXT,
                    exchange_address TEXT,
                    exchange_name TEXT,
                    exchange_logo TEXT,
                    bought_address TEXT,
                    bought_name TEXT,
                    bought_symbol TEXT,
                    bought_logo TEXT,
                    bought_amount NUMERIC(40, 18),
                    bought_usd_price NUMERIC(20, 8),
                    bought_usd_amount NUMERIC(20, 2),
                    sold_address TEXT,
                    sold_name TEXT,
                    sold_symbol TEXT,
                    sold_logo TEXT,
                    sold_amount NUMERIC(40, 18),
                    sold_usd_price NUMERIC(20, 8),
                    sold_usd_amount NUMERIC(20, 2),
                    base_quote_price NUMERIC(40, 18),
                    total_value_usd NUMERIC(20, 2),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Token holder stats with distribution categories
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moralis_token_holder_stats (
                    id SERIAL PRIMARY KEY,
                    token_address TEXT,
                    total_holders INT,
                    holder_supply_top10 NUMERIC(40, 18),
                    holder_supply_top10_percent NUMERIC(10, 6),
                    holder_supply_top25 NUMERIC(40, 18),
                    holder_supply_top25_percent NUMERIC(10, 6),
                    holder_supply_top50 NUMERIC(40, 18),
                    holder_supply_top50_percent NUMERIC(10, 6),
                    holder_supply_top100 NUMERIC(40, 18),
                    holder_supply_top100_percent NUMERIC(10, 6),
                    holder_change_5min INT,
                    holder_change_5min_percent NUMERIC(10, 6),
                    holder_change_1h INT,
                    holder_change_1h_percent NUMERIC(10, 6),
                    holder_change_24h INT,
                    holder_change_24h_percent NUMERIC(10, 6),
                    holders_by_swap INT,
                    holders_by_transfer INT,
                    holders_by_airdrop INT,
                    whales_count INT,
                    sharks_count INT,
                    dolphins_count INT,
                    fish_count INT,
                    octopus_count INT,
                    crabs_count INT,
                    shrimps_count INT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, timestamp)
                )
            """)

            # Historical holders timeseries
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moralis_historical_holders_enhanced (
                    id SERIAL PRIMARY KEY,
                    token_address TEXT,
                    timestamp TIMESTAMP,
                    total_holders INT,
                    net_holder_change INT,
                    holder_percent_change NUMERIC(10, 6),
                    new_holders_by_swap INT,
                    new_holders_by_transfer INT,
                    new_holders_by_airdrop INT,
                    holders_in_whales INT,
                    holders_in_sharks INT,
                    holders_in_dolphins INT,
                    holders_in_fish INT,
                    holders_in_octopus INT,
                    holders_in_crabs INT,
                    holders_in_shrimps INT,
                    holders_out_whales INT,
                    holders_out_sharks INT,
                    holders_out_dolphins INT,
                    holders_out_fish INT,
                    holders_out_octopus INT,
                    holders_out_crabs INT,
                    holders_out_shrimps INT,
                    UNIQUE(token_address, timestamp)
                )
            """)

            # Pair stats with comprehensive metrics
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moralis_pair_stats_enhanced (
                    id SERIAL PRIMARY KEY,
                    pair_address TEXT,
                    token_address TEXT,
                    token_name TEXT,
                    token_symbol TEXT,
                    token_logo TEXT,
                    pair_created TIMESTAMP,
                    pair_label TEXT,
                    exchange TEXT,
                    exchange_address TEXT,
                    exchange_logo TEXT,
                    exchange_url TEXT,
                    current_usd_price NUMERIC(20, 10),
                    current_native_price NUMERIC(20, 10),
                    total_liquidity_usd NUMERIC(20, 2),
                    price_change_5min NUMERIC(10, 6),
                    price_change_1h NUMERIC(10, 6),
                    price_change_4h NUMERIC(10, 6),
                    price_change_24h NUMERIC(10, 6),
                    liquidity_change_5min NUMERIC(10, 6),
                    liquidity_change_1h NUMERIC(10, 6),
                    liquidity_change_4h NUMERIC(10, 6),
                    liquidity_change_24h NUMERIC(10, 6),
                    buys_5min INT,
                    buys_1h INT,
                    buys_4h INT,
                    buys_24h INT,
                    sells_5min INT,
                    sells_1h INT,
                    sells_4h INT,
                    sells_24h INT,
                    volume_5min NUMERIC(20, 2),
                    volume_1h NUMERIC(20, 2),
                    volume_4h NUMERIC(20, 2),
                    volume_24h NUMERIC(20, 2),
                    buy_volume_5min NUMERIC(20, 2),
                    buy_volume_1h NUMERIC(20, 2),
                    buy_volume_4h NUMERIC(20, 2),
                    buy_volume_24h NUMERIC(20, 2),
                    sell_volume_5min NUMERIC(20, 2),
                    sell_volume_1h NUMERIC(20, 2),
                    sell_volume_4h NUMERIC(20, 2),
                    sell_volume_24h NUMERIC(20, 2),
                    buyers_5min INT,
                    buyers_1h INT,
                    buyers_4h INT,
                    buyers_24h INT,
                    sellers_5min INT,
                    sellers_1h INT,
                    sellers_4h INT,
                    sellers_24h INT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(pair_address, timestamp)
                )
            """)

            # Token analytics with comprehensive time-based metrics
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moralis_token_analytics_enhanced (
                    id SERIAL PRIMARY KEY,
                    token_address TEXT,
                    category_id TEXT,
                    buy_volume_5m NUMERIC(20, 2),
                    buy_volume_1h NUMERIC(20, 2),
                    buy_volume_6h NUMERIC(20, 2),
                    buy_volume_24h NUMERIC(20, 2),
                    sell_volume_5m NUMERIC(20, 2),
                    sell_volume_1h NUMERIC(20, 2),
                    sell_volume_6h NUMERIC(20, 2),
                    sell_volume_24h NUMERIC(20, 2),
                    buyers_5m INT,
                    buyers_1h INT,
                    buyers_6h INT,
                    buyers_24h INT,
                    sellers_5m INT,
                    sellers_1h INT,
                    sellers_6h INT,
                    sellers_24h INT,
                    buys_5m INT,
                    buys_1h INT,
                    buys_6h INT,
                    buys_24h INT,
                    sells_5m INT,
                    sells_1h INT,
                    sells_6h INT,
                    sells_24h INT,
                    liquidity_5m NUMERIC(20, 2),
                    liquidity_1h NUMERIC(20, 2),
                    liquidity_6h NUMERIC(20, 2),
                    liquidity_24h NUMERIC(20, 2),
                    fdv_5m NUMERIC(20, 2),
                    fdv_1h NUMERIC(20, 2),
                    fdv_6h NUMERIC(20, 2),
                    fdv_24h NUMERIC(20, 2),
                    price_change_5m NUMERIC(10, 6),
                    price_change_1h NUMERIC(10, 6),
                    price_change_6h NUMERIC(10, 6),
                    price_change_24h NUMERIC(10, 6),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, timestamp)
                )
            """)

            # Enhanced snipers table with PnL data
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moralis_snipers_enhanced (
                    id SERIAL PRIMARY KEY,
                    pair_address TEXT,
                    transaction_hash TEXT,
                    block_timestamp TIMESTAMP,
                    block_number BIGINT,
                    wallet_address TEXT,
                    total_tokens_sniped NUMERIC(40, 18),
                    total_sniped_usd NUMERIC(20, 2),
                    total_sniped_transactions INT,
                    total_tokens_sold NUMERIC(40, 18),
                    total_sold_usd NUMERIC(20, 2),
                    total_sell_transactions INT,
                    current_balance NUMERIC(40, 18),
                    current_balance_usd_value NUMERIC(20, 2),
                    realized_profit_percentage NUMERIC(10, 6),
                    realized_profit_usd NUMERIC(20, 2),
                    blocks_after_creation INT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(pair_address, wallet_address)
                )
            """)

            # Top gainers/profitable wallets
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moralis_top_gainers (
                    id SERIAL PRIMARY KEY,
                    token_address TEXT,
                    wallet_address TEXT,
                    avg_buy_price_usd NUMERIC(20, 8),
                    avg_cost_of_quantity_sold NUMERIC(20, 8),
                    avg_sell_price_usd NUMERIC(20, 8),
                    count_of_trades INT,
                    realized_profit_percentage NUMERIC(10, 6),
                    realized_profit_usd NUMERIC(20, 2),
                    total_sold_usd NUMERIC(20, 2),
                    total_tokens_bought NUMERIC(40, 18),
                    total_tokens_sold NUMERIC(40, 18),
                    total_usd_invested NUMERIC(20, 2),
                    timeframe TEXT, -- all, 7, 30 days
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, wallet_address, timeframe)
                )
            """)

            # Token stats (simple endpoint)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moralis_token_stats_simple (
                    id SERIAL PRIMARY KEY,
                    token_address TEXT,
                    total_transfers BIGINT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, timestamp)
                )
            """)

    async def init_session(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()

    # New API endpoint implementations
    async def fetch_token_swaps(self, token_address: str, limit: int = 100) -> List[Dict]:
        """Fetch swap transactions by token address"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{token_address}/swaps"
            params = {
                "chain": "bsc",
                "limit": limit,
                "order": "DESC"
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    swaps = data.get("result", [])
                    logger.info(f"Fetched {len(swaps)} token swaps")
                    return swaps
                else:
                    text = await response.text()
                    logger.warning(f"Token swaps API returned {response.status}: {text[:200]}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching token swaps: {e}")
            return []

    async def fetch_token_holder_stats(self, token_address: str) -> Dict:
        """Get holder statistics for a token"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{token_address}/holders"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched token holder stats")
                    return data
                else:
                    logger.warning(f"Holder stats API returned {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching holder stats: {e}")
            return {}

    async def fetch_historical_holders(self, token_address: str, from_date: str, to_date: str, timeframe: str = "1h") -> List[Dict]:
        """Get historical holder data"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{token_address}/holders/historical"
            params = {
                "chain": "bsc",
                "fromDate": from_date,
                "toDate": to_date,
                "timeFrame": timeframe
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get("result", [])
                    logger.info(f"Fetched {len(result)} historical holder records")
                    return result
                else:
                    logger.warning(f"Historical holders API returned {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching historical holders: {e}")
            return []

    async def fetch_pair_stats(self, pair_address: str) -> Dict:
        """Get comprehensive pair statistics"""
        try:
            url = f"{MORALIS_BASE_URL}/pairs/{pair_address}/stats"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched pair stats")
                    return data
                else:
                    logger.warning(f"Pair stats API returned {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching pair stats: {e}")
            return {}

    async def fetch_token_analytics(self, token_address: str) -> Dict:
        """Get comprehensive token analytics"""
        try:
            url = f"{MORALIS_BASE_URL}/tokens/{token_address}/analytics"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched token analytics")
                    return data
                else:
                    logger.warning(f"Token analytics API returned {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching token analytics: {e}")
            return {}

    async def fetch_token_stats(self, token_address: str) -> Dict:
        """Get simple token stats (transfer count)"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{token_address}/stats"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched token stats")
                    return data
                else:
                    logger.warning(f"Token stats API returned {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching token stats: {e}")
            return {}

    async def fetch_snipers(self, pair_address: str, blocks_after_creation: int = 10) -> Dict:
        """Get sniper wallets for a pair"""
        try:
            url = f"{MORALIS_BASE_URL}/pairs/{pair_address}/snipers"
            params = {
                "chain": "bsc",
                "blocksAfterCreation": blocks_after_creation
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched snipers data")
                    return data
                else:
                    logger.warning(f"Snipers API returned {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching snipers: {e}")
            return {}

    async def fetch_top_gainers(self, token_address: str, days: str = "all") -> Dict:
        """Get top profitable wallets for a token"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{token_address}/top-gainers"
            params = {
                "chain": "bsc",
                "days": days
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched top gainers")
                    return data
                else:
                    logger.warning(f"Top gainers API returned {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return {}

    # Storage methods for new data
    async def store_token_swaps(self, swaps: List[Dict]):
        """Store enhanced swap data"""
        if not swaps:
            return

        async with self.db_pool.acquire() as conn:
            for swap in swaps:
                try:
                    # Parse timestamp
                    block_timestamp = swap.get("blockTimestamp", "")
                    if block_timestamp:
                        block_dt = datetime.fromisoformat(block_timestamp.replace("Z", "+00:00"))
                    else:
                        block_dt = datetime.utcnow()

                    bought = swap.get("bought", {})
                    sold = swap.get("sold", {})

                    await conn.execute("""
                        INSERT INTO moralis_swaps_enhanced (
                            transaction_hash, transaction_index, transaction_type, sub_category,
                            block_number, block_timestamp, wallet_address, wallet_address_label,
                            entity, entity_logo, pair_address, pair_label, exchange_address,
                            exchange_name, exchange_logo, bought_address, bought_name, bought_symbol,
                            bought_logo, bought_amount, bought_usd_price, bought_usd_amount,
                            sold_address, sold_name, sold_symbol, sold_logo, sold_amount,
                            sold_usd_price, sold_usd_amount, base_quote_price, total_value_usd
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                                 $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31)
                        ON CONFLICT (transaction_hash) DO NOTHING
                    """,
                        swap.get("transactionHash"),
                        swap.get("transactionIndex", 0),
                        swap.get("transactionType"),
                        swap.get("subCategory"),
                        swap.get("blockNumber", 0),
                        block_dt,
                        swap.get("walletAddress"),
                        swap.get("walletAddressLabel"),
                        swap.get("entity"),
                        swap.get("entityLogo"),
                        swap.get("pairAddress"),
                        swap.get("pairLabel"),
                        swap.get("exchangeAddress"),
                        swap.get("exchangeName"),
                        swap.get("exchangeLogo"),
                        bought.get("address"),
                        bought.get("name"),
                        bought.get("symbol"),
                        bought.get("logo"),
                        Decimal(str(bought.get("amount", 0))),
                        Decimal(str(bought.get("usdPrice", 0))),
                        Decimal(str(bought.get("usdAmount", 0))),
                        sold.get("address"),
                        sold.get("name"),
                        sold.get("symbol"),
                        sold.get("logo"),
                        Decimal(str(sold.get("amount", 0))),
                        Decimal(str(sold.get("usdPrice", 0))),
                        Decimal(str(sold.get("usdAmount", 0))),
                        Decimal(str(swap.get("baseQuotePrice", 0))),
                        Decimal(str(swap.get("totalValueUsd", 0)))
                    )
                except Exception as e:
                    logger.error(f"Error storing swap: {e}")

    async def store_holder_stats(self, token_address: str, stats: Dict):
        """Store holder statistics"""
        if not stats:
            return

        async with self.db_pool.acquire() as conn:
            try:
                holder_supply = stats.get("holderSupply", {})
                holder_change = stats.get("holderChange", {})
                holders_by_acq = stats.get("holdersByAcquisition", {})
                holder_dist = stats.get("holderDistribution", {})

                await conn.execute("""
                    INSERT INTO moralis_token_holder_stats (
                        token_address, total_holders,
                        holder_supply_top10, holder_supply_top10_percent,
                        holder_supply_top25, holder_supply_top25_percent,
                        holder_supply_top50, holder_supply_top50_percent,
                        holder_supply_top100, holder_supply_top100_percent,
                        holder_change_5min, holder_change_5min_percent,
                        holder_change_1h, holder_change_1h_percent,
                        holder_change_24h, holder_change_24h_percent,
                        holders_by_swap, holders_by_transfer, holders_by_airdrop,
                        whales_count, sharks_count, dolphins_count, fish_count,
                        octopus_count, crabs_count, shrimps_count
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
                             $17, $18, $19, $20, $21, $22, $23, $24, $25, $26)
                    ON CONFLICT (token_address, timestamp) DO NOTHING
                """,
                    token_address,
                    stats.get("totalHolders", 0),
                    Decimal(str(holder_supply.get("top10", {}).get("supply", 0))),
                    Decimal(str(holder_supply.get("top10", {}).get("supplyPercent", 0))),
                    Decimal(str(holder_supply.get("top25", {}).get("supply", 0))),
                    Decimal(str(holder_supply.get("top25", {}).get("supplyPercent", 0))),
                    Decimal(str(holder_supply.get("top50", {}).get("supply", 0))),
                    Decimal(str(holder_supply.get("top50", {}).get("supplyPercent", 0))),
                    Decimal(str(holder_supply.get("top100", {}).get("supply", 0))),
                    Decimal(str(holder_supply.get("top100", {}).get("supplyPercent", 0))),
                    holder_change.get("5min", {}).get("change", 0),
                    Decimal(str(holder_change.get("5min", {}).get("changePercent", 0))),
                    holder_change.get("1h", {}).get("change", 0),
                    Decimal(str(holder_change.get("1h", {}).get("changePercent", 0))),
                    holder_change.get("24h", {}).get("change", 0),
                    Decimal(str(holder_change.get("24h", {}).get("changePercent", 0))),
                    holders_by_acq.get("swap", 0),
                    holders_by_acq.get("transfer", 0),
                    holders_by_acq.get("airdrop", 0),
                    holder_dist.get("whales", 0),
                    holder_dist.get("sharks", 0),
                    holder_dist.get("dolphins", 0),
                    holder_dist.get("fish", 0),
                    holder_dist.get("octopus", 0),
                    holder_dist.get("crabs", 0),
                    holder_dist.get("shrimps", 0)
                )
                logger.info("Stored holder stats")
            except Exception as e:
                logger.error(f"Error storing holder stats: {e}")

    async def store_pair_stats(self, stats: Dict):
        """Store pair statistics"""
        if not stats:
            return

        async with self.db_pool.acquire() as conn:
            try:
                # Parse created date
                pair_created = stats.get("pairCreated", "")
                if pair_created:
                    created_dt = datetime.fromisoformat(pair_created.replace("Z", "+00:00"))
                else:
                    created_dt = None

                price_change = stats.get("pricePercentChange", {})
                liquidity_change = stats.get("liquidityPercentChange", {})
                buys = stats.get("buys", {})
                sells = stats.get("sells", {})
                volume = stats.get("totalVolume", {})
                buy_volume = stats.get("buyVolume", {})
                sell_volume = stats.get("sellVolume", {})
                buyers = stats.get("buyers", {})
                sellers = stats.get("sellers", {})

                await conn.execute("""
                    INSERT INTO moralis_pair_stats_enhanced (
                        pair_address, token_address, token_name, token_symbol, token_logo,
                        pair_created, pair_label, exchange, exchange_address, exchange_logo,
                        exchange_url, current_usd_price, current_native_price, total_liquidity_usd,
                        price_change_5min, price_change_1h, price_change_4h, price_change_24h,
                        liquidity_change_5min, liquidity_change_1h, liquidity_change_4h, liquidity_change_24h,
                        buys_5min, buys_1h, buys_4h, buys_24h,
                        sells_5min, sells_1h, sells_4h, sells_24h,
                        volume_5min, volume_1h, volume_4h, volume_24h,
                        buy_volume_5min, buy_volume_1h, buy_volume_4h, buy_volume_24h,
                        sell_volume_5min, sell_volume_1h, sell_volume_4h, sell_volume_24h,
                        buyers_5min, buyers_1h, buyers_4h, buyers_24h,
                        sellers_5min, sellers_1h, sellers_4h, sellers_24h
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18,
                             $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34,
                             $35, $36, $37, $38, $39, $40, $41, $42, $43, $44, $45, $46, $47, $48, $49, $50)
                    ON CONFLICT (pair_address, timestamp) DO NOTHING
                """,
                    stats.get("pairAddress"),
                    stats.get("tokenAddress"),
                    stats.get("tokenName"),
                    stats.get("tokenSymbol"),
                    stats.get("tokenLogo"),
                    created_dt,
                    stats.get("pairLabel"),
                    stats.get("exchange"),
                    stats.get("exchangeAddress"),
                    stats.get("exchangeLogo"),
                    stats.get("exchangeUrl"),
                    Decimal(str(stats.get("currentUsdPrice", 0))),
                    Decimal(str(stats.get("currentNativePrice", 0))),
                    Decimal(str(stats.get("totalLiquidityUsd", 0))),
                    Decimal(str(price_change.get("5min", 0))),
                    Decimal(str(price_change.get("1h", 0))),
                    Decimal(str(price_change.get("4h", 0))),
                    Decimal(str(price_change.get("24h", 0))),
                    Decimal(str(liquidity_change.get("5min", 0))),
                    Decimal(str(liquidity_change.get("1h", 0))),
                    Decimal(str(liquidity_change.get("4h", 0))),
                    Decimal(str(liquidity_change.get("24h", 0))),
                    buys.get("5min", 0),
                    buys.get("1h", 0),
                    buys.get("4h", 0),
                    buys.get("24h", 0),
                    sells.get("5min", 0),
                    sells.get("1h", 0),
                    sells.get("4h", 0),
                    sells.get("24h", 0),
                    Decimal(str(volume.get("5min", 0))),
                    Decimal(str(volume.get("1h", 0))),
                    Decimal(str(volume.get("4h", 0))),
                    Decimal(str(volume.get("24h", 0))),
                    Decimal(str(buy_volume.get("5min", 0))),
                    Decimal(str(buy_volume.get("1h", 0))),
                    Decimal(str(buy_volume.get("4h", 0))),
                    Decimal(str(buy_volume.get("24h", 0))),
                    Decimal(str(sell_volume.get("5min", 0))),
                    Decimal(str(sell_volume.get("1h", 0))),
                    Decimal(str(sell_volume.get("4h", 0))),
                    Decimal(str(sell_volume.get("24h", 0))),
                    buyers.get("5min", 0),
                    buyers.get("1h", 0),
                    buyers.get("4h", 0),
                    buyers.get("24h", 0),
                    sellers.get("5min", 0),
                    sellers.get("1h", 0),
                    sellers.get("4h", 0),
                    sellers.get("24h", 0)
                )
                logger.info("Stored pair stats")
            except Exception as e:
                logger.error(f"Error storing pair stats: {e}")

    async def run_monitoring_cycle(self):
        """Run one complete monitoring cycle with all endpoints"""
        logger.info("Starting enhanced monitoring cycle...")

        # Fetch all new data types
        swaps = await self.fetch_token_swaps(BTCB_ADDRESS)
        holder_stats = await self.fetch_token_holder_stats(BTCB_ADDRESS)
        pair_stats = await self.fetch_pair_stats(POOL_ADDRESS)
        token_analytics = await self.fetch_token_analytics(BTCB_ADDRESS)
        token_stats = await self.fetch_token_stats(BTCB_ADDRESS)
        snipers = await self.fetch_snipers(POOL_ADDRESS)
        top_gainers = await self.fetch_top_gainers(BTCB_ADDRESS)

        # Fetch historical holders (last 24 hours)
        now = datetime.utcnow()
        from_date = (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
        to_date = now.strftime('%Y-%m-%dT%H:%M:%S')
        historical_holders = await self.fetch_historical_holders(BTCB_ADDRESS, from_date, to_date)

        # Store all data
        await self.store_token_swaps(swaps)
        await self.store_holder_stats(BTCB_ADDRESS, holder_stats)
        await self.store_pair_stats(pair_stats)

        # Log summary
        logger.info(f"""
            Enhanced monitoring cycle complete:
            - Token Swaps: {len(swaps)}
            - Holder Stats: {'✓' if holder_stats else '✗'}
            - Pair Stats: {'✓' if pair_stats else '✗'}
            - Token Analytics: {'✓' if token_analytics else '✗'}
            - Snipers: {'✓' if snipers else '✗'}
            - Top Gainers: {'✓' if top_gainers else '✗'}
            - Historical Holders: {len(historical_holders)}
        """)

    async def run(self):
        """Main monitoring loop"""
        await self.init_db()
        await self.init_session()

        logger.info("Enhanced Moralis Monitor initialized")

        while True:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(60)  # Run every 1 minute
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)


async def main():
    monitor = EnhancedMoralisMonitor()
    try:
        await monitor.run()
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())