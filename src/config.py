"""Configuration management for DEX onchain analytics"""

import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseSettings, Field

load_dotenv()

class Config(BaseSettings):
    """Application configuration"""

    # Etherscan API
    etherscan_api_key: str = Field(default=os.getenv("ETHERSCAN_API_KEY"))
    etherscan_app_name: str = Field(default=os.getenv("ETHERSCAN_APP_NAME", "analytics"))
    etherscan_rate_limit: int = Field(default=int(os.getenv("ETHERSCAN_RATE_LIMIT_PER_SECOND", "5")))
    etherscan_daily_limit: int = Field(default=int(os.getenv("ETHERSCAN_DAILY_LIMIT", "100000")))

    # Database
    database_url: str = Field(default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/dex_analytics"))

    # Chains
    supported_chains: List[int] = Field(default_factory=lambda: [
        int(x) for x in os.getenv("SUPPORTED_CHAINS", "1,56,137").split(",")
    ])

    # Logging
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    class Config:
        env_file = ".env"

# Chain configurations
CHAIN_CONFIG = {
    1: {
        "name": "Ethereum",
        "symbol": "ETH",
        "api_url": "https://api.etherscan.io/v2/api",
        "explorer": "https://etherscan.io",
        "dex_factories": {
            "uniswap_v2": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
            "uniswap_v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
            "sushiswap": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
        }
    },
    56: {
        "name": "BSC",
        "symbol": "BNB",
        "api_url": "https://api.bscscan.com/v2/api",
        "explorer": "https://bscscan.com",
        "dex_factories": {
            "pancakeswap_v2": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
            "pancakeswap_v3": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
        }
    },
    137: {
        "name": "Polygon",
        "symbol": "MATIC",
        "api_url": "https://api.polygonscan.com/v2/api",
        "explorer": "https://polygonscan.com",
        "dex_factories": {
            "quickswap": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
            "uniswap_v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
        }
    },
    42161: {
        "name": "Arbitrum",
        "symbol": "ETH",
        "api_url": "https://api.arbiscan.io/v2/api",
        "explorer": "https://arbiscan.io",
        "dex_factories": {
            "uniswap_v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
            "sushiswap": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
        }
    },
    10: {
        "name": "Optimism",
        "symbol": "ETH",
        "api_url": "https://api-optimistic.etherscan.io/v2/api",
        "explorer": "https://optimistic.etherscan.io",
        "dex_factories": {
            "uniswap_v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
            "velodrome": "0x25CbdDb98b35ab1FF77413456B31EC81A6B6B746"
        }
    },
    8453: {
        "name": "Base",
        "symbol": "ETH",
        "api_url": "https://api.basescan.org/v2/api",
        "explorer": "https://basescan.org",
        "dex_factories": {
            "uniswap_v3": "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
            "aerodrome": "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
        }
    },
    43114: {
        "name": "Avalanche",
        "symbol": "AVAX",
        "api_url": "https://api.snowtrace.io/v2/api",
        "explorer": "https://snowtrace.io",
        "dex_factories": {
            "traderjoe_v2": "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10",
            "pangolin": "0xefa94DE7a4656D787667C749f7E1223D71E9FD88"
        }
    }
}

config = Config()