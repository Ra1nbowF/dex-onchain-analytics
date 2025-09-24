"""Run both the generic DEX collector and BSC pool monitor"""

import asyncio
import sys
import logging
from collector import DEXDataCollector
from bsc_pool_monitor import BSCPoolMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_generic_collector():
    """Run the generic DEX data collector"""
    collector = DEXDataCollector()
    try:
        await collector.initialize()
        await collector.run_continuous()
    finally:
        await collector.cleanup()


async def run_bsc_monitor():
    """Run the BSC pool monitor"""
    monitor = BSCPoolMonitor()
    try:
        await monitor.initialize()
        await monitor.monitor_pool()
    finally:
        await monitor.cleanup()


async def main():
    """Run both monitors concurrently"""
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"

    if mode == "generic":
        logger.info("Starting generic DEX collector only...")
        await run_generic_collector()
    elif mode == "bsc":
        logger.info("Starting BSC pool monitor only...")
        await run_bsc_monitor()
    else:
        logger.info("Starting both collectors...")
        await asyncio.gather(
            run_generic_collector(),
            run_bsc_monitor()
        )


if __name__ == "__main__":
    asyncio.run(main())