import asyncio
import aiohttp
from datetime import datetime, timedelta

# Moralis API Configuration
MORALIS_API_KEY = \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk\"
BASE_URL = \"https://deep-index.moralis.io/api/v2.2\"

# Token and pair addresses from the BSC pool monitor
BTCB_ADDRESS = \"0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c\"
USDT_ADDRESS = \"0x55d398326f99059fF775485246999027B3197955\"
PAIR_ADDRESS = \"0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4\"

class MoralisTokenAnalytics:
    def __init__(self):
        self.headers = {
            \"accept\": \"application/json\",
            \"X-API-Key\": MORALIS_API_KEY
        }
        self.session = None

    async def initialize(self):
        \"\"\"Initialize HTTP session\"\"\"
        self.session = aiohttp.ClientSession(headers=self.headers)
        print(\"Moralis Token Analytics initialized\")

    async def cleanup(self):
        \"\"\"Close HTTP session\"\"\"
        if self.session:
            await self.session.close()

    async def get_token_stats(self, token_address, chain=\"bsc\"):
        \"\"\"Get token statistics - based on documentation: /token/{address}/stats\"\"\"
        url = f\"{BASE_URL}/token/{token_address}/stats\"
        params = {\"chain\": chain}
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                print(f\"\\n--- Token Stats for {token_address} ---\")
                print(f\"24h Volume: {data.get('volume24h', 'N/A')}\")
                print(f\"Market Cap: {data.get('marketCap', 'N/A')}\")
                print(f\"Price (USD): {data.get('price', 'N/A')}\")
                print(f\"Price Change 24h: {data.get('priceChange24h', 'N/A')}%\"\)
                print(f\"Total Supply: {data.get('totalSupply', 'N/A')}\")
                return data
        except Exception as e:
            print(f\"Error getting token stats for {token_address}: {e}\")
            return None

    async def get_token_holder_stats(self, token_address, chain=\"bsc\"):
        \"\"\"Get token holder statistics - based on documentation: /token/{address}/holder-stats\"\"\"
        url = f\"{BASE_URL}/token/{token_address}/holder-stats\"
        params = {\"chain\": chain}
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                print(f\"\\n--- Token Holder Stats for {token_address} ---\")
                print(f\"Total Holders: {data.get('totalHolders', 'N/A')}\")
                print(f\"New Holders (24h): {data.get('newHolders24h', 'N/A')}\")
                print(f\"Gini Coefficient: {data.get('giniCoefficient', 'N/A')}\")
                print(f\"Top 10 Concentration: {data.get('top10Concentration', 'N/A')}%\"\)
                print(f\"Top 100 Concentration: {data.get('top100Concentration', 'N/A')}%\"\)
                return data
        except Exception as e:
            print(f\"Error getting token holder stats for {token_address}: {e}\")
            return None

    async def get_token_transfers(self, token_address, chain=\"bsc\", limit=25, order=\"DESC\"):
        \"\"\"Get token transfers - based on documentation format: /token/{address}/transfers\"\"\"
        url = f\"{BASE_URL}/token/{token_address}/transfers\"
        params = {\"chain\": chain, \"limit\": limit, \"order\": order}
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                transfers = data.get('result', [])
                print(f\"\\n--- Recent Transfers for {token_address} ---\")
                for i, transfer in enumerate(transfers[:5]):  # Show first 5 transfers
                    print(f\"Transfer {i+1}:\")
                    print(f\"  From: {transfer.get('from_address', 'N/A')}\")
                    print(f\"  To: {transfer.get('to_address', 'N/A')}\")
                    print(f\"  Value: {transfer.get('value', 'N/A')}\")
                    print(f\"  Transaction Hash: {transfer.get('transaction_hash', 'N/A')}\")
                    print(f\"  Block Number: {transfer.get('block_number', 'N/A')}\")
                    print(f\"  Timestamp: {transfer.get('block_timestamp', 'N/A')}\")
                return data
        except Exception as e:
            print(f\"Error getting token transfers for {token_address}: {e}\")
            return None

    async def get_token_analytics(self, token_address, chain=\"bsc\"):
        \"\"\"Get comprehensive token analytics - based on documentation: /token/{address}/analytics\"\"\"
        url = f\"{BASE_URL}/token/{token_address}/analytics\"
        params = {\"chain\": chain}
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                print(f\"\\n--- Token Analytics for {token_address} ---\")
                print(f\"24h Volume: {data.get('volume24h', 'N/A')}\")
                print(f\"Market Cap: {data.get('marketCap', 'N/A')}\")
                print(f\"Price (USD): {data.get('price', 'N/A')}\")
                print(f\"Price Change 24h: {data.get('priceChange24h', 'N/A')}%\"\)
                print(f\"Total Supply: {data.get('totalSupply', 'N/A')}\")
                return data
        except Exception as e:
            print(f\"Error getting token analytics for {token_address}: {e}\")
            return None

    async def get_swaps_by_token(self, token_address, chain=\"bsc\", limit=25, order=\"DESC\"):
        \"\"\"Get swap transactions for a token - based on documentation: /token/{address}/swaps\"\"\"
        url = f\"{BASE_URL}/token/{token_address}/swaps\"
        params = {\"chain\": chain, \"limit\": limit, \"order\": order}
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                swaps = data.get('result', [])
                print(f\"\\n--- Recent Swaps for {token_address} ---\")
                for i, swap in enumerate(swaps[:5]):  # Show first 5 swaps
                    print(f\"Swap {i+1}:\")
                    print(f\"  Pair Address: {swap.get('pairAddress', 'N/A')}\")
                    print(f\"  Amount In: {swap.get('amountIn', 'N/A')}\")
                    print(f\"  Amount Out: {swap.get('amountOut', 'N/A')}\")
                    print(f\"  Transaction Hash: {swap.get('transactionHash', 'N/A')}\")
                    print(f\"  Block Number: {swap.get('blockNumber', 'N/A')}\")
                    print(f\"  Block Timestamp: {swap.get('blockTimestamp', 'N/A')}\")
                    print(f\"  From Address: {swap.get('fromAddress', 'N/A')}\")
                return data
        except Exception as e:
            print(f\"Error getting swaps for {token_address}: {e}\")
            return None

    async def get_historical_token_holders(self, token_address, chain=\"bsc\", 
                                         from_date=None, to_date=None, time_frame=\"10min\"):
        \"\"\"Get historical token holders - based on documentation: /token/{address}/historical-holder-counts\"\"\"
        if not from_date:
            from_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:00:00Z')  # Format: 2025-09-20T01:00:00Z
        if not to_date:
            to_date = datetime.utcnow().strftime('%Y-%m-%dT%H:00:00Z')  # Format: 2025-09-20T02:00:00Z
            
        # URL based on documentation: /token/{address}/historical-holder-counts
        url = f\"{BASE_URL}/token/{token_address}/historical-holder-counts\"
        params = {
            \"chain\": chain,
            \"fromDate\": from_date,
            \"toDate\": to_date,
            \"timeframe\": time_frame
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                print(f\"\\n--- Historical Holders for {token_address} ---\")
                if 'result' in data:
                    for i, record in enumerate(data['result'][:5]):  # Show first 5 records
                        print(f\"Date: {record.get('date', 'N/A')}, Holders: {record.get('holderCount', 'N/A')}\")
                return data
        except Exception as e:
            print(f\"Error getting historical holders for {token_address}: {e}\")
            return None

    async def get_top_profitable_wallet_per_token(self, token_address, chain=\"bsc\"):
        \"\"\"Get top profitable wallet for a token - based on documentation: /token/{address}/top-profitable-wallet\"\"\"
        url = f\"{BASE_URL}/token/{token_address}/top-profitable-wallet\"
        params = {\"chain\": chain}
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                print(f\"\\n--- Top Profitable Wallet for {token_address} ---\")
                if 'result' in data:
                    result = data['result']
                    print(f\"Wallet Address: {result.get('walletAddress', 'N/A')}\")
                    print(f\"Profit: {result.get('profit', 'N/A')}\")
                    print(f\"ROI: {result.get('roi', 'N/A')}%\"\)
                    print(f\"Trades Count: {result.get('tradesCount', 'N/A')}\")
                return data
        except Exception as e:
            print(f\"Error getting top profitable wallet for {token_address}: {e}\")
            return None

    async def get_token_pair_stats(self, pair_address, chain=\"bsc\"):
        \"\"\"Get token pair statistics - based on documentation: /defi/pair/{address}/stats\"\"\"
        url = f\"{BASE_URL}/defi/pair/{pair_address}/stats\"
        params = {\"chain\": chain}
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                print(f\"\\n--- Pair Stats for {pair_address} ---\")
                print(f\"Base Token: {data.get('baseToken', 'N/A')}\")
                print(f\"Quote Token: {data.get('quoteToken', 'N/A')}\")
                print(f\"24h Volume: {data.get('volume24h', 'N/A')}\")
                print(f\"Liquidity: {data.get('liquidity', 'N/A')}\")
                print(f\"Price: {data.get('price', 'N/A')}\")
                return data
        except Exception as e:
            print(f\"Error getting pair stats for {pair_address}: {e}\")
            return None

    async def get_snipers_by_pair_address(self, pair_address, chain=\"bsc\", blocks_after_creation=1000):
        \"\"\"Get snipers for a pair - based on documentation: /defi/snipers\"\"\"
        url = f\"{BASE_URL}/defi/snipers\"
        params = {
            \"chain\": chain,
            \"address\": pair_address,
            \"blocksAfterCreation\": blocks_after_creation
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                print(f\"\\n--- Snipers for {pair_address} ---\")
                if 'result' in data:
                    for i, sniper in enumerate(data['result'][:5]):  # Show first 5 snipers
                        print(f\"Sniper {i+1}: {sniper.get('walletAddress', 'N/A')}\")
                        print(f\"  Profit: {sniper.get('profit', 'N/A')}\")
                        print(f\"  Trade Count: {sniper.get('tradeCount', 'N/A')}\")
                return data
        except Exception as e:
            print(f\"Error getting snipers for {pair_address}: {e}\")
            return None

    async def run_full_analysis(self):
        \"\"\"Run comprehensive analysis for BTCB and USDT tokens and their pair\"\"\"
        print(f\"Starting comprehensive analysis for BTCB and USDT tokens and pair {PAIR_ADDRESS}\")
        print(f\"BTCB Address: {BTCB_ADDRESS}\")
        print(f\"USDT Address: {USDT_ADDRESS}\")
        print(\"=\" * 80)

        # Analyze BTCB token
        print(\"\\nAnalyzing BTCB token...\")
        await self.get_token_stats(BTCB_ADDRESS, \"bsc\")
        await self.get_token_holder_stats(BTCB_ADDRESS, \"bsc\")
        await self.get_token_transfers(BTCB_ADDRESS, \"bsc\")
        await self.get_swaps_by_token(BTCB_ADDRESS, \"bsc\")
        await self.get_historical_token_holders(BTCB_ADDRESS, \"bsc\")
        await self.get_top_profitable_wallet_per_token(BTCB_ADDRESS, \"bsc\")

        # Analyze USDT token
        print(\"\\nAnalyzing USDT token...\")
        await self.get_token_stats(USDT_ADDRESS, \"bsc\")
        await self.get_token_holder_stats(USDT_ADDRESS, \"bsc\")
        await self.get_token_transfers(USDT_ADDRESS, \"bsc\")
        await self.get_swaps_by_token(USDT_ADDRESS, \"bsc\")
        await self.get_historical_token_holders(USDT_ADDRESS, \"bsc\")
        await self.get_top_profitable_wallet_per_token(USDT_ADDRESS, \"bsc\")

        # Note: The pair address provided (0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4) 
        # is for PancakeSwap V2 and may not be directly supported by Moralis API for pair stats
        print(\"\\nAnalyzing token pair...\")
        await self.get_snipers_by_pair_address(PAIR_ADDRESS, \"bsc\")

        print(\"\\nAnalysis complete!\")


async def main():
    analytics = MoralisTokenAnalytics()
    try:
        await analytics.initialize()
        await analytics.run_full_analysis()
    finally:
        await analytics.cleanup()


if __name__ == \"__main__\":
    asyncio.run(main())