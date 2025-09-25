# DEX On-Chain Analytics Platform - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Infrastructure Components](#infrastructure-components)
4. [Core Services](#core-services)
5. [Database Schema](#database-schema)
6. [Data Collection Pipeline](#data-collection-pipeline)
7. [Visualization Layer](#visualization-layer)
8. [Deployment & Operations](#deployment--operations)
9. [API Integration](#api-integration)
10. [Monitoring & Alerts](#monitoring--alerts)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Performance Optimization](#performance-optimization)

---

## Project Overview

### Purpose
A comprehensive blockchain analytics platform that monitors, analyzes, and visualizes DEX (Decentralized Exchange) trading activity on Binance Smart Chain (BSC), with a primary focus on the BTCB/USDT trading pair on PancakeSwap V2.

### Key Features
- **Real-time monitoring** of pool metrics and trading activity
- **Historical data analysis** with trend detection
- **Holder analytics** including whale tracking and distribution analysis
- **Volume analysis** with buy/sell pressure indicators
- **Profit/loss tracking** for top traders
- **Market manipulation detection** including wash trading alerts
- **Automated data collection** with fault tolerance
- **Interactive Grafana dashboards** for data visualization

### Technology Stack
- **Backend**: Python 3.10+ with asyncio/aiohttp
- **Database**: PostgreSQL 17.6
- **Visualization**: Grafana 8.0+
- **Container**: Docker & Docker Compose
- **Cloud Platform**: Railway
- **Blockchain Data**: Moralis Web3 API, BSC RPC
- **Version Control**: Git/GitHub
- **CI/CD**: Railway automatic deployments

---

## Architecture

### System Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     External Data Sources                    │
├──────────────────────┬────────────────┬────────────────────┤
│   Moralis Web3 API   │   BSC RPC Node │   BSCScan API      │
└──────────┬───────────┴────────┬───────┴──────────┬─────────┘
           │                    │                   │
    ┌──────▼──────┐      ┌──────▼──────┐    ┌──────▼──────┐
    │   main.py   │      │ bsc_pool_   │    │  External   │
    │  (Moralis   │      │ monitor.py  │    │  API Calls  │
    │  Monitor)   │      │             │    │             │
    └──────┬──────┘      └──────┬──────┘    └──────┬──────┘
           │                    │                   │
    ┌──────▼────────────────────▼───────────────────▼──────┐
    │              collector.py (Orchestrator)              │
    │         - Thread management                           │
    │         - Health checks                               │
    │         - Auto-restart logic                          │
    └───────────────────────┬──────────────────────────────┘
                            │
    ┌───────────────────────▼──────────────────────────────┐
    │           PostgreSQL Database (Railway Cloud)         │
    │         - 44 tables                                   │
    │         - Time-series data                           │
    │         - Analytics aggregations                      │
    └───────────────────────┬──────────────────────────────┘
                            │
    ┌───────────────────────▼──────────────────────────────┐
    │                 Grafana Dashboards                    │
    │         - Real-time metrics                          │
    │         - Historical trends                          │
    │         - Custom SQL queries                         │
    └───────────────────────────────────────────────────────┘
```

### Data Flow Patterns
1. **Synchronous Collection**: Monitors fetch data from APIs
2. **Asynchronous Processing**: Data processed in parallel threads
3. **Batch Insertion**: Optimized database writes
4. **Real-time Updates**: 60-second intervals for BSC, 10-minute for Moralis

---

## Infrastructure Components

### 1. Database Infrastructure

#### Local Development Database
- **Type**: PostgreSQL 15 Alpine (Docker)
- **Port**: 5433
- **Credentials**: postgres/postgres
- **Database Name**: dex_analytics
- **Purpose**: Development and testing

#### Production Database (Railway)
- **Type**: PostgreSQL 17.6
- **Host**: metro.proxy.rlwy.net
- **Port**: 54031
- **Database**: railway
- **Features**:
  - Automatic backups
  - Point-in-time recovery
  - SSL encryption
  - Connection pooling

#### Database Statistics
- **Total Tables**: 44
- **Total Sequences**: 43
- **Constraints**: 65
- **Indexes**: 30+
- **Data Volume**: ~500MB and growing
- **Average Row Count**: 1.5M+ across all tables

### 2. Container Infrastructure

#### Docker Services
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    ports: 5433:5432
    volumes: postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports: 6380:6379

  grafana:
    image: grafana/grafana:latest
    ports: 3000:3000
    volumes: ./grafana:/etc/grafana/provisioning

  bsc_pool_monitor:
    build: .
    environment:
      DATABASE_URL: ${DATABASE_URL}

  moralis_btcb_monitor:
    build: .
    environment:
      DATABASE_URL: ${DATABASE_URL}
      MORALIS_API_KEY: ${MORALIS_API_KEY}
```

### 3. Cloud Infrastructure (Railway)

#### Deployment Configuration
- **Build System**: Nixpacks
- **Start Command**: `python collector.py`
- **Restart Policy**: ON_FAILURE with max 10 retries
- **Environment Variables**:
  - DATABASE_URL (auto-injected)
  - MONITOR_INTERVAL_MINUTES: 10
  - MORALIS_API_KEY: (backup key active)

#### Resource Limits
- **Memory**: 512MB
- **CPU**: Shared
- **Disk**: Ephemeral
- **Network**: Public IPv4
- **Logs**: 500 logs/sec limit

---

## Core Services

### 1. Moralis Monitor (`main.py`)

#### Configuration
```python
DATABASE_URL = os.getenv("DATABASE_URL")
MORALIS_API_KEY = "eyJhbGci..." # Backup key
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"
MONITOR_INTERVAL_MINUTES = 10  # For 40K CU/day limit

# Target addresses
BTCB_ADDRESS = "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
```

#### API Endpoints Monitored
1. **Token Swaps** (`/erc20/{address}/swaps`)
   - Fetches recent swap transactions
   - Includes buy/sell classification
   - USD values and token amounts

2. **Token Transfers** (`/erc20/{address}/transfers`)
   - All token movements
   - From/to addresses
   - Transaction metadata

3. **Top Gainers** (Calculated from swaps)
   - Profit/loss analysis
   - Trading frequency
   - Success rate metrics

4. **Pair Statistics** (`/pairs/{pair}/stats`)
   - Current price (USD and native)
   - Liquidity metrics
   - 24h volume and changes

5. **Token Analytics** (`/erc20/{address}/analytics`)
   - Buy/sell volumes by timeframe
   - Buyer/seller counts
   - Trade distribution

6. **Holder Statistics** (`/erc20/{address}/holders`)
   - Total holder count
   - Distribution by size
   - Acquisition methods

7. **Historical Holders** (`/erc20/{address}/holders/historical`)
   - 30-day holder trends
   - Net changes
   - Growth patterns

8. **Top Holders** (Calculated from swaps)
   - Top 100 by balance
   - Percentage of supply
   - Holder classification

9. **Snipers Detection** (`/pairs/{pair}/snipers`)
   - Early buyers identification
   - Sniper wallet tracking
   - Entry timing analysis

#### Data Processing Logic
```python
class MoralisFinalMonitor:
    async def monitor_cycle(self):
        # Fetch data from all endpoints
        swaps = await self.fetch_token_swaps(200)
        transfers = await self.fetch_transfers(100)
        top_gainers = await self.fetch_top_gainers(7)
        pair_stats = await self.fetch_pair_stats()
        token_analytics = await self.fetch_token_analytics()
        holder_stats = await self.fetch_holder_stats()
        historical_holders = await self.fetch_historical_holders()
        top_holders = await self.fetch_top_holders(100)
        snipers = await self.fetch_snipers(3)

        # Store in database
        await self.store_swaps(swaps)
        await self.store_transfers(transfers)
        await self.store_top_gainers(top_gainers)
        await self.store_pair_stats(pair_stats)
        await self.store_token_analytics(token_analytics)
        await self.store_holder_stats(holder_stats)
        await self.store_historical_holders(historical_holders)
        await self.store_holders(top_holders)
        await self.store_snipers(snipers)
```

### 2. BSC Pool Monitor (`bsc_pool_monitor.py`)

#### Configuration
```python
BSC_RPC = "https://bsc-dataseed1.binance.org/"
BSCSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Contract addresses
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BTCB_ADDRESS = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"
PANCAKE_FACTORY = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
```

#### Monitoring Features
1. **Pool Reserves Tracking**
   ```python
   async def fetch_pool_reserves(self):
       # Direct RPC call to get reserves
       reserves = await self.contract.functions.getReserves().call()
       return {
           "btcb_reserve": reserves[0] / 10**18,
           "usdt_reserve": reserves[1] / 10**18,
           "tvl": calculate_tvl(reserves),
           "price": reserves[1] / reserves[0]
       }
   ```

2. **Trade Monitoring**
   - Swap events from contract logs
   - Trade direction detection
   - Slippage calculation
   - MEV detection

3. **Liquidity Events**
   - Add/Remove liquidity tracking
   - LP token calculations
   - Provider analysis

4. **Market Analysis**
   - Wash trading detection
   - Price manipulation alerts
   - Unusual volume detection

### 3. Collector Service (`collector.py`)

#### Thread Management
```python
def main():
    # Start monitors in separate threads
    bsc_thread = threading.Thread(target=run_bsc_monitor, daemon=True)
    moralis_thread = threading.Thread(target=run_moralis_monitor, daemon=True)

    bsc_thread.start()
    moralis_thread.start()

    # Health check loop
    while True:
        time.sleep(60)
        health_check_counter += 1

        if health_check_counter % 5 == 0:
            # Check and restart dead threads
            if not bsc_thread.is_alive():
                bsc_thread = threading.Thread(target=run_bsc_monitor, daemon=True)
                bsc_thread.start()
```

---

## Database Schema

### Core Analytics Tables

#### 1. moralis_swaps_correct
```sql
CREATE TABLE moralis_swaps_correct (
    transaction_hash VARCHAR(66) PRIMARY KEY,
    transaction_index INTEGER,
    transaction_type VARCHAR(10), -- 'buy' or 'sell'
    block_timestamp TIMESTAMP,
    block_number BIGINT,
    wallet_address VARCHAR(66),
    wallet_address_label TEXT,
    bought_amount DECIMAL(30, 18),
    bought_usd_amount DECIMAL(20, 2),
    sold_amount DECIMAL(30, 18),
    sold_usd_amount DECIMAL(20, 2),
    total_value_usd DECIMAL(20, 2), -- For Grafana compatibility
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### 2. moralis_holder_stats_correct
```sql
CREATE TABLE moralis_holder_stats_correct (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(66),
    total_holders INTEGER,
    top10_supply_percent DECIMAL(10, 2),
    top25_supply_percent DECIMAL(10, 2),
    top50_supply_percent DECIMAL(10, 2),
    holder_change_24h INTEGER,
    holder_change_percent_24h DECIMAL(10, 2),
    holders_by_swap INTEGER,
    holders_by_transfer INTEGER,
    holders_by_airdrop INTEGER,
    whales INTEGER,      -- >1% supply
    sharks INTEGER,      -- 0.5-1%
    dolphins INTEGER,    -- 0.1-0.5%
    fish INTEGER,        -- 0.01-0.1%
    shrimps INTEGER,     -- <0.01%
    timestamp TIMESTAMP DEFAULT NOW(),
    UNIQUE(token_address, timestamp)
);
```

#### 3. bsc_pool_metrics
```sql
CREATE TABLE bsc_pool_metrics (
    id SERIAL PRIMARY KEY,
    pool_address VARCHAR(66),
    token0_reserve DECIMAL(30, 18),
    token1_reserve DECIMAL(30, 18),
    total_liquidity_usd DECIMAL(20, 2),
    tvl DECIMAL(20, 2),
    price_btcb_usdt DECIMAL(20, 8),
    pool_ratio DECIMAL(10, 6),
    lp_token_supply DECIMAL(30, 18),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### 4. moralis_holders
```sql
CREATE TABLE moralis_holders (
    id SERIAL PRIMARY KEY,
    holder_address VARCHAR(66),
    balance DECIMAL(30, 18),
    balance_formatted DECIMAL(30, 18),
    percentage_of_supply DECIMAL(10, 6),
    holder_type VARCHAR(20), -- 'Whale', 'Shark', etc.
    total_trades INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### 5. moralis_top_gainers
```sql
CREATE TABLE moralis_top_gainers (
    wallet_address VARCHAR(66) PRIMARY KEY,
    avg_buy_price_usd DECIMAL(20, 8),
    avg_sell_price_usd DECIMAL(20, 8),
    total_tokens_bought DECIMAL(30, 18),
    total_tokens_sold DECIMAL(30, 18),
    total_usd_invested DECIMAL(20, 2),
    total_sold_usd DECIMAL(20, 2),
    realized_profit_usd DECIMAL(20, 2),
    realized_profit_percentage DECIMAL(10, 2),
    count_of_trades INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### Complete Table List
```
Analytics Tables (15):
- dex_trades
- liquidity_pools
- token_prices
- chain_stats
- wallet_activity
- wallet_pnl
- token_metrics
- pool_metrics
- volume_metrics
- price_history
- market_depth
- arbitrage_opportunities
- impermanent_loss
- gas_analytics
- mev_transactions

Moralis Tables (20):
- moralis_swaps_correct
- moralis_transfers
- moralis_liquidity_correct
- moralis_price_history_correct
- moralis_pair_stats_correct
- moralis_volume_metrics_correct
- moralis_whale_activity_correct
- moralis_arbitrage_correct
- moralis_holder_stats_correct
- moralis_historical_holders_correct
- moralis_holders
- moralis_top_gainers
- moralis_snipers_correct
- moralis_token_analytics_correct
- moralis_token_stats
- moralis_metrics_summary
- moralis_pair_stats_enhanced
- moralis_token_analytics_enhanced
- moralis_holder_distribution
- moralis_holder_stats_complete

BSC Tables (9):
- bsc_pool_metrics
- bsc_trades
- bsc_liquidity_events
- bsc_dex_trades
- bsc_pool_events
- bsc_wallet_metrics
- wash_trade_suspects
- manipulation_alerts
- token_distribution
```

---

## Data Collection Pipeline

### 1. Collection Schedule

#### Moralis Monitor (10-minute intervals)
```
00:00 → Cycle 1 → Fetch all 9 endpoints → Store data
00:10 → Cycle 2 → Fetch all 9 endpoints → Store data
...continues 24/7
```

#### BSC Monitor (60-second intervals)
```
Every minute:
- Fetch pool reserves
- Calculate TVL and price
- Check for new trades
- Detect liquidity events
- Analyze trading patterns
```

### 2. API Rate Limiting

#### Moralis API Limits
- **Plan**: 40,000 Compute Units per day
- **Usage per cycle**: ~225 CU (9 endpoints × 25 CU)
- **Cycles per day**: 144 (every 10 minutes)
- **Daily usage**: 32,400 CU (81% of limit)
- **Buffer**: 7,600 CU for retries/errors

#### Rate Limit Management
```python
MONITOR_INTERVAL_MINUTES = int(os.getenv("MONITOR_INTERVAL_MINUTES", "10"))

# Adaptive rate limiting based on plan:
# 40K CU/day: 10 minutes
# 100K CU/day: 5 minutes
# 350K CU/day: 2 minutes
```

### 3. Error Handling

#### Retry Logic
```python
async def fetch_with_retry(url, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await session.get(url, params=params)
            if response.status == 200:
                return await response.json()
            elif response.status == 429:  # Rate limited
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error(f"API error {response.status}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise
    return None
```

#### Database Transaction Management
```python
async with self.db_pool.acquire() as conn:
    async with conn.transaction():
        # All inserts in transaction
        await conn.execute(insert_query, *values)
        # Auto-rollback on error
```

---

## Visualization Layer

### Grafana Dashboards

#### 1. Main Dashboard (`moralis-bsc-dashboard.json`)

**Key Panels:**

1. **Overview Section**
   - Total Value Locked (TVL)
   - Current BTCB Price
   - 24h Volume
   - Total Holders

2. **Holder Analytics**
   - Total Holders (stat)
   - Top 10 Concentration (gauge)
   - Holder Distribution (pie chart)
   - Whale Count (stat)
   - Historical Holder Trends (time series)

3. **Trading Analytics**
   - Buy vs Sell Volume (time series)
   - Top Profitable Traders (table)
   - Recent Swaps (table)
   - Volume by Hour (bar chart)

4. **Price Analytics**
   - Price Chart (time series)
   - 24h Price Change (stat)
   - Price vs Volume Correlation (scatter)

5. **Liquidity Analytics**
   - Liquidity Changes (time series)
   - Add/Remove Events (table)
   - LP Provider Analysis (table)

#### 2. BSC Dashboard (`bsc-dashboard-fixed.json`)

**Specialized Panels:**
- Pool Reserves Tracking
- TVL Historical Chart
- Price Impact Calculator
- Arbitrage Opportunities
- Wash Trading Alerts

### SQL Query Examples

#### Buy vs Sell Volume Query
```sql
SELECT
    DATE_TRUNC('hour', block_timestamp) as time,
    SUM(CASE WHEN transaction_type = 'buy'
        THEN total_value_usd ELSE 0 END) as "Buy Volume",
    SUM(CASE WHEN transaction_type = 'sell'
        THEN total_value_usd ELSE 0 END) as "Sell Volume"
FROM moralis_swaps_correct
WHERE block_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1;
```

#### Top Holders Query
```sql
SELECT
    ROW_NUMBER() OVER (ORDER BY balance DESC) as "Rank",
    holder_address as "Address",
    balance_formatted as "Balance",
    balance_formatted * 97245 as "USD Value",
    percentage_of_supply as "% Supply",
    holder_type as "Type"
FROM moralis_holders
ORDER BY balance DESC
LIMIT 100;
```

---

## Deployment & Operations

### 1. Local Development Setup

```bash
# Clone repository
git clone https://github.com/Ra1nbowF/dex-onchain-analytics.git
cd dex-onchain-analytics

# Start Docker services
docker-compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/dex_analytics"
export MORALIS_API_KEY="your_api_key"

# Run monitors locally
python main.py  # Moralis monitor
python bsc_pool_monitor.py  # BSC monitor
```

### 2. Railway Deployment

#### Automatic Deployment
```bash
# Any push to main branch triggers deployment
git add .
git commit -m "Update monitors"
git push origin main

# Railway automatically:
# 1. Builds container
# 2. Runs migrations
# 3. Starts collector.py
# 4. Monitors health
```

#### Manual Deployment Commands
```bash
# Check deployment status
railway status

# View logs
railway logs

# Restart service
railway restart

# Update environment variables
railway variables set MONITOR_INTERVAL_MINUTES=5
```

### 3. Database Operations

#### Backup Procedures
```bash
# Export data
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Import data
psql $DATABASE_URL < backup.sql
```

#### Maintenance Queries
```sql
-- Clean old data (keep 30 days)
DELETE FROM moralis_swaps_correct
WHERE timestamp < NOW() - INTERVAL '30 days';

-- Vacuum and analyze
VACUUM ANALYZE;

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## API Integration

### 1. Moralis Web3 API

#### Authentication
```python
headers = {
    "accept": "application/json",
    "X-API-Key": MORALIS_API_KEY
}
```

#### Endpoint Usage
| Endpoint | CU Cost | Frequency | Purpose |
|----------|---------|-----------|---------|
| /erc20/swaps | 25 | 10 min | Trade data |
| /erc20/transfers | 25 | 10 min | Transfer tracking |
| /pairs/stats | 25 | 10 min | Price/volume |
| /erc20/holders | 25 | 10 min | Holder stats |
| /erc20/analytics | 25 | 10 min | Token metrics |

### 2. BSC RPC Integration

#### Web3 Connection
```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(BSC_RPC))
pool_contract = w3.eth.contract(
    address=POOL_ADDRESS,
    abi=POOL_ABI
)
```

#### Contract Calls
```python
# Get reserves
reserves = pool_contract.functions.getReserves().call()

# Get events
events = pool_contract.events.Swap.createFilter(
    fromBlock='latest'
).get_all_entries()
```

---

## Monitoring & Alerts

### 1. Health Checks

#### System Health Indicators
- Database connectivity
- API response times
- Data freshness
- Error rates
- Thread status

#### Health Check Implementation
```python
async def health_check():
    checks = {
        "database": await check_db_connection(),
        "moralis_api": await check_moralis_api(),
        "bsc_rpc": await check_bsc_rpc(),
        "data_freshness": await check_data_freshness()
    }
    return all(checks.values())
```

### 2. Alert Conditions

#### Critical Alerts
- Database connection lost
- API key expired/invalid
- No data for >30 minutes
- Thread crash

#### Warning Alerts
- High API usage (>90% of limit)
- Slow query performance
- Data lag >15 minutes
- Memory usage >80%

### 3. Monitoring Metrics

#### Performance KPIs
- Records processed per minute
- API response time (p50, p95, p99)
- Database query time
- Data lag (current time - last record)

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. No Data in Grafana
```bash
# Check if monitors are running
docker ps | grep monitor

# Check database for recent data
psql $DATABASE_URL -c "
SELECT table_name, MAX(timestamp)
FROM information_schema.tables t
JOIN pg_stat_user_tables s ON t.table_name = s.relname
WHERE table_name LIKE 'moralis%'
GROUP BY table_name;"

# Restart monitors
docker-compose restart bsc_pool_monitor
docker-compose restart moralis_btcb_monitor
```

#### 2. API Rate Limit Errors
```python
# Solution 1: Increase interval
export MONITOR_INTERVAL_MINUTES=20

# Solution 2: Use backup API key
export MORALIS_API_KEY="backup_key_here"

# Solution 3: Reduce endpoints
# Comment out non-critical endpoints in monitor_cycle()
```

#### 3. Database Connection Issues
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check connection pool
SELECT count(*) FROM pg_stat_activity;

# Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < NOW() - INTERVAL '10 minutes';
```

#### 4. Missing Columns Errors
```sql
-- Add missing column
ALTER TABLE moralis_swaps_correct
ADD COLUMN IF NOT EXISTS total_value_usd DECIMAL(20,2);

-- Update values
UPDATE moralis_swaps_correct
SET total_value_usd = ABS(
    CASE
        WHEN transaction_type = 'buy' THEN bought_usd_amount
        WHEN transaction_type = 'sell' THEN sold_usd_amount
    END
);
```

---

## Performance Optimization

### 1. Database Optimization

#### Index Strategy
```sql
-- Critical indexes for query performance
CREATE INDEX idx_swaps_timestamp ON moralis_swaps_correct(block_timestamp DESC);
CREATE INDEX idx_swaps_wallet ON moralis_swaps_correct(wallet_address);
CREATE INDEX idx_swaps_type ON moralis_swaps_correct(transaction_type);
CREATE INDEX idx_holders_balance ON moralis_holders(balance DESC);
CREATE INDEX idx_metrics_timestamp ON bsc_pool_metrics(timestamp DESC);
```

#### Partitioning Strategy
```sql
-- Partition large tables by month
CREATE TABLE moralis_swaps_correct_2024_09
PARTITION OF moralis_swaps_correct
FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');
```

### 2. Query Optimization

#### Materialized Views
```sql
CREATE MATERIALIZED VIEW daily_volume_summary AS
SELECT
    DATE(block_timestamp) as date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN transaction_type = 'buy'
        THEN total_value_usd END) as buy_volume,
    SUM(CASE WHEN transaction_type = 'sell'
        THEN total_value_usd END) as sell_volume,
    COUNT(DISTINCT wallet_address) as unique_traders
FROM moralis_swaps_correct
GROUP BY DATE(block_timestamp);

-- Refresh daily
REFRESH MATERIALIZED VIEW daily_volume_summary;
```

### 3. Application Optimization

#### Connection Pooling
```python
# Optimal pool settings
db_pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=5,
    max_size=20,
    command_timeout=60,
    max_queries=50000,
    max_inactive_connection_lifetime=300
)
```

#### Batch Processing
```python
# Batch inserts for better performance
async def batch_insert(records, batch_size=100):
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        await conn.executemany(insert_query, batch)
```

---

## Security Considerations

### 1. API Key Management
- Store keys in environment variables
- Rotate keys regularly
- Use separate keys for dev/prod
- Monitor key usage

### 2. Database Security
- Use SSL connections
- Implement row-level security
- Regular security audits
- Encrypted backups

### 3. Code Security
- Input validation
- SQL injection prevention
- Rate limiting
- Error message sanitization

---

## Future Enhancements

### Planned Features
1. **Multi-chain Support**: Ethereum, Polygon, Arbitrum
2. **Additional DEXs**: Uniswap, SushiSwap, Curve
3. **Machine Learning**: Price prediction, anomaly detection
4. **Real-time WebSocket**: Live data streaming
5. **Mobile App**: iOS/Android dashboards
6. **Alert System**: Telegram/Discord notifications
7. **API Service**: RESTful API for data access
8. **Advanced Analytics**: Impermanent loss calculator, yield optimization

### Scaling Considerations
- Kubernetes deployment for horizontal scaling
- Redis caching layer for frequent queries
- TimescaleDB for better time-series performance
- Apache Kafka for event streaming
- GraphQL API for flexible data queries

---

## Contact & Support

### Repository
- GitHub: https://github.com/Ra1nbowF/dex-onchain-analytics
- Issues: https://github.com/Ra1nbowF/dex-onchain-analytics/issues

### Documentation
- This document: PROJECT_DOCUMENTATION.md
- Database schema: database_schema_complete.md
- API docs: Moralis API Documentation

### Monitoring
- Railway Dashboard: https://railway.app
- Grafana: http://localhost:3000 (local)

---

*Last Updated: September 2024*
*Version: 1.0.0*