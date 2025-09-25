"""Test monitors locally with Railway database"""

import os
import subprocess
import sys
import time

# Set Railway DATABASE_URL for testing
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"
os.environ["DATABASE_URL"] = RAILWAY_URL

print("="*60)
print("Testing Monitors with Railway Database")
print("="*60)
print(f"DATABASE_URL: {RAILWAY_URL.split('@')[1]}")
print()

def test_monitor(script_name, duration=30):
    """Test a monitor script for specified duration"""
    print(f"\nTesting {script_name} for {duration} seconds...")
    print("-"*40)
    
    try:
        # Run the monitor with timeout
        result = subprocess.run(
            [sys.executable, script_name],
            timeout=duration,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("\nOutput (last 500 chars):")
            print(result.stdout[-500:])
            
        if result.stderr:
            print("\nErrors (last 500 chars):")
            print(result.stderr[-500:])
            
    except subprocess.TimeoutExpired:
        print(f"[OK] Monitor ran for {duration} seconds without crashing")
    except FileNotFoundError:
        print(f"[ERROR] {script_name} not found")
    except Exception as e:
        print(f"[ERROR] {e}")

# Test BSC monitor
if os.path.exists("bsc_pool_monitor.py"):
    test_monitor("bsc_pool_monitor.py", 10)
else:
    print("BSC monitor not found")

# Test Moralis monitor (main.py contains the code)
if os.path.exists("main.py"):
    test_monitor("main.py", 10)
else:
    print("Main.py not found")

print("\n" + "="*60)
print("Test Complete")
print("Check Railway logs for actual deployment status")
print("="*60)