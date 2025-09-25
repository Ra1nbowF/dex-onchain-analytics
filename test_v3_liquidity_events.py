"""Test PancakeSwap V3 liquidity events for our pool"""

from web3 import Web3
from datetime import datetime

# Connect to BSC
rpc_url = "https://bsc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    print("Failed to connect to BSC")
    exit(1)

print("Testing PancakeSwap V3 Liquidity Events")
print("=" * 60)

POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
V3_POSITION_MANAGER = "0x46a15b0b27311cedf172ab29e4f4766fbe7f4364"

pool = w3.to_checksum_address(POOL_ADDRESS)
position_manager = w3.to_checksum_address(V3_POSITION_MANAGER)

print(f"Pool: {pool}")
print(f"V3 Position Manager: {position_manager}")

# Get current block
current_block = w3.eth.block_number
from_block = current_block - 2000  # Last ~100 minutes

print(f"\nSearching blocks {from_block} to {current_block}...")

# V3 Event signatures
MINT_TOPIC = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"  # Mint event
BURN_TOPIC = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45e3de096f3d50e8798e28391ffc"  # Burn event  
COLLECT_TOPIC = "0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0"  # Collect event
SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"  # Swap event

# Get events from the pool
try:
    # Check Mint events (liquidity adds)
    mint_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': pool,
        'topics': [MINT_TOPIC]
    })
    
    print(f"\nFound {len(mint_logs)} Mint events (liquidity adds)")
    
    # Check Burn events (liquidity removes)
    burn_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': pool,
        'topics': [BURN_TOPIC]
    })
    
    print(f"Found {len(burn_logs)} Burn events (liquidity removes)")
    
    # Check Collect events (fee collection)
    collect_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': pool,
        'topics': [COLLECT_TOPIC]
    })
    
    print(f"Found {len(collect_logs)} Collect events (fee collections)")
    
    # Check Swap events
    swap_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': pool,
        'topics': [SWAP_TOPIC]
    })
    
    print(f"Found {len(swap_logs)} Swap events")
    
    # Show recent liquidity events
    if mint_logs:
        print("\nRecent Mint Events (last 3):")
        for i, log in enumerate(mint_logs[-3:], 1):
            print(f"\n  Mint {i}:")
            print(f"    Block: {log['blockNumber']}")
            print(f"    TxHash: {log['transactionHash'].hex()[:10]}...")
            
            # Decode mint data (owner, tickLower, tickUpper, amount, amount0, amount1)
            # Note: This is complex ABI decoding, showing basic info
            if len(log['topics']) > 1:
                owner = "0x" + log['topics'][1].hex()[-40:]
                print(f"    Owner: {owner[:10]}...")
    
    if burn_logs:
        print("\nRecent Burn Events (last 3):")
        for i, log in enumerate(burn_logs[-3:], 1):
            print(f"\n  Burn {i}:")
            print(f"    Block: {log['blockNumber']}")
            print(f"    TxHash: {log['transactionHash'].hex()[:10]}...")
            
            if len(log['topics']) > 1:
                owner = "0x" + log['topics'][1].hex()[-40:]
                print(f"    Owner: {owner[:10]}...")
    
    # Check for IncreaseLiquidity and DecreaseLiquidity events on Position Manager
    print("\n" + "=" * 60)
    print("Checking Position Manager events related to our pool...")
    
    # IncreaseLiquidity event
    INCREASE_LIQ_TOPIC = "0x3067048beee31b25b2f1681f88dac838c8bba36af25ba6a0fd4e5b7d4833ba01"
    increase_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': position_manager,
        'topics': [INCREASE_LIQ_TOPIC]
    })
    
    print(f"\nFound {len(increase_logs)} IncreaseLiquidity events on Position Manager")
    
    # DecreaseLiquidity event
    DECREASE_LIQ_TOPIC = "0x26f6a048ee9138f2c0ce266f32263994616a4a3e94e3ae2b5eb980bb55fc14ec"
    decrease_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': position_manager,
        'topics': [DECREASE_LIQ_TOPIC]
    })
    
    print(f"Found {len(decrease_logs)} DecreaseLiquidity events on Position Manager")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Summary:")
print(f"- Pool has {len(swap_logs)} swaps in last 2000 blocks")
print(f"- Pool has {len(mint_logs)} liquidity adds")
print(f"- Pool has {len(burn_logs)} liquidity removes")
print(f"- Position Manager has {len(increase_logs)} liquidity increases")
print(f"- Position Manager has {len(decrease_logs)} liquidity decreases")

if len(mint_logs) == 0 and len(burn_logs) == 0:
    print("\n[!] No liquidity events found. Pool may be inactive or we need a wider time range.")
else:
    print("\n[OK] Found liquidity activity in the pool")