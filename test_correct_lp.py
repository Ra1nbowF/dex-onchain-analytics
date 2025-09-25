"""Test LP token transfers with correct LP token address"""

import asyncio
from web3 import Web3
from datetime import datetime

# Correct addresses
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"  # Pool contract
LP_TOKEN_ADDRESS = "0x41ff9aa7e16b8b1a8a8dc4f0efacd93d02d071c9"  # LP token contract

async def test_correct_lp():
    w3 = Web3(Web3.HTTPProvider("https://bsc.publicnode.com"))

    if not w3.is_connected():
        print("Failed to connect to BSC")
        return

    latest_block = w3.eth.block_number
    print(f"Connected to BSC. Latest block: {latest_block}")
    print(f"Pool address: {POOL_ADDRESS}")
    print(f"LP token address: {LP_TOKEN_ADDRESS}")
    print("=" * 60)

    # ERC20 Transfer event signature
    transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

    # Check just 10 blocks to avoid rate limits
    from_block = latest_block - 10
    to_block = latest_block

    try:
        event_filter = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'address': Web3.to_checksum_address(LP_TOKEN_ADDRESS),
            'topics': [transfer_topic]
        }

        logs = w3.eth.get_logs(event_filter)

        if logs:
            print(f"\n[OK] Found {len(logs)} LP token transfers in last 100 blocks!")

            # Show recent transfers
            for i, log in enumerate(logs[-5:], 1):  # Last 5
                block = w3.eth.get_block(log['blockNumber'])
                timestamp = datetime.fromtimestamp(block['timestamp'])

                from_addr = "0x" + log['topics'][1].hex()[26:]
                to_addr = "0x" + log['topics'][2].hex()[26:]
                amount = int(log['data'].hex(), 16) / 10**18

                print(f"\nTransfer #{i}:")
                print(f"  Block: {log['blockNumber']}")
                print(f"  Time: {timestamp}")
                print(f"  TX: {log['transactionHash'].hex()[:20]}...")
                print(f"  From: {from_addr[:10]}...")
                print(f"  To: {to_addr[:10]}...")
                print(f"  Amount: {amount:.6f} LP tokens")

                # Check transfer type
                if from_addr.lower() == "0x" + "0" * 40:
                    print(f"  Type: MINT (Liquidity Added)")
                elif to_addr.lower() == "0x" + "0" * 40:
                    print(f"  Type: BURN (Liquidity Removed)")
                else:
                    print(f"  Type: TRANSFER")

        else:
            print(f"\nNo LP token transfers found in blocks {from_block}-{to_block}")
            print("Checking if LP token contract exists...")

            # Verify contract
            code = w3.eth.get_code(Web3.to_checksum_address(LP_TOKEN_ADDRESS))
            if code:
                print(f"[OK] LP token contract exists (code size: {len(code)} bytes)")
            else:
                print("[FAIL] No contract found at LP token address")

    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_correct_lp())