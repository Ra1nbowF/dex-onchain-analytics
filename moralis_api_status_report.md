# Moralis API Endpoints Status Report

## Summary of Testing Results

### Working Endpoints (7 out of 9)

1. ✅ **SWAPS** (`/erc20/{address}/swaps`)
   - Status: WORKING
   - Returns: Swap transactions with buy/sell details

2. ✅ **TRANSFERS** (`/erc20/{address}/transfers`)
   - Status: WORKING
   - Returns: Token transfer transactions

3. ❌ **TOP-GAINERS** (`/erc20/{address}/top-gainers`)
   - Status: PARTIALLY WORKING
   - Issue: Not supported on BSC chain, only works on ETH and Polygon
   - Solution: Skip for BSC monitoring or use mock data

4. ✅ **PAIR-STATS** (`/pairs/{address}/stats`)
   - Status: WORKING
   - Returns: Comprehensive pair statistics

5. ✅ **TOKEN-ANALYTICS** (`/tokens/{address}/analytics`)
   - Status: WORKING
   - Returns: Detailed trading analytics with volumes and counts

6. ❌ **TOKEN-STATS** (`/erc20/{address}/stats`)
   - Status: NOT WORKING
   - Issue: Server error (500) on all chains and tokens
   - Solution: Use TOKEN-ANALYTICS as alternative

7. ✅ **HOLDER-STATS** (`/erc20/{address}/holders`)
   - Status: WORKING
   - Returns: Holder statistics and distribution

8. ✅ **HISTORICAL-HOLDERS** (`/erc20/{address}/holders/historical`)
   - Status: WORKING
   - Returns: Time-series holder data

9. ✅ **SNIPERS** (`/pairs/{address}/snipers`)
   - Status: WORKING (but returns 0 results for our pool)
   - Returns: Sniper wallet information

### Additional Working Endpoints (Not in required list)

- ✅ **PRICE** (`/erc20/{address}/price`)
- ✅ **OWNERS** (`/erc20/{address}/owners`)
- ✅ **METADATA** (`/erc20/metadata`)

## Recommendations

1. **For BSC Monitoring:**
   - Use 7 working endpoints
   - Skip TOP-GAINERS (not supported on BSC)
   - Skip TOKEN-STATS (server error)
   - Use TOKEN-ANALYTICS for comprehensive stats

2. **Data Coverage:**
   - We can get 80% of required data from working endpoints
   - TOKEN-ANALYTICS provides most of the data that TOKEN-STATS would have
   - For TOP-GAINERS on BSC, consider calculating from swap data

3. **Database Schema:**
   - Already created tables for all working endpoints
   - Schema matches actual API responses
   - Ready for data ingestion

## Next Steps

1. Implement monitor with 7 working endpoints
2. Add error handling for failed endpoints
3. Consider implementing calculated metrics for missing data
4. Monitor API status for when TOKEN-STATS is fixed