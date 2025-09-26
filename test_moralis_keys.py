"""Test Moralis API keys to verify they're working"""

import asyncio
import aiohttp
from moralis_config import MORALIS_API_KEYS

MORALIS_API_URL = "https://deep-index.moralis.io/api/v2.2"

# Test pair address (BTCB/USDT on BSC)
TEST_PAIR = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

async def test_api_key(key_info, session):
    """Test a single API key"""
    headers = {"X-API-Key": key_info["key"]}
    
    # Test endpoint: getPairStats
    url = f"{MORALIS_API_URL}/pairs/{TEST_PAIR}/stats"
    params = {"chain": "bsc"}
    
    try:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "name": key_info["name"],
                    "status": "OK",
                    "pair_address": data.get("pairAddress", "N/A"),
                    "liquidity_usd": data.get("liquidityUsd", 0)
                }
            elif response.status == 429:
                return {
                    "name": key_info["name"],
                    "status": "RATE_LIMITED",
                    "error": "Rate limit exceeded"
                }
            else:
                error_text = await response.text()
                return {
                    "name": key_info["name"],
                    "status": "ERROR",
                    "error": f"Status {response.status}: {error_text[:100]}"
                }
    except Exception as e:
        return {
            "name": key_info["name"],
            "status": "ERROR",
            "error": str(e)
        }

async def test_all_keys():
    """Test all configured Moralis API keys"""
    print("Testing Moralis API Keys")
    print("=" * 60)
    print(f"Total keys configured: {len(MORALIS_API_KEYS)}")
    print(f"Test endpoint: getPairStats for {TEST_PAIR}")
    print()
    
    async with aiohttp.ClientSession() as session:
        tasks = [test_api_key(key_info, session) for key_info in MORALIS_API_KEYS]
        results = await asyncio.gather(*tasks)
        
        # Display results
        working_keys = 0
        rate_limited = 0
        failed_keys = 0
        
        for result in results:
            print(f"{result['name']}:")
            print(f"  Status: {result['status']}")
            
            if result['status'] == 'OK':
                working_keys += 1
                print(f"  Pair: {result['pair_address']}")
                print(f"  Liquidity: ${result['liquidity_usd']:,.2f}")
            elif result['status'] == 'RATE_LIMITED':
                rate_limited += 1
                print(f"  Error: {result['error']}")
            else:
                failed_keys += 1
                print(f"  Error: {result['error']}")
            print()
        
        # Summary
        print("=" * 60)
        print("Summary:")
        print(f"  Working keys: {working_keys}/{len(MORALIS_API_KEYS)}")
        print(f"  Rate limited: {rate_limited}/{len(MORALIS_API_KEYS)}")
        print(f"  Failed keys: {failed_keys}/{len(MORALIS_API_KEYS)}")
        
        if working_keys == len(MORALIS_API_KEYS):
            print("\n[SUCCESS] All API keys are working!")
            print("Total daily capacity: 160,000 CU (40K per key)")
        elif working_keys > 0:
            print(f"\n[PARTIAL] {working_keys} keys working")
            print(f"Available daily capacity: {working_keys * 40000:,} CU")
        else:
            print("\n[ERROR] No working API keys found")

if __name__ == "__main__":
    asyncio.run(test_all_keys())