import asyncio
import aiohttp

MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

BTCB_ADDRESS = "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"

async def test_top_gainers_chains():
    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    # According to docs, supported chains for top-gainers are:
    # eth, mainnet, 0x1, matic, 0x89, polygon, bsc, binance, 0x38,
    # fantom, ftm, 0xfa, arbitrum, 0xa4b1, optimism, 0xa, base, 0x2105,
    # linea, 0xe708, 0x7e4, ronin

    chains_to_test = [
        "bsc",
        "binance",
        "0x38",
        "eth",
        "polygon"
    ]

    async with aiohttp.ClientSession(headers=headers) as session:
        print("Testing TOP-GAINERS endpoint with different chain parameters:")
        print("="*60)

        for chain in chains_to_test:
            url = f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/top-gainers"
            params = {"chain": chain, "days": "7"}  # Try 7 days instead of "all"

            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_count = len(data.get('result', [])) if 'result' in data else 0
                        print(f"OK  Chain: {chain:10} - SUCCESS with {result_count} results")
                    else:
                        error_text = await response.text()
                        print(f"FAIL Chain: {chain:10} - Status {response.status}: {error_text[:80]}")
            except Exception as e:
                print(f"ERROR Chain: {chain:10} - {str(e)[:80]}")

        # Also test with Ethereum address on ETH chain
        print("\nTesting with Ethereum WETH token on eth chain:")
        WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        url = f"{MORALIS_BASE_URL}/erc20/{WETH_ADDRESS}/top-gainers"
        params = {"chain": "eth", "days": "7"}

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result_count = len(data.get('result', [])) if 'result' in data else 0
                    print(f"OK  WETH on eth - SUCCESS with {result_count} results")
                    if result_count > 0:
                        print("Sample result fields:", list(data['result'][0].keys())[:5])
                else:
                    error_text = await response.text()
                    print(f"FAIL WETH on eth - Status {response.status}: {error_text[:80]}")
        except Exception as e:
            print(f"ERROR WETH on eth - {str(e)[:80]}")

if __name__ == "__main__":
    asyncio.run(test_top_gainers_chains())