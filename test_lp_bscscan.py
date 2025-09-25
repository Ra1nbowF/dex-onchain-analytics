import asyncio
import aiohttp
import json
from datetime import datetime

LP_TOKEN_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BSCSCAN_API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"

async def test_lp_transfers():
    async with aiohttp.ClientSession() as session:
        url = "https://api.bscscan.com/api"

        # Test getting LP token transfers
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": LP_TOKEN_ADDRESS,
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": "10",  # Get last 10 transfers
            "sort": "desc",
            "apikey": BSCSCAN_API_KEY
        }

        print(f"Fetching LP token transfers for: {LP_TOKEN_ADDRESS}")
        print("Using BSCScan API endpoint...")

        async with session.get(url, params=params) as response:
            data = await response.json()

            print(f"\nStatus: {data.get('status')}")
            print(f"Message: {data.get('message')}")

            if data.get("status") == "1" and data.get("result"):
                transfers = data["result"]
                print(f"\nFound {len(transfers)} recent LP token transfers:")

                for i, tx in enumerate(transfers[:5], 1):  # Show first 5
                    print(f"\n--- Transfer #{i} ---")
                    print(f"  Hash: {tx.get('hash')[:10]}...")
                    print(f"  Block: {tx.get('blockNumber')}")
                    print(f"  From: {tx.get('from')[:10]}...")
                    print(f"  To: {tx.get('to')[:10]}...")

                    value = int(tx.get('value', 0)) / 10**18
                    print(f"  Amount: {value:.6f} LP tokens")

                    timestamp = int(tx.get('timeStamp', 0))
                    dt = datetime.fromtimestamp(timestamp)
                    print(f"  Time: {dt}")

                    # Check if it's mint/burn
                    from_addr = tx.get('from', '').lower()
                    to_addr = tx.get('to', '').lower()
                    if from_addr == "0x" + "0" * 40:
                        print(f"  Type: MINT (Add Liquidity)")
                    elif to_addr == "0x" + "0" * 40:
                        print(f"  Type: BURN (Remove Liquidity)")
                    else:
                        print(f"  Type: TRANSFER")
            else:
                print(f"\nNo transfers found or error: {data}")

asyncio.run(test_lp_transfers())