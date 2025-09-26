"""Check V3 NFT positions specifically for our BTCB/USDT pool"""

from web3 import Web3
import json

# Connect to BSC
rpc_url = "https://bsc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

print("Checking V3 Positions for BTCB/USDT Pool")
print("=" * 70)

# Our specific pool and tokens
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BTCB_ADDRESS = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"
V3_POSITION_MANAGER = "0x46a15b0b27311cedf172ab29e4f4766fbe7f4364"

print(f"Pool: {POOL_ADDRESS}")
print(f"BTCB: {BTCB_ADDRESS}")
print(f"USDT: {USDT_ADDRESS}")
print()

# Pool events to find NFT positions
MINT_TOPIC = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
BURN_TOPIC = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45e3de096f3d50e8798e28391ffc"

current_block = w3.eth.block_number
from_block = current_block - 50000  # Last ~40 hours

print("1. Checking Pool Mint Events:")
print("-" * 50)

try:
    # Get mint events from our specific pool
    mint_logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': Web3.to_checksum_address(POOL_ADDRESS),
        'topics': [MINT_TOPIC]
    })
    
    print(f"Found {len(mint_logs)} mint events in our pool")
    
    if mint_logs:
        # V3 Position Manager ABI for positions function
        POSITION_ABI = json.loads('''[
            {
                "name": "positions",
                "type": "function",
                "stateMutability": "view",
                "inputs": [{"name": "tokenId", "type": "uint256"}],
                "outputs": [
                    {"name": "nonce", "type": "uint96"},
                    {"name": "operator", "type": "address"},
                    {"name": "token0", "type": "address"},
                    {"name": "token1", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "tickLower", "type": "int24"},
                    {"name": "tickUpper", "type": "int24"},
                    {"name": "liquidity", "type": "uint128"},
                    {"name": "feeGrowthInside0LastX128", "type": "uint256"},
                    {"name": "feeGrowthInside1LastX128", "type": "uint256"},
                    {"name": "tokensOwed0", "type": "uint128"},
                    {"name": "tokensOwed1", "type": "uint128"}
                ]
            }
        ]''')
        
        position_manager = w3.eth.contract(
            address=Web3.to_checksum_address(V3_POSITION_MANAGER),
            abi=POSITION_ABI
        )
        
        print("\nRecent Mint Events (last 5):")
        for i, log in enumerate(mint_logs[-5:], 1):
            print(f"\nMint {i}:")
            print(f"  Block: {log['blockNumber']}")
            print(f"  TX: {log['transactionHash'].hex()[:10]}...")
            
            # Decode mint event data
            # Mint event has: owner, tickLower, tickUpper, amount, amount0, amount1
            if len(log['topics']) > 1:
                owner = "0x" + log['topics'][1].hex()[-40:]
                print(f"  Owner: {owner[:10]}...{owner[-4:]}")
                
                # The data field contains: tickLower, tickUpper, amount, amount0, amount1
                if log['data']:
                    data_hex = log['data'].hex()
                    # Each value is 32 bytes (64 hex chars)
                    if len(data_hex) >= 320:  # 5 values * 64 chars
                        tick_lower = int(data_hex[0:64], 16)
                        if tick_lower > 2**23:  # Handle negative values
                            tick_lower = tick_lower - 2**24
                        
                        tick_upper = int(data_hex[64:128], 16)
                        if tick_upper > 2**23:
                            tick_upper = tick_upper - 2**24
                        
                        liquidity = int(data_hex[128:192], 16)
                        amount0 = int(data_hex[192:256], 16) / 10**18  # BTCB
                        amount1 = int(data_hex[256:320], 16) / 10**18  # USDT
                        
                        print(f"  Liquidity: {liquidity}")
                        print(f"  BTCB deposited: {amount0:.8f}")
                        print(f"  USDT deposited: {amount1:.2f}")
                        print(f"  Tick Lower: {tick_lower}")
                        print(f"  Tick Upper: {tick_upper}")
                        
                        # Calculate price range
                        price_lower = 1.0001 ** tick_lower
                        price_upper = 1.0001 ** tick_upper
                        print(f"  Price Range: {price_lower:.2f} - {price_upper:.2f} BTCB/USDT")
        
        # Check burn events too
        print("\n2. Checking Pool Burn Events:")
        print("-" * 50)
        
        burn_logs = w3.eth.get_logs({
            'fromBlock': from_block,
            'toBlock': current_block,
            'address': Web3.to_checksum_address(POOL_ADDRESS),
            'topics': [BURN_TOPIC]
        })
        
        print(f"Found {len(burn_logs)} burn events in our pool")
        
        if burn_logs:
            print("\nRecent Burn Events (last 3):")
            for i, log in enumerate(burn_logs[-3:], 1):
                print(f"\nBurn {i}:")
                print(f"  Block: {log['blockNumber']}")
                print(f"  TX: {log['transactionHash'].hex()[:10]}...")
                
                if len(log['topics']) > 1:
                    owner = "0x" + log['topics'][1].hex()[-40:]
                    print(f"  Owner: {owner[:10]}...{owner[-4:]}")
    else:
        print("\nNo mint events found in this time range.")
        print("The pool may be inactive or using a different mechanism.")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"- Pool has {len(mint_logs)} mints and {len(burn_logs)} burns in last ~40 hours")
    
    if len(mint_logs) > 0 or len(burn_logs) > 0:
        print("\n[DATA AVAILABLE] This pool has V3 liquidity activity!")
        print("The mint/burn events contain:")
        print("  - Liquidity amounts")
        print("  - Token amounts (BTCB and USDT)")
        print("  - Price ranges (tick bounds)")
        print("  - Owner addresses")
        print("\nThis data should be properly decoded and stored.")
    else:
        print("\n[LOW ACTIVITY] Pool has very low liquidity activity")
        
except Exception as e:
    print(f"Error: {e}")