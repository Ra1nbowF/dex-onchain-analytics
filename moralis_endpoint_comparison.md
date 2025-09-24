# Moralis API Endpoint Comparison Report

## Required Endpoints (from user's list)

1. **get-swaps-by-token-address**
   - API Path: `/erc20/{address}/swaps`
   - Description: Get swap transactions (buy/sell) for a specific ERC20 token
   - Current Implementation: ❌ NOT IMPLEMENTED (using transfers instead)

2. **get-token-transfers**
   - API Path: `/erc20/{address}/transfers`
   - Description: Get ERC20 token transfers by contract address
   - Current Implementation: ✅ IMPLEMENTED (fetch_token_transfers)

3. **get-top-profitable-wallet-per-token**
   - API Path: `/erc20/{address}/top-gainers`
   - Description: List the most profitable wallets that have traded a specific ERC20 token
   - Current Implementation: ❌ NOT IMPLEMENTED (using mock data)

4. **get-token-pair-stats**
   - API Path: `/pairs/{address}/stats`
   - Description: Access key statistics for a token pair (price, buyers, sellers, liquidity, volume)
   - Current Implementation: ❌ NOT IMPLEMENTED

5. **get-token-analytics**
   - API Path: `/tokens/{tokenAddress}/analytics`
   - Description: Retrieve detailed trading analytics (buy/sell volume, buyers, sellers, transactions, liquidity, FDV trends)
   - Current Implementation: ❌ NOT IMPLEMENTED

6. **get-token-stats**
   - API Path: `/erc20/{address}/stats`
   - Description: Get the total number of transfers for a given ERC20
   - Current Implementation: ❌ NOT IMPLEMENTED

7. **get-token-holder-stats**
   - API Path: `/erc20/{tokenAddress}/holders`
   - Description: Returns total holders, holder supply, holder trends, distribution and acquisition metrics
   - Current Implementation: ❌ NOT IMPLEMENTED (using /owners endpoint instead)

8. **get-historical-token-holders**
   - API Path: `/erc20/{tokenAddress}/holders/historical`
   - Description: Track changes in holder base over time with timeseries data
   - Current Implementation: ❌ NOT IMPLEMENTED (creating mock data)

9. **get-snipers-by-pair-address**
   - API Path: `/pairs/{address}/snipers`
   - Description: Identify sniper wallets that bought within specified timeframe after creation
   - Current Implementation: ❌ NOT IMPLEMENTED (using mock data)

## Currently Implemented Endpoints

1. `/erc20/{address}/transfers` - ✅ Correctly used
2. `/erc20/{address}/price` - ✅ Working but not in required list
3. `/erc20/{address}/owners` - ✅ Working but should use `/holders` endpoint
4. `/erc20/metadata` - ✅ Working but not in required list

## Key Issues Found

1. **Wrong endpoints**: Using `/owners` instead of `/holders` for holder stats
2. **Missing endpoints**: 7 out of 9 required endpoints are not implemented
3. **Mock data**: Creating fake data instead of calling real APIs
4. **API Response Structure**: Need to verify actual response structure matches our database schema

## Next Steps

1. Implement all 9 required Moralis API endpoints correctly
2. Update database schema to match actual API responses
3. Remove mock data generation
4. Test each endpoint with real API calls
5. Update Grafana dashboard to use correct data fields