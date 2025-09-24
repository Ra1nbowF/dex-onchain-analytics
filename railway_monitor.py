"""
Railway deployment wrapper for BSC and Moralis monitors
Runs both monitors concurrently with Railway database
"""

import asyncio
import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Railway provides DATABASE_URL automatically
RAILWAY_DATABASE_URL = os.getenv("DATABASE_URL")
if not RAILWAY_DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set!")
    logger.info("This script is designed to run on Railway with PostgreSQL")
    sys.exit(1)

# Use private URL if available (better performance)
if os.getenv("DATABASE_PRIVATE_URL"):
    RAILWAY_DATABASE_URL = os.getenv("DATABASE_PRIVATE_URL")
    logger.info("Using private database URL for better performance")

# Log connection info (without password)
db_parts = RAILWAY_DATABASE_URL.split('@')
if len(db_parts) > 1:
    logger.info(f"Connecting to database at: {db_parts[1]}")

# Set the DATABASE_URL for child processes
os.environ["DATABASE_URL"] = RAILWAY_DATABASE_URL

def run_bsc_monitor():
    """Run BSC pool monitor"""
    logger.info("Starting BSC Pool Monitor...")
    try:
        # Run bsc_pool_monitor.py as a subprocess
        result = subprocess.run(
            [sys.executable, "bsc_pool_monitor.py"],
            env=os.environ.copy(),
            capture_output=False,
            text=True
        )
        logger.info(f"BSC Pool Monitor exited with code: {result.returncode}")
    except Exception as e:
        logger.error(f"BSC Pool Monitor error: {e}")

def run_moralis_monitor():
    """Run Moralis BTCB monitor"""
    logger.info("Starting Moralis Final Monitor...")
    try:
        # Run moralis_final_monitor.py as the latest version
        result = subprocess.run(
            [sys.executable, "moralis_final_monitor.py"],
            env=os.environ.copy(),
            capture_output=False,
            text=True
        )
        logger.info(f"Moralis Monitor exited with code: {result.returncode}")
    except Exception as e:
        logger.error(f"Moralis Monitor error: {e}")

async def health_check():
    """Periodic health check and status reporting"""
    import psycopg2

    while True:
        try:
            # Check database connection
            conn = psycopg2.connect(RAILWAY_DATABASE_URL)
            cur = conn.cursor()

            # Get data counts
            cur.execute("SELECT COUNT(*) FROM bsc_pool_metrics")
            bsc_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM moralis_swaps_enhanced")
            moralis_count = cur.fetchone()[0]

            cur.execute("SELECT MAX(timestamp) FROM bsc_pool_metrics")
            bsc_latest = cur.fetchone()[0]

            cur.execute("SELECT MAX(timestamp) FROM moralis_swaps_enhanced")
            moralis_latest = cur.fetchone()[0]

            logger.info(f"Health Check - BSC: {bsc_count} records (latest: {bsc_latest})")
            logger.info(f"Health Check - Moralis: {moralis_count} records (latest: {moralis_latest})")

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Health check failed: {e}")

        # Wait 5 minutes before next check
        await asyncio.sleep(300)

async def main():
    """Main entry point for Railway deployment"""
    logger.info("="*60)
    logger.info("Railway Monitor Service Starting")
    logger.info("="*60)
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Database configured: {'Yes' if RAILWAY_DATABASE_URL else 'No'}")

    # Create thread pool for running monitors
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Start both monitors in separate threads
        bsc_future = executor.submit(run_bsc_monitor)
        moralis_future = executor.submit(run_moralis_monitor)

        # Start health check in async
        health_task = asyncio.create_task(health_check())

        logger.info("All monitors started successfully")

        # Wait for any monitor to complete (they should run forever)
        try:
            await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: bsc_future.result() or moralis_future.result()
            )
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        finally:
            health_task.cancel()
            logger.info("Shutting down monitors...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)