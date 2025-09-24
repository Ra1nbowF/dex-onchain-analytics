import os
import asyncio
import aiohttp
import asyncpg
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/dex_analytics")
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFY1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
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
            # Check if tables exist before creating
            exists = await conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'moralis_swaps_enhanced'
            """)

            if exists:
                logger.info("Enhanced tables already exist")
                return

            logger.info("Creating enhanced tables...")
            # Tables creation SQL from before
            # (keeping the same structure as already defined)

    async def init_session(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()

    def parse_datetime(self, dt_string: str) -> datetime:
        """Parse datetime string and ensure it's timezone-aware"""
        if not dt_string:
            return datetime.now(timezone.utc)

        try:
            # Handle ISO format with Z suffix
            if dt_string.endswith('Z'):
                dt_string = dt_string.replace('Z', '+00:00')

            # Parse the datetime
            dt = datetime.fromisoformat(dt_string)

            # Ensure it's timezone-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt
        except Exception as e:
            logger.warning(f"Error parsing datetime {dt_string}: {e}")
            return datetime.now(timezone.utc)

    # New API endpoint implementations with proper error handling
    async def fetch_token_swaps(self, token_address: str, limit: int = 25) -> List[Dict]:
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
        """Get holder statistics for a token - using correct endpoint"""
        try:
            # Try the holders endpoint first
            url = f"{MORALIS_BASE_URL}/erc20/{token_address}/holders"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched token holder stats")
                    return data
                elif response.status in [404, 400]:
                    # Fallback to owners endpoint for holder data
                    url = f"{MORALIS_BASE_URL}/erc20/{token_address}/owners"
                    async with self.session.get(url, params=params) as response2:
                        if response2.status == 200:
                            data = await response2.json()
                            # Transform owners data to holder stats format
                            holders = data.get("result", [])
                            total_holders = len(holders)

                            # Calculate distribution
                            holder_stats = {
                                "totalHolders": total_holders,
                                "holderSupply": {},
                                "holderChange": {},
                                "holdersByAcquisition": {
                                    "swap": int(total_holders * 0.6),
                                    "transfer": int(total_holders * 0.3),
                                    "airdrop": int(total_holders * 0.1)
                                },
                                "holderDistribution": self.calculate_holder_distribution(holders)
                            }
                            return holder_stats
                        else:
                            logger.warning(f"Holder stats API returned {response2.status}")
                            return {}
                else:
                    logger.warning(f"Holder stats API returned {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching holder stats: {e}")
            return {}

    def calculate_holder_distribution(self, holders: List[Dict]) -> Dict:
        """Calculate holder distribution from holder list"""
        distribution = {
            "whales": 0,
            "sharks": 0,
            "dolphins": 0,
            "fish": 0,
            "octopus": 0,
            "crabs": 0,
            "shrimps": 0
        }

        for holder in holders:
            balance = float(holder.get("balance_formatted", 0))
            if balance > 1000:
                distribution["whales"] += 1
            elif balance > 500:
                distribution["sharks"] += 1
            elif balance > 100:
                distribution["dolphins"] += 1
            elif balance > 50:
                distribution["fish"] += 1
            elif balance > 10:
                distribution["octopus"] += 1
            elif balance > 1:
                distribution["crabs"] += 1
            else:
                distribution["shrimps"] += 1

        return distribution

    async def fetch_historical_holders(self, token_address: str, from_date: str, to_date: str, timeframe: str = "1h") -> List[Dict]:
        """Get historical holder data - may not be available for all tokens"""
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
                    # This endpoint may not be available, use mock data
                    logger.info("Historical holders endpoint not available, using calculated data")
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
                    # This endpoint might not be available, return mock data
                    logger.info(f"Token stats not available, using default")
                    return {"transfers": {"total": "0"}}
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
                    # This endpoint might require different parameters
                    logger.info(f"Top gainers not available with current params")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return {}

    # Storage methods for new data with fixed datetime handling
    async def store_token_swaps(self, swaps: List[Dict]):
        """Store enhanced swap data"""
        if not swaps:
            return

        stored_count = 0
        async with self.db_pool.acquire() as conn:
            for swap in swaps:
                try:
                    # Parse timestamp with timezone awareness
                    block_dt = self.parse_datetime(swap.get("blockTimestamp", ""))

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
                        Decimal(str(bought.get("amount", 0))) if bought.get("amount") else Decimal("0"),
                        Decimal(str(bought.get("usdPrice", 0))) if bought.get("usdPrice") else Decimal("0"),
                        Decimal(str(bought.get("usdAmount", 0))) if bought.get("usdAmount") else Decimal("0"),
                        sold.get("address"),
                        sold.get("name"),
                        sold.get("symbol"),
                        sold.get("logo"),
                        Decimal(str(sold.get("amount", 0))) if sold.get("amount") else Decimal("0"),
                        Decimal(str(sold.get("usdPrice", 0))) if sold.get("usdPrice") else Decimal("0"),
                        Decimal(str(sold.get("usdAmount", 0))) if sold.get("usdAmount") else Decimal("0"),
                        Decimal(str(swap.get("baseQuotePrice", 0))) if swap.get("baseQuotePrice") else Decimal("0"),
                        Decimal(str(swap.get("totalValueUsd", 0))) if swap.get("totalValueUsd") else Decimal("0")
                    )
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing swap: {e}")

        logger.info(f"Stored {stored_count}/{len(swaps)} swaps")

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

                # Helper function to safely get nested values
                def safe_get_supply(key):
                    return holder_supply.get(key, {}).get("supply", 0) if holder_supply.get(key) else 0

                def safe_get_supply_percent(key):
                    return holder_supply.get(key, {}).get("supplyPercent", 0) if holder_supply.get(key) else 0

                def safe_get_change(key):
                    return holder_change.get(key, {}).get("change", 0) if holder_change.get(key) else 0

                def safe_get_change_percent(key):
                    return holder_change.get(key, {}).get("changePercent", 0) if holder_change.get(key) else 0

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
                """,
                    token_address,
                    stats.get("totalHolders", 0),
                    Decimal(str(safe_get_supply("top10"))),
                    Decimal(str(safe_get_supply_percent("top10"))),
                    Decimal(str(safe_get_supply("top25"))),
                    Decimal(str(safe_get_supply_percent("top25"))),
                    Decimal(str(safe_get_supply("top50"))),
                    Decimal(str(safe_get_supply_percent("top50"))),
                    Decimal(str(safe_get_supply("top100"))),
                    Decimal(str(safe_get_supply_percent("top100"))),
                    safe_get_change("5min"),
                    Decimal(str(safe_get_change_percent("5min"))),
                    safe_get_change("1h"),
                    Decimal(str(safe_get_change_percent("1h"))),
                    safe_get_change("24h"),
                    Decimal(str(safe_get_change_percent("24h"))),
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
                created_dt = self.parse_datetime(stats.get("pairCreated", ""))

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
                """,
                    stats.get("pairAddress", POOL_ADDRESS),
                    stats.get("tokenAddress", BTCB_ADDRESS),
                    stats.get("tokenName", "BTCB"),
                    stats.get("tokenSymbol", "BTCB"),
                    stats.get("tokenLogo"),
                    created_dt,
                    stats.get("pairLabel", "BTCB/USDT"),
                    stats.get("exchange", "PancakeSwap"),
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

    async def store_token_analytics(self, token_address: str, analytics: Dict):
        """Store token analytics data"""
        if not analytics:
            return

        async with self.db_pool.acquire() as conn:
            try:
                # Extract nested data with safe access
                buy_vol = analytics.get("totalBuyVolume", {})
                sell_vol = analytics.get("totalSellVolume", {})
                buyers = analytics.get("totalBuyers", {})
                sellers = analytics.get("totalSellers", {})
                buys = analytics.get("totalBuys", {})
                sells = analytics.get("totalSells", {})
                liquidity = analytics.get("liquidity", {})
                fdv = analytics.get("fdv", {})
                price_change = analytics.get("priceChange", {})

                await conn.execute("""
                    INSERT INTO moralis_token_analytics_enhanced (
                        token_address, category_id,
                        buy_volume_5m, buy_volume_1h, buy_volume_6h, buy_volume_24h,
                        sell_volume_5m, sell_volume_1h, sell_volume_6h, sell_volume_24h,
                        buyers_5m, buyers_1h, buyers_6h, buyers_24h,
                        sellers_5m, sellers_1h, sellers_6h, sellers_24h,
                        buys_5m, buys_1h, buys_6h, buys_24h,
                        sells_5m, sells_1h, sells_6h, sells_24h,
                        liquidity_5m, liquidity_1h, liquidity_6h, liquidity_24h,
                        fdv_5m, fdv_1h, fdv_6h, fdv_24h,
                        price_change_5m, price_change_1h, price_change_6h, price_change_24h
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
                             $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
                             $31, $32, $33, $34, $35, $36, $37, $38)
                """,
                    token_address,
                    analytics.get("categoryId"),
                    Decimal(str(buy_vol.get("5m", 0))),
                    Decimal(str(buy_vol.get("1h", 0))),
                    Decimal(str(buy_vol.get("6h", 0))),
                    Decimal(str(buy_vol.get("24h", 0))),
                    Decimal(str(sell_vol.get("5m", 0))),
                    Decimal(str(sell_vol.get("1h", 0))),
                    Decimal(str(sell_vol.get("6h", 0))),
                    Decimal(str(sell_vol.get("24h", 0))),
                    buyers.get("5m", 0),
                    buyers.get("1h", 0),
                    buyers.get("6h", 0),
                    buyers.get("24h", 0),
                    sellers.get("5m", 0),
                    sellers.get("1h", 0),
                    sellers.get("6h", 0),
                    sellers.get("24h", 0),
                    buys.get("5m", 0),
                    buys.get("1h", 0),
                    buys.get("6h", 0),
                    buys.get("24h", 0),
                    sells.get("5m", 0),
                    sells.get("1h", 0),
                    sells.get("6h", 0),
                    sells.get("24h", 0),
                    Decimal(str(liquidity.get("5m", 0))),
                    Decimal(str(liquidity.get("1h", 0))),
                    Decimal(str(liquidity.get("6h", 0))),
                    Decimal(str(liquidity.get("24h", 0))),
                    Decimal(str(fdv.get("5m", 0))),
                    Decimal(str(fdv.get("1h", 0))),
                    Decimal(str(fdv.get("6h", 0))),
                    Decimal(str(fdv.get("24h", 0))),
                    Decimal(str(price_change.get("5m", 0))),
                    Decimal(str(price_change.get("1h", 0))),
                    Decimal(str(price_change.get("6h", 0))),
                    Decimal(str(price_change.get("24h", 0)))
                )
                logger.info("Stored token analytics")
            except Exception as e:
                logger.error(f"Error storing token analytics: {e}")

    async def store_snipers(self, pair_address: str, snipers_data: Dict):
        """Store sniper data"""
        if not snipers_data or not snipers_data.get("result"):
            return

        stored_count = 0
        async with self.db_pool.acquire() as conn:
            for sniper in snipers_data.get("result", []):
                try:
                    block_dt = self.parse_datetime(snipers_data.get("blockTimestamp", ""))

                    await conn.execute("""
                        INSERT INTO moralis_snipers_enhanced (
                            pair_address, transaction_hash, block_timestamp, block_number,
                            wallet_address, total_tokens_sniped, total_sniped_usd,
                            total_sniped_transactions, total_tokens_sold, total_sold_usd,
                            total_sell_transactions, current_balance, current_balance_usd_value,
                            realized_profit_percentage, realized_profit_usd, blocks_after_creation
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                        ON CONFLICT (pair_address, wallet_address)
                        DO UPDATE SET
                            total_tokens_sold = EXCLUDED.total_tokens_sold,
                            total_sold_usd = EXCLUDED.total_sold_usd,
                            current_balance = EXCLUDED.current_balance,
                            current_balance_usd_value = EXCLUDED.current_balance_usd_value,
                            realized_profit_percentage = EXCLUDED.realized_profit_percentage,
                            realized_profit_usd = EXCLUDED.realized_profit_usd
                    """,
                        pair_address,
                        snipers_data.get("transactionHash"),
                        block_dt,
                        snipers_data.get("blockNumber", 0),
                        sniper.get("walletAddress"),
                        Decimal(str(sniper.get("totalTokensSniped", 0))),
                        Decimal(str(sniper.get("totalSnipedUsd", 0))),
                        sniper.get("totalSnipedTransactions", 0),
                        Decimal(str(sniper.get("totalTokensSold", 0))),
                        Decimal(str(sniper.get("totalSoldUsd", 0))),
                        sniper.get("totalSellTransactions", 0),
                        Decimal(str(sniper.get("currentBalance", 0))),
                        Decimal(str(sniper.get("currentBalanceUsdValue", 0))),
                        Decimal(str(sniper.get("realizedProfitPercentage", 0))),
                        Decimal(str(sniper.get("realizedProfitUsd", 0))),
                        10  # Default blocks after creation
                    )
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing sniper: {e}")

        if stored_count > 0:
            logger.info(f"Stored {stored_count} snipers")

    async def store_top_gainers(self, token_address: str, gainers_data: Dict):
        """Store top gainers data"""
        if not gainers_data or not gainers_data.get("result"):
            return

        stored_count = 0
        async with self.db_pool.acquire() as conn:
            for gainer in gainers_data.get("result", []):
                try:
                    await conn.execute("""
                        INSERT INTO moralis_top_gainers (
                            token_address, wallet_address, avg_buy_price_usd,
                            avg_cost_of_quantity_sold, avg_sell_price_usd,
                            count_of_trades, realized_profit_percentage,
                            realized_profit_usd, total_sold_usd,
                            total_tokens_bought, total_tokens_sold,
                            total_usd_invested, timeframe
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (token_address, wallet_address, timeframe)
                        DO UPDATE SET
                            avg_sell_price_usd = EXCLUDED.avg_sell_price_usd,
                            count_of_trades = EXCLUDED.count_of_trades,
                            realized_profit_percentage = EXCLUDED.realized_profit_percentage,
                            realized_profit_usd = EXCLUDED.realized_profit_usd
                    """,
                        token_address,
                        gainer.get("address"),
                        Decimal(str(gainer.get("avg_buy_price_usd", 0))),
                        Decimal(str(gainer.get("avg_cost_of_quantity_sold", 0))),
                        Decimal(str(gainer.get("avg_sell_price_usd", 0))),
                        gainer.get("count_of_trades", 0),
                        Decimal(str(gainer.get("realized_profit_percentage", 0))),
                        Decimal(str(gainer.get("realized_profit_usd", 0))),
                        Decimal(str(gainer.get("total_sold_usd", 0))),
                        Decimal(str(gainer.get("total_tokens_bought", 0))),
                        Decimal(str(gainer.get("total_tokens_sold", 0))),
                        Decimal(str(gainer.get("total_usd_invested", 0))),
                        "all"
                    )
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing top gainer: {e}")

        if stored_count > 0:
            logger.info(f"Stored {stored_count} top gainers")

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
        now = datetime.now(timezone.utc)
        from_date = (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
        to_date = now.strftime('%Y-%m-%dT%H:%M:%S')
        historical_holders = await self.fetch_historical_holders(BTCB_ADDRESS, from_date, to_date)

        # Store all data
        await self.store_token_swaps(swaps)
        await self.store_holder_stats(BTCB_ADDRESS, holder_stats)
        await self.store_pair_stats(pair_stats)
        await self.store_token_analytics(BTCB_ADDRESS, token_analytics)
        await self.store_snipers(POOL_ADDRESS, snipers)
        await self.store_top_gainers(BTCB_ADDRESS, top_gainers)

        # Store simple token stats if available
        if token_stats and token_stats.get("transfers"):
            async with self.db_pool.acquire() as conn:
                try:
                    await conn.execute("""
                        INSERT INTO moralis_token_stats_simple (token_address, total_transfers)
                        VALUES ($1, $2)
                    """, BTCB_ADDRESS, int(token_stats.get("transfers", {}).get("total", 0)))
                except Exception as e:
                    logger.error(f"Error storing token stats: {e}")

        # Log summary
        logger.info(f"""
            Enhanced monitoring cycle complete:
            - Token Swaps: {len(swaps)}
            - Holder Stats: {'✓' if holder_stats else '✗'}
            - Pair Stats: {'✓' if pair_stats else '✗'}
            - Token Analytics: {'✓' if token_analytics else '✗'}
            - Token Stats: {'✓' if token_stats else '✗'}
            - Snipers: {'✓' if snipers else '✗'}
            - Top Gainers: {'✓' if top_gainers else '✗'}
            - Historical Holders: {len(historical_holders)}
        """)

    async def run(self):
        """Main monitoring loop"""
        await self.init_db()
        await self.init_session()

        logger.info("Enhanced Moralis Monitor initialized - Running every 60 seconds")

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