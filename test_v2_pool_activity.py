"""Test PancakeSwap V2 WBNB/USDT pool activity"""

from web3 import Web3
from datetime import datetime

# Connect to BSC
rpc_url = "https://bsc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    print("Failed to connect to BSC")
    exit(1)

print("Testing PancakeSwap V2 WBNB/USDT Pool Activity")
print("=" * 60)

# PancakeSwap V2 WBNB/USDT pool (LP token address is same as pool)
V2_POOL_ADDRESS = "0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae"
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"

pool = w3.to_checksum_address(V2_POOL_ADDRESS)

print(f"V2 Pool/LP Token: {pool}")
print(f"Pair: WBNB/USDT")

# Verify contract
pool_code = w3.eth.get_code(pool)
print(f"\nContract Verification:")
print(f"  Pool: {'Valid' if len(pool_code) > 2 else 'Invalid'} ({len(pool_code)} bytes)")

# Get current block
current_block = w3.eth.block_number
from_block = current_block - 1000  # Last ~50 minutes

print(f"\nSearching blocks {from_block} to {current_block}...")

# ERC20 Transfer event signature
transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Get LP token transfers
try:
    logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': pool,  # In V2, LP token address = pool address
        'topics': [transfer_topic]
    })
    
    print(f"\nFound {len(logs)} LP token transfers in last 100 blocks")
    
    # Analyze transfer types
    mints = 0
    burns = 0
    transfers = 0
    
    for log in logs:
        if len(log['topics']) >= 3:
            from_addr = "0x" + log['topics'][1].hex()[-40:].lower()
            to_addr = "0x" + log['topics'][2].hex()[-40:].lower()
            
            if from_addr == "0x" + "0" * 40:
                mints += 1
            elif to_addr == "0x" + "0" * 40:
                burns += 1
            else:
                transfers += 1
    
    print(f"\nTransfer Types:")
    print(f"  Mints (Add Liquidity): {mints}")
    print(f"  Burns (Remove Liquidity): {burns}")
    print(f"  Regular Transfers: {transfers}")
    
    if logs:
        print(f"\nRecent LP Token Transfers (last 5):")
        for i, log in enumerate(logs[-5:], 1):
            print(f"\nTransfer {i}:")
            print(f"  Block: {log['blockNumber']}")
            print(f"  TxHash: {log['transactionHash'].hex()[:10]}...")
            
            # Decode from/to
            from_addr = "0x" + log['topics'][1].hex()[-40:]
            to_addr = "0x" + log['topics'][2].hex()[-40:]
            print(f"  From: {from_addr[:10]}...{from_addr[-4:]}")
            print(f"  To: {to_addr[:10]}...{to_addr[-4:]}")
            
            # Decode amount
            amount = int(log['data'].hex(), 16) / 10**18
            print(f"  Amount: {amount:.6f} LP tokens")
            
            # Type
            if from_addr.lower() == "0x" + "0" * 40:
                print(f"  Type: MINT (Add Liquidity)")
            elif to_addr.lower() == "0x" + "0" * 40:
                print(f"  Type: BURN (Remove Liquidity)")
            else:
                print(f"  Type: TRANSFER")
    
    # Also check Swap events
    print("\n" + "=" * 60)
    print("Checking Swap Activity...")
    
    # PancakeSwap V2 Swap event
    SWAP_TOPIC = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
    
    swap_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': pool,
        'topics': [SWAP_TOPIC]
    })
    
    print(f"Found {len(swap_logs)} swap events in last 100 blocks")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Summary:")
print(f"- V2 pools use ERC20 LP tokens (pool address = LP token address)")
print(f"- This pool shows {'HIGH' if len(logs) > 10 else 'MODERATE' if len(logs) > 0 else 'LOW'} activity")
print(f"- Found {mints} liquidity adds, {burns} removes, {transfers} transfers")
if len(swap_logs) > 0:
    print(f"- Active trading with {len(swap_logs)} swaps in ~5 minutes")