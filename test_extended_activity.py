"""Check extended timeframe for LP token activity"""

import asyncio
from web3 import Web3
from datetime import datetime, timedelta

LP_TOKEN_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

async def check_extended_activity():
    # Connect to BSC
    w3 = Web3(Web3.HTTPProvider("https://bsc.publicnode.com"))

    if not w3.is_connected():
        print("Failed to connect to BSC")
        return

    latest_block = w3.eth.block_number
    print(f"Connected to BSC. Latest block: {latest_block}")

    # Check larger ranges (1 day = ~28,800 blocks on BSC)
    hours_back = [1, 6, 12, 24]
    transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

    for hours in hours_back:
        blocks_back = hours * 1200  # ~3 seconds per block
        from_block = latest_block - blocks_back

        # Check just a small sample to avoid rate limits
        sample_size = 20  # Check 20 blocks
        to_block = from_block + sample_size

        try:
            event_filter = {
                'fromBlock': from_block,
                'toBlock': to_block,
                'address': Web3.to_checksum_address(LP_TOKEN_ADDRESS),
                'topics': [transfer_topic]
            }

            logs = w3.eth.get_logs(event_filter)

            if logs:
                print(f"\n✓ Found {len(logs)} transfers in {hours} hours ago sample:")
                log = logs[0]
                block = w3.eth.get_block(log['blockNumber'])
                timestamp = datetime.fromtimestamp(block['timestamp'])

                from_addr = "0x" + log['topics'][1].hex()[26:]
                to_addr = "0x" + log['topics'][2].hex()[26:]
                amount = int(log['data'].hex(), 16) / 10**18

                transfer_type = "TRANSFER"
                if from_addr.lower() == "0x" + "0" * 40:
                    transfer_type = "MINT (Add Liquidity)"
                elif to_addr.lower() == "0x" + "0" * 40:
                    transfer_type = "BURN (Remove Liquidity)"

                print(f"  Type: {transfer_type}")
                print(f"  Amount: {amount:.6f} LP tokens")
                print(f"  Time: {timestamp}")
                print(f"  TX: {log['transactionHash'].hex()}")
                break
            else:
                print(f"No transfers found ~{hours} hours ago (blocks {from_block}-{to_block})")
        except Exception as e:
            if "limit exceeded" in str(e):
                print(f"Rate limit hit checking {hours} hours ago")
            else:
                print(f"Error checking {hours} hours ago: {e}")

asyncio.run(check_extended_activity())