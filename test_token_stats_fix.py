import asyncio
import aiohttp

MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

async def test_token_stats():
    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    test_cases = [
        # Test different tokens on BSC
        ("BTCB on BSC", "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c", "bsc"),
        ("USDT on BSC", "0x55d398326f99059fF775485246999027B3197955", "bsc"),
        ("BNB on BSC", "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", "bsc"),

        # Test on Ethereum
        ("WETH on ETH", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "eth"),
        ("USDT on ETH", "0xdAC17F958D2ee523a2206206994597C13D831ec7", "eth"),

        # Test on Polygon
        ("WMATIC on Polygon", "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", "polygon"),
    ]

    async with aiohttp.ClientSession(headers=headers) as session:
        print("Testing TOKEN-STATS endpoint with different tokens and chains:")
        print("="*70)

        for name, address, chain in test_cases:
            url = f"{MORALIS_BASE_URL}/erc20/{address}/stats"
            params = {"chain": chain}

            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        transfers = data.get('transfers', {}).get('total', 'N/A')
                        print(f"OK  {name:20} - SUCCESS - Total transfers: {transfers}")
                    else:
                        error_text = await response.text()
                        print(f"FAIL {name:20} - Status {response.status}: {error_text[:60]}")
            except Exception as e:
                print(f"ERROR {name:20} - {str(e)[:60]}")

        # Test with different API versions
        print("\nTesting with different API versions:")
        versions = ["v2", "v2.2", "v2.1"]

        for version in versions:
            base_url = f"https://deep-index.moralis.io/api/{version}"
            url = f"{base_url}/erc20/0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c/stats"
            params = {"chain": "bsc"}

            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        transfers = data.get('transfers', {}).get('total', 'N/A')
                        print(f"OK  Version {version:4} - SUCCESS - Total transfers: {transfers}")
                    else:
                        error_text = await response.text()
                        print(f"FAIL Version {version:4} - Status {response.status}: {error_text[:60]}")
            except Exception as e:
                print(f"ERROR Version {version:4} - {str(e)[:60]}")

if __name__ == "__main__":
    asyncio.run(test_token_stats())