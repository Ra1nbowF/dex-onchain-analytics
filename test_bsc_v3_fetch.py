"""Test BSC monitor V3 liquidity fetching"""

import asyncio
import sys
sys.path.insert(0, '.')

from bsc_pool_monitor import BSCPoolMonitor

async def test():
    monitor = BSCPoolMonitor()
    
    print("Testing V3 liquidity event fetching...")
    print("=" * 60)
    
    # Test fetching V3 liquidity events
    events = await monitor.fetch_v3_liquidity_events(hours=168)  # Last 7 days
    
    print(f"\nFound {len(events)} V3 liquidity events")
    
    if events:
        print("\nSample events:")
        for i, event in enumerate(events[:3], 1):
            print(f"\nEvent {i}:")
            print(f"  Type: {event['transfer_type']}")
            print(f"  TxHash: {event['tx_hash']}")
            print(f"  Block: {event['block_number']}")
            if event['transfer_type'] == 'mint':
                print(f"  To: {event['to_address'][:10]}...")
            else:
                print(f"  From: {event['from_address'][:10]}...")
    else:
        print("\nNo V3 liquidity events found in the last 24 hours")
        print("This pool may have low activity or we may need to:")
        print("  1. Check a wider time range")
        print("  2. Verify the event signatures are correct")
        print("  3. Check if the pool is actually a V3 pool")
    
    print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(test())