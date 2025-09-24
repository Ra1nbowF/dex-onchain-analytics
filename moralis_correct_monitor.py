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
DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

# BSC BTCB Token and Pool addresses
BTCB_ADDRESS = "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

class MoralisCorrectMonitor:
    def __init__(self):
        self.db_pool = None
        self.session = None
        self.headers = {
            "accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }

    async def init_db(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(DATABASE_URL)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

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
        """Parse datetime string and ensure it's timezone-naive for PostgreSQL"""
        if not dt_string:
            return datetime.utcnow()

        try:
            if dt_string.endswith('Z'):
                dt_string = dt_string[:-1]
            if '+' in dt_string:
                dt_string = dt_string.split('+')[0]
            if 'T' in dt_string:
                dt = datetime.fromisoformat(dt_string)
            else:
                dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")

            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)

            return dt
        except Exception as e:
            logger.warning(f"Error parsing datetime {dt_string}: {e}")
            return datetime.utcnow()

    # 1. GET SWAPS BY TOKEN ADDRESS
    async def fetch_token_swaps(self, limit: int = 100) -> List[Dict]:
        """Fetch swap transactions (buy/sell) for a specific ERC20 token"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/swaps"
            params = {
                "chain": "bsc",
                "limit": limit,
                "order": "DESC"
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    swaps = data.get("result", []) if isinstance(data, dict) else []
                    logger.info(f"Fetched {len(swaps)} swaps")
                    return swaps
                else:
                    error_text = await response.text()
                    logger.warning(f"Swaps API returned {response.status}: {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching swaps: {e}")
            return []

    # 2. GET TOKEN TRANSFERS
    async def fetch_token_transfers(self, limit: int = 100) -> List[Dict]:
        """Fetch ERC20 token transfers by contract address"""
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
                    transfers = data.get("result", []) if isinstance(data, dict) else []
                    logger.info(f"Fetched {len(transfers)} transfers")
                    return transfers
                else:
                    logger.warning(f"Transfers API returned {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching transfers: {e}")
            return []

    # 3. GET TOP PROFITABLE WALLETS
    async def fetch_top_gainers(self, days: str = "all") -> List[Dict]:
        """List the most profitable wallets that have traded a specific ERC20 token"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/top-gainers"
            params = {
                "chain": "bsc",
                "days": days
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    gainers = data.get("result", []) if isinstance(data, dict) else []
                    logger.info(f"Fetched {len(gainers)} top gainers")
                    return gainers
                else:
                    error_text = await response.text()
                    logger.warning(f"Top gainers API returned {response.status}: {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return []

    # 4. GET TOKEN PAIR STATS
    async def fetch_pair_stats(self) -> Dict:
        """Access key statistics for a token pair"""
        try:
            url = f"{MORALIS_BASE_URL}/pairs/{POOL_ADDRESS}/stats"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched pair stats successfully")
                    return data
                else:
                    error_text = await response.text()
                    logger.warning(f"Pair stats API returned {response.status}: {error_text}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching pair stats: {e}")
            return {}

    # 5. GET TOKEN ANALYTICS
    async def fetch_token_analytics(self) -> Dict:
        """Retrieve detailed trading analytics for a specific token"""
        try:
            url = f"{MORALIS_BASE_URL}/tokens/{BTCB_ADDRESS}/analytics"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched token analytics successfully")
                    return data
                else:
                    error_text = await response.text()
                    logger.warning(f"Token analytics API returned {response.status}: {error_text}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching token analytics: {e}")
            return {}

    # 6. GET TOKEN STATS
    async def fetch_token_stats(self) -> Dict:
        """Get the total number of transfers for a given ERC20"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/stats"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched token stats successfully")
                    return data
                else:
                    error_text = await response.text()
                    logger.warning(f"Token stats API returned {response.status}: {error_text}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching token stats: {e}")
            return {}

    # 7. GET TOKEN HOLDER STATS
    async def fetch_holder_stats(self) -> Dict:
        """Returns total holders and aggregated holder statistics"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/holders"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched holder stats successfully")
                    return data
                else:
                    error_text = await response.text()
                    logger.warning(f"Holder stats API returned {response.status}: {error_text}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching holder stats: {e}")
            return {}

    # 8. GET HISTORICAL TOKEN HOLDERS
    async def fetch_historical_holders(self, from_date: str, to_date: str, time_frame: str = "1d") -> List[Dict]:
        """Track changes in holder base over time with timeseries data"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/holders/historical"
            params = {
                "chain": "bsc",
                "fromDate": from_date,
                "toDate": to_date,
                "timeFrame": time_frame
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    holders = data.get("result", []) if isinstance(data, dict) else []
                    logger.info(f"Fetched {len(holders)} historical holder records")
                    return holders
                else:
                    error_text = await response.text()
                    logger.warning(f"Historical holders API returned {response.status}: {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching historical holders: {e}")
            return []

    # 9. GET SNIPERS BY PAIR ADDRESS
    async def fetch_snipers(self, blocks_after_creation: int = 3) -> List[Dict]:
        """Identify sniper wallets that bought within specified timeframe"""
        try:
            url = f"{MORALIS_BASE_URL}/pairs/{POOL_ADDRESS}/snipers"
            params = {
                "chain": "bsc",
                "blocksAfterCreation": blocks_after_creation
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    snipers = data.get("result", []) if isinstance(data, dict) else []
                    logger.info(f"Fetched {len(snipers)} snipers")
                    return snipers
                else:
                    error_text = await response.text()
                    logger.warning(f"Snipers API returned {response.status}: {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching snipers: {e}")
            return []

    # Database storage methods
    async def store_swaps(self, swaps: List[Dict]):
        """Store swap transactions in database"""
        if not swaps:
            return

        async with self.db_pool.acquire() as conn:
            for swap in swaps:
                try:
                    await conn.execute("""
                        INSERT INTO moralis_swaps_enhanced (
                            transaction_hash, transaction_type, wallet_address,
                            block_timestamp, block_number, pair_address,
                            bought_token_address, bought_amount, bought_usd_value,
                            sold_token_address, sold_amount, sold_usd_value,
                            total_value_usd, exchange_name, timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                        ON CONFLICT (transaction_hash) DO UPDATE SET
                            total_value_usd = EXCLUDED.total_value_usd,
                            timestamp = EXCLUDED.timestamp
                    """,
                        swap.get('transactionHash'),
                        swap.get('transactionType', 'unknown'),
                        swap.get('walletAddress'),
                        self.parse_datetime(swap.get('blockTimestamp')),
                        swap.get('blockNumber', 0),
                        swap.get('pairAddress'),
                        swap.get('bought', {}).get('address'),
                        Decimal(str(swap.get('bought', {}).get('amount', '0'))),
                        Decimal(str(swap.get('bought', {}).get('usdAmount', '0'))),
                        swap.get('sold', {}).get('address'),
                        Decimal(str(swap.get('sold', {}).get('amount', '0'))),
                        Decimal(str(swap.get('sold', {}).get('usdAmount', '0'))),
                        Decimal(str(swap.get('totalValueUsd', '0'))),
                        swap.get('exchangeName', 'Unknown'),
                        datetime.utcnow()
                    )
                except Exception as e:
                    logger.error(f"Error storing swap: {e}")

    async def store_transfers(self, transfers: List[Dict]):
        """Store token transfers in database"""
        if not transfers:
            return

        async with self.db_pool.acquire() as conn:
            for transfer in transfers:
                try:
                    value = transfer.get('value', '0')
                    if len(str(value).split('.')[0]) > 30:
                        value = '0'

                    await conn.execute("""
                        INSERT INTO moralis_transfers (
                            transaction_hash, from_address, to_address,
                            value, block_timestamp, block_number, timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (transaction_hash) DO UPDATE SET
                            value = EXCLUDED.value,
                            timestamp = EXCLUDED.timestamp
                    """,
                        transfer.get('transaction_hash'),
                        transfer.get('from_address'),
                        transfer.get('to_address'),
                        Decimal(str(value)),
                        self.parse_datetime(transfer.get('block_timestamp')),
                        int(transfer.get('block_number', 0)),
                        datetime.utcnow()
                    )
                except Exception as e:
                    logger.error(f"Error storing transfer: {e}")

    async def store_top_gainers(self, gainers: List[Dict], token_info: Dict = None):
        """Store top profitable wallets"""
        if not gainers:
            return

        async with self.db_pool.acquire() as conn:
            # Clear old data
            await conn.execute("DELETE FROM moralis_top_gainers")

            for gainer in gainers:
                try:
                    await conn.execute("""
                        INSERT INTO moralis_top_gainers (
                            wallet_address, avg_buy_price_usd, avg_sell_price_usd,
                            total_tokens_bought, total_tokens_sold, total_usd_invested,
                            total_sold_usd, realized_profit_usd, realized_profit_percentage,
                            count_of_trades, timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                        gainer.get('address'),
                        Decimal(str(gainer.get('avg_buy_price_usd', '0'))),
                        Decimal(str(gainer.get('avg_sell_price_usd', '0'))),
                        Decimal(str(gainer.get('total_tokens_bought', '0'))),
                        Decimal(str(gainer.get('total_tokens_sold', '0'))),
                        Decimal(str(gainer.get('total_usd_invested', '0'))),
                        Decimal(str(gainer.get('total_sold_usd', '0'))),
                        Decimal(str(gainer.get('realized_profit_usd', '0'))),
                        Decimal(str(gainer.get('realized_profit_percentage', '0'))),
                        gainer.get('count_of_trades', 0),
                        datetime.utcnow()
                    )
                except Exception as e:
                    logger.error(f"Error storing top gainer: {e}")

    async def store_pair_stats(self, stats: Dict):
        """Store pair statistics"""
        if not stats:
            return

        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO moralis_pair_stats_enhanced (
                        pair_address, pair_label, token_address, current_usd_price,
                        total_liquidity_usd, price_change_5min, price_change_1h,
                        price_change_24h, liquidity_change_24h,
                        buys_24h, sells_24h, buyers_24h, sellers_24h,
                        buy_volume_24h, sell_volume_24h, total_volume_24h,
                        exchange_name, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                    ON CONFLICT (pair_address, timestamp) DO UPDATE SET
                        current_usd_price = EXCLUDED.current_usd_price,
                        total_liquidity_usd = EXCLUDED.total_liquidity_usd
                """,
                    stats.get('pairAddress', POOL_ADDRESS),
                    stats.get('pairLabel', 'BTCB/USDT'),
                    stats.get('tokenAddress', BTCB_ADDRESS),
                    Decimal(str(stats.get('currentUsdPrice', '0'))),
                    Decimal(str(stats.get('totalLiquidityUsd', '0'))),
                    Decimal(str(stats.get('pricePercentChange', {}).get('5min', '0'))),
                    Decimal(str(stats.get('pricePercentChange', {}).get('1h', '0'))),
                    Decimal(str(stats.get('pricePercentChange', {}).get('24h', '0'))),
                    Decimal(str(stats.get('liquidityPercentChange', {}).get('24h', '0'))),
                    stats.get('buys', {}).get('24h', 0),
                    stats.get('sells', {}).get('24h', 0),
                    stats.get('buyers', {}).get('24h', 0),
                    stats.get('sellers', {}).get('24h', 0),
                    Decimal(str(stats.get('buyVolume', {}).get('24h', '0'))),
                    Decimal(str(stats.get('sellVolume', {}).get('24h', '0'))),
                    Decimal(str(stats.get('totalVolume', {}).get('24h', '0'))),
                    stats.get('exchange', 'PancakeSwap'),
                    datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error storing pair stats: {e}")

    async def store_token_analytics(self, analytics: Dict):
        """Store token analytics"""
        if not analytics:
            return

        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO moralis_token_analytics_enhanced (
                        token_address, buy_volume_5m, buy_volume_1h, buy_volume_24h,
                        sell_volume_5m, sell_volume_1h, sell_volume_24h,
                        buyers_5m, buyers_1h, buyers_24h,
                        sellers_5m, sellers_1h, sellers_24h,
                        buys_5m, buys_1h, buys_24h,
                        sells_5m, sells_1h, sells_24h,
                        timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    ON CONFLICT (token_address, timestamp) DO UPDATE SET
                        buy_volume_24h = EXCLUDED.buy_volume_24h,
                        sell_volume_24h = EXCLUDED.sell_volume_24h
                """,
                    BTCB_ADDRESS,
                    Decimal(str(analytics.get('totalBuyVolume', {}).get('5m', '0'))),
                    Decimal(str(analytics.get('totalBuyVolume', {}).get('1h', '0'))),
                    Decimal(str(analytics.get('totalBuyVolume', {}).get('24h', '0'))),
                    Decimal(str(analytics.get('totalSellVolume', {}).get('5m', '0'))),
                    Decimal(str(analytics.get('totalSellVolume', {}).get('1h', '0'))),
                    Decimal(str(analytics.get('totalSellVolume', {}).get('24h', '0'))),
                    analytics.get('totalBuyers', {}).get('5m', 0),
                    analytics.get('totalBuyers', {}).get('1h', 0),
                    analytics.get('totalBuyers', {}).get('24h', 0),
                    analytics.get('totalSellers', {}).get('5m', 0),
                    analytics.get('totalSellers', {}).get('1h', 0),
                    analytics.get('totalSellers', {}).get('24h', 0),
                    analytics.get('totalBuys', {}).get('5m', 0),
                    analytics.get('totalBuys', {}).get('1h', 0),
                    analytics.get('totalBuys', {}).get('24h', 0),
                    analytics.get('totalSells', {}).get('5m', 0),
                    analytics.get('totalSells', {}).get('1h', 0),
                    analytics.get('totalSells', {}).get('24h', 0),
                    datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error storing token analytics: {e}")

    async def store_token_stats(self, stats: Dict):
        """Store token stats"""
        if not stats:
            return

        async with self.db_pool.acquire() as conn:
            try:
                total_transfers = stats.get('transfers', {}).get('total', '0')
                await conn.execute("""
                    INSERT INTO moralis_token_stats_simple (
                        token_address, total_transfers, timestamp
                    ) VALUES ($1, $2, $3)
                    ON CONFLICT (token_address, timestamp) DO UPDATE SET
                        total_transfers = EXCLUDED.total_transfers
                """,
                    BTCB_ADDRESS,
                    int(total_transfers),
                    datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error storing token stats: {e}")

    async def store_holder_stats(self, holder_stats: Dict):
        """Store holder statistics"""
        if not holder_stats:
            return

        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO moralis_holder_stats_complete (
                        token_address, total_holders,
                        top10_supply, top10_supply_percent,
                        top25_supply, top25_supply_percent,
                        top100_supply, top100_supply_percent,
                        holder_change_24h, holder_change_percent_24h,
                        holders_by_swap, holders_by_transfer, holders_by_airdrop,
                        whales, sharks, dolphins, fish, shrimps,
                        timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                    ON CONFLICT (token_address, timestamp) DO UPDATE SET
                        total_holders = EXCLUDED.total_holders
                """,
                    BTCB_ADDRESS,
                    holder_stats.get('totalHolders', 0),
                    Decimal(str(holder_stats.get('holderSupply', {}).get('top10', {}).get('supply', '0'))),
                    Decimal(str(holder_stats.get('holderSupply', {}).get('top10', {}).get('supplyPercent', '0'))),
                    Decimal(str(holder_stats.get('holderSupply', {}).get('top25', {}).get('supply', '0'))),
                    Decimal(str(holder_stats.get('holderSupply', {}).get('top25', {}).get('supplyPercent', '0'))),
                    Decimal(str(holder_stats.get('holderSupply', {}).get('top100', {}).get('supply', '0'))),
                    Decimal(str(holder_stats.get('holderSupply', {}).get('top100', {}).get('supplyPercent', '0'))),
                    holder_stats.get('holderChange', {}).get('24h', {}).get('change', 0),
                    Decimal(str(holder_stats.get('holderChange', {}).get('24h', {}).get('changePercent', '0'))),
                    holder_stats.get('holdersByAcquisition', {}).get('swap', 0),
                    holder_stats.get('holdersByAcquisition', {}).get('transfer', 0),
                    holder_stats.get('holdersByAcquisition', {}).get('airdrop', 0),
                    holder_stats.get('holderDistribution', {}).get('whales', 0),
                    holder_stats.get('holderDistribution', {}).get('sharks', 0),
                    holder_stats.get('holderDistribution', {}).get('dolphins', 0),
                    holder_stats.get('holderDistribution', {}).get('fish', 0),
                    holder_stats.get('holderDistribution', {}).get('shrimps', 0),
                    datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error storing holder stats: {e}")

    async def store_historical_holders(self, holders: List[Dict]):
        """Store historical holder data"""
        if not holders:
            return

        async with self.db_pool.acquire() as conn:
            for holder in holders:
                try:
                    await conn.execute("""
                        INSERT INTO moralis_historical_holders_enhanced (
                            token_address, timestamp, total_holders, net_holder_change,
                            holder_percent_change, new_holders_by_swap, new_holders_by_transfer,
                            new_holders_by_airdrop, holders_in_whales, holders_in_sharks,
                            holders_in_dolphins, holders_in_fish, holders_in_shrimps,
                            holders_out_whales, holders_out_sharks, holders_out_dolphins,
                            holders_out_fish, holders_out_shrimps
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                        ON CONFLICT (token_address, timestamp) DO UPDATE SET
                            total_holders = EXCLUDED.total_holders,
                            net_holder_change = EXCLUDED.net_holder_change
                    """,
                        BTCB_ADDRESS,
                        self.parse_datetime(holder.get('timestamp')),
                        holder.get('totalHolders', 0),
                        holder.get('netHolderChange', 0),
                        Decimal(str(holder.get('holderPercentChange', '0'))),
                        holder.get('newHoldersByAcquisition', {}).get('swap', 0),
                        holder.get('newHoldersByAcquisition', {}).get('transfer', 0),
                        holder.get('newHoldersByAcquisition', {}).get('airdrop', 0),
                        holder.get('holdersIn', {}).get('whales', 0),
                        holder.get('holdersIn', {}).get('sharks', 0),
                        holder.get('holdersIn', {}).get('dolphins', 0),
                        holder.get('holdersIn', {}).get('fish', 0),
                        holder.get('holdersIn', {}).get('shrimps', 0),
                        holder.get('holdersOut', {}).get('whales', 0),
                        holder.get('holdersOut', {}).get('sharks', 0),
                        holder.get('holdersOut', {}).get('dolphins', 0),
                        holder.get('holdersOut', {}).get('fish', 0),
                        holder.get('holdersOut', {}).get('shrimps', 0)
                    )
                except Exception as e:
                    logger.error(f"Error storing historical holder: {e}")

    async def store_snipers(self, snipers: List[Dict]):
        """Store sniper wallets"""
        if not snipers:
            return

        async with self.db_pool.acquire() as conn:
            # Clear old data
            await conn.execute("DELETE FROM moralis_snipers_enhanced")

            for sniper in snipers:
                try:
                    await conn.execute("""
                        INSERT INTO moralis_snipers_enhanced (
                            wallet_address, total_tokens_sniped, total_sniped_usd,
                            total_sniped_transactions, total_tokens_sold, total_sold_usd,
                            total_sell_transactions, current_balance, current_balance_usd,
                            realized_profit_percentage, realized_profit_usd, timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                        sniper.get('walletAddress'),
                        Decimal(str(sniper.get('totalTokensSniped', '0'))),
                        Decimal(str(sniper.get('totalSnipedUsd', '0'))),
                        sniper.get('totalSnipedTransactions', 0),
                        Decimal(str(sniper.get('totalTokensSold', '0'))),
                        Decimal(str(sniper.get('totalSoldUsd', '0'))),
                        sniper.get('totalSellTransactions', 0),
                        Decimal(str(sniper.get('currentBalance', '0'))),
                        Decimal(str(sniper.get('currentBalanceUsdValue', '0'))),
                        Decimal(str(sniper.get('realizedProfitPercentage', '0'))),
                        Decimal(str(sniper.get('realizedProfitUsd', '0'))),
                        datetime.utcnow()
                    )
                except Exception as e:
                    logger.error(f"Error storing sniper: {e}")

    async def monitor_cycle(self):
        """Run one monitoring cycle"""
        try:
            logger.info("Starting monitoring cycle...")

            # 1. Fetch and store swaps
            swaps = await self.fetch_token_swaps(100)
            await self.store_swaps(swaps)

            # 2. Fetch and store transfers
            transfers = await self.fetch_token_transfers(100)
            await self.store_transfers(transfers)

            # 3. Fetch and store top gainers
            top_gainers = await self.fetch_top_gainers("all")
            await self.store_top_gainers(top_gainers)

            # 4. Fetch and store pair stats
            pair_stats = await self.fetch_pair_stats()
            await self.store_pair_stats(pair_stats)

            # 5. Fetch and store token analytics
            token_analytics = await self.fetch_token_analytics()
            await self.store_token_analytics(token_analytics)

            # 6. Fetch and store token stats
            token_stats = await self.fetch_token_stats()
            await self.store_token_stats(token_stats)

            # 7. Fetch and store holder stats
            holder_stats = await self.fetch_holder_stats()
            await self.store_holder_stats(holder_stats)

            # 8. Fetch and store historical holders
            to_date = datetime.utcnow().isoformat()
            from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
            historical_holders = await self.fetch_historical_holders(from_date, to_date, "1d")
            await self.store_historical_holders(historical_holders)

            # 9. Fetch and store snipers
            snipers = await self.fetch_snipers(3)
            await self.store_snipers(snipers)

            logger.info(f"""
            Monitoring cycle complete:
            - Swaps: {len(swaps)}
            - Transfers: {len(transfers)}
            - Top Gainers: {len(top_gainers)}
            - Pair Stats: {'Yes' if pair_stats else 'No'}
            - Token Analytics: {'Yes' if token_analytics else 'No'}
            - Token Stats: {'Yes' if token_stats else 'No'}
            - Holder Stats: {'Yes' if holder_stats else 'No'}
            - Historical Holders: {len(historical_holders)}
            - Snipers: {len(snipers)}
            """)

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")

    async def run(self):
        """Main run loop"""
        await self.init_db()
        await self.init_session()

        try:
            while True:
                await self.monitor_cycle()
                await asyncio.sleep(60)  # Wait 1 minute
        finally:
            await self.close()

async def main():
    monitor = MoralisCorrectMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())