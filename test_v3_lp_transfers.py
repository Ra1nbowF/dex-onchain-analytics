"""Test PancakeSwap V3 LP token transfers"""

from web3 import Web3
from datetime import datetime

# Connect to BSC
rpc_url = "https://bsc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    print("Failed to connect to BSC")
    exit(1)

print("Testing PancakeSwap V3 LP Token Transfers")
print("=" * 60)

# PancakeSwap V3 NFT Position Manager (LP token for V3)
V3_LP_TOKEN = "0x46a15b0b27311cedf172ab29e4f4766fbe7f4364"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

lp_token = w3.to_checksum_address(V3_LP_TOKEN)
pool = w3.to_checksum_address(POOL_ADDRESS)

print(f"V3 LP Token (NFT Position Manager): {lp_token}")
print(f"Pool Contract: {pool}")

# Verify contracts
lp_code = w3.eth.get_code(lp_token)
pool_code = w3.eth.get_code(pool)

print(f"\nContract Verification:")
print(f"  V3 LP Token: {'Valid' if len(lp_code) > 2 else 'Invalid'} ({len(lp_code)} bytes)")
print(f"  Pool: {'Valid' if len(pool_code) > 2 else 'Invalid'} ({len(pool_code)} bytes)")

# Get current block
current_block = w3.eth.block_number
from_block = current_block - 1000  # Last ~50 minutes

print(f"\nSearching blocks {from_block} to {current_block}...")

# ERC721 Transfer event signature (V3 uses NFTs for positions)
transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Get all transfers of the V3 LP token
try:
    logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': lp_token,
        'topics': [transfer_topic]
    })
    
    print(f"\nFound {len(logs)} total V3 LP transfers")
    
    # Filter for pool-related transfers
    pool_related = []
    pool_addr_lower = pool.lower()
    
    for log in logs:
        if len(log['topics']) >= 3:
            from_addr = "0x" + log['topics'][1].hex()[-40:].lower()
            to_addr = "0x" + log['topics'][2].hex()[-40:].lower()
            
            # Check if transfer involves our pool
            if from_addr == pool_addr_lower or to_addr == pool_addr_lower:
                pool_related.append(log)
    
    print(f"Found {len(pool_related)} transfers involving our pool")
    
    if pool_related:
        print("\nPool-related transfers (last 5):")
        for i, log in enumerate(pool_related[-5:], 1):
            print(f"\nTransfer {i}:")
            print(f"  Block: {log['blockNumber']}")
            print(f"  TxHash: {log['transactionHash'].hex()}")
            
            # Decode from/to
            from_addr = "0x" + log['topics'][1].hex()[-40:]
            to_addr = "0x" + log['topics'][2].hex()[-40:]
            print(f"  From: {from_addr[:10]}...{from_addr[-4:]}")
            print(f"  To: {to_addr[:10]}...{to_addr[-4:]}")
            
            # Check if it's mint/burn
            if from_addr.lower() == "0x" + "0" * 40:
                print(f"  Type: MINT (Add Liquidity)")
            elif to_addr.lower() == "0x" + "0" * 40:
                print(f"  Type: BURN (Remove Liquidity)")
            elif to_addr.lower() == pool_addr_lower:
                print(f"  Type: TRANSFER TO POOL")
            elif from_addr.lower() == pool_addr_lower:
                print(f"  Type: TRANSFER FROM POOL")
            else:
                print(f"  Type: TRANSFER")
            
            # For V3, the data field contains the token ID (NFT position)
            if log['data']:
                token_id = int(log['data'].hex(), 16)
                print(f"  Position ID: {token_id}")
    else:
        print("\nNo transfers found involving our pool in the last 1000 blocks")
        print("Checking if there are ANY transfers to/from the pool...")
        
        # Show some sample transfers to understand the pattern
        if logs:
            print(f"\nSample V3 LP transfers (first 3):")
            for i, log in enumerate(logs[:3], 1):
                from_addr = "0x" + log['topics'][1].hex()[-40:]
                to_addr = "0x" + log['topics'][2].hex()[-40:]
                token_id = int(log['data'].hex(), 16) if log['data'] else 0
                print(f"\n  Transfer {i}:")
                print(f"    From: {from_addr[:10]}...")
                print(f"    To: {to_addr[:10]}...")
                print(f"    Token ID: {token_id}")
                
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Summary:")
print(f"- V3 uses NFT positions (ERC721) instead of fungible LP tokens (ERC20)")
print(f"- Each liquidity position is represented by a unique NFT with an ID")
print(f"- The NFT Position Manager contract: {V3_LP_TOKEN}")
print(f"- We need to track transfers of these NFTs related to our pool")