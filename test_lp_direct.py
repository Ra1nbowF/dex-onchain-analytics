import asyncio
import aiohttp
import json

POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BSCSCAN_API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"

async def test_apis():
    async with aiohttp.ClientSession() as session:
        # Test 1: Try the correct BSCScan API endpoint
        url = "https://api.bscscan.com/api"

        # Get total supply
        params = {
            "module": "stats",
            "action": "tokensupply",
            "contractaddress": POOL_ADDRESS,
            "apikey": BSCSCAN_API_KEY
        }

        print("Testing total supply endpoint...")
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"Response: {json.dumps(data, indent=2)}")

        # Get LP token transfers
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": POOL_ADDRESS,
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": "5",
            "sort": "desc",
            "apikey": BSCSCAN_API_KEY
        }

        print("\nTesting token transfers endpoint...")
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            if data.get('result') and isinstance(data['result'], list):
                print(f"Found {len(data['result'])} transfers")
                if len(data['result']) > 0:
                    print("\nFirst transfer:")
                    for key, value in data['result'][0].items():
                        print(f"  {key}: {value}")

asyncio.run(test_apis())