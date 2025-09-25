"""Test Etherscan V2 API for BSC"""

import asyncio
import aiohttp

API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

async def test_v2():
    async with aiohttp.ClientSession() as session:
        print("Testing Etherscan V2 API for BSC (chainid=56)")
        print("=" * 60)

        # Test V2 tokenbalance endpoint
        url = "https://api.etherscan.io/v2/api"
        params = {
            "chainid": "56",  # BSC
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": USDT_ADDRESS,
            "address": POOL_ADDRESS,
            "tag": "latest",
            "apikey": API_KEY
        }

        print("\n1. Testing V2 tokenbalance endpoint:")
        print(f"   URL: {url}")
        print(f"   ChainID: 56 (BSC)")

        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")

            if data.get('status') == '1':
                balance = int(data.get('result', 0)) / 10**18
                print(f"   [SUCCESS] USDT Balance: {balance:,.2f}")
            else:
                print(f"   Result: {data.get('result')}")

asyncio.run(test_v2())