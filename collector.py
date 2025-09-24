"""Collector that runs BSC and Moralis monitors - Railway compatible"""

import os
import sys
import subprocess
import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set DATABASE_URL for child processes
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    logger.info(f"Using Railway DATABASE_URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
else:
    logger.warning("DATABASE_URL not set - using default")

def run_bsc_monitor():
    """Run BSC pool monitor"""
    logger.info("Starting BSC Pool Monitor thread...")
    retry_count = 0
    max_retries = 5

    while True:
        try:
            logger.info(f"Launching bsc_pool_monitor.py (attempt {retry_count + 1})...")
            result = subprocess.run(
                [sys.executable, "bsc_pool_monitor.py"],
                env=os.environ.copy(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("BSC Monitor completed successfully")
                retry_count = 0
            else:
                logger.error(f"BSC Monitor exited with code {result.returncode}")
                if result.stderr:
                    logger.error(f"BSC Monitor stderr: {result.stderr[:1000]}")
                retry_count += 1

            if retry_count >= max_retries:
                logger.error(f"BSC Monitor failed {max_retries} times, waiting longer...")
                time.sleep(300)  # Wait 5 minutes after multiple failures
                retry_count = 0
            else:
                time.sleep(30)  # Wait before restart

        except subprocess.TimeoutExpired:
            logger.warning("BSC Monitor timed out after 5 minutes, restarting...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"BSC Monitor exception: {e}")
            time.sleep(30)

def run_moralis_monitor():
    """Run Moralis monitor"""
    logger.info("Starting Moralis Monitor thread...")
    retry_count = 0
    max_retries = 5

    # Try different monitor files in order of preference
    monitor_files = [
        "main.py",  # Now contains moralis_final_monitor code
        "moralis_final_monitor.py",
        "moralis_complete_monitor.py",
        "moralis_enhanced_monitor.py",
        "moralis_correct_monitor.py",
        "moralis_bsc_monitor.py"
    ]

    # Find which monitor exists
    monitor_to_use = None
    for monitor in monitor_files:
        if os.path.exists(monitor):
            monitor_to_use = monitor
            logger.info(f"Found Moralis monitor: {monitor}")
            break

    if not monitor_to_use:
        logger.error("No Moralis monitor file found!")
        logger.info("Available files in directory:")
        for f in os.listdir('.'):
            logger.info(f"  - {f}")
        return

    while True:
        try:
            logger.info(f"Launching {monitor_to_use} (attempt {retry_count + 1})...")
            result = subprocess.run(
                [sys.executable, monitor_to_use],
                env=os.environ.copy(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("Moralis Monitor completed successfully")
                retry_count = 0
            else:
                logger.error(f"Moralis Monitor exited with code {result.returncode}")
                if result.stderr:
                    logger.error(f"Moralis Monitor stderr: {result.stderr[:1000]}")
                retry_count += 1

            if retry_count >= max_retries:
                logger.error(f"Moralis Monitor failed {max_retries} times, waiting longer...")
                time.sleep(300)  # Wait 5 minutes after multiple failures
                retry_count = 0
            else:
                time.sleep(30)  # Wait before restart

        except subprocess.TimeoutExpired:
            logger.warning("Moralis Monitor timed out after 5 minutes, restarting...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Moralis Monitor exception: {e}")
            time.sleep(30)

def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("Railway Monitor Service Starting")
    logger.info("="*60)
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"DATABASE_URL set: {bool(DATABASE_URL)}")

    # List files to debug
    logger.info("Available files in /app:")
    all_files = os.listdir('.')
    py_files = [f for f in all_files if f.endswith('.py')]
    logger.info(f"Total files: {len(all_files)}, Python files: {len(py_files)}")
    for file in py_files[:10]:  # Show first 10 files
        logger.info(f"  - {file}")

    # Start monitors in threads
    bsc_thread = threading.Thread(target=run_bsc_monitor, daemon=True)
    moralis_thread = threading.Thread(target=run_moralis_monitor, daemon=True)

    bsc_thread.start()
    moralis_thread.start()

    logger.info("Both monitors started in background threads")

    # Health check counter
    health_check_counter = 0

    # Keep main thread alive with periodic health checks
    try:
        while True:
            time.sleep(60)
            health_check_counter += 1

            # Log status every minute
            logger.info(f"Health check #{health_check_counter}: Monitors running...")

            # Every 5 minutes, log thread status
            if health_check_counter % 5 == 0:
                logger.info(f"BSC thread alive: {bsc_thread.is_alive()}")
                logger.info(f"Moralis thread alive: {moralis_thread.is_alive()}")

                # Restart dead threads
                if not bsc_thread.is_alive():
                    logger.warning("BSC thread died, restarting...")
                    bsc_thread = threading.Thread(target=run_bsc_monitor, daemon=True)
                    bsc_thread.start()

                if not moralis_thread.is_alive():
                    logger.warning("Moralis thread died, restarting...")
                    moralis_thread = threading.Thread(target=run_moralis_monitor, daemon=True)
                    moralis_thread.start()

    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        sys.exit(0)

if __name__ == "__main__":
    main()