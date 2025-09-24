#!/usr/bin/env python3
"""
Simple start script for Railway deployment
"""

import os
import sys
import subprocess

print("="*60)
print("Railway Deployment Starting...")
print("="*60)

# Print environment info
print(f"Current directory: {os.getcwd()}")
print(f"Python version: {sys.version}")
print(f"Files in directory:")
for file in os.listdir('.'):
    print(f"  - {file}")

# Check for DATABASE_URL
db_url = os.getenv("DATABASE_URL")
if db_url:
    print(f"\nDATABASE_URL is set: {db_url.split('@')[1] if '@' in db_url else 'Invalid URL'}")
else:
    print("\nWARNING: DATABASE_URL not set!")

# Try to import and run the monitor
try:
    print("\n" + "="*60)
    print("Starting monitors...")
    print("="*60)

    # Import and run directly instead of subprocess
    import railway_monitor
    import asyncio

    asyncio.run(railway_monitor.main())

except ImportError as e:
    print(f"\nImportError: {e}")
    print("\nTrying alternative: Running individual monitors...")

    # Try running individual monitors
    try:
        subprocess.run([sys.executable, "bsc_pool_monitor.py"])
    except Exception as e:
        print(f"Failed to run bsc_pool_monitor.py: {e}")

except Exception as e:
    print(f"\nError: {e}")
    sys.exit(1)