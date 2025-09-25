"""Test LP token transfers from BSCScan API"""

import asyncio
import aiohttp
from datetime import datetime

API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"
LP_TOKEN_ADDRESS = "0x41ff9aa7e16b8b1a8a8dc4f0efacd93d02d071c9"  # Correct LP token address

async def test_lp_transfers():
    async with aiohttp.ClientSession() as session:
        print("Testing LP Token Transfer Endpoint")
        print("=" * 60)
        print(f"LP Token Address: {LP_TOKEN_ADDRESS}")
        print()
        
        # Test tokentx endpoint for LP token transfers
        url = "https://api.bscscan.com/api"
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": LP_TOKEN_ADDRESS,
            "page": "1",
            "offset": "10",  # Get last 10 transfers
            "sort": "desc",
            "apikey": API_KEY
        }
        
        print("Testing BSCScan tokentx endpoint...")
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            
            if data.get("status") == "1" and data.get("result"):
                transfers = data.get("result", [])
                print(f"\nFound {len(transfers)} transfers")
                
                for i, tx in enumerate(transfers[:3], 1):
                    print(f"\nTransfer {i}:")
                    print(f"  Hash: {tx.get('hash')}")
                    print(f"  From: {tx.get('from')[:10]}...")
                    print(f"  To: {tx.get('to')[:10]}...")
                    value = int(tx.get('value', 0)) / 10**18
                    print(f"  Amount: {value:.6f} LP tokens")
                    timestamp = datetime.fromtimestamp(int(tx.get('timeStamp', 0)))
                    print(f"  Time: {timestamp}")
                    
                    # Check transfer type
                    from_addr = tx.get('from', '').lower()
                    to_addr = tx.get('to', '').lower()
                    if from_addr == "0x" + "0" * 40:
                        print(f"  Type: MINT (Add Liquidity)")
                    elif to_addr == "0x" + "0" * 40:
                        print(f"  Type: BURN (Remove Liquidity)")
                    else:
                        print(f"  Type: TRANSFER")
            else:
                print(f"\nNo transfers found or API error")
                print(f"Result: {data.get('result')}")

asyncio.run(test_lp_transfers())