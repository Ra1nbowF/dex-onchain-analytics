"""Investigate V3 NFT Position data"""

from web3 import Web3
import json
from datetime import datetime

# Connect to BSC
rpc_url = "https://bsc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    print("Failed to connect to BSC")
    exit(1)

print("Investigating PancakeSwap V3 NFT Position Data")
print("=" * 70)

# V3 Contracts
V3_POSITION_MANAGER = "0x46a15b0b27311cedf172ab29e4f4766fbe7f4364"
V3_POOL = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

# V3 Position Manager ABI (partial - just what we need)
POSITION_MANAGER_ABI = json.loads('''
[
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
    },
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "owner", "type": "address"}],
        "outputs": [{"name": "balance", "type": "uint256"}]
    },
    {
        "name": "tokenOfOwnerByIndex",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "index", "type": "uint256"}
        ],
        "outputs": [{"name": "tokenId", "type": "uint256"}]
    },
    {
        "name": "ownerOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "outputs": [{"name": "owner", "type": "address"}]
    }
]
''')

# Create contract instance
position_manager = w3.eth.contract(
    address=Web3.to_checksum_address(V3_POSITION_MANAGER),
    abi=POSITION_MANAGER_ABI
)

print(f"V3 Position Manager: {V3_POSITION_MANAGER}")
print(f"V3 Pool: {V3_POOL}")
print()

# Function to decode tick to price
def tick_to_price(tick, decimals0=18, decimals1=18):
    """Convert tick to price"""
    return 1.0001 ** tick * (10 ** (decimals0 - decimals1))

def format_liquidity(liquidity):
    """Format liquidity amount"""
    if liquidity > 10**12:
        return f"{liquidity / 10**18:.4f}"
    else:
        return str(liquidity)

# Get recent Transfer events to find NFT IDs
print("1. Finding Recent V3 Position NFTs:")
print("-" * 50)

current_block = w3.eth.block_number
from_block = current_block - 10000  # Last ~8 hours

# ERC721 Transfer event
transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

try:
    logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': Web3.to_checksum_address(V3_POSITION_MANAGER),
        'topics': [transfer_topic]
    })
    
    print(f"Found {len(logs)} NFT transfers in last 10,000 blocks")
    
    # Get unique token IDs
    token_ids = set()
    recent_positions = []
    
    for log in logs[-20:]:  # Last 20 transfers
        # For ERC721, tokenId is usually in topic[3] or data field
        # Let's try both approaches
        token_id = None

        if len(log['topics']) >= 4:
            # Token ID might be in topic[3]
            token_id = int(log['topics'][3].hex(), 16)
        elif log['data'] and len(log['data']) > 2:
            # Or in data field
            token_id = int(log['data'].hex(), 16)

        if token_id:
            token_ids.add(token_id)
            
            # Get from/to addresses
            from_addr = "0x" + log['topics'][1].hex()[-40:] if len(log['topics']) > 1 else "0x0"
            to_addr = "0x" + log['topics'][2].hex()[-40:] if len(log['topics']) > 2 else "0x0"
            
            recent_positions.append({
                'token_id': token_id,
                'from': from_addr,
                'to': to_addr,
                'block': log['blockNumber'],
                'tx_hash': log['transactionHash'].hex()
            })
    
    print(f"Unique position NFTs: {len(token_ids)}")
    
    # Analyze some positions
    print("\n2. V3 Position Details:")
    print("-" * 50)
    
    analyzed = 0
    for pos in recent_positions[-5:]:  # Analyze last 5
        token_id = pos['token_id']
        print(f"\nNFT Position #{token_id}:")
        print(f"  TX: {pos['tx_hash'][:10]}...")
        print(f"  Block: {pos['block']}")
        
        try:
            # Get position data
            position = position_manager.functions.positions(token_id).call()
            
            # Unpack position data
            nonce = position[0]
            operator = position[1]
            token0 = position[2]
            token1 = position[3]
            fee = position[4]
            tick_lower = position[5]
            tick_upper = position[6]
            liquidity = position[7]
            fee_growth0 = position[8]
            fee_growth1 = position[9]
            tokens_owed0 = position[10]
            tokens_owed1 = position[11]
            
            print(f"  Token0: {token0[:10]}... (BTCB)")
            print(f"  Token1: {token1[:10]}... (USDT)")
            print(f"  Fee Tier: {fee/10000}%")
            print(f"  Liquidity: {format_liquidity(liquidity)}")
            
            # Calculate price range
            price_lower = tick_to_price(tick_lower)
            price_upper = tick_to_price(tick_upper)
            
            print(f"  Price Range:")
            print(f"    Lower: {price_lower:.2f} BTCB/USDT")
            print(f"    Upper: {price_upper:.2f} BTCB/USDT")
            print(f"    Tick Lower: {tick_lower}")
            print(f"    Tick Upper: {tick_upper}")
            
            print(f"  Uncollected Fees:")
            print(f"    Token0: {tokens_owed0 / 10**18:.8f} BTCB")
            print(f"    Token1: {tokens_owed1 / 10**18:.2f} USDT")
            
            # Check if position is active
            if liquidity > 0:
                print(f"  Status: ACTIVE")
                
                # Try to get owner
                try:
                    owner = position_manager.functions.ownerOf(token_id).call()
                    print(f"  Owner: {owner[:10]}...{owner[-4:]}")
                except:
                    print(f"  Owner: Position may be burned")
            else:
                print(f"  Status: INACTIVE (liquidity removed)")
            
            analyzed += 1
            
        except Exception as e:
            print(f"  Error reading position: {e}")
    
    # Summary
    print("\n3. Summary of V3 NFT Positions:")
    print("-" * 50)
    print(f"Total transfers found: {len(logs)}")
    print(f"Unique positions: {len(token_ids)}")
    print(f"Positions analyzed: {analyzed}")
    
    if analyzed > 0:
        print("\n[INSIGHT] V3 NFT positions contain:")
        print("  - Liquidity amount")
        print("  - Price range (tick bounds)")
        print("  - Fee tier")
        print("  - Uncollected fees")
        print("  - Token pair addresses")
        print("\nThis data is valuable for:")
        print("  - Tracking concentrated liquidity positions")
        print("  - Analyzing price range strategies")
        print("  - Calculating impermanent loss")
        print("  - Monitoring fee accumulation")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("V3 NFT positions are rich data sources that should be tracked!")
print("They contain liquidity amounts, price ranges, and fee data.")