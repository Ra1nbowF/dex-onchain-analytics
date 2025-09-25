"""Test getting Transfer logs directly from BSCScan"""

import asyncio
import aiohttp
from datetime import datetime

API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"
LP_TOKEN_ADDRESS = "0x41ff9aa7e16b8b1a8a8dc4f0efacd93d02d071c9"

async def test_logs():
    async with aiohttp.ClientSession() as session:
        print("Testing BSCScan getLogs for LP Token Transfers")
        print("=" * 60)
        
        # First get current block
        url = "https://api.bscscan.com/api"
        params = {
            "module": "proxy",
            "action": "eth_blockNumber",
            "apikey": API_KEY
        }
        
        async with session.get(url, params=params) as response:
            data = await response.json()
            current_block = int(data.get('result', '0x0'), 16)
            print(f"Current block: {current_block}")
            
        # Now get Transfer events
        from_block = current_block - 500  # Last 500 blocks (~25 minutes)
        
        # ERC20 Transfer event signature
        transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        
        params = {
            "module": "logs",
            "action": "getLogs",
            "address": LP_TOKEN_ADDRESS,
            "fromBlock": str(from_block),
            "toBlock": str(current_block),
            "topic0": transfer_topic,
            "apikey": API_KEY
        }
        
        print(f"\nFetching Transfer events from blocks {from_block} to {current_block}...")
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            
            if data.get('status') == '1' and data.get('result'):
                logs = data.get('result', [])
                print(f"\n[SUCCESS] Found {len(logs)} Transfer events\n")
                
                # Analyze transfer types
                mints = 0
                burns = 0
                transfers = 0
                
                for log in logs:
                    topics = log.get('topics', [])
                    if len(topics) >= 3:
                        from_addr = topics[1][-40:].lower()
                        to_addr = topics[2][-40:].lower()
                        
                        if from_addr == "0" * 40:
                            mints += 1
                        elif to_addr == "0" * 40:
                            burns += 1
                        else:
                            transfers += 1
                
                print(f"Transfer Types:")
                print(f"  Mints (Add Liquidity): {mints}")
                print(f"  Burns (Remove Liquidity): {burns}")
                print(f"  Regular Transfers: {transfers}")
                
                # Show recent events
                print(f"\nRecent Events (last 5):")
                for i, log in enumerate(logs[-5:], 1):
                    print(f"\nEvent {i}:")
                    print(f"  Block: {int(log.get('blockNumber', '0x0'), 16)}")
                    print(f"  TxHash: {log.get('transactionHash', '')}")
                    
                    # Decode from/to
                    topics = log.get('topics', [])
                    if len(topics) >= 3:
                        from_addr = "0x" + topics[1][-40:]
                        to_addr = "0x" + topics[2][-40:]
                        print(f"  From: {from_addr[:10]}...{from_addr[-4:]}")
                        print(f"  To: {to_addr[:10]}...{to_addr[-4:]}")
                        
                        # Decode amount
                        data_hex = log.get('data', '0x0')
                        amount = int(data_hex, 16) / 10**18
                        print(f"  Amount: {amount:.6f} LP tokens")
                        
                        # Type
                        if from_addr.lower().endswith("0" * 40):
                            print(f"  Type: MINT (Add Liquidity)")
                        elif to_addr.lower().endswith("0" * 40):
                            print(f"  Type: BURN (Remove Liquidity)")
                        else:
                            print(f"  Type: TRANSFER")
                        
                        # Time
                        timestamp_hex = log.get('timeStamp', '0x0')
                        timestamp = int(timestamp_hex, 16)
                        dt = datetime.fromtimestamp(timestamp)
                        print(f"  Time: {dt}")
            else:
                print(f"\n[FAILED] {data.get('result', 'No results')}")
                print(f"\nDebug info:")
                print(f"  LP Token: {LP_TOKEN_ADDRESS}")
                print(f"  From Block: {from_block}")
                print(f"  To Block: {current_block}")
                print(f"  Topic0: {transfer_topic}")

asyncio.run(test_logs())