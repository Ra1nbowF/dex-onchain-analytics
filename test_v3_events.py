"""Test V3 pool events - Mint, Burn, Swap"""

import asyncio
from web3 import Web3
from datetime import datetime

POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

# V3 Pool Event Signatures
EVENTS = {
    # Mint(address sender, address owner, int24 tickLower, int24 tickUpper, uint128 amount, uint256 amount0, uint256 amount1)
    "Mint": "0x7a53080ba414158be7ec69b987b5fb7d07dee101bff85ac92034b59dfc01b",

    # Burn(address owner, int24 tickLower, int24 tickUpper, uint128 amount, uint256 amount0, uint256 amount1)
    "Burn": "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c",

    # Swap(address sender, address recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
    "Swap": "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67",

    # Collect(address owner, address recipient, int24 tickLower, int24 tickUpper, uint128 amount0, uint128 amount1)
    "Collect": "0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0"
}

async def check_v3_events():
    w3 = Web3(Web3.HTTPProvider("https://bsc.publicnode.com"))

    if not w3.is_connected():
        print("Failed to connect to BSC")
        return

    latest_block = w3.eth.block_number
    print(f"Connected to BSC. Latest block: {latest_block}")
    print(f"Checking V3 pool: {POOL_ADDRESS}")
    print("=" * 60)

    # Check last 500 blocks (~25 minutes)
    from_block = latest_block - 500

    for event_name, topic in EVENTS.items():
        try:
            event_filter = {
                'fromBlock': from_block,
                'toBlock': latest_block,
                'address': Web3.to_checksum_address(POOL_ADDRESS),
                'topics': [topic]
            }

            logs = w3.eth.get_logs(event_filter)

            if logs:
                print(f"\n✓ {event_name} Events: {len(logs)}")

                # Show most recent event
                log = logs[-1]
                block = w3.eth.get_block(log['blockNumber'])
                timestamp = datetime.fromtimestamp(block['timestamp'])

                print(f"  Latest at block {log['blockNumber']} ({timestamp})")
                print(f"  TX: {log['transactionHash'].hex()}")

                if event_name == "Swap":
                    # Decode swap amounts (amount0 and amount1 are in data)
                    data = log['data'][2:]  # Remove 0x
                    # First 32 bytes = amount0, next 32 bytes = amount1
                    amount0_raw = data[:64]
                    amount1_raw = data[64:128]

                    # Handle signed integers
                    amount0 = int(amount0_raw, 16)
                    if amount0 > 2**255:
                        amount0 -= 2**256
                    amount1 = int(amount1_raw, 16)
                    if amount1 > 2**255:
                        amount1 -= 2**256

                    print(f"  BTCB: {amount0/10**18:.6f}")
                    print(f"  USDT: {amount1/10**18:.2f}")

                elif event_name in ["Mint", "Burn"]:
                    # Decode liquidity amounts
                    data = log['data'][2:]
                    # Skip first value (amount/liquidity), get amount0 and amount1
                    amount0 = int(data[64:128], 16) / 10**18
                    amount1 = int(data[128:192], 16) / 10**18

                    print(f"  BTCB added/removed: {amount0:.6f}")
                    print(f"  USDT added/removed: {amount1:.2f}")

            else:
                print(f"\n✗ {event_name} Events: 0")

        except Exception as e:
            if "limit exceeded" in str(e).lower():
                print(f"\n✗ {event_name} Events: Rate limited")
            else:
                print(f"\n✗ {event_name} Events: Error - {e}")

asyncio.run(check_v3_events())