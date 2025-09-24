import asyncio
import aiohttp

MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

BTCB_ADDRESS = "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

async def test_endpoints():
    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        endpoints = [
            (f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/transfers", {"chain": "bsc", "limit": 5}),
            (f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/price", {"chain": "bsc"}),
            (f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/owners", {"chain": "bsc", "limit": 5}),
            (f"{MORALIS_BASE_URL}/erc20/metadata", {"chain": "bsc", "addresses": [BTCB_ADDRESS]}),
        ]

        for url, params in endpoints:
            try:
                async with session.get(url, params=params) as response:
                    endpoint = url.split('/api/v2.2/')[-1]
                    if response.status == 200:
                        data = await response.json()
                        print(f"OK {endpoint}: SUCCESS")
                        # Show sample data
                        if isinstance(data, dict):
                            if 'result' in data:
                                print(f"   Found {len(data['result'])} results")
                            elif 'usdPrice' in data:
                                print(f"   Price: ${data['usdPrice']}")
                        elif isinstance(data, list) and len(data) > 0:
                            print(f"   Found {len(data)} items")
                    else:
                        print(f"FAIL {endpoint}: {response.status}")
            except Exception as e:
                print(f"ERROR {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())