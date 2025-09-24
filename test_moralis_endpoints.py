import asyncio
import aiohttp

MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

BTCB_ADDRESS = "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

async def test_all_endpoints():
    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        endpoints = [
            # 1. SWAPS
            ("SWAPS", f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/swaps", {"chain": "bsc", "limit": 5}),

            # 2. TRANSFERS
            ("TRANSFERS", f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/transfers", {"chain": "bsc", "limit": 5}),

            # 3. TOP GAINERS
            ("TOP-GAINERS", f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/top-gainers", {"chain": "bsc", "days": "all"}),

            # 4. PAIR STATS
            ("PAIR-STATS", f"{MORALIS_BASE_URL}/pairs/{POOL_ADDRESS}/stats", {"chain": "bsc"}),

            # 5. TOKEN ANALYTICS
            ("TOKEN-ANALYTICS", f"{MORALIS_BASE_URL}/tokens/{BTCB_ADDRESS}/analytics", {"chain": "bsc"}),

            # 6. TOKEN STATS
            ("TOKEN-STATS", f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/stats", {"chain": "bsc"}),

            # 7. HOLDER STATS
            ("HOLDER-STATS", f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/holders", {"chain": "bsc"}),

            # 8. HISTORICAL HOLDERS (requires dates)
            ("HISTORICAL-HOLDERS", f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/holders/historical", {
                "chain": "bsc",
                "fromDate": "2025-01-01T00:00:00",
                "toDate": "2025-01-24T00:00:00",
                "timeFrame": "1d"
            }),

            # 9. SNIPERS
            ("SNIPERS", f"{MORALIS_BASE_URL}/pairs/{POOL_ADDRESS}/snipers", {"chain": "bsc", "blocksAfterCreation": 3}),

            # Also test the working endpoints we know
            ("PRICE", f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/price", {"chain": "bsc"}),
            ("OWNERS", f"{MORALIS_BASE_URL}/erc20/{BTCB_ADDRESS}/owners", {"chain": "bsc", "limit": 5}),
            ("METADATA", f"{MORALIS_BASE_URL}/erc20/metadata", {"chain": "bsc", "addresses": [BTCB_ADDRESS]}),
        ]

        print("="*60)
        print("TESTING ALL MORALIS ENDPOINTS")
        print("="*60)

        for name, url, params in endpoints:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Check response structure
                        if isinstance(data, dict):
                            if 'result' in data:
                                count = len(data['result']) if isinstance(data['result'], list) else 1
                                print(f"OK {name:20} SUCCESS - {count} results")
                                # Show sample structure
                                if isinstance(data['result'], list) and len(data['result']) > 0:
                                    sample = data['result'][0]
                                    keys = list(sample.keys())[:5]
                                    print(f"   Sample fields: {', '.join(keys)}")
                            else:
                                print(f"OK {name:20} SUCCESS - Direct response")
                                keys = list(data.keys())[:5]
                                print(f"   Fields: {', '.join(keys)}")
                        elif isinstance(data, list):
                            print(f"OK {name:20} SUCCESS - {len(data)} items")
                            if len(data) > 0:
                                keys = list(data[0].keys())[:5]
                                print(f"   Sample fields: {', '.join(keys)}")
                        else:
                            print(f"OK {name:20} SUCCESS - Simple value")
                    else:
                        error_text = await response.text()
                        error_msg = error_text[:100] if len(error_text) > 100 else error_text
                        print(f"FAIL {name:20} FAILED ({response.status}) - {error_msg}")
            except Exception as e:
                print(f"ERROR {name:20} ERROR - {str(e)[:80]}")

        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())