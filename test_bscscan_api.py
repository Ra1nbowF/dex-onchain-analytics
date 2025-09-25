"""Test BSCScan API directly"""

import asyncio
import aiohttp
import os

# Test with the key we have
API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"

async def test_api():
    async with aiohttp.ClientSession() as session:
        print("Testing BSCScan API with current key...")
        print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
        print("=" * 60)

        # Test 1: Token balance (the failing endpoint)
        url = "https://api.bscscan.com/api"
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": "0x55d398326f99059fF775485246999027B3197955",  # USDT
            "address": "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4",  # Pool
            "tag": "latest",
            "apikey": API_KEY
        }

        print("\n1. Testing tokenbalance endpoint:")
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            if data.get('status') == '1':
                balance = int(data.get('result', 0)) / 10**18
                print(f"   Balance: {balance:.2f} USDT")
            else:
                print(f"   Result: {data.get('result')}")

        # Test 2: Try without API key
        params_no_key = params.copy()
        del params_no_key['apikey']

        print("\n2. Testing same endpoint WITHOUT API key:")
        async with session.get(url, params=params_no_key) as response:
            data = await response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Result: {data.get('result', '')[:100]}")

        # Test 3: Try account balance (BNB balance)
        params_bnb = {
            "module": "account",
            "action": "balance",
            "address": "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4",
            "tag": "latest",
            "apikey": API_KEY
        }

        print("\n3. Testing BNB balance endpoint:")
        async with session.get(url, params=params_bnb) as response:
            data = await response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            if data.get('status') == '1':
                balance = int(data.get('result', 0)) / 10**18
                print(f"   Balance: {balance:.6f} BNB")
            else:
                print(f"   Result: {data.get('result', '')[:100]}")

asyncio.run(test_api())