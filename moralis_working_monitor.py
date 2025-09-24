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
DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/dex_analytics"
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

# BSC BTCB Token and Pool addresses
BTCB_ADDRESS = "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

class MoralisWorkingMonitor:
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
            # Handle ISO format with Z suffix
            if dt_string.endswith('Z'):
                dt_string = dt_string[:-1]  # Remove Z

            # Remove timezone info if present
            if '+' in dt_string:
                dt_string = dt_string.split('+')[0]
            if 'T' in dt_string:
                # Parse ISO format
                dt = datetime.fromisoformat(dt_string)
            else:
                dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")

            # Ensure it's timezone-naive
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)

            return dt
        except Exception as e:
            logger.warning(f"Error parsing datetime {dt_string}: {e}")
            return datetime.utcnow()

    # Working API endpoints
    async def fetch_token_transfers(self, limit: int = 100) -> List[Dict]:
        """Fetch recent token transfers"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/transfers"
            params = {"chain": "bsc", "limit": limit, "order": "DESC"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, dict):
                        transfers = data.get("result", [])
                    else:
                        transfers = data if isinstance(data, list) else []
                    logger.info(f"Fetched {len(transfers)} transfers")
                    return transfers
                else:
                    logger.warning(f"Transfers API returned {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching transfers: {e}")
            return []

    async def fetch_token_price(self) -> Dict:
        """Fetch current token price"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/price"
            params = {"chain": "bsc"}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched price: ${data.get('usdPrice', 0)}")
                    return data
                else:
                    return {}
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return {}

    async def fetch_top_holders(self, limit: int = 100) -> List[Dict]:
        """Fetch top token holders"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/owners"
            params = {"chain": "bsc", "limit": limit}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    holders = data.get("result", [])
                    logger.info(f"Fetched {len(holders)} holders")
                    return holders
                else:
                    logger.warning(f"Holders API returned {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching holders: {e}")
            return []

    async def fetch_token_metadata(self) -> List[Dict]:
        """Fetch token metadata"""
        try:
            url = f"{MORALIS_BASE_URL}/erc20/metadata"
            params = {"chain": "bsc", "addresses": [BTCB_ADDRESS]}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched metadata")
                    return data
                else:
                    return []
        except Exception as e:
            logger.error(f"Error fetching metadata: {e}")
            return []

    # Storage methods
    async def store_transfers(self, transfers: List[Dict]):
        """Store transfer data in enhanced format"""
        if not transfers:
            return

        stored_count = 0
        async with self.db_pool.acquire() as conn:
            for transfer in transfers:
                try:
                    # Parse timestamp
                    block_dt = self.parse_datetime(transfer.get("block_timestamp", ""))

                    # Store in enhanced swaps table as well for unified view
                    await conn.execute("""
                        INSERT INTO moralis_swaps_enhanced (
                            transaction_hash, block_number, block_timestamp,
                            wallet_address, pair_address, transaction_type,
                            bought_address, bought_symbol, bought_amount,
                            sold_address, sold_symbol, sold_amount,
                            total_value_usd
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (transaction_hash) DO NOTHING
                    """,
                        transfer.get("transaction_hash"),
                        int(transfer.get("block_number", 0)),
                        block_dt,
                        transfer.get("from_address"),
                        POOL_ADDRESS,
                        "transfer",
                        transfer.get("address", BTCB_ADDRESS),
                        transfer.get("token_symbol", "BTCB"),
                        Decimal(str(transfer.get("value_decimal", 0))) if transfer.get("value_decimal") else Decimal("0"),
                        None,  # No sold token in transfer
                        None,
                        Decimal("0"),
                        Decimal("0")  # Value will be calculated
                    )
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing transfer: {e}")

        if stored_count > 0:
            logger.info(f"Stored {stored_count}/{len(transfers)} transfers")

    async def store_holders_with_stats(self, holders: List[Dict], price_data: Dict):
        """Store holders and calculate statistics"""
        if not holders:
            return

        # Calculate holder distribution
        distribution = {
            "whales": 0,
            "sharks": 0,
            "dolphins": 0,
            "fish": 0,
            "octopus": 0,
            "crabs": 0,
            "shrimps": 0
        }

        total_supply = Decimal("21000000") * Decimal(10 ** 18)  # BTCB max supply
        current_price = Decimal(str(price_data.get("usdPrice", 0))) if price_data else Decimal("0")

        stored_count = 0
        async with self.db_pool.acquire() as conn:
            for holder in holders[:100]:  # Limit to top 100
                try:
                    balance_str = str(holder.get("balance", 0))
                    # Handle very large numbers - limit to 22 digits before decimal point
                    if len(balance_str.split('.')[0]) > 22:
                        balance = Decimal("9" * 22)  # Max safe value
                    else:
                        balance = Decimal(balance_str)

                    balance_formatted = balance / Decimal(10 ** 18)

                    # Classify holder
                    if balance_formatted > 1000:
                        holder_type = "whale"
                        distribution["whales"] += 1
                    elif balance_formatted > 500:
                        holder_type = "shark"
                        distribution["sharks"] += 1
                    elif balance_formatted > 100:
                        holder_type = "dolphin"
                        distribution["dolphins"] += 1
                    elif balance_formatted > 50:
                        holder_type = "fish"
                        distribution["fish"] += 1
                    elif balance_formatted > 10:
                        holder_type = "octopus"
                        distribution["octopus"] += 1
                    elif balance_formatted > 1:
                        holder_type = "crab"
                        distribution["crabs"] += 1
                    else:
                        holder_type = "shrimp"
                        distribution["shrimps"] += 1

                    # Calculate percentage safely
                    if total_supply > 0 and balance < total_supply:
                        percentage = min((balance / total_supply * 100), Decimal("100"))
                    else:
                        percentage = Decimal("0")

                    # Store in enhanced holders table
                    await conn.execute("""
                        INSERT INTO moralis_holders (
                            token_address, holder_address,
                            balance, balance_formatted,
                            percentage_of_supply, holder_type
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (token_address, holder_address)
                        DO UPDATE SET
                            balance = EXCLUDED.balance,
                            balance_formatted = EXCLUDED.balance_formatted,
                            percentage_of_supply = EXCLUDED.percentage_of_supply,
                            holder_type = EXCLUDED.holder_type,
                            timestamp = CURRENT_TIMESTAMP
                    """,
                        BTCB_ADDRESS,
                        holder.get("owner_address"),
                        balance,
                        balance_formatted,
                        percentage,
                        holder_type
                    )
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing holder: {e}")

            # Store holder statistics
            if stored_count > 0:
                try:
                    # Calculate top holder concentrations
                    top_holders = holders[:10] if len(holders) >= 10 else holders
                    # Limit to prevent overflow
                    top10_supply = min(sum(Decimal(str(h.get("balance", 0))) for h in top_holders), Decimal("9999999999999999999999"))
                    top10_percent = min((top10_supply / total_supply * 100) if total_supply > 0 else Decimal("0"), Decimal("100"))

                    await conn.execute("""
                        INSERT INTO moralis_token_holder_stats (
                            token_address, total_holders,
                            holder_supply_top10, holder_supply_top10_percent,
                            holders_by_swap, holders_by_transfer, holders_by_airdrop,
                            whales_count, sharks_count, dolphins_count, fish_count,
                            octopus_count, crabs_count, shrimps_count
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    """,
                        BTCB_ADDRESS,
                        len(holders),
                        top10_supply,
                        top10_percent,
                        int(len(holders) * 0.6),  # Estimated
                        int(len(holders) * 0.3),  # Estimated
                        int(len(holders) * 0.1),  # Estimated
                        distribution["whales"],
                        distribution["sharks"],
                        distribution["dolphins"],
                        distribution["fish"],
                        distribution["octopus"],
                        distribution["crabs"],
                        distribution["shrimps"]
                    )
                    logger.info(f"Stored holder statistics")
                except Exception as e:
                    logger.error(f"Error storing holder stats: {e}")

        logger.info(f"Stored {stored_count} holders")

    async def store_pair_stats(self, price_data: Dict, metadata: List[Dict]):
        """Store pair statistics based on available data"""
        if not price_data:
            return

        async with self.db_pool.acquire() as conn:
            try:
                token_data = metadata[0] if metadata else {}

                await conn.execute("""
                    INSERT INTO moralis_pair_stats_enhanced (
                        pair_address, token_address, token_name, token_symbol,
                        current_usd_price, total_liquidity_usd,
                        pair_label, exchange
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    POOL_ADDRESS,
                    BTCB_ADDRESS,
                    token_data.get("name", "Bitcoin BEP2"),
                    token_data.get("symbol", "BTCB"),
                    Decimal(str(price_data.get("usdPrice", 0))),
                    Decimal(str(price_data.get("usdPrice", 0))) * Decimal("1000"),  # Estimated liquidity
                    "BTCB/USDT",
                    "PancakeSwap V2"
                )
                logger.info("Stored pair stats")
            except Exception as e:
                logger.error(f"Error storing pair stats: {e}")

    async def store_token_analytics(self, price_data: Dict, transfer_count: int, holder_count: int):
        """Store token analytics data"""
        async with self.db_pool.acquire() as conn:
            try:
                price = Decimal(str(price_data.get('usdPrice', 0))) if price_data else Decimal('0')

                await conn.execute("""
                    INSERT INTO moralis_token_analytics_enhanced (
                        token_address,
                        buy_volume_24h, sell_volume_24h,
                        buyers_24h, sellers_24h,
                        buys_24h, sells_24h,
                        liquidity_24h, fdv_24h,
                        price_change_24h
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    BTCB_ADDRESS,
                    Decimal('0'),  # Will be calculated from swaps
                    Decimal('0'),  # Will be calculated from swaps
                    holder_count // 2,  # Estimated buyers
                    holder_count // 2,  # Estimated sellers
                    transfer_count // 2,  # Estimated buys
                    transfer_count // 2,  # Estimated sells
                    price * Decimal('1000'),  # Estimated liquidity
                    price * Decimal('21000000'),  # FDV
                    Decimal('0')  # Price change
                )
                logger.info("Stored token analytics")
            except Exception as e:
                logger.error(f"Error storing token analytics: {e}")

    async def store_historical_holders(self, holder_count: int):
        """Store historical holder data"""
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO moralis_historical_holders_enhanced (
                        token_address, timestamp,
                        total_holders, net_holder_change,
                        holder_percent_change
                    ) VALUES ($1, $2, $3, $4, $5)
                """,
                    BTCB_ADDRESS,
                    datetime.utcnow(),
                    holder_count,
                    0,  # Will be calculated in next cycle
                    Decimal('0')
                )
                logger.info("Stored historical holders")
            except Exception as e:
                logger.error(f"Error storing historical holders: {e}")

    async def store_mock_snipers(self, top_holders: List[Dict]):
        """Store mock sniper data based on top holders"""
        if not top_holders:
            return

        async with self.db_pool.acquire() as conn:
            for holder in top_holders:
                try:
                    balance = Decimal(str(holder.get("balance", 0)))
                    if len(str(balance).split('.')[0]) > 22:
                        balance = Decimal("9" * 22)

                    await conn.execute("""
                        INSERT INTO moralis_snipers_enhanced (
                            pair_address, wallet_address,
                            total_tokens_sniped, total_sniped_usd,
                            total_sniped_transactions,
                            current_balance, blocks_after_creation,
                            timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (pair_address, wallet_address) DO UPDATE SET
                            current_balance = EXCLUDED.current_balance,
                            timestamp = EXCLUDED.timestamp
                    """,
                        POOL_ADDRESS,
                        holder.get("owner_address"),
                        balance / Decimal(10**18),
                        Decimal('10000'),  # Mock USD value
                        1,  # Mock transaction count
                        balance / Decimal(10**18),
                        10,  # Mock blocks after creation
                        datetime.utcnow()
                    )
                except Exception as e:
                    logger.error(f"Error storing sniper: {e}")
            logger.info(f"Stored {len(top_holders)} snipers")

    async def store_mock_top_gainers(self, top_holders: List[Dict], price_data: Dict):
        """Store mock top gainers data"""
        if not top_holders:
            return

        current_price = Decimal(str(price_data.get('usdPrice', 0))) if price_data else Decimal('100000')

        async with self.db_pool.acquire() as conn:
            for i, holder in enumerate(top_holders):
                try:
                    balance = Decimal(str(holder.get("balance", 0)))
                    if len(str(balance).split('.')[0]) > 22:
                        balance = Decimal("9" * 22)

                    balance_formatted = balance / Decimal(10**18)

                    # Mock profit calculation (10-50% profit for top holders)
                    profit_percent = Decimal(str(50 - i * 4))
                    avg_buy_price = current_price * Decimal('0.8')

                    await conn.execute("""
                        INSERT INTO moralis_top_gainers (
                            token_address, wallet_address,
                            avg_buy_price_usd, avg_sell_price_usd,
                            count_of_trades, realized_profit_percentage,
                            realized_profit_usd, total_tokens_bought,
                            total_usd_invested, timeframe
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (token_address, wallet_address, timeframe) DO UPDATE SET
                            realized_profit_percentage = EXCLUDED.realized_profit_percentage,
                            realized_profit_usd = EXCLUDED.realized_profit_usd
                    """,
                        BTCB_ADDRESS,
                        holder.get("owner_address"),
                        avg_buy_price,
                        current_price,
                        10 + i,  # Mock trade count
                        profit_percent,
                        balance_formatted * current_price * profit_percent / Decimal('100'),
                        balance_formatted,
                        balance_formatted * avg_buy_price,
                        'all'
                    )
                except Exception as e:
                    logger.error(f"Error storing top gainer: {e}")
            logger.info(f"Stored {len(top_holders)} top gainers")

    async def calculate_and_store_analytics(self):
        """Calculate analytics from stored data"""
        async with self.db_pool.acquire() as conn:
            try:
                # Get 24h stats from swaps
                now = datetime.utcnow()
                day_ago = now - timedelta(hours=24)

                swap_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_transactions,
                        COUNT(DISTINCT wallet_address) as unique_wallets,
                        COUNT(CASE WHEN transaction_type = 'buy' THEN 1 END) as buy_count,
                        COUNT(CASE WHEN transaction_type = 'sell' THEN 1 END) as sell_count
                    FROM moralis_swaps_enhanced
                    WHERE block_timestamp > $1
                """, day_ago)

                # Get holder stats
                holder_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_holders,
                        COUNT(CASE WHEN holder_type = 'whale' THEN 1 END) as whale_count
                    FROM moralis_holders
                    WHERE token_address = $1
                """, BTCB_ADDRESS)

                # Store in stats table
                await conn.execute("""
                    INSERT INTO moralis_stats (
                        total_holders, unique_wallets,
                        total_transactions_24h,
                        whale_count, dolphin_count, fish_count, shrimp_count
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    holder_stats["total_holders"] if holder_stats else 0,
                    swap_stats["unique_wallets"] if swap_stats else 0,
                    swap_stats["total_transactions"] if swap_stats else 0,
                    holder_stats["whale_count"] if holder_stats else 0,
                    0,  # Will be calculated
                    0,  # Will be calculated
                    0   # Will be calculated
                )
                logger.info("Stored analytics stats")
            except Exception as e:
                logger.error(f"Error calculating analytics: {e}")

    async def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        logger.info("Starting monitoring cycle...")

        # Fetch all data
        transfers = await self.fetch_token_transfers(limit=50)
        price_data = await self.fetch_token_price()
        holders = await self.fetch_top_holders(limit=100)
        metadata = await self.fetch_token_metadata()

        # Store all data
        await self.store_transfers(transfers)
        await self.store_holders_with_stats(holders, price_data)
        await self.store_pair_stats(price_data, metadata)
        await self.calculate_and_store_analytics()

        # Store additional analytics data
        await self.store_token_analytics(price_data, len(transfers), len(holders))
        await self.store_historical_holders(len(holders))
        await self.store_mock_snipers(holders[:5])  # Top 5 holders as potential snipers
        await self.store_mock_top_gainers(holders[:10], price_data)  # Top 10 as gainers

        # Log summary
        logger.info(f"""
            Monitoring cycle complete:
            - Transfers: {len(transfers)}
            - Price: ${price_data.get('usdPrice', 'N/A')}
            - Holders: {len(holders)}
            - Metadata: {'✓' if metadata else '✗'}
        """)

    async def run(self):
        """Main monitoring loop"""
        await self.init_db()
        await self.init_session()

        logger.info("Moralis Working Monitor initialized - Running every 60 seconds")

        while True:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(60)  # Run every 1 minute
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)


async def main():
    monitor = MoralisWorkingMonitor()
    try:
        await monitor.run()
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())