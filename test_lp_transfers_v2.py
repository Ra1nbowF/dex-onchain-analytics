"""Test LP token transfers using Etherscan V2 API"""

import asyncio
import aiohttp
from datetime import datetime

API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"
LP_TOKEN_ADDRESS = "0x41ff9aa7e16b8b1a8a8dc4f0efacd93d02d071c9"  # LP token
SAMPLE_WALLET = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"  # Pool address for testing

async def test_v2_transfers():
    async with aiohttp.ClientSession() as session:
        print("Testing Etherscan V2 API for LP Token Transfers")
        print("=" * 60)
        
        # Test 1: Get token transfers for a specific address
        print("\n1. Testing V2 tokentransfers endpoint:")
        url = "https://api.etherscan.io/v2/api"
        params = {
            "chainid": "56",  # BSC
            "module": "account",
            "action": "tokentransfers",  # V2 endpoint for token transfers
            "address": SAMPLE_WALLET,  # Address to check transfers for
            "contractaddress": LP_TOKEN_ADDRESS,  # Filter by LP token
            "page": "1",
            "offset": "10",
            "sort": "desc",
            "apikey": API_KEY
        }
        
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            if data.get('status') == '1':
                transfers = data.get('result', [])
                print(f"   [SUCCESS] Found {len(transfers)} transfers")
                
                for i, tx in enumerate(transfers[:3], 1):
                    print(f"\n   Transfer {i}:")
                    print(f"     From: {tx.get('from', '')[:10]}...")
                    print(f"     To: {tx.get('to', '')[:10]}...")
                    value = int(tx.get('value', 0)) / 10**18
                    print(f"     Amount: {value:.6f} LP")
            else:
                print(f"   [FAILED] {data.get('result')}")
        
        # Test 2: Try alternate endpoint - get all ERC20 transfers
        print("\n2. Testing V2 erc20transfers endpoint:")
        params2 = {
            "chainid": "56",
            "module": "account",
            "action": "tokentx",  # Try original name with V2
            "contractaddress": LP_TOKEN_ADDRESS,
            "page": "1",
            "offset": "10",
            "sort": "desc",
            "apikey": API_KEY
        }
        
        async with session.get(url, params=params2) as response:
            data = await response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            if data.get('status') == '1':
                print(f"   [SUCCESS]")
            else:
                print(f"   [FAILED] {data.get('result', '')[:100]}")
        
        # Test 3: Get events using logs endpoint
        print("\n3. Testing V2 logs endpoint for Transfer events:")
        
        # Get current block
        block_params = {
            "chainid": "56",
            "module": "proxy",
            "action": "eth_blockNumber",
            "apikey": API_KEY
        }
        
        async with session.get(url, params=block_params) as response:
            block_data = await response.json()
            if block_data.get('status') == '1':
                current_block = int(block_data.get('result', '0x0'), 16)
                from_block = current_block - 1000  # Last 1000 blocks
                
                # Transfer event topic
                transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                
                log_params = {
                    "chainid": "56",
                    "module": "logs",
                    "action": "getLogs",
                    "address": LP_TOKEN_ADDRESS,
                    "fromBlock": str(from_block),
                    "toBlock": "latest",
                    "topic0": transfer_topic,
                    "page": "1",
                    "offset": "10",
                    "apikey": API_KEY
                }
                
                async with session.get(url, params=log_params) as response:
                    data = await response.json()
                    print(f"   Status: {data.get('status')}")
                    print(f"   Message: {data.get('message')}")
                    
                    if data.get('status') == '1':
                        logs = data.get('result', [])
                        print(f"   [SUCCESS] Found {len(logs)} Transfer events")
                        
                        for i, log in enumerate(logs[:3], 1):
                            print(f"\n   Event {i}:")
                            print(f"     Block: {int(log.get('blockNumber', '0x0'), 16)}")
                            print(f"     TxHash: {log.get('transactionHash', '')[:10]}...")
                            
                            # Decode from/to from topics
                            topics = log.get('topics', [])
                            if len(topics) >= 3:
                                from_addr = "0x" + topics[1][-40:]
                                to_addr = "0x" + topics[2][-40:]
                                print(f"     From: {from_addr[:10]}...")
                                print(f"     To: {to_addr[:10]}...")
                                
                                # Decode amount
                                data_hex = log.get('data', '0x0')
                                amount = int(data_hex, 16) / 10**18
                                print(f"     Amount: {amount:.6f} LP")
                    else:
                        print(f"   [FAILED] {data.get('result', '')}")

asyncio.run(test_v2_transfers())