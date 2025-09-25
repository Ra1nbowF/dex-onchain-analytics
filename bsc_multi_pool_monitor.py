"""BSC Multi-Pool Monitor - Tracks multiple PancakeSwap pools"""

import asyncio
import aiohttp
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import os
import json

# Try importing Web3
try:
    from web3 import Web3
except ImportError:
    Web3 = None
    print("Web3 not available, using API-only mode")

# Configuration
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", "YZEHUAFGEUNSGKFQVVETB67299E24NMCPH")
BSC_RPC = "https://bsc.publicnode.com"

# Database connection for Railway
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"
)

# Pool configurations
POOLS = {
    "BTCB/USDT_V3": {
        "address": "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4",
        "version": "V3",
        "token0": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",  # BTCB
        "token1": "0x55d398326f99059fF775485246999027B3197955",  # USDT
        "token0_symbol": "BTCB",
        "token1_symbol": "USDT",
        "lp_token": "0x46a15b0b27311cedf172ab29e4f4766fbe7f4364",  # V3 Position Manager
        "decimals0": 18,
        "decimals1": 18
    },
    "WBNB/USDT_V2": {
        "address": "0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae",
        "version": "V2",
        "token0": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",  # WBNB
        "token1": "0x55d398326f99059fF775485246999027B3197955",  # USDT
        "token0_symbol": "WBNB",
        "token1_symbol": "USDT",
        "lp_token": "0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae",  # Same as pool for V2
        "decimals0": 18,
        "decimals1": 18
    }
}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class MultiPoolMonitor:
    def __init__(self):
        self.session = None
        self.db_pool = None
        self.pools = POOLS
        
    async def initialize(self):
        """Initialize connections"""
        self.session = aiohttp.ClientSession()
        self.db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info(f"Monitoring {len(self.pools)} pools")
        
    async def close(self):
        """Close connections"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
            
    async def fetch_v2_lp_transfers(self, pool_config: Dict, hours: int = 1) -> List[Dict]:
        """Fetch V2 LP token transfers"""
        transfers = []
        try:
            # For V2, LP token address = pool address
            pool_address = pool_config["address"]
            
            if Web3 is not None:
                # Use Web3 if available
                rpc_url = BSC_RPC
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                if w3.is_connected():
                    current_block = w3.eth.block_number
                    blocks_per_hour = 1200
                    from_block = max(0, current_block - (blocks_per_hour * hours))
                    
                    # ERC20 Transfer event
                    transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                    
                    logs = w3.eth.get_logs({
                        'fromBlock': from_block,
                        'toBlock': current_block,
                        'address': Web3.to_checksum_address(pool_address),
                        'topics': [transfer_topic]
                    })
                    
                    for log in logs:
                        if len(log['topics']) >= 3:
                            from_addr = "0x" + log['topics'][1].hex()[-40:]
                            to_addr = "0x" + log['topics'][2].hex()[-40:]
                            amount = int(log['data'].hex(), 16) / 10**18
                            
                            transfer_type = "transfer"
                            if from_addr.lower() == "0x" + "0" * 40:
                                transfer_type = "mint"
                            elif to_addr.lower() == "0x" + "0" * 40:
                                transfer_type = "burn"
                                
                            transfers.append({
                                "pool_address": pool_address,
                                "pool_name": f"{pool_config['token0_symbol']}/{pool_config['token1_symbol']}",
                                "version": "V2",
                                "tx_hash": log['transactionHash'].hex(),
                                "block_number": log['blockNumber'],
                                "from_address": from_addr,
                                "to_address": to_addr,
                                "lp_amount": amount,
                                "transfer_type": transfer_type,
                                "timestamp": datetime.utcnow()
                            })
                            
            logger.info(f"Found {len(transfers)} V2 LP transfers for {pool_config['token0_symbol']}/{pool_config['token1_symbol']}")
            return transfers
            
        except Exception as e:
            logger.error(f"Error fetching V2 transfers: {e}")
            return []
            
    async def fetch_v3_liquidity_events(self, pool_config: Dict, hours: int = 1) -> List[Dict]:
        """Fetch V3 liquidity events"""
        events = []
        try:
            pool_address = pool_config["address"]
            
            # V3 Event signatures
            MINT_TOPIC = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
            BURN_TOPIC = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45e3de096f3d50e8798e28391ffc"
            
            if Web3 is not None:
                w3 = Web3(Web3.HTTPProvider(BSC_RPC))
                if w3.is_connected():
                    current_block = w3.eth.block_number
                    blocks_per_hour = 1200
                    from_block = max(0, current_block - (blocks_per_hour * hours))
                    
                    # Get Mint events
                    mint_logs = w3.eth.get_logs({
                        'fromBlock': from_block,
                        'toBlock': current_block,
                        'address': Web3.to_checksum_address(pool_address),
                        'topics': [MINT_TOPIC]
                    })
                    
                    for log in mint_logs:
                        owner = "0x" + log['topics'][1].hex()[-40:] if len(log['topics']) > 1 else ""
                        events.append({
                            "pool_address": pool_address,
                            "pool_name": f"{pool_config['token0_symbol']}/{pool_config['token1_symbol']}",
                            "version": "V3",
                            "tx_hash": log['transactionHash'].hex(),
                            "block_number": log['blockNumber'],
                            "from_address": "0x" + "0" * 40,
                            "to_address": owner,
                            "transfer_type": "mint",
                            "timestamp": datetime.utcnow()
                        })
                    
                    # Get Burn events
                    burn_logs = w3.eth.get_logs({
                        'fromBlock': from_block,
                        'toBlock': current_block,
                        'address': Web3.to_checksum_address(pool_address),
                        'topics': [BURN_TOPIC]
                    })
                    
                    for log in burn_logs:
                        owner = "0x" + log['topics'][1].hex()[-40:] if len(log['topics']) > 1 else ""
                        events.append({
                            "pool_address": pool_address,
                            "pool_name": f"{pool_config['token0_symbol']}/{pool_config['token1_symbol']}",
                            "version": "V3",
                            "tx_hash": log['transactionHash'].hex(),
                            "block_number": log['blockNumber'],
                            "from_address": owner,
                            "to_address": "0x" + "0" * 40,
                            "transfer_type": "burn",
                            "timestamp": datetime.utcnow()
                        })
                        
            logger.info(f"Found {len(events)} V3 liquidity events for {pool_config['token0_symbol']}/{pool_config['token1_symbol']}")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching V3 events: {e}")
            return []
            
    async def monitor_pools(self):
        """Main monitoring loop for all pools"""
        await self.initialize()
        
        while True:
            try:
                all_lp_activity = []
                
                for pool_name, pool_config in self.pools.items():
                    logger.info(f"Checking {pool_name}...")
                    
                    if pool_config["version"] == "V2":
                        # Fetch V2 LP transfers
                        transfers = await self.fetch_v2_lp_transfers(pool_config, hours=1)
                        all_lp_activity.extend(transfers)
                    else:
                        # Fetch V3 liquidity events
                        events = await self.fetch_v3_liquidity_events(pool_config, hours=1)
                        all_lp_activity.extend(events)
                        
                # Store all LP activity in database
                for activity in all_lp_activity:
                    try:
                        async with self.db_pool.acquire() as conn:
                            await conn.execute("""
                                INSERT INTO multi_pool_lp_activity (
                                    pool_address, pool_name, pool_version,
                                    tx_hash, block_number, from_address, to_address,
                                    transfer_type, lp_amount, timestamp
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                                ON CONFLICT (tx_hash, pool_address) DO NOTHING
                            """,
                                activity["pool_address"],
                                activity["pool_name"],
                                activity["version"],
                                activity["tx_hash"],
                                activity["block_number"],
                                activity["from_address"],
                                activity["to_address"],
                                activity["transfer_type"],
                                activity.get("lp_amount", 0),
                                activity["timestamp"]
                            )
                    except Exception as e:
                        logger.error(f"Error storing LP activity: {e}")
                        
                logger.info(f"Stored {len(all_lp_activity)} LP activities across all pools")
                
                # Wait before next cycle
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
                
async def main():
    monitor = MultiPoolMonitor()
    try:
        await monitor.monitor_pools()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await monitor.close()
        
if __name__ == "__main__":
    asyncio.run(main())