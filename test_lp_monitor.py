"""Test LP token transfer monitoring in bsc_pool_monitor"""

import asyncio
import sys
sys.path.insert(0, '.')

from bsc_pool_monitor import BSCPoolMonitor

async def test_lp_monitoring():
    monitor = BSCPoolMonitor()
    await monitor.initialize()

    try:

        print("Testing LP token transfer collection...")
        print("=" * 50)

        # Fetch LP token transfers for the last 24 hours
        transfers = await monitor.fetch_lp_token_transfers(hours=24)

        if transfers:
            print(f"\nFound {len(transfers)} LP token transfers in the last 24 hours:")

            # Show summary by transfer type
            mints = [t for t in transfers if t['transfer_type'] == 'mint']
            burns = [t for t in transfers if t['transfer_type'] == 'burn']
            regular = [t for t in transfers if t['transfer_type'] == 'transfer']

            print(f"\nTransfer Types:")
            print(f"  - Mints (Add Liquidity): {len(mints)}")
            print(f"  - Burns (Remove Liquidity): {len(burns)}")
            print(f"  - Regular Transfers: {len(regular)}")

            # Show recent transfers
            print(f"\nMost Recent Transfers (up to 5):")
            for i, transfer in enumerate(transfers[:5], 1):
                print(f"\n{i}. {transfer['transfer_type'].upper()}")
                print(f"   TX: {transfer['tx_hash'][:10]}...")
                print(f"   Block: {transfer['block_number']}")
                print(f"   From: {transfer['from_address'][:10]}...")
                print(f"   To: {transfer['to_address'][:10]}...")
                print(f"   LP Amount: {transfer['lp_amount']:.6f}")
                print(f"   Value: ${transfer.get('total_value_usd', 0):.2f}")
                print(f"   Pool Share: {transfer.get('pool_share_percent', 0):.4f}%")
                print(f"   Time: {transfer['timestamp']}")
        else:
            print("\nNo LP token transfers found in the last 24 hours")
            print("This could mean:")
            print("1. The pool has low activity")
            print("2. API rate limits are preventing data collection")
            print("3. The LP token address might need verification")

    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await monitor.cleanup()

if __name__ == "__main__":
    asyncio.run(test_lp_monitoring())