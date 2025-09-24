"""Main monitor that runs BSC and Moralis monitors for Railway deployment"""

import os
import sys
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure DATABASE_URL uses Railway's PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    os.environ["DATABASE_URL"] = DATABASE_URL
    logger.info(f"Using Railway DATABASE_URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'set'}")
else:
    logger.warning("DATABASE_URL not set - monitors may use local database")

def run_bsc_monitor():
    """Run BSC pool monitor as subprocess"""
    logger.info("Starting BSC Pool Monitor...")
    try:
        result = subprocess.run(
            [sys.executable, "bsc_pool_monitor.py"],
            env=os.environ.copy()
        )
        logger.info(f"BSC Monitor exited: {result.returncode}")
    except Exception as e:
        logger.error(f"BSC Monitor error: {e}")

def run_moralis_monitor():
    """Run Moralis final monitor as subprocess"""
    logger.info("Starting Moralis Final Monitor...")
    try:
        result = subprocess.run(
            [sys.executable, "moralis_final_monitor.py"],
            env=os.environ.copy()
        )
        logger.info(f"Moralis Monitor exited: {result.returncode}")
    except Exception as e:
        logger.error(f"Moralis Monitor error: {e}")

async def main():
    """Run both monitors concurrently"""
    logger.info("="*60)
    logger.info("Railway Main Monitor Starting")
    logger.info("="*60)

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Start both monitors
        bsc_future = executor.submit(run_bsc_monitor)
        moralis_future = executor.submit(run_moralis_monitor)

        logger.info("Both monitors started")

        # Wait for completion
        try:
            await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: bsc_future.result() or moralis_future.result()
            )
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        except Exception as e:
            logger.error(f"Monitor error: {e}")

if __name__ == "__main__":
    asyncio.run(main())