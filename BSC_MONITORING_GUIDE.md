# BSC USDT/BTCB Pool Monitoring System

## Overview
Complete monitoring solution for the PancakeSwap USDT/BTCB 0.05% pool on BSC.

**Pool Details:**
- Pool Address: `0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4`
- BTCB Contract: `0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c`
- USDT Contract: `0x55d398326f99059fF775485246999027B3197955`
- DEX: PancakeSwap V2
- Fee Tier: 0.05%

## Metrics Categories

### Category 1: Liquidity & Capital Metrics
Monitor market maker capital commitment and liquidity health.

#### 1. Total Value Locked (TVL)
- **What it shows**: Total USD value of assets in the pool
- **Why it matters**: Main indicator of liquidity depth
- **Red flags**:
  - Sudden drops without major trades
  - TVL below promised amounts
  - Consistent decline over time

#### 2. LP Token Tracking
- **What it shows**: Market maker's LP token balance
- **Why it matters**: Shows if MM is removing liquidity
- **Red flags**:
  - Regular LP token transfers to other addresses
  - Declining LP token balance
  - Conversion back to base tokens

#### 3. Pool Composition
- **What it shows**: Ratio of BTCB vs USDT value
- **Ideal state**: 50/50 balance
- **Red flags**:
  - Ratio beyond 40/60 or 60/40
  - Inability to rebalance after large trades
  - Persistent imbalance

### Category 2: Market Activity Metrics
Track trading patterns and market health.

#### 1. Trading Volume Analysis
- **Total Volume**: Can be artificially inflated
- **Unique Wallet Volume**: More reliable metric
- **Volume/Unique Traders Ratio**: Identifies wash trading

#### 2. Unique Address Tracking
- **New Holders (24h)**: Growth indicator
- **Active Traders**: Market participation
- **Holder Growth Rate**: Project momentum

#### 3. Transaction Patterns
- **Trade Count**: Overall activity
- **Average Trade Size**: Retail vs whale activity
- **Trade Frequency**: Market liquidity

### Category 3: Market Health & Manipulation Detection

#### 1. Slippage Monitoring
- **What it shows**: Price impact of trades
- **Calculation**: Actual price vs expected price
- **Thresholds**:
  - Good: <0.5% for $500 trades
  - Acceptable: 0.5-1%
  - Poor: >2%

#### 2. Wash Trading Detection
System automatically detects:
- Same wallet buying/selling repeatedly
- Circular trading between related wallets
- Identical trade amounts with minimal time gaps
- High volume with low unique traders

**Detection Signals**:
- Trade frequency > 2 per minute from same wallet
- Volume/unique trader ratio > $10,000
- Circular patterns between 2-3 wallets
- Standard deviation of trade sizes < 10% of average

#### 3. PnL Tracking
Identifies potential insiders by tracking:
- Wallets with consistent profits
- Trading before major announcements
- Abnormal win rates (>70%)
- Large positions before price movements

### Category 4: Distribution Metrics

#### 1. Gini Coefficient
- **Range**: 0 (perfect equality) to 1 (maximum inequality)
- **Good**: < 0.6
- **Concerning**: 0.6-0.8
- **Critical**: > 0.8

#### 2. Concentration Analysis
- **Top 10 Holders**: Should be < 50%
- **Top 50 Holders**: Should be < 75%
- **Top 100 Holders**: Should be < 90%

#### 3. Whale Monitoring
- **Definition**: Wallets holding > 1% of supply
- **Tracking**: Movement patterns, accumulation/distribution
- **Alerts**: Large transfers, new whale addresses

## Dashboard Panels Explained

### Main KPIs (Top Row)
1. **TVL**: Current total value locked
2. **Pool Balance**: BTCB/USDT ratio (ideal: 50%)
3. **Price**: Current BTCB/USDT exchange rate
4. **Gini Coefficient**: Distribution inequality metric

### Trend Charts
1. **TVL & Liquidity Trend**: Historical liquidity changes
2. **Trading Volume & Unique Traders**: Activity metrics over time
3. **Buy vs Sell Pressure**: Market sentiment indicator
4. **Trading Activity Heatmap**: Trade size distribution

### Analytics Tables
1. **Top Traders by PnL**: Identifies successful traders (potential insiders)
2. **Wash Trading Suspects**: Wallets with suspicious patterns
3. **Token Concentration**: Distribution breakdown

### Health Indicators
1. **Pool Health Score**: Composite metric (0-100)
2. **Average Slippage**: Liquidity quality indicator
3. **New Holders**: Growth metric

## Alert Conditions

The system automatically generates alerts for:

### Critical Alerts
- TVL drops > 20% in 1 hour
- Gini coefficient > 0.9
- Pool ratio beyond 35/65
- Wash trading detection with >80% confidence

### Warning Alerts
- TVL drops > 10% in 1 hour
- New whale wallets (>1% of supply)
- Slippage > 2% for small trades
- Suspicious PnL patterns detected

### Info Alerts
- New LP providers
- Large trades (>$100,000)
- New trading patterns detected

## Running the Monitor

### Start BSC Monitor Only
```bash
cd C:\Users\ramaz\dex-onchain-analytics
docker-compose -f docker-compose-bsc.yml up -d
```

### View Logs
```bash
docker logs -f bsc_pool_monitor
```

### Import Dashboard
1. Open Grafana (http://localhost:3000)
2. Import `grafana/bsc-pool-dashboard.json`
3. Select PostgreSQL data source
4. View real-time metrics

## API Rate Limits
- BscScan API: 5 calls/second
- Daily limit: 100,000 calls
- Monitor cycle: 60 seconds

## Database Tables

### Core Tables
- `bsc_pool_metrics`: Pool reserves and TVL
- `bsc_trades`: All swap transactions
- `bsc_wallet_metrics`: Wallet-level analytics
- `wash_trade_suspects`: Detected wash traders
- `bsc_liquidity_events`: LP add/remove events
- `manipulation_alerts`: System-generated alerts
- `token_distribution`: Distribution metrics

## Troubleshooting

### No Data Showing
1. Check monitor is running: `docker ps | grep bsc`
2. Verify API key: Check ETHERSCAN_API_KEY in .env
3. Check logs: `docker logs bsc_pool_monitor`

### Incorrect Prices
- Verify BTCB price feed
- Check decimal handling (BTCB: 18, USDT: 18)
- Validate contract addresses

### High Slippage Readings
- Normal for low liquidity periods
- Check pool TVL
- Verify calculation methodology

## Customization

### Adjust Alert Thresholds
Edit `bsc_pool_monitor.py`:
- Wash trading confidence: Line 450
- Slippage thresholds: Line 320
- Gini coefficient limits: Line 580

### Add New Metrics
1. Add database table/column
2. Implement collection in monitor
3. Add panel to Grafana dashboard

## Best Practices

1. **Regular Monitoring**
   - Check dashboard at least 3x daily
   - Set up alerts for critical metrics
   - Document unusual patterns

2. **Data Validation**
   - Cross-reference with BscScan
   - Verify large trades manually
   - Compare with other DEX aggregators

3. **Response Actions**
   - Document all anomalies
   - Screenshot evidence
   - Report wash trading to community

## Contact & Support
For issues or improvements, modify the monitoring scripts in:
- Main monitor: `bsc_pool_monitor.py`
- Dashboard: `grafana/bsc-pool-dashboard.json`
- Database schema: `bsc_pool_monitor.py` (create_tables method)