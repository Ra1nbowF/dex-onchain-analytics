"""Test to check recent activity on the LP token"""

import asyncio
from web3 import Web3
from datetime import datetime

LP_TOKEN_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

async def check_pool_activity():
    # Connect to BSC
    w3 = Web3(Web3.HTTPProvider("https://bsc.publicnode.com"))

    if not w3.is_connected():
        print("Failed to connect to BSC")
        return

    print(f"Connected to BSC. Latest block: {w3.eth.block_number}")

    # Get LP token info using a single block to test
    latest_block = w3.eth.block_number

    # Check multiple block ranges to find activity
    ranges = [
        (latest_block - 10, latest_block),        # Last ~30 seconds
        (latest_block - 100, latest_block - 90),  # ~5 minutes ago
        (latest_block - 500, latest_block - 490), # ~25 minutes ago
        (latest_block - 1000, latest_block - 990) # ~50 minutes ago
    ]

    transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    total_transfers = 0

    for from_block, to_block in ranges:
        try:
            event_filter = {
                'fromBlock': from_block,
                'toBlock': to_block,
                'address': Web3.to_checksum_address(LP_TOKEN_ADDRESS),
                'topics': [transfer_topic]
            }

            logs = w3.eth.get_logs(event_filter)

            if logs:
                print(f"\nFound {len(logs)} transfers in blocks {from_block}-{to_block}:")
                total_transfers += len(logs)

                for log in logs[:2]:  # Show first 2
                    block = w3.eth.get_block(log['blockNumber'])
                    timestamp = datetime.fromtimestamp(block['timestamp'])

                    from_addr = "0x" + log['topics'][1].hex()[26:]
                    to_addr = "0x" + log['topics'][2].hex()[26:]
                    amount = int(log['data'].hex(), 16) / 10**18

                    print(f"  Block {log['blockNumber']}: {amount:.6f} LP tokens")
                    print(f"    From: {from_addr[:10]}...")
                    print(f"    To: {to_addr[:10]}...")
                    print(f"    Time: {timestamp}")
        except Exception as e:
            print(f"Error checking blocks {from_block}-{to_block}: {e}")

    if total_transfers == 0:
        print("\nNo recent LP token transfers found")
        print("The pool might have low activity or be inactive")

        # Check if contract exists
        code = w3.eth.get_code(Web3.to_checksum_address(LP_TOKEN_ADDRESS))
        if code:
            print(f"Contract exists at {LP_TOKEN_ADDRESS} (code size: {len(code)} bytes)")
        else:
            print(f"No contract found at {LP_TOKEN_ADDRESS}")

asyncio.run(check_pool_activity())