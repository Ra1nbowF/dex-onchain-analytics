import asyncio
import aiohttp
from web3 import Web3
from datetime import datetime, timedelta
import json

# BSC RPC endpoints
BSC_RPC_ENDPOINTS = [
    "https://bsc-dataseed.binance.org/",
    "https://bsc-dataseed1.defibit.io/",
    "https://bsc-dataseed1.ninicoin.io/",
    "https://bsc.publicnode.com"
]

LP_TOKEN_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

# ERC20 Transfer event signature
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

async def test_lp_transfers_web3():
    # Try different RPC endpoints
    for rpc_url in BSC_RPC_ENDPOINTS:
        try:
            print(f"\nTrying RPC: {rpc_url}")
            w3 = Web3(Web3.HTTPProvider(rpc_url))

            if not w3.is_connected():
                print("  Connection failed")
                continue

            print(f"  Connected! Block number: {w3.eth.block_number}")

            # Get recent blocks
            latest_block = w3.eth.block_number
            from_block = latest_block - 10  # Last ~30 seconds of blocks

            print(f"  Fetching LP token transfers from block {from_block} to {latest_block}")

            # Create filter for Transfer events
            event_filter = {
                'fromBlock': from_block,
                'toBlock': latest_block,
                'address': Web3.to_checksum_address(LP_TOKEN_ADDRESS),
                'topics': [TRANSFER_TOPIC]
            }

            # Get logs
            logs = w3.eth.get_logs(event_filter)
            print(f"  Found {len(logs)} transfer events")

            if logs:
                print("\n  Recent LP token transfers:")
                for i, log in enumerate(logs[-5:], 1):  # Show last 5
                    # Decode transfer event
                    from_addr = "0x" + log['topics'][1].hex()[26:]
                    to_addr = "0x" + log['topics'][2].hex()[26:]
                    value = int(log['data'].hex(), 16) / 10**18

                    # Get block info
                    block = w3.eth.get_block(log['blockNumber'])
                    timestamp = datetime.fromtimestamp(block['timestamp'])

                    print(f"\n  Transfer #{i}:")
                    print(f"    Block: {log['blockNumber']}")
                    print(f"    Tx: {log['transactionHash'].hex()[:10]}...")
                    print(f"    From: {from_addr[:10]}...")
                    print(f"    To: {to_addr[:10]}...")
                    print(f"    Amount: {value:.6f} LP tokens")
                    print(f"    Time: {timestamp}")

                    # Check transfer type
                    if from_addr.lower() == "0x" + "0" * 40:
                        print(f"    Type: MINT (Add Liquidity)")
                    elif to_addr.lower() == "0x" + "0" * 40:
                        print(f"    Type: BURN (Remove Liquidity)")
                    else:
                        print(f"    Type: TRANSFER")

                return True  # Success

        except Exception as e:
            print(f"  Error: {str(e)[:100]}")
            continue

    return False

if __name__ == "__main__":
    success = asyncio.run(test_lp_transfers_web3())
    if not success:
        print("\nAll RPC endpoints failed. BSC network might be having issues.")