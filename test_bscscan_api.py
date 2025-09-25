import asyncio
import aiohttp
import json

POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BSCSCAN_API_KEY = "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"

async def test_correct_api():
    async with aiohttp.ClientSession() as session:
        # Test getting current block number
        url = "https://api.bscscan.com/api"
        params = {
            "module": "proxy",
            "action": "eth_blockNumber",
            "apikey": BSCSCAN_API_KEY
        }

        print("1. Testing block number:")
        async with session.get(url, params=params) as response:
            data = await response.json()
            print(f"Response: {data}")
            if data.get("result"):
                block = int(data["result"], 16) if "0x" in str(data["result"]) else int(data["result"])
                print(f"Current block: {block}")

        # Test getting token balance
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",  # BTCB
            "address": POOL_ADDRESS,
            "tag": "latest",
            "apikey": BSCSCAN_API_KEY
        }

        print("\n2. Testing token balance:")
        async with session.get(url, params=params) as response:
            data = await response.json()
            if data.get("status") == "1":
                balance = int(data["result"]) / 10**18
                print(f"BTCB balance in pool: {balance:.4f}")
            else:
                print(f"Error: {data}")

        # Test getting LP token transfers (ERC20 Transfer events)
        current_block = 34000000  # Recent block
        start_block = current_block - 1000  # Last 1000 blocks

        params = {
            "module": "logs",
            "action": "getLogs",
            "address": POOL_ADDRESS,
            "fromBlock": str(start_block),
            "toBlock": str(current_block),
            "topic0": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer
            "apikey": BSCSCAN_API_KEY
        }

        print(f"\n3. Testing LP token transfers (blocks {start_block} to {current_block}):")
        async with session.get(url, params=params) as response:
            data = await response.json()
            if data.get("status") == "1" and data.get("result"):
                print(f"Found {len(data['result'])} transfer events")
                if len(data['result']) > 0:
                    print("First transfer event:")
                    tx = data['result'][0]
                    print(f"  Block: {int(tx['blockNumber'], 16)}")
                    print(f"  TX: {tx['transactionHash']}")
                    if len(tx['topics']) >= 3:
                        from_addr = "0x" + tx['topics'][1][-40:]
                        to_addr = "0x" + tx['topics'][2][-40:]
                        amount = int(tx['data'], 16) / 10**18 if tx['data'] != "0x" else 0
                        print(f"  From: {from_addr}")
                        print(f"  To: {to_addr}")
                        print(f"  Amount: {amount:.6f} LP tokens")
            else:
                print(f"No transfers found or error: {data}")

asyncio.run(test_correct_api())