import asyncio
import aiohttp
import json

POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BTCB_ADDRESS = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"
BSCSCAN_API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"

async def test_v2_api():
    async with aiohttp.ClientSession() as session:
        # Try V2 endpoint with chainid
        url = "https://api.etherscan.io/v2/api"

        # Test with chainid for BSC
        params = {
            "chainid": "56",  # BSC chain ID
            "module": "proxy",
            "action": "eth_blockNumber",
            "apikey": BSCSCAN_API_KEY
        }

        print("1. Testing V2 API with chainid 56 (BSC):")
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"Response: {json.dumps(data, indent=2)}")

        # Try getting token balance on BSC
        params = {
            "chainid": "56",
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": BTCB_ADDRESS,
            "address": POOL_ADDRESS,
            "tag": "latest",
            "apikey": BSCSCAN_API_KEY
        }

        print("\n2. Testing token balance on BSC via V2:")
        async with session.get(url, params=params) as response:
            data = await response.json()
            if data.get("status") == "1":
                balance = int(data["result"]) / 10**18
                print(f"BTCB balance: {balance:.4f}")
            else:
                print(f"Response: {json.dumps(data, indent=2)}")

asyncio.run(test_v2_api())