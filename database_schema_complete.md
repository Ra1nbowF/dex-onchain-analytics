# DEX On-Chain Analytics - Complete Database Schema Documentation

## Database Infrastructure

### Docker Setup
- **Database**: PostgreSQL 15 Alpine
- **Container**: `dex_postgres`
- **Port**: 5433 (host) -> 5432 (container)
- **Database Name**: `dex_analytics`
- **Additional Services**: Redis cache (`dex_redis` on port 6380)

## Database Statistics
- **Total Tables**: 44
- **Total Sequences**: 43 (auto-increment IDs)
- **Total Unique Constraints**: 22
- **No Foreign Keys**: Schema uses loose coupling

## Sequences
All 43 sequences are standard SERIAL (INTEGER) with:
- Start Value: 1
- Increment: 1
- Min Value: 1
- Max Value: 2147483647
- No Cycling

## Complete Table Schemas

### 1. Core Trading Tables

#### dex_trades (28 MB, Most Active)
```sql
id                INTEGER PRIMARY KEY (sequence)
chain_id          INTEGER NOT NULL
chain_name        VARCHAR(50)
dex_name          VARCHAR(50) NOT NULL
pair              VARCHAR(50) NOT NULL
token_in          VARCHAR(20)
token_out         VARCHAR(20)
amount_in         DECIMAL(30,8)
amount_out        DECIMAL(30,8)
price             DECIMAL(20,8)
value_usd         DECIMAL(30,2)
trader_address    VARCHAR(42)
tx_hash           VARCHAR(66)
gas_used          INTEGER
timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: timestamp DESC, chain_id+timestamp, dex_name+timestamp, pair, trader_address

#### liquidity_pools (5.6 MB)
```sql
id                  INTEGER PRIMARY KEY (sequence)
chain_id            INTEGER NOT NULL
chain_name          VARCHAR(50)
dex_name            VARCHAR(50) NOT NULL
pool_address        VARCHAR(42)
token0_symbol       VARCHAR(20)
token1_symbol       VARCHAR(20)
token0_reserve      DECIMAL(30,8)
token1_reserve      DECIMAL(30,8)
total_liquidity_usd DECIMAL(30,2)
volume_24h          DECIMAL(30,2)
fees_24h            DECIMAL(20,2)
apy                 DECIMAL(10,4)
timestamp           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: timestamp DESC, dex_name+timestamp

#### token_prices (4.3 MB)
```sql
id                INTEGER PRIMARY KEY (sequence)
chain_id          INTEGER NOT NULL
token_symbol      VARCHAR(20) NOT NULL
token_address     VARCHAR(42)
price_usd         DECIMAL(20,8)
volume_24h        DECIMAL(30,2)
price_change_24h  DECIMAL(10,4)
market_cap        DECIMAL(30,2)
timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: timestamp DESC, token_symbol+timestamp

### 2. BSC-Specific Tables

#### bsc_trades (Empty)
```sql
id             INTEGER PRIMARY KEY (sequence)
tx_hash        VARCHAR(66) UNIQUE
block_number   BIGINT
trader_address VARCHAR(42)
token_in       VARCHAR(42)
token_out      VARCHAR(42)
amount_in      DECIMAL(40,18)
amount_out     DECIMAL(40,18)
price          DECIMAL(20,8)
value_usd      DECIMAL(30,2)
gas_used       BIGINT
slippage       DECIMAL(10,4)
is_buy         BOOLEAN
timestamp      TIMESTAMP
```
**Indexes**: tx_hash UNIQUE, timestamp DESC, trader_address

#### bsc_pool_metrics (128 KB)
```sql
id                  INTEGER PRIMARY KEY (sequence)
pool_address        VARCHAR(42)
token0_reserve      DECIMAL(40,18)
token1_reserve      DECIMAL(40,18)
total_liquidity_usd DECIMAL(30,2)
tvl                 DECIMAL(30,2)
price_btcb_usdt     DECIMAL(20,8)
pool_ratio          DECIMAL(10,4)
lp_token_supply     DECIMAL(40,18)
timestamp           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: timestamp DESC

#### bsc_liquidity_events (Empty)
```sql
id               INTEGER PRIMARY KEY (sequence)
tx_hash          VARCHAR(66) UNIQUE
event_type       VARCHAR(20)
provider_address VARCHAR(42)
btcb_amount      DECIMAL(40,18)
usdt_amount      DECIMAL(40,18)
lp_tokens        DECIMAL(40,18)
share_of_pool    DECIMAL(10,4)
timestamp        TIMESTAMP
```
**Indexes**: tx_hash UNIQUE

#### bsc_wallet_metrics (Empty, 16 columns)
```sql
id                 INTEGER PRIMARY KEY (sequence)
wallet_address     VARCHAR(42)
btcb_balance       DECIMAL(40,18)
usdt_balance       DECIMAL(40,18)
lp_token_balance   DECIMAL(40,18)
total_trades       INTEGER DEFAULT 0
total_volume_usd   DECIMAL(30,2) DEFAULT 0
realized_pnl       DECIMAL(30,2) DEFAULT 0
unrealized_pnl     DECIMAL(30,2) DEFAULT 0
win_rate           DECIMAL(5,2)
avg_trade_size     DECIMAL(30,2)
first_seen         TIMESTAMP
last_seen          TIMESTAMP
is_mm_suspect      BOOLEAN DEFAULT false
is_insider_suspect BOOLEAN DEFAULT false
updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: realized_pnl DESC, total_volume_usd DESC

### 3. Moralis Integration Tables

#### moralis_swaps_enhanced (1.5 MB, 33 columns)
```sql
id                   INTEGER PRIMARY KEY (sequence)
transaction_hash     TEXT UNIQUE
transaction_index    INTEGER
transaction_type     TEXT
sub_category         TEXT
block_number         BIGINT
block_timestamp      TIMESTAMP
wallet_address       TEXT
wallet_address_label TEXT
entity               TEXT
entity_logo          TEXT
pair_address         TEXT
pair_label           TEXT
exchange_address     TEXT
exchange_name        TEXT
exchange_logo        TEXT
bought_address       TEXT
bought_name          TEXT
bought_symbol        TEXT
bought_logo          TEXT
bought_amount        DECIMAL(40,18)
bought_usd_price     DECIMAL(20,8)
bought_usd_amount    DECIMAL(20,2)
sold_address         TEXT
sold_name            TEXT
sold_symbol          TEXT
sold_logo            TEXT
sold_amount          DECIMAL(40,18)
sold_usd_price       DECIMAL(20,8)
sold_usd_amount      DECIMAL(20,2)
base_quote_price     DECIMAL(40,18)
total_value_usd      DECIMAL(20,2)
timestamp            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: transaction_hash UNIQUE, block_timestamp, transaction_type, wallet_address

#### moralis_token_analytics_enhanced (40 columns)
```sql
id               INTEGER PRIMARY KEY (sequence)
token_address    TEXT
category_id      TEXT
buy_volume_5m    DECIMAL(20,2)
buy_volume_1h    DECIMAL(20,2)
buy_volume_6h    DECIMAL(20,2)
buy_volume_24h   DECIMAL(20,2)
sell_volume_5m   DECIMAL(20,2)
sell_volume_1h   DECIMAL(20,2)
sell_volume_6h   DECIMAL(20,2)
sell_volume_24h  DECIMAL(20,2)
buyers_5m        INTEGER
buyers_1h        INTEGER
buyers_6h        INTEGER
buyers_24h       INTEGER
sellers_5m       INTEGER
sellers_1h       INTEGER
sellers_6h       INTEGER
sellers_24h      INTEGER
buys_5m          INTEGER
buys_1h          INTEGER
buys_6h          INTEGER
buys_24h         INTEGER
sells_5m         INTEGER
sells_1h         INTEGER
sells_6h         INTEGER
sells_24h        INTEGER
liquidity_5m     DECIMAL(20,2)
liquidity_1h     DECIMAL(20,2)
liquidity_6h     DECIMAL(20,2)
liquidity_24h    DECIMAL(20,2)
fdv_5m           DECIMAL(20,2)
fdv_1h           DECIMAL(20,2)
fdv_6h           DECIMAL(20,2)
fdv_24h          DECIMAL(20,2)
price_change_5m  DECIMAL(10,6)
price_change_1h  DECIMAL(10,6)
price_change_6h  DECIMAL(10,6)
price_change_24h DECIMAL(10,6)
timestamp        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Unique Constraint**: (token_address, timestamp)

#### moralis_pair_stats_enhanced (52 columns)
```sql
id                              INTEGER PRIMARY KEY (sequence)
pair_address                    TEXT
pair_label                      TEXT
base_token_address              TEXT
base_token_name                 TEXT
base_token_symbol               TEXT
quote_token_address             TEXT
quote_token_name                TEXT
quote_token_symbol              TEXT
price_native                    DECIMAL(40,18)
price_usd                       DECIMAL(20,8)
liquidity_usd                   DECIMAL(20,2)
liquidity_base                  DECIMAL(40,18)
liquidity_quote                 DECIMAL(40,18)
fdv_usd                         DECIMAL(20,2)
market_cap_usd                  DECIMAL(20,2)
price_change_5m_percent         DECIMAL(10,4)
price_change_1h_percent         DECIMAL(10,4)
price_change_6h_percent         DECIMAL(10,4)
price_change_24h_percent        DECIMAL(10,4)
liquidity_change_5m_percent     DECIMAL(10,4)
liquidity_change_1h_percent     DECIMAL(10,4)
liquidity_change_6h_percent     DECIMAL(10,4)
liquidity_change_24h_percent    DECIMAL(10,4)
volume_5m_usd                   DECIMAL(20,2)
volume_1h_usd                   DECIMAL(20,2)
volume_6h_usd                   DECIMAL(20,2)
volume_24h_usd                  DECIMAL(20,2)
volume_change_5m_percent        DECIMAL(10,4)
volume_change_1h_percent        DECIMAL(10,4)
volume_change_6h_percent        DECIMAL(10,4)
volume_change_24h_percent       DECIMAL(10,4)
trades_5m                       INTEGER
trades_1h                       INTEGER
trades_6h                       INTEGER
trades_24h                      INTEGER
buy_trades_5m                   INTEGER
buy_trades_1h                   INTEGER
buy_trades_6h                   INTEGER
buy_trades_24h                  INTEGER
sell_trades_5m                  INTEGER
sell_trades_1h                  INTEGER
sell_trades_6h                  INTEGER
sell_trades_24h                 INTEGER
buyers_5m                       INTEGER
buyers_1h                       INTEGER
buyers_6h                       INTEGER
buyers_24h                      INTEGER
sellers_5m                      INTEGER
sellers_1h                      INTEGER
sellers_6h                      INTEGER
sellers_24h                     INTEGER
timestamp                       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Unique Constraint**: (pair_address, timestamp)

#### moralis_holder_distribution (168 KB)
```sql
id                   INTEGER PRIMARY KEY (sequence)
token_address        VARCHAR(42)
holder_address       VARCHAR(42)
balance              DECIMAL(40,18)
balance_usd          DECIMAL(30,2)
percentage_of_supply DECIMAL(10,6)
first_transaction    TIMESTAMP
last_transaction     TIMESTAMP
transaction_count    INTEGER
is_whale             BOOLEAN DEFAULT false
is_active            BOOLEAN DEFAULT true
holder_type          VARCHAR(50)
timestamp            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Unique Constraint**: (token_address, holder_address)
**Indexes**: balance_usd DESC

#### moralis_stats (22 columns)
```sql
id                      INTEGER PRIMARY KEY (sequence)
timestamp               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
total_holders           INTEGER
unique_wallets          INTEGER
total_volume_24h        DECIMAL(20,2)
total_transactions_24h  INTEGER
buy_volume_24h          DECIMAL(20,2)
sell_volume_24h         DECIMAL(20,2)
unique_buyers_24h       INTEGER
unique_sellers_24h      INTEGER
price_usd               DECIMAL(20,8)
market_cap              DECIMAL(20,2)
fully_diluted_valuation DECIMAL(20,2)
total_supply            DECIMAL(40,18)
circulating_supply      DECIMAL(40,18)
gini_coefficient        DECIMAL(5,4)
top10_concentration     DECIMAL(10,6)
top100_concentration    DECIMAL(10,6)
whale_count             INTEGER
dolphin_count           INTEGER
fish_count              INTEGER
shrimp_count            INTEGER
```

### 4. Risk & Monitoring Tables

#### manipulation_alerts (Empty)
```sql
id          INTEGER PRIMARY KEY (sequence)
alert_type  VARCHAR(50)
severity    VARCHAR(20)
description TEXT
evidence    JSONB
timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### market_manipulation_alerts (8 KB)
```sql
id           INTEGER PRIMARY KEY (sequence)
alert_type   VARCHAR(50)
severity     VARCHAR(20)
pair_address VARCHAR(42)
description  TEXT
metrics      JSONB
timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: timestamp DESC

#### wash_trading_complete (15 columns)
```sql
id                    INTEGER PRIMARY KEY (sequence)
wallet_address        VARCHAR(42)
pair_address          VARCHAR(42)
detection_type        VARCHAR(50)
buy_count             INTEGER
sell_count            INTEGER
round_trips           INTEGER
avg_hold_time_seconds INTEGER
total_volume          DECIMAL(30,2)
net_pnl               DECIMAL(30,2)
time_window_minutes   INTEGER
confidence_score      DECIMAL(5,2)
related_wallets       TEXT[]
details               JSONB
timestamp             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: confidence_score DESC

#### wash_trade_suspects (Empty)
```sql
id                  INTEGER PRIMARY KEY (sequence)
wallet_address      VARCHAR(42)
related_wallets     TEXT[]
suspicious_tx_count INTEGER
circular_volume     DECIMAL(30,2)
detection_score     DECIMAL(5,2)
evidence            JSONB
detected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### 5. Analytics Tables

#### wallet_activity (16 KB)
```sql
id              INTEGER PRIMARY KEY (sequence)
chain_id        INTEGER NOT NULL
wallet_address  VARCHAR(42) NOT NULL
wallet_label    VARCHAR(100)
total_trades    INTEGER DEFAULT 0
volume_24h      DECIMAL(30,2)
profit_loss     DECIMAL(20,2)
win_rate        DECIMAL(5,2)
tokens_traded   INTEGER
last_trade_time TIMESTAMP
timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Indexes**: timestamp DESC, volume_24h DESC

#### wallet_pnl (72 KB)
```sql
id             INTEGER PRIMARY KEY (sequence)
wallet_address VARCHAR(42)
token_address  VARCHAR(42)
total_bought   DECIMAL(40,18)
total_sold     DECIMAL(40,18)
avg_buy_price  DECIMAL(30,10)
avg_sell_price DECIMAL(30,10)
realized_pnl   DECIMAL(30,2)
unrealized_pnl DECIMAL(30,2)
trade_count    INTEGER
first_trade    TIMESTAMP
last_trade     TIMESTAMP
timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
**Unique Constraint**: (wallet_address, token_address)
**Indexes**: realized_pnl DESC

#### token_distribution (56 KB)
```sql
id                    INTEGER PRIMARY KEY (sequence)
top_10_concentration  DECIMAL(10,4)
top_50_concentration  DECIMAL(10,4)
top_100_concentration DECIMAL(10,4)
gini_coefficient      DECIMAL(10,4)
unique_holders        INTEGER
new_holders_24h       INTEGER
whale_count           INTEGER
timestamp             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### chain_stats (176 KB)
```sql
id                 INTEGER PRIMARY KEY (sequence)
chain_name         VARCHAR(50) NOT NULL
chain_id           INTEGER NOT NULL
total_volume_24h   DECIMAL(30,2)
total_transactions INTEGER
active_wallets     INTEGER
timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

## Materialized Views

### hourly_dex_stats
- Aggregates trades by hour, chain, and DEX
- Includes trade count, volume, average gas, unique traders
- Unique index on (hour, chain_name, dex_name)

### top_pairs_24h
- Top 100 trading pairs by volume in last 24 hours
- Includes trade count, volume, average price
- Unique index on (pair, chain_name, dex_name)

## Key Observations

1. **Data Types Pattern**:
   - Ethereum addresses: VARCHAR(42)
   - Transaction hashes: VARCHAR(66)
   - Token amounts: DECIMAL(40,18) - full precision
   - USD values: DECIMAL(30,2) - 2 decimal places
   - Percentages: DECIMAL(10,4) or (10,6)
   - Prices: DECIMAL(20,8)

2. **Table Variants**:
   - Many tables have "correct" and "enhanced" versions
   - Suggests iterative schema improvements
   - Enhanced versions typically have more columns

3. **No Foreign Keys**:
   - Tables are loosely coupled
   - Relationships managed at application level
   - Allows for flexible data insertion

4. **Indexing Strategy**:
   - Heavy emphasis on timestamp indexes (DESC)
   - Composite unique constraints for preventing duplicates
   - Performance indexes on financial metrics (volume, PnL)

5. **JSON Storage**:
   - JSONB used for flexible evidence/metrics storage
   - TEXT[] arrays for related wallet addresses

6. **Data Volume**:
   - dex_trades (28 MB) - main trading data
   - moralis_swaps_enhanced (1.5 MB) - detailed swap data
   - Most specialized tables are empty or small