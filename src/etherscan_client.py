"""Etherscan API client with rate limiting and multi-chain support"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from aiolimiter import AsyncLimiter
import logging
from src.config import config, CHAIN_CONFIG

logger = logging.getLogger(__name__)


class EtherscanClient:
    """Async client for Etherscan API with rate limiting"""

    def __init__(self):
        self.api_key = config.etherscan_api_key
        # Rate limiter: 5 calls per second
        self.rate_limiter = AsyncLimiter(config.etherscan_rate_limit, 1.0)
        # Daily limit tracking
        self.daily_calls = 0
        self.daily_limit = config.etherscan_daily_limit
        self.last_reset = datetime.now()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _check_daily_limit(self):
        """Check and reset daily limit if needed"""
        now = datetime.now()
        if now - self.last_reset > timedelta(days=1):
            self.daily_calls = 0
            self.last_reset = now

        if self.daily_calls >= self.daily_limit:
            raise Exception(f"Daily API limit reached: {self.daily_limit}")

    async def _make_request(self, chain_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a rate-limited request to Etherscan API"""
        self._check_daily_limit()

        if chain_id not in CHAIN_CONFIG:
            raise ValueError(f"Unsupported chain ID: {chain_id}")

        chain = CHAIN_CONFIG[chain_id]
        url = chain["api_url"]

        # Add API key and chain ID
        params["apikey"] = self.api_key
        params["chainid"] = chain_id

        async with self.rate_limiter:
            try:
                async with self.session.get(url, params=params) as response:
                    self.daily_calls += 1
                    data = await response.json()

                    if data.get("status") == "0":
                        error_msg = data.get("message", "Unknown error")
                        if "rate limit" in error_msg.lower():
                            logger.warning(f"Rate limit hit: {error_msg}")
                            await asyncio.sleep(1)  # Back off
                        raise Exception(f"API Error: {error_msg}")

                    return data

            except Exception as e:
                logger.error(f"Request failed for chain {chain_id}: {e}")
                raise

    async def get_token_transfers(
        self,
        chain_id: int,
        address: str,
        contract_address: Optional[str] = None,
        start_block: int = 0,
        end_block: int = 99999999
    ) -> List[Dict]:
        """Get ERC20 token transfers for an address"""
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "desc"
        }

        if contract_address:
            params["contractaddress"] = contract_address

        result = await self._make_request(chain_id, params)
        return result.get("result", [])

    async def get_transaction_list(
        self,
        chain_id: int,
        address: str,
        start_block: int = 0,
        end_block: int = 99999999
    ) -> List[Dict]:
        """Get normal transactions for an address"""
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "desc"
        }

        result = await self._make_request(chain_id, params)
        return result.get("result", [])

    async def get_token_balance(
        self,
        chain_id: int,
        contract_address: str,
        address: str
    ) -> str:
        """Get ERC20 token balance for an address"""
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": contract_address,
            "address": address,
            "tag": "latest"
        }

        result = await self._make_request(chain_id, params)
        return result.get("result", "0")

    async def get_eth_balance(self, chain_id: int, address: str) -> str:
        """Get native token balance for an address"""
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest"
        }

        result = await self._make_request(chain_id, params)
        return result.get("result", "0")

    async def get_event_logs(
        self,
        chain_id: int,
        address: str,
        topics: Optional[List[str]] = None,
        from_block: int = 0,
        to_block: int = 99999999
    ) -> List[Dict]:
        """Get event logs from a contract"""
        params = {
            "module": "logs",
            "action": "getLogs",
            "address": address,
            "fromBlock": from_block,
            "toBlock": to_block
        }

        # Add topics if provided
        if topics:
            for i, topic in enumerate(topics):
                if topic:
                    params[f"topic{i}"] = topic

        result = await self._make_request(chain_id, params)
        return result.get("result", [])

    async def get_contract_abi(self, chain_id: int, address: str) -> str:
        """Get contract ABI"""
        params = {
            "module": "contract",
            "action": "getabi",
            "address": address
        }

        result = await self._make_request(chain_id, params)
        return result.get("result", "")

    async def get_block_by_timestamp(
        self,
        chain_id: int,
        timestamp: int,
        closest: str = "before"
    ) -> int:
        """Get block number by timestamp"""
        params = {
            "module": "block",
            "action": "getblocknobytime",
            "timestamp": timestamp,
            "closest": closest
        }

        result = await self._make_request(chain_id, params)
        return int(result.get("result", 0))

    async def get_token_info(self, chain_id: int, contract_address: str) -> Dict:
        """Get token information including name, symbol, decimals"""
        # This would require multiple calls or contract interaction
        # For now, return basic structure
        return {
            "address": contract_address,
            "chain_id": chain_id,
            # Additional info would be fetched from contract
        }

    async def get_dex_trades(
        self,
        chain_id: int,
        dex_address: str,
        from_block: int,
        to_block: int
    ) -> List[Dict]:
        """Get DEX swap events"""
        # Uniswap V2/V3 Swap event signature
        swap_topic = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"  # V2
        swap_v3_topic = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"  # V3

        logs = await self.get_event_logs(
            chain_id=chain_id,
            address=dex_address,
            topics=[swap_topic],  # Can be modified for V3
            from_block=from_block,
            to_block=to_block
        )

        return logs

    async def get_multi_chain_balance(
        self,
        address: str,
        chains: Optional[List[int]] = None
    ) -> Dict[int, str]:
        """Get balance across multiple chains"""
        if not chains:
            chains = config.supported_chains

        balances = {}
        for chain_id in chains:
            try:
                balance = await self.get_eth_balance(chain_id, address)
                balances[chain_id] = balance
            except Exception as e:
                logger.error(f"Failed to get balance for chain {chain_id}: {e}")
                balances[chain_id] = "0"

        return balances