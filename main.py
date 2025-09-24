"""Main application for DEX onchain analytics"""

import asyncio
import logging
from typing import List, Dict
from datetime import datetime
import asyncpg
from src.etherscan_client import EtherscanClient
from src.config import config, CHAIN_CONFIG

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def track_wallet(address: str, label: str = None):
    """Add a wallet for tracking"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO wallets (address, label, first_seen, last_seen)
            VALUES ($1, $2, $3, $3)
            ON CONFLICT (address) DO UPDATE
            SET label = COALESCE($2, wallets.label),
                last_seen = $3
        """, address.lower(), label, datetime.now())

    logger.info(f"Added wallet {address} for tracking")

async def run_continuous_monitoring():
    """Run continuous monitoring tasks"""
    logger.info("Starting continuous monitoring...")

    while True:
        try:
            for chain_id in config.supported_chains:
                # Sleep between chains to respect rate limits
                await asyncio.sleep(2)

            # Wait before next cycle
            await asyncio.sleep(300)  # 5 minutes

        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
            await asyncio.sleep(60)


async def main():
    """Main entry point"""
    global db_pool
    db_pool = await asyncpg.create_pool(
        config.database_url,
        min_size=5,
        max_size=20
    )

    client = EtherscanClient()
    await client.__aenter__()

    logger.info("Application initialized successfully")

    try:
        # Example: Track a known trader wallet
        await track_wallet(
            "0x0000000000000000000000000000000000000000",
            "Example Trader"
        )

        # Start monitoring (comment out for one-time analysis)
        # await run_continuous_monitoring()

    finally:
        await client.__aexit__(None, None, None)
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())