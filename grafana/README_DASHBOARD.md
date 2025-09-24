# Grafana Dashboard Setup Instructions

## Dashboard Files

1. **moralis-corrected-dashboard.json** - Fixed version with correct table names
2. **moralis-enhanced-dashboard.json** - Original with incorrect table names (deprecated)

## How to Import the Dashboard

1. Open Grafana (usually at http://localhost:3000)
2. Click on "Dashboards" in the left menu
3. Click "New" → "Import"
4. Upload the `moralis-corrected-dashboard.json` file
5. Select your PostgreSQL datasource
6. Click "Import"

## Database Tables Being Used

The dashboard queries the following tables:
- `moralis_swaps_correct` - Swap transactions (81+ records)
- `moralis_token_analytics_correct` - Token analytics (updating every minute)
- `moralis_historical_holders_correct` - Historical holder data (31 days)
- `moralis_pair_stats_correct` - Pair statistics
- `moralis_holder_stats_correct` - Holder distribution
- `moralis_snipers_correct` - Sniper detection
- `moralis_top_gainers` - Top profitable traders

## Dashboard Panels

### Token Holder Statistics
- Total Holders
- Top 10 Concentration
- Whales Count
- 24h Holder Change
- Holders via Swaps
- Shrimps Count

### Pair Statistics & Liquidity
- Current Price (USD)
- Total Liquidity
- 24h Price Change
- 24h Volume

### Historical Analysis
- Historical Holder Trends (7-day chart)
- Holder Distribution Categories (pie chart)

### Trading Activity
- Buy vs Sell Volume (24h bar chart)
- Recent Labeled Entity Swaps (table)

### Token Analytics
- 24h Buy Volume
- 24h Sell Volume
- 24h Unique Buyers
- 24h Unique Sellers
- Buyer/Seller Activity Trends (time series)
- Top Profitable Traders (table)

## Data Update Frequency

- Dashboard auto-refreshes every 30 seconds
- Data is collected from Moralis API every 60 seconds
- Monitor script: `moralis_final_monitor.py`

## Running the Monitor

```bash
# Start the data collection
python moralis_final_monitor.py

# Check if data is being collected
docker exec dex_postgres psql -U postgres -d dex_analytics -c "SELECT COUNT(*) FROM moralis_swaps_correct"
```

## Troubleshooting

### No Data Showing
1. Check if monitor is running: `ps aux | grep moralis_final_monitor`
2. Check database connection: PostgreSQL on port 5433
3. Verify tables exist: Run the SQL check above

### Missing Panels
Some panels may show "No data" because:
- `moralis_holder_stats_correct` - Needs column mapping fix
- `moralis_pair_stats_correct` - Needs column mapping fix
- `moralis_top_gainers` - Calculated from swaps, may be empty initially

## API Endpoints Status

✅ Working:
- Swaps
- Transfers
- Token Analytics
- Historical Holders
- Pair Stats
- Holder Stats
- Snipers

⚠️ With Workarounds:
- Top Gainers (calculated from swaps)
- Token Stats (using analytics as fallback)

## Database Connection

```
Host: localhost
Port: 5433
Database: dex_analytics
User: postgres
Password: postgres
```

## Notes

- BTCB/USDT pair on BSC chain
- Pool Address: 0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4
- Token Address: 0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c