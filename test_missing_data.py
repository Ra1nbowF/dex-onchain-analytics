import asyncio
import aiohttp
import json

MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

BTCB_ADDRESS = "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

async def test_missing_endpoints():
    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # Test holder stats
        print("="*60)
        print("1. Testing HOLDER STATS endpoint:")
        url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/holders"
        params = {"chain": "bsc"}

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                print(f"SUCCESS - Response keys: {list(data.keys())[:10]}")
                print(f"Total holders: {data.get('totalHolders', 'N/A')}")

                # Show holder distribution
                if 'holderDistribution' in data:
                    print("Holder Distribution:")
                    for key, value in data['holderDistribution'].items():
                        print(f"  {key}: {value}")

                # Show holder supply
                if 'holderSupply' in data:
                    print("Holder Supply Top Concentrations:")
                    for key, value in list(data['holderSupply'].items())[:3]:
                        print(f"  {key}: {value}")

            else:
                print(f"FAILED - Status: {response.status}")

        # Test pair stats
        print("\n" + "="*60)
        print("2. Testing PAIR STATS endpoint:")
        url = f"{MORALIS_BASE_URL}/pairs/{POOL_ADDRESS}/stats"
        params = {"chain": "bsc"}

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                print(f"SUCCESS - Response keys: {list(data.keys())[:10]}")
                print(f"Current USD Price: {data.get('currentUsdPrice', 'N/A')}")
                print(f"Total Liquidity: {data.get('totalLiquidityUsd', 'N/A')}")
                print(f"24h Volume: {data.get('totalVolume', {}).get('24h', 'N/A')}")

                # Show price changes
                if 'pricePercentChange' in data:
                    print("Price Changes:")
                    for key, value in data['pricePercentChange'].items():
                        print(f"  {key}: {value}%")

            else:
                print(f"FAILED - Status: {response.status}")

        # Test price endpoint (we know this works)
        print("\n" + "="*60)
        print("3. Testing PRICE endpoint (for comparison):")
        url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/price"
        params = {"chain": "bsc"}

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                print(f"SUCCESS - USD Price: ${data.get('usdPrice', 'N/A')}")
            else:
                print(f"FAILED - Status: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_missing_endpoints())