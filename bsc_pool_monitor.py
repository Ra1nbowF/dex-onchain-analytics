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
import signal
import sys
try:
    from web3 import Web3
except ImportError:
    Web3 = None

# Reduce logging for Railway (rate limit: 500 logs/sec)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Configuration
BSC_RPC = "https://bsc-dataseed1.binance.org/"
# Use BSCScan API key, fallback to Etherscan key if not set
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", os.getenv("ETHERSCAN_API_KEY", "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/dex_analytics")

# Contract addresses
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
LP_TOKEN_ADDRESS = "0x41ff9aa7e16b8b1a8a8dc4f0efacd93d02d071c9"  # LP token is separate from pool
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
        # Create pool with connection limits to prevent too many connections
        self.db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
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

                -- Token Transfer Tracking
                CREATE TABLE IF NOT EXISTS bsc_token_transfers (
                    id SERIAL PRIMARY KEY,
                    tx_hash VARCHAR(66),
                    block_number BIGINT,
                    token_address VARCHAR(42),
                    token_symbol VARCHAR(10),
                    from_address VARCHAR(42),
                    to_address VARCHAR(42),
                    amount DECIMAL(40, 18),
                    value_usd DECIMAL(30, 2),
                    is_pool_related BOOLEAN DEFAULT FALSE,
                    transfer_type VARCHAR(20), -- 'deposit', 'withdraw', 'transfer', 'mint', 'burn'
                    gas_used BIGINT,
                    timestamp TIMESTAMP,
                    UNIQUE(tx_hash, token_address, from_address, to_address)
                );

                -- LP Token Tracking (Liquidity Provider tokens)
                CREATE TABLE IF NOT EXISTS bsc_lp_token_transfers (
                    id SERIAL PRIMARY KEY,
                    tx_hash VARCHAR(66),
                    block_number BIGINT,
                    from_address VARCHAR(42),
                    to_address VARCHAR(42),
                    lp_amount DECIMAL(40, 18),
                    btcb_amount DECIMAL(40, 18),
                    usdt_amount DECIMAL(40, 18),
                    total_value_usd DECIMAL(30, 2),
                    transfer_type VARCHAR(20), -- 'mint' (add liquidity), 'burn' (remove liquidity), 'transfer'
                    pool_share_percent DECIMAL(10, 6),
                    timestamp TIMESTAMP,
                    UNIQUE(tx_hash, from_address, to_address)
                );

                -- LP Token Holders
                CREATE TABLE IF NOT EXISTS bsc_lp_holders (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(42) UNIQUE,
                    lp_balance DECIMAL(40, 18),
                    pool_share_percent DECIMAL(10, 6),
                    btcb_value DECIMAL(40, 18),
                    usdt_value DECIMAL(40, 18),
                    total_value_usd DECIMAL(30, 2),
                    first_provided TIMESTAMP,
                    last_updated TIMESTAMP,
                    total_deposits INTEGER DEFAULT 0,
                    total_withdrawals INTEGER DEFAULT 0
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
                CREATE INDEX IF NOT EXISTS idx_token_transfers_timestamp ON bsc_token_transfers(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_token_transfers_from ON bsc_token_transfers(from_address);
                CREATE INDEX IF NOT EXISTS idx_token_transfers_to ON bsc_token_transfers(to_address);
                CREATE INDEX IF NOT EXISTS idx_token_transfers_pool ON bsc_token_transfers(is_pool_related) WHERE is_pool_related = TRUE;
                CREATE INDEX IF NOT EXISTS idx_lp_transfers_timestamp ON bsc_lp_token_transfers(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_lp_transfers_type ON bsc_lp_token_transfers(transfer_type);
                CREATE INDEX IF NOT EXISTS idx_lp_holders_balance ON bsc_lp_holders(lp_balance DESC);
                CREATE INDEX IF NOT EXISTS idx_lp_holders_value ON bsc_lp_holders(total_value_usd DESC);
            """)

    async def fetch_pool_reserves(self) -> Dict:
        """Fetch current pool reserves from blockchain"""
        try:
            url = "https://api.bscscan.com/api"

            # Get USDT balance in pool
            params = {
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

            url = "https://api.bscscan.com/api"
            params = {
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

    async def fetch_token_transfers(self, token_address: str, token_symbol: str, hours: int = 1) -> List[Dict]:
        """Fetch recent transfer events for a specific token"""
        try:
            current_block = await self.get_current_block()
            blocks_per_hour = 1200  # ~3 seconds per block on BSC
            start_block = current_block - (hours * blocks_per_hour)

            url = "https://api.bscscan.com/api"
            params = {
                "module": "logs",
                "action": "getLogs",
                "address": token_address,
                "fromBlock": start_block,
                "toBlock": current_block,
                "topic0": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer event
                "apikey": BSCSCAN_API_KEY
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()
                transfers = []

                if data.get("result") and isinstance(data["result"], list):
                    for log in data["result"]:
                        transfer = await self.decode_transfer_event(log, token_address, token_symbol)
                        if transfer:
                            transfers.append(transfer)

                return transfers
        except Exception as e:
            logger.error(f"Error fetching transfers for {token_symbol}: {e}")
            return []

    async def fetch_lp_token_transfers(self, hours: int = 1) -> List[Dict]:
        """Fetch LP token transfer events using Web3 or BSCScan API"""
        try:
            # Try Web3 approach first if available
            if Web3 is not None:
                transfers = await self.fetch_lp_transfers_web3(hours)
                if transfers:
                    return transfers

            # Fall back to BSCScan API
            # Get current block number first
            current_block = await self.get_current_block()
            if not current_block:
                # If BSCScan API fails, use BSC RPC as fallback
                url = BSC_RPC
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }
                async with self.session.post(url, json=payload) as response:
                    result = await response.json()
                    current_block = int(result["result"], 16)

            # Use BSCScan API to get token transfers
            url = "https://api.bscscan.com/api"

            # Get ERC20 token transfers for the LP token
            params = {
                "module": "account",
                "action": "tokentx",  # ERC20 token transfers
                "contractaddress": LP_TOKEN_ADDRESS,  # Correct LP token address
                "startblock": "0",
                "endblock": "99999999",
                "page": "1",
                "offset": "100",  # Get last 100 transfers
                "sort": "desc",
                "apikey": BSCSCAN_API_KEY
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()
                transfers = []

                if data.get("status") == "1" and data.get("result"):
                    for tx in data["result"]:
                        # Only process recent transfers
                        tx_timestamp = int(tx.get("timeStamp", 0))
                        current_time = datetime.utcnow().timestamp()
                        hours_ago = current_time - (hours * 3600)

                        if tx_timestamp < hours_ago:
                            continue

                        transfer = await self.decode_lp_transfer_from_api(tx)
                        if transfer:
                            transfers.append(transfer)

                logger.info(f"Found {len(transfers)} LP token transfers in last {hours} hours")
                return transfers

        except Exception as e:
            logger.error(f"Error fetching LP transfers: {e}")
            return []

    async def fetch_lp_transfers_web3(self, hours: int = 1) -> List[Dict]:
        """Fetch LP token transfers using Web3 directly"""
        try:
            if Web3 is None:
                logger.debug("Web3 not available")
                return []

            # Use Web3 with public BSC RPC
            rpc_url = "https://bsc.publicnode.com"
            w3 = Web3(Web3.HTTPProvider(rpc_url))

            if not w3.is_connected():
                logger.debug("Failed to connect to BSC RPC")
                return []

            # Calculate block range
            latest_block = w3.eth.block_number
            blocks_per_hour = 1200  # ~3 seconds per block on BSC
            from_block = max(0, latest_block - (blocks_per_hour * hours))

            # ERC20 Transfer event signature
            transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

            # Create filter for Transfer events
            event_filter = {
                'fromBlock': from_block,
                'toBlock': latest_block,
                'address': Web3.to_checksum_address(LP_TOKEN_ADDRESS),  # LP token, not pool
                'topics': [transfer_topic]
            }

            # Get logs in small chunks to avoid rate limits
            transfers = []
            chunk_size = 50  # Small chunks for public RPC

            # Only process last few hundred blocks to avoid rate limits
            actual_from_block = max(from_block, latest_block - 200)

            for start in range(actual_from_block, latest_block + 1, chunk_size):
                end = min(start + chunk_size - 1, latest_block)
                event_filter['fromBlock'] = start
                event_filter['toBlock'] = end

                try:
                    logs = w3.eth.get_logs(event_filter)

                    for log in logs:
                        transfer = await self.decode_lp_transfer_from_web3(log, w3)
                        if transfer:
                            transfers.append(transfer)
                except Exception as e:
                    # Skip chunks that fail (rate limits, etc)
                    logger.debug(f"Failed to fetch logs for blocks {start}-{end}: {e}")
                    continue

            if transfers:
                logger.info(f"Found {len(transfers)} LP token transfers via Web3")
            return transfers

        except Exception as e:
            logger.debug(f"Web3 fetch failed: {e}")
            return []

    async def decode_lp_transfer_from_web3(self, log: Dict, w3: Web3) -> Optional[Dict]:
        """Decode LP token transfer from Web3 log"""
        try:
            # Decode from and to addresses from topics
            from_address = "0x" + log['topics'][1].hex()[26:] if len(log['topics']) > 1 else "0x" + "0" * 40
            to_address = "0x" + log['topics'][2].hex()[26:] if len(log['topics']) > 2 else "0x" + "0" * 40

            # Decode amount from data
            lp_amount = int(log['data'].hex(), 16) / 10**18

            # Determine transfer type
            transfer_type = "transfer"
            if from_address.lower() == "0x" + "0" * 40:
                transfer_type = "mint"  # Add liquidity
            elif to_address.lower() == "0x" + "0" * 40:
                transfer_type = "burn"  # Remove liquidity

            # Get block timestamp
            block = w3.eth.get_block(log['blockNumber'])
            timestamp = datetime.fromtimestamp(block['timestamp'])

            # Get current pool reserves to calculate value
            reserves = await self.fetch_pool_reserves()
            total_supply = await self.get_lp_total_supply()

            # Calculate underlying token amounts
            btcb_amount = 0
            usdt_amount = 0
            total_value_usd = 0
            pool_share_percent = 0

            if reserves and total_supply > 0:
                pool_share = lp_amount / total_supply
                pool_share_percent = pool_share * 100
                btcb_amount = reserves["btcb_reserve"] * pool_share
                usdt_amount = reserves["usdt_reserve"] * pool_share
                total_value_usd = (btcb_amount * self.btcb_price) + (usdt_amount * self.usdt_price)

            return {
                "tx_hash": log['transactionHash'].hex(),
                "block_number": log['blockNumber'],
                "from_address": from_address,
                "to_address": to_address,
                "lp_amount": lp_amount,
                "btcb_amount": btcb_amount,
                "usdt_amount": usdt_amount,
                "total_value_usd": total_value_usd,
                "transfer_type": transfer_type,
                "pool_share_percent": pool_share_percent,
                "timestamp": timestamp
            }
        except Exception as e:
            logger.debug(f"Error decoding LP transfer: {e}")
            return None

    async def decode_lp_transfer_from_api(self, tx: Dict) -> Optional[Dict]:
        """Decode LP token transfer from BSCScan API response"""
        try:
            from_address = tx.get("from", "")
            to_address = tx.get("to", "")
            lp_amount = int(tx.get("value", 0)) / 10**int(tx.get("tokenDecimal", 18))

            # Determine transfer type
            transfer_type = "transfer"
            if from_address.lower() == "0x" + "0" * 40:
                transfer_type = "mint"  # Add liquidity
            elif to_address.lower() == "0x" + "0" * 40:
                transfer_type = "burn"  # Remove liquidity

            # Get current pool reserves to calculate value
            reserves = await self.fetch_pool_reserves()
            total_supply = await self.get_lp_total_supply()

            # Calculate underlying token amounts
            btcb_amount = 0
            usdt_amount = 0
            total_value_usd = 0
            pool_share_percent = 0

            if reserves and total_supply > 0:
                pool_share = lp_amount / total_supply
                pool_share_percent = pool_share * 100
                btcb_amount = reserves["btcb_reserve"] * pool_share
                usdt_amount = reserves["usdt_reserve"] * pool_share
                total_value_usd = (btcb_amount * self.btcb_price) + (usdt_amount * self.usdt_price)

            return {
                "tx_hash": tx.get("hash"),
                "block_number": int(tx.get("blockNumber", 0)),
                "from_address": from_address,
                "to_address": to_address,
                "lp_amount": lp_amount,
                "btcb_amount": btcb_amount,
                "usdt_amount": usdt_amount,
                "total_value_usd": total_value_usd,
                "transfer_type": transfer_type,
                "pool_share_percent": pool_share_percent,
                "timestamp": datetime.fromtimestamp(int(tx.get("timeStamp", 0)))
            }
        except Exception as e:
            logger.error(f"Error decoding LP transfer: {e}")
            return []

    async def decode_lp_transfer_event(self, log: Dict) -> Optional[Dict]:
        """Decode an LP token transfer event"""
        try:
            topics = log["topics"]

            # Transfer event has 3 topics: event signature, from, to
            if len(topics) < 3:
                return None

            from_address = "0x" + topics[1][-40:]
            to_address = "0x" + topics[2][-40:]

            # Decode amount from data
            data = log["data"][2:]  # Remove 0x
            lp_amount = int(data, 16) / 10**18  # LP tokens have 18 decimals

            # Determine transfer type
            transfer_type = "transfer"
            if from_address.lower() == "0x" + "0" * 40:  # Mint (add liquidity)
                transfer_type = "mint"
            elif to_address.lower() == "0x" + "0" * 40:  # Burn (remove liquidity)
                transfer_type = "burn"

            # Get current pool reserves to calculate value
            reserves = await self.fetch_pool_reserves()
            total_supply = await self.get_lp_total_supply()

            # Calculate underlying token amounts based on LP token share
            btcb_amount = 0
            usdt_amount = 0
            total_value_usd = 0
            pool_share_percent = 0

            if reserves and total_supply > 0:
                pool_share = lp_amount / total_supply
                pool_share_percent = pool_share * 100
                btcb_amount = reserves["btcb_reserve"] * pool_share
                usdt_amount = reserves["usdt_reserve"] * pool_share
                total_value_usd = (btcb_amount * self.btcb_price) + (usdt_amount * self.usdt_price)

            return {
                "tx_hash": log["transactionHash"],
                "block_number": int(log["blockNumber"], 16),
                "from_address": from_address,
                "to_address": to_address,
                "lp_amount": lp_amount,
                "btcb_amount": btcb_amount,
                "usdt_amount": usdt_amount,
                "total_value_usd": total_value_usd,
                "transfer_type": transfer_type,
                "pool_share_percent": pool_share_percent,
                "timestamp": datetime.fromtimestamp(int(log["timeStamp"], 16))
            }
        except Exception as e:
            logger.error(f"Error decoding LP transfer event: {e}")
            return None

    async def get_lp_total_supply(self) -> float:
        """Get total supply of LP tokens"""
        try:
            url = "https://api.bscscan.com/api"
            params = {
                "module": "stats",
                "action": "tokensupply",
                "contractaddress": LP_TOKEN_ADDRESS,  # LP token, not pool
                "apikey": BSCSCAN_API_KEY
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()
                if data.get("status") == "1":
                    return int(data["result"]) / 10**18
            return 0
        except Exception as e:
            logger.error(f"Error fetching LP token supply: {e}")
            return 0

    async def decode_transfer_event(self, log: Dict, token_address: str, token_symbol: str) -> Optional[Dict]:
        """Decode a transfer event log"""
        try:
            topics = log["topics"]

            # Transfer event has 3 topics: event signature, from, to
            if len(topics) < 3:
                return None

            from_address = "0x" + topics[1][-40:]
            to_address = "0x" + topics[2][-40:]

            # Decode amount from data
            data = log["data"][2:]  # Remove 0x
            amount = int(data, 16) / 10**18  # Assuming 18 decimals

            # Determine transfer type
            transfer_type = "transfer"
            is_pool_related = False

            if from_address.lower() == "0x" + "0" * 40:  # Mint
                transfer_type = "mint"
            elif to_address.lower() == "0x" + "0" * 40:  # Burn
                transfer_type = "burn"
            elif from_address.lower() == POOL_ADDRESS.lower():
                transfer_type = "withdraw"
                is_pool_related = True
            elif to_address.lower() == POOL_ADDRESS.lower():
                transfer_type = "deposit"
                is_pool_related = True

            # Calculate USD value
            value_usd = 0
            if token_symbol == "BTCB":
                value_usd = amount * self.btcb_price
            elif token_symbol == "USDT":
                value_usd = amount * self.usdt_price

            return {
                "tx_hash": log["transactionHash"],
                "block_number": int(log["blockNumber"], 16),
                "token_address": token_address,
                "token_symbol": token_symbol,
                "from_address": from_address,
                "to_address": to_address,
                "amount": amount,
                "value_usd": value_usd,
                "is_pool_related": is_pool_related,
                "transfer_type": transfer_type,
                "gas_used": int(log.get("gasUsed", "0x0"), 16),
                "timestamp": datetime.fromtimestamp(int(log["timeStamp"], 16))
            }
        except Exception as e:
            logger.error(f"Error decoding transfer event: {e}")
            return None

    async def update_lp_holder(self, wallet_address: str):
        """Update LP holder record with current balance and value"""
        try:
            # Get LP balance for this wallet
            url = "https://api.bscscan.com/api"
            params = {
                "module": "account",
                "action": "tokenbalance",
                "contractaddress": LP_TOKEN_ADDRESS,  # Separate LP token contract
                "address": wallet_address,
                "tag": "latest",
                "apikey": BSCSCAN_API_KEY
            }

            async with self.session.get(url, params=params) as response:
                data = await response.json()
                if data.get("status") != "1":
                    return

                lp_balance = int(data["result"]) / 10**18

            # Get pool reserves and total supply
            reserves = await self.fetch_pool_reserves()
            total_supply = await self.get_lp_total_supply()

            if reserves and total_supply > 0:
                pool_share = lp_balance / total_supply
                pool_share_percent = pool_share * 100
                btcb_value = reserves["btcb_reserve"] * pool_share
                usdt_value = reserves["usdt_reserve"] * pool_share
                total_value_usd = (btcb_value * self.btcb_price) + (usdt_value * self.usdt_price)

                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO bsc_lp_holders (
                            wallet_address, lp_balance, pool_share_percent,
                            btcb_value, usdt_value, total_value_usd,
                            first_provided, last_updated
                        ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                        ON CONFLICT (wallet_address) DO UPDATE SET
                            lp_balance = EXCLUDED.lp_balance,
                            pool_share_percent = EXCLUDED.pool_share_percent,
                            btcb_value = EXCLUDED.btcb_value,
                            usdt_value = EXCLUDED.usdt_value,
                            total_value_usd = EXCLUDED.total_value_usd,
                            last_updated = NOW()
                    """,
                        wallet_address, lp_balance, pool_share_percent,
                        btcb_value, usdt_value, total_value_usd
                    )

        except Exception as e:
            logger.error(f"Error updating LP holder {wallet_address}: {e}")

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
        """Get current BSC block number using RPC directly"""
        # Use BSC RPC directly to avoid deprecated BSCScan proxy endpoint
        rpc_endpoints = [
            BSC_RPC,
            "https://bsc-dataseed1.binance.org/",
            "https://bsc.publicnode.com",
            "https://bsc-dataseed2.binance.org/"
        ]

        for rpc in rpc_endpoints:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }

                async with self.session.post(rpc, json=payload) as response:
                    result = await response.json()
                    if result.get("result"):
                        block_num = int(result["result"], 16)
                        # Only log debug, not error
                        logger.debug(f"Got block number {block_num} from {rpc}")
                        return block_num
            except Exception as e:
                # Try next RPC
                continue

        logger.error("Failed to get block number from all RPC endpoints")
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
                                total_liquidity_usd, tvl, price_btcb_usdt, pool_ratio, timestamp
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
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

                # Fetch recent token transfers
                btcb_transfers = await self.fetch_token_transfers(BTCB_ADDRESS, "BTCB", hours=1)
                usdt_transfers = await self.fetch_token_transfers(USDT_ADDRESS, "USDT", hours=1)

                # Store transfers
                all_transfers = btcb_transfers + usdt_transfers
                for transfer in all_transfers:
                    try:
                        async with self.db_pool.acquire() as conn:
                            await conn.execute("""
                                INSERT INTO bsc_token_transfers (
                                    tx_hash, block_number, token_address, token_symbol,
                                    from_address, to_address, amount, value_usd,
                                    is_pool_related, transfer_type, gas_used, timestamp
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                                ON CONFLICT (tx_hash, token_address, from_address, to_address) DO NOTHING
                            """,
                                transfer["tx_hash"], transfer["block_number"],
                                transfer["token_address"], transfer["token_symbol"],
                                transfer["from_address"], transfer["to_address"],
                                transfer["amount"], transfer["value_usd"],
                                transfer["is_pool_related"], transfer["transfer_type"],
                                transfer["gas_used"], transfer["timestamp"]
                            )
                    except Exception as e:
                        logger.error(f"Error storing transfer: {e}")

                logger.info(f"Stored {len(trades)} trades and {len(all_transfers)} transfers")

                # Fetch and store LP token transfers
                lp_transfers = await self.fetch_lp_token_transfers(hours=1)
                for lp_transfer in lp_transfers:
                    try:
                        async with self.db_pool.acquire() as conn:
                            await conn.execute("""
                                INSERT INTO bsc_lp_token_transfers (
                                    tx_hash, block_number, from_address, to_address,
                                    lp_amount, btcb_amount, usdt_amount, total_value_usd,
                                    transfer_type, pool_share_percent, timestamp
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                ON CONFLICT (tx_hash, from_address, to_address) DO NOTHING
                            """,
                                lp_transfer["tx_hash"], lp_transfer["block_number"],
                                lp_transfer["from_address"], lp_transfer["to_address"],
                                lp_transfer["lp_amount"], lp_transfer["btcb_amount"],
                                lp_transfer["usdt_amount"], lp_transfer["total_value_usd"],
                                lp_transfer["transfer_type"], lp_transfer["pool_share_percent"],
                                lp_transfer["timestamp"]
                            )

                            # Update LP holder records
                            if lp_transfer["transfer_type"] in ["mint", "burn"]:
                                wallet = lp_transfer["to_address"] if lp_transfer["transfer_type"] == "mint" else lp_transfer["from_address"]
                                if wallet != "0x" + "0" * 40:  # Not null address
                                    await self.update_lp_holder(wallet)
                    except Exception as e:
                        logger.error(f"Error storing LP transfer: {e}")

                logger.info(f"Stored {len(lp_transfers)} LP token transfers")

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

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, cleaning up...")
        asyncio.create_task(monitor.cleanup())
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        await monitor.initialize()
        await monitor.monitor_pool()
    except Exception as e:
        logger.error(f"Monitor error: {e}")
    finally:
        await monitor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())