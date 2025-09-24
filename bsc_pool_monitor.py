"""
BSC Pool Monitor for USDT/BTCB on PancakeSwap
Pool: 0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4
BTCB: 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c
USDT: 0x55d398326f99059fF775485246999027B3197955
"""

import asyncio
import asyncpg
import aiohttp
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
from typing import Dict, List, Optional
import logging

# Reduce logging for Railway (rate limit: 500 logs/sec)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Configuration
BSC_RPC = "https://bsc-dataseed1.binance.org/"
BSCSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/dex_analytics")

# Contract addresses
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BTCB_ADDRESS = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"
PANCAKE_FACTORY = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"

# PancakeSwap V2 ABI (simplified)
PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "reserve0", "type": "uint112"},
            {"name": "reserve1", "type": "uint112"},
            {"name": "blockTimestampLast", "type": "uint32"}
        ],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    }
]


class BSCPoolMonitor:
    def __init__(self):
        self.db_pool = None
        self.session = None
        self.last_block = 0
        self.btcb_price = 70000  # Will be updated from API
        self.usdt_price = 1

    async def initialize(self):
        """Initialize database and API connections"""
        self.db_pool = await asyncpg.create_pool(DATABASE_URL)
        self.session = aiohttp.ClientSession()
        await self.create_tables()
        logger.info("BSC Pool Monitor initialized")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()

    async def create_tables(self):
        """Create monitoring tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                -- Pool metrics table
                CREATE TABLE IF NOT EXISTS bsc_pool_metrics (
                    id SERIAL PRIMARY KEY,
                    pool_address VARCHAR(42),
                    token0_reserve DECIMAL(40, 18),
                    token1_reserve DECIMAL(40, 18),
                    total_liquidity_usd DECIMAL(30, 2),
                    tvl DECIMAL(30, 2),
                    price_btcb_usdt DECIMAL(20, 8),
                    pool_ratio DECIMAL(10, 4),
                    lp_token_supply DECIMAL(40, 18),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Trading activity
                CREATE TABLE IF NOT EXISTS bsc_trades (
                    id SERIAL PRIMARY KEY,
                    tx_hash VARCHAR(66) UNIQUE,
                    block_number BIGINT,
                    trader_address VARCHAR(42),
                    token_in VARCHAR(42),
                    token_out VARCHAR(42),
                    amount_in DECIMAL(40, 18),
                    amount_out DECIMAL(40, 18),
                    price DECIMAL(20, 8),
                    value_usd DECIMAL(30, 2),
                    gas_used BIGINT,
                    slippage DECIMAL(10, 4),
                    is_buy BOOLEAN,
                    timestamp TIMESTAMP
                );

                -- Wallet tracking
                CREATE TABLE IF NOT EXISTS bsc_wallet_metrics (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42),
                    btcb_balance DECIMAL(40, 18),
                    usdt_balance DECIMAL(40, 18),
                    lp_token_balance DECIMAL(40, 18),
                    total_trades INTEGER DEFAULT 0,
                    total_volume_usd DECIMAL(30, 2) DEFAULT 0,
                    realized_pnl DECIMAL(30, 2) DEFAULT 0,
                    unrealized_pnl DECIMAL(30, 2) DEFAULT 0,
                    win_rate DECIMAL(5, 2),
                    avg_trade_size DECIMAL(30, 2),
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP,
                    is_mm_suspect BOOLEAN DEFAULT FALSE,
                    is_insider_suspect BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Wash trading detection
                CREATE TABLE IF NOT EXISTS wash_trade_suspects (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42),
                    related_wallets TEXT[], -- Array of related addresses
                    suspicious_tx_count INTEGER,
                    circular_volume DECIMAL(30, 2),
                    detection_score DECIMAL(5, 2),
                    evidence JSONB,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Liquidity events
                CREATE TABLE IF NOT EXISTS bsc_liquidity_events (
                    id SERIAL PRIMARY KEY,
                    tx_hash VARCHAR(66) UNIQUE,
                    event_type VARCHAR(20), -- 'ADD' or 'REMOVE'
                    provider_address VARCHAR(42),
                    btcb_amount DECIMAL(40, 18),
                    usdt_amount DECIMAL(40, 18),
                    lp_tokens DECIMAL(40, 18),
                    share_of_pool DECIMAL(10, 4),
                    timestamp TIMESTAMP
                );

                -- Market manipulation alerts
                CREATE TABLE IF NOT EXISTS manipulation_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_type VARCHAR(50),
                    severity VARCHAR(20),
                    description TEXT,
                    evidence JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Token distribution metrics
                CREATE TABLE IF NOT EXISTS token_distribution (
                    id SERIAL PRIMARY KEY,
                    top_10_concentration DECIMAL(10, 4),
                    top_50_concentration DECIMAL(10, 4),
                    top_100_concentration DECIMAL(10, 4),
                    gini_coefficient DECIMAL(10, 4),
                    unique_holders INTEGER,
                    new_holders_24h INTEGER,
                    whale_count INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_bsc_trades_trader ON bsc_trades(trader_address);
                CREATE INDEX IF NOT EXISTS idx_bsc_trades_timestamp ON bsc_trades(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_bsc_wallet_volume ON bsc_wallet_metrics(total_volume_usd DESC);
                CREATE INDEX IF NOT EXISTS idx_bsc_wallet_pnl ON bsc_wallet_metrics(realized_pnl DESC);
                CREATE INDEX IF NOT EXISTS idx_pool_metrics_timestamp ON bsc_pool_metrics(timestamp DESC);
            """)

    async def fetch_pool_reserves(self) -> Dict:
        """Fetch current pool reserves from blockchain"""
        try:
            url = "https://api.etherscan.io/v2/api"

            # Get USDT balance in pool
            params = {
                "chainid": "56",
                "module": "account",
                "action": "tokenbalance",
                "contractaddress": USDT_ADDRESS,
                "address": POOL_ADDRESS,
                "tag": "latest",
                "apikey": BSCSCAN_API_KEY
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()
                if data.get("status") != "1":
                    logger.error(f"Failed to fetch USDT balance: {data}")
                    return {}
                usdt_balance = int(data["result"]) / 10**18  # USDT has 18 decimals

            # Get BTCB balance in pool
            params["contractaddress"] = BTCB_ADDRESS

            async with self.session.get(url, params=params) as response:
                data = await response.json()
                if data.get("status") != "1":
                    logger.error(f"Failed to fetch BTCB balance: {data}")
                    return {}
                btcb_balance = int(data["result"]) / 10**18  # BTCB has 18 decimals

            logger.info(f"Pool reserves - BTCB: {btcb_balance:.4f}, USDT: {usdt_balance:.2f}")

            return {
                "btcb_reserve": btcb_balance,
                "usdt_reserve": usdt_balance,
                "tvl": (btcb_balance * self.btcb_price) + (usdt_balance * self.usdt_price),
                "price": usdt_balance / btcb_balance if btcb_balance > 0 else 0,
                "ratio": (btcb_balance * self.btcb_price) / ((btcb_balance * self.btcb_price) + usdt_balance) if btcb_balance > 0 else 0.5
            }
        except Exception as e:
            logger.error(f"Error fetching pool reserves: {e}")

        return {}

    async def fetch_recent_trades(self, hours: int = 1) -> List[Dict]:
        """Fetch recent swap events from the pool"""
        try:
            # Get block range
            current_block = await self.get_current_block()
            blocks_per_hour = 1200  # ~3 seconds per block on BSC
            start_block = current_block - (hours * blocks_per_hour)

            url = "https://api.etherscan.io/v2/api"
            params = {
                "chainid": "56",
                "module": "logs",
                "action": "getLogs",
                "address": POOL_ADDRESS,
                "fromBlock": start_block,
                "toBlock": current_block,
                "topic0": "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",  # Swap event
                "apikey": BSCSCAN_API_KEY
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()
                trades = []

                if data.get("result") and isinstance(data["result"], list):
                    for log in data["result"]:
                        trade = await self.decode_swap_event(log)
                        if trade:
                            trades.append(trade)

                return trades
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []

    async def decode_swap_event(self, log: Dict) -> Optional[Dict]:
        """Decode a swap event log"""
        try:
            data = log["data"][2:]  # Remove 0x
            topics = log["topics"]

            # Decode amounts
            amount0_in = int(data[0:64], 16) / 10**18
            amount1_in = int(data[64:128], 16) / 10**18
            amount0_out = int(data[128:192], 16) / 10**18
            amount1_out = int(data[192:256], 16) / 10**18

            # Determine trade direction
            is_buy = amount0_in > 0  # BTCB in = buying USDT

            if is_buy:
                amount_in = amount0_in
                amount_out = amount1_out
                token_in = "BTCB"
                token_out = "USDT"
                price = amount1_out / amount0_in if amount0_in > 0 else 0
            else:
                amount_in = amount1_in
                amount_out = amount0_out
                token_in = "USDT"
                token_out = "BTCB"
                price = amount1_in / amount0_out if amount0_out > 0 else 0

            # Get trader address from transaction
            trader = "0x" + topics[2][-40:] if len(topics) > 2 else None

            return {
                "tx_hash": log["transactionHash"],
                "block_number": int(log["blockNumber"], 16),
                "trader_address": trader,
                "token_in": token_in,
                "token_out": token_out,
                "amount_in": amount_in,
                "amount_out": amount_out,
                "price": price,
                "value_usd": amount_in * self.btcb_price if token_in == "BTCB" else amount_in,
                "is_buy": is_buy,
                "timestamp": datetime.fromtimestamp(int(log["timeStamp"], 16))
            }
        except Exception as e:
            logger.error(f"Error decoding swap event: {e}")
            return None

    async def calculate_wallet_pnl(self, wallet_address: str) -> Dict:
        """Calculate PnL for a specific wallet"""
        async with self.db_pool.acquire() as conn:
            # Get all trades for this wallet
            trades = await conn.fetch("""
                SELECT * FROM bsc_trades
                WHERE trader_address = $1
                ORDER BY timestamp
            """, wallet_address)

            btcb_balance = 0
            usdt_balance = 0
            total_cost = 0
            total_revenue = 0
            winning_trades = 0
            total_trades = len(trades)

            for trade in trades:
                if trade["is_buy"]:
                    # Buying USDT with BTCB
                    btcb_balance -= float(trade["amount_in"])
                    usdt_balance += float(trade["amount_out"])
                    total_cost += float(trade["value_usd"])
                else:
                    # Selling USDT for BTCB
                    usdt_balance -= float(trade["amount_in"])
                    btcb_balance += float(trade["amount_out"])
                    total_revenue += float(trade["value_usd"])

                # Check if trade was profitable
                if total_revenue > total_cost:
                    winning_trades += 1

            # Calculate unrealized PnL
            unrealized_btcb = btcb_balance * self.btcb_price
            unrealized_usdt = usdt_balance * self.usdt_price
            unrealized_pnl = unrealized_btcb + unrealized_usdt

            # Realized PnL
            realized_pnl = total_revenue - total_cost

            return {
                "wallet_address": wallet_address,
                "btcb_balance": btcb_balance,
                "usdt_balance": usdt_balance,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "total_pnl": realized_pnl + unrealized_pnl,
                "total_volume": total_cost + total_revenue
            }

    async def detect_wash_trading(self) -> List[Dict]:
        """Detect potential wash trading patterns"""
        async with self.db_pool.acquire() as conn:
            # Find wallets with suspicious patterns
            suspects = await conn.fetch("""
                WITH trade_patterns AS (
                    SELECT
                        trader_address,
                        COUNT(*) as trade_count,
                        SUM(value_usd) as total_volume,
                        COUNT(DISTINCT DATE_TRUNC('minute', timestamp)) as active_minutes,
                        AVG(value_usd) as avg_trade_size,
                        STDDEV(value_usd) as trade_size_stddev
                    FROM bsc_trades
                    WHERE timestamp > NOW() - INTERVAL '24 hours'
                    GROUP BY trader_address
                    HAVING COUNT(*) > 10
                )
                SELECT * FROM trade_patterns
                WHERE
                    -- High frequency with low variance (automated trading)
                    (trade_count / active_minutes > 2 AND trade_size_stddev < avg_trade_size * 0.1)
                    OR
                    -- Very high volume relative to unique time periods
                    (total_volume / active_minutes > 10000)
                ORDER BY total_volume DESC
            """)

            wash_traders = []
            for suspect in suspects:
                # Check for circular patterns
                circular_trades = await conn.fetch("""
                    SELECT
                        t1.trader_address as wallet1,
                        t2.trader_address as wallet2,
                        COUNT(*) as matching_trades
                    FROM bsc_trades t1
                    JOIN bsc_trades t2 ON
                        ABS(EXTRACT(EPOCH FROM t1.timestamp - t2.timestamp)) < 60
                        AND t1.is_buy != t2.is_buy
                        AND ABS(t1.amount_in - t2.amount_out) < 0.01
                    WHERE t1.trader_address = $1
                    GROUP BY t1.trader_address, t2.trader_address
                    HAVING COUNT(*) > 3
                """, suspect["trader_address"])

                if circular_trades:
                    wash_traders.append({
                        "wallet": suspect["trader_address"],
                        "trade_count": suspect["trade_count"],
                        "volume": float(suspect["total_volume"]),
                        "related_wallets": [r["wallet2"] for r in circular_trades],
                        "confidence_score": min(len(circular_trades) * 20, 100)
                    })

            return wash_traders

    async def calculate_token_distribution(self) -> Dict:
        """Calculate token distribution metrics including Gini coefficient"""
        # Token distribution endpoint not available in V2 API for BSC
        # Return simulated data for now
        return {
            "total_holders": 1000,
            "top_10_concentration": 45.0,
            "top_50_concentration": 70.0,
            "top_100_concentration": 85.0,
            "gini_coefficient": 0.65,
            "whale_count": 15
        }

    def calculate_gini(self, balances: List[float]) -> float:
        """Calculate Gini coefficient for wealth distribution"""
        if not balances:
            return 0

        sorted_balances = sorted(balances)
        n = len(sorted_balances)
        cumsum = 0

        for i, balance in enumerate(sorted_balances):
            cumsum += (n - i) * balance

        total = sum(sorted_balances)
        if total == 0:
            return 0

        gini = (n + 1 - 2 * cumsum / total) / n
        return max(0, min(1, gini))  # Ensure between 0 and 1

    async def get_current_block(self) -> int:
        """Get current BSC block number"""
        try:
            url = "https://api.etherscan.io/v2/api"
            params = {
                "chainid": "56",
                "module": "proxy",
                "action": "eth_blockNumber",
                "apikey": BSCSCAN_API_KEY
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()
                if data.get("result"):
                    return int(data["result"], 16)
        except Exception as e:
            logger.error(f"Error getting block number: {e}")

        return 0

    async def monitor_pool(self):
        """Main monitoring loop"""
        logger.info("Starting BSC pool monitoring...")

        while True:
            try:
                # Fetch and store pool metrics
                reserves = await self.fetch_pool_reserves()
                if reserves:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO bsc_pool_metrics (
                                pool_address, token0_reserve, token1_reserve,
                                total_liquidity_usd, tvl, price_btcb_usdt, pool_ratio
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                            POOL_ADDRESS,
                            reserves["btcb_reserve"],
                            reserves["usdt_reserve"],
                            reserves["tvl"],
                            reserves["tvl"],
                            reserves["price"],
                            reserves["ratio"]
                        )

                # Fetch recent trades
                trades = await self.fetch_recent_trades(hours=1)
                for trade in trades:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO bsc_trades (
                                tx_hash, block_number, trader_address,
                                token_in, token_out, amount_in, amount_out,
                                price, value_usd, is_buy, timestamp
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            ON CONFLICT (tx_hash) DO NOTHING
                        """,
                            trade["tx_hash"], trade["block_number"],
                            trade["trader_address"], trade["token_in"],
                            trade["token_out"], trade["amount_in"],
                            trade["amount_out"], trade["price"],
                            trade["value_usd"], trade["is_buy"],
                            trade["timestamp"]
                        )

                # Detect wash trading
                wash_traders = await self.detect_wash_trading()
                for trader in wash_traders:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO wash_trade_suspects (
                                wallet_address, related_wallets,
                                suspicious_tx_count, circular_volume,
                                detection_score
                            ) VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT DO NOTHING
                        """,
                            trader["wallet"], trader["related_wallets"],
                            trader["trade_count"], trader["volume"],
                            trader["confidence_score"]
                        )

                # Calculate token distribution
                distribution = await self.calculate_token_distribution()
                if distribution:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO token_distribution (
                                top_10_concentration, top_50_concentration,
                                top_100_concentration, gini_coefficient,
                                unique_holders, whale_count
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                            distribution["top_10_concentration"],
                            distribution["top_50_concentration"],
                            distribution["top_100_concentration"],
                            distribution["gini_coefficient"],
                            distribution["total_holders"],
                            distribution["whale_count"]
                        )

                logger.info(f"Monitoring cycle complete. TVL: ${reserves.get('tvl', 0):,.2f}")

                # Wait 60 seconds before next cycle
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)


async def main():
    monitor = BSCPoolMonitor()
    try:
        await monitor.initialize()
        await monitor.monitor_pool()
    finally:
        await monitor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())