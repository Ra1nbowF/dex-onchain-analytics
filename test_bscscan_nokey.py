import asyncio
import aiohttp
import json

POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

async def test_without_key():
    async with aiohttp.ClientSession() as session:
        # Test without API key (BSCScan allows some requests)
        url = "https://api.bscscan.com/api"

        # Get current block
        params = {
            "module": "proxy",
            "action": "eth_blockNumber"
        }

        print("1. Testing block number (no API key):")
        async with session.get(url, params=params) as response:
            data = await response.json()
            if data.get("result") and "0x" in str(data.get("result")):
                block = int(data["result"], 16)
                print(f"Current block: {block}")
            else:
                print(f"Response: {data}")

        # Try getting transfers through account module
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": POOL_ADDRESS,
            "page": "1",
            "offset": "5",
            "sort": "desc"
        }

        print("\n2. Testing token transfers (account module):")
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            if data.get("result") and isinstance(data["result"], list):
                print(f"Found {len(data['result'])} transfers")
                if len(data['result']) > 0:
                    tx = data['result'][0]
                    print("\nLatest transfer:")
                    print(f"  Block: {tx.get('blockNumber')}")
                    print(f"  From: {tx.get('from')[:10]}...")
                    print(f"  To: {tx.get('to')[:10]}...")
                    print(f"  Value: {int(tx.get('value', 0)) / 10**18:.6f} LP tokens")
                    print(f"  Time: {tx.get('timeStamp')}")

asyncio.run(test_without_key())