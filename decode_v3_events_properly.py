"""Properly decode V3 mint/burn events from our pool"""

from web3 import Web3
from eth_abi import decode
import struct

# Connect to BSC
rpc_url = "https://bsc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

print("Decoding V3 Mint Events from BTCB/USDT Pool")
print("=" * 70)

POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
MINT_TOPIC = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"

current_block = w3.eth.block_number
from_block = current_block - 10000

# Get mint events
mint_logs = w3.eth.get_logs({
    'fromBlock': from_block,
    'toBlock': current_block,
    'address': Web3.to_checksum_address(POOL_ADDRESS),
    'topics': [MINT_TOPIC]
})

print(f"Found {len(mint_logs)} mint events\n")

if mint_logs:
    print("Decoded Mint Events (last 5):")
    print("-" * 50)
    
    for i, log in enumerate(mint_logs[-5:], 1):
        print(f"\nMint Event {i}:")
        print(f"  Block: {log['blockNumber']}")
        print(f"  TX: {log['transactionHash'].hex()}")
        
        # Topic[0] = event signature
        # Topic[1] = indexed owner address
        # Topic[2] = indexed tickLower
        # Topic[3] = indexed tickUpper
        
        if len(log['topics']) >= 4:
            owner = "0x" + log['topics'][1].hex()[-40:]
            
            # Ticks are stored as bytes32, need to extract int24 from the last 3 bytes
            tick_lower_bytes = log['topics'][2]
            tick_upper_bytes = log['topics'][3]

            # Take last 3 bytes and convert to signed int24
            tick_lower = int.from_bytes(tick_lower_bytes[-3:], 'big', signed=False)
            if tick_lower > 0x7FFFFF:  # If greater than max positive int24
                tick_lower = tick_lower - 0x1000000  # Convert to negative

            tick_upper = int.from_bytes(tick_upper_bytes[-3:], 'big', signed=False)
            if tick_upper > 0x7FFFFF:
                tick_upper = tick_upper - 0x1000000
            
            print(f"  Owner: {owner}")
            print(f"  Tick Lower: {tick_lower}")
            print(f"  Tick Upper: {tick_upper}")
            
            # Calculate price range
            price_lower = 1.0001 ** tick_lower
            price_upper = 1.0001 ** tick_upper
            print(f"  Price Range: {price_lower:.4f} - {price_upper:.4f} BTCB/USDT")
        
        # Data contains: sender, amount, amount0, amount1
        if log['data'] and len(log['data']) > 2:
            try:
                # Remove '0x' prefix
                data_hex = log['data'].hex() if isinstance(log['data'], bytes) else log['data'][2:]
                
                # Each parameter is 32 bytes (64 hex chars)
                # sender (address) - first 32 bytes
                # amount (uint128) - second 32 bytes
                # amount0 (uint256) - third 32 bytes
                # amount1 (uint256) - fourth 32 bytes
                
                if len(data_hex) >= 256:  # 4 * 64
                    sender = "0x" + data_hex[24:64]  # Address is in last 20 bytes of 32 bytes
                    liquidity = int(data_hex[64:128], 16)
                    amount0_raw = int(data_hex[128:192], 16)
                    amount1_raw = int(data_hex[192:256], 16)
                    
                    # Convert to readable amounts
                    amount0 = amount0_raw / 10**18  # BTCB has 18 decimals
                    amount1 = amount1_raw / 10**18  # USDT has 18 decimals
                    
                    print(f"  Sender: {sender}")
                    print(f"  Liquidity Added: {liquidity}")
                    print(f"  BTCB Amount: {amount0:.8f} BTCB")
                    print(f"  USDT Amount: {amount1:.2f} USDT")
                    
                    # Calculate value
                    btc_price = 70000  # Approximate
                    total_value = (amount0 * btc_price) + amount1
                    print(f"  Total Value: ${total_value:,.2f} USD")
                    
                    # Check if this is concentrated liquidity
                    tick_range = tick_upper - tick_lower
                    if tick_range < 1000:
                        print(f"  [CONCENTRATED] Narrow range: {tick_range} ticks")
                    else:
                        print(f"  [WIDE] Range span: {tick_range} ticks")
                        
            except Exception as e:
                print(f"  Error decoding data: {e}")
    
    # Analyze patterns
    print("\n" + "=" * 70)
    print("ANALYSIS:")
    
    # Count unique owners
    owners = set()
    total_liquidity = 0
    concentrated_positions = 0
    
    for log in mint_logs:
        if len(log['topics']) >= 4:
            owner = "0x" + log['topics'][1].hex()[-40:]
            owners.add(owner)
            
            # Check tick range
            tick_lower_bytes = log['topics'][2]
            tick_upper_bytes = log['topics'][3]

            tick_lower = int.from_bytes(tick_lower_bytes[-3:], 'big', signed=False)
            if tick_lower > 0x7FFFFF:
                tick_lower = tick_lower - 0x1000000

            tick_upper = int.from_bytes(tick_upper_bytes[-3:], 'big', signed=False)
            if tick_upper > 0x7FFFFF:
                tick_upper = tick_upper - 0x1000000
            
            if abs(tick_upper - tick_lower) < 1000:
                concentrated_positions += 1
    
    print(f"Total mint events: {len(mint_logs)}")
    print(f"Unique liquidity providers: {len(owners)}")
    print(f"Concentrated positions: {concentrated_positions}")
    print(f"Wide range positions: {len(mint_logs) - concentrated_positions}")
    
    print("\n[INSIGHT] V3 mint events contain valuable data:")
    print("  - Exact liquidity amounts")
    print("  - Token deposits (BTCB and USDT amounts)")
    print("  - Price ranges (for concentrated liquidity)")
    print("  - Can track LP strategies and position sizes")
    print("\nThis data should be stored in bsc_v3_liquidity_events table!")
else:
    print("No mint events found in the specified range")