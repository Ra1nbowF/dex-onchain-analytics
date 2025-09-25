"""Check LP token activity using Web3"""

from web3 import Web3
from datetime import datetime, timedelta

# BSC RPC
rpc_url = "https://bsc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    print("Failed to connect to BSC")
    exit(1)

print("Connected to BSC")
print("=" * 60)

LP_TOKEN_ADDRESS = "0x41ff9aa7e16b8b1a8a8dc4f0efacd93d02d071c9"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

# Check LP token contract
lp_token = w3.to_checksum_address(LP_TOKEN_ADDRESS)
pool = w3.to_checksum_address(POOL_ADDRESS)

print(f"LP Token: {lp_token}")
print(f"Pool: {pool}")

# Check if LP token is a contract
lp_code = w3.eth.get_code(lp_token)
if len(lp_code) > 2:
    print(f"[OK] LP token is a valid contract (code size: {len(lp_code)} bytes)")
else:
    print(f"[ERROR] LP token address has no code!")

# Check pool code
pool_code = w3.eth.get_code(pool)
if len(pool_code) > 2:
    print(f"[OK] Pool is a valid contract (code size: {len(pool_code)} bytes)")
else:
    print(f"[ERROR] Pool address has no code!")

# Get recent blocks and check for events
current_block = w3.eth.block_number
print(f"\nCurrent block: {current_block}")

# Transfer event signature
transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Check last 100 blocks for any Transfer events
from_block = current_block - 100
print(f"Checking blocks {from_block} to {current_block} for LP token transfers...")

try:
    # Get logs
    logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': lp_token,
        'topics': [transfer_topic]
    })
    
    print(f"\nFound {len(logs)} Transfer events")
    
    if logs:
        for i, log in enumerate(logs[:3], 1):
            print(f"\nTransfer {i}:")
            print(f"  Block: {log['blockNumber']}")
            print(f"  TxHash: {log['transactionHash'].hex()}")
            
            # Decode from/to
            if len(log['topics']) >= 3:
                from_addr = "0x" + log['topics'][1].hex()[-40:]
                to_addr = "0x" + log['topics'][2].hex()[-40:]
                print(f"  From: {from_addr[:10]}...")
                print(f"  To: {to_addr[:10]}...")
                
                # Amount
                amount = int(log['data'].hex(), 16) / 10**18
                print(f"  Amount: {amount:.6f} LP")
    else:
        print("  No events found")

except Exception as e:
    print(f"Error fetching logs: {e}")

# Try getting all events from the pool
print("\n" + "=" * 60)
print("Checking pool contract for any events...")

try:
    pool_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': pool
    })
    
    print(f"Found {len(pool_logs)} events from pool contract")
    
    # Count event types
    event_types = {}
    for log in pool_logs:
        if log['topics']:
            topic = log['topics'][0].hex()
            event_types[topic] = event_types.get(topic, 0) + 1
    
    if event_types:
        print("\nEvent types:")
        for topic, count in list(event_types.items())[:5]:
            print(f"  {topic[:10]}...: {count} events")
            
            # Known events
            if topic == transfer_topic:
                print(f"    ^ Transfer events")
            elif topic.startswith("0xdccd412f"):
                print(f"    ^ Sync events")
            elif topic.startswith("0x1c411e9a"):
                print(f"    ^ Swap events")
            elif topic.startswith("0x4c209b5f"):
                print(f"    ^ Mint events")
            elif topic.startswith("0xdccd412f0e2d0df4d0510c5d3a3f8c202c8478cd8c87ba618b0ba99103d089f3c9"):
                print(f"    ^ Burn events")
                
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Summary:")
if len(lp_code) <= 2:
    print("[X] LP token address appears to be incorrect - no contract code found")
    print("   This means the address 0x41ff9aa7e16b8b1a8a8dc4f0efacd93d02d071c9 is NOT the LP token")
    print("   Need to find the correct LP token address for this pool")
else:
    print("[OK] LP token contract exists")
    if logs:
        print(f"[OK] Found {len(logs)} recent transfers")
    else:
        print("[!] No recent transfers found (pool might be inactive)")