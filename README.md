# DEX Onchain Analytics

A comprehensive system for analyzing decentralized exchange (DEX) trading data using Etherscan's Multichain API.

## Features

- **Multi-chain Support**: Analyze DEX activity across Ethereum, BSC, Polygon, Arbitrum, Optimism, Base, and Avalanche
- **Rate Limiting**: Respects API limits (5 calls/second, 100k calls/day)
- **Wallet Tracking**: Monitor smart money and whale wallets
- **Database Storage**: PostgreSQL database for historical data

## API Credentials

Your Etherscan API credentials are stored in `.env`:
- **App Name**: analytics
- **API Key**: YZEHUAFGEUNSGKFQVVETB67299E24NMCPH
- **Rate Limit**: 5 calls/second
- **Daily Limit**: 100,000 calls

## Setup

1. **Install PostgreSQL** (if not already installed)
   ```bash
   # Windows: Download from https://www.postgresql.org/download/windows/
   # Or use Docker:
   docker run -d --name postgres-dex -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
   ```

2. **Create Database**
   ```bash
   psql -U postgres
   CREATE DATABASE dex_analytics;
   \q
   ```

3. **Install Python Dependencies**
   ```bash
   cd C:\Users\ramaz\dex-onchain-analytics
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Initialize Database Schema**
   ```bash
   psql -U postgres -d dex_analytics -f database/schema.sql
   ```

5. **Configure Environment** (already done in `.env`)

## Project Structure

```
dex-onchain-analytics/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration and chain settings
│   └── etherscan_client.py # Etherscan API client with rate limiting
├── database/
│   └── schema.sql          # PostgreSQL database schema
├── .env                    # Environment variables (API keys)
├── requirements.txt        # Python dependencies
├── main.py                # Main application
└── README.md              # Documentation
```

## Supported Chains

| Chain ID | Network   | DEXs Tracked                    |
|----------|-----------|----------------------------------|
| 1        | Ethereum  | Uniswap V2/V3, SushiSwap       |
| 56       | BSC       | PancakeSwap V2/V3               |
| 137      | Polygon   | QuickSwap, Uniswap V3           |
| 42161    | Arbitrum  | Uniswap V3, SushiSwap           |
| 10       | Optimism  | Uniswap V3, Velodrome           |
| 8453     | Base      | Uniswap V3, Aerodrome           |
| 43114    | Avalanche | TraderJoe V2, Pangolin          |

## Database Tables

- **chains**: Blockchain networks
- **dex_protocols**: DEX protocols and factories
- **tokens**: Token information
- **dex_pairs**: Trading pairs/pools
- **token_transfers**: ERC20 transfers
- **wallets**: Tracked wallet addresses
- **wallet_balances**: Token balance snapshots

## Running Continuous Monitoring

To run continuous monitoring:

```bash
python main.py
```

This will:
1. Track configured wallets
2. Store all data in PostgreSQL

## API Rate Limits

The system automatically handles rate limiting:
- Maximum 5 requests per second
- Maximum 100,000 requests per day
- Automatic backoff on rate limit errors
- Daily limit reset at midnight

## Next Steps

1. **Add Web Dashboard**: Create FastAPI dashboard for visualization
2. **Implement Webhooks**: Real-time alerts for opportunities
3. **Add More DEXs**: Integrate additional DEX protocols
4. **Price Oracles**: Integrate Chainlink for USD pricing
5. **MEV Detection**: Identify sandwich attacks and front-running
6. **Machine Learning**: Predict profitable trading patterns

## Troubleshooting

- **Rate Limit Errors**: Reduce `ETHERSCAN_RATE_LIMIT_PER_SECOND` in `.env`
- **Database Connection**: Check PostgreSQL is running and credentials are correct
- **Missing Data**: Some chains may have limited historical data available

## License

Private use only - contains API credentials
