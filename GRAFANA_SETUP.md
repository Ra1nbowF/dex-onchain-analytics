# Adding DEX Analytics Dashboard to Grafana

## Step 1: Access Grafana
Open your browser and go to: http://localhost:3000

Default credentials (if needed):
- Username: admin
- Password: admin

## Step 2: Add PostgreSQL Data Source

1. Go to **Configuration** → **Data Sources** (or click the gear icon)
2. Click **"Add data source"**
3. Select **PostgreSQL**
4. Configure the connection:
   - **Name**: DEX Analytics
   - **Host**: host.docker.internal:5433
   - **Database**: dex_analytics
   - **User**: postgres
   - **Password**: postgres
   - **SSL Mode**: disable
   - **Version**: 15.x
5. Click **"Save & Test"** to verify the connection

## Step 3: Import Dashboard

1. Go to **Dashboards** → **Import** (or click the + icon)
2. Click **"Upload JSON file"**
3. Select: `C:\Users\ramaz\dex-onchain-analytics\grafana\dex-analytics-dashboard.json`
4. Select the **DEX Analytics** data source you just created
5. Click **"Import"**

## Dashboard Features

The dashboard includes:
- **Total Volume (24h)** - Total trading volume in USD
- **Total Trades (24h)** - Number of trades executed
- **Unique Traders (24h)** - Number of unique wallet addresses
- **Average Trade Size** - Average trade value in USD
- **Trading Volume by DEX** - Time series chart of volume per DEX
- **Token Prices** - Real-time token price tracking
- **Volume by Chain** - Pie chart showing volume distribution
- **Volume by DEX** - Pie chart showing DEX market share
- **Top Trading Pairs** - Bar gauge of most traded pairs
- **Recent Large Trades** - Table of significant trades
- **Trading Activity Heatmap** - Visual representation of activity
- **Gas Usage Trend** - Gas costs over time

## Data Updates

The collector generates new data every 0.5-2 seconds, simulating real trading activity across:
- 6 blockchain networks (Ethereum, BSC, Polygon, Arbitrum, Optimism, Base)
- 6 DEX protocols (Uniswap V3, V2, SushiSwap, PancakeSwap, Curve, Balancer)
- 12 trading pairs (ETH/USDT, BTC/USDT, etc.)

## Viewing Live Data

After importing the dashboard:
1. Set the time range to "Last 3 hours"
2. Set refresh interval to "5s" (top right corner)
3. Watch the live data flow in!

## Troubleshooting

If you don't see data:
1. Check the collector is running: `docker ps`
2. View collector logs: `docker-compose logs -f dex_collector`
3. Verify database connection in Grafana data source settings
4. Wait 1-2 minutes for initial data to accumulate

## Stopping the System

To stop all containers:
```bash
cd C:\Users\ramaz\dex-onchain-analytics
docker-compose down
```

To stop but keep data:
```bash
docker-compose stop
```

To restart:
```bash
docker-compose start
```