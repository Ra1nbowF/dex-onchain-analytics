"""Moralis API Configuration with Multiple Keys"""

# Moralis API Keys - 4 keys with 40K CU/day each = 160K CU/day total
# These keys are rotated automatically when rate limits are hit

MORALIS_API_KEYS = [
    {
        "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjE4MzllMjEzLWFiNTAtNDI5Ny1iMzM3LWVhZDM3MTE5OTJjMSIsIm9yZ0lkIjoiNDcyMjEzIiwidXNlcklkIjoiNDg1NzY4IiwidHlwZUlkIjoiNTE3NjkxZWQtMTlmZC00NTQ5LThjZjYtOWMxMDhlM2E0NTkwIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg3Mjc4MTAsImV4cCI6NDkxNDQ4NzgxMH0.cWOzKINUOPnKRTz5mDJTmBS4JG5ScVu61DtWyMephHo",
        "name": "Key 1",
        "limit": 40000,  # 40K CU/day
        "description": "Original key 1"
    },
    {
        "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImEwZTY5NWEzLTMyMWYtNDg4ZC1hOWE5LTcwNTVkNDk4NmJjZiIsIm9yZ0lkIjoiMjM3NDkyIiwidXNlcklkIjoiMjM4OTk4IiwidHlwZUlkIjoiNjE0ZDkyZDYtOTdmNy00ZDVkLWJiZTktYTViY2UwYjBlZTNjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg2ODQwMDcsImV4cCI6NDkxNDQ0NDAwN30.Wf8nL2zhKaVk0AfobeiF3r57OM_qNYeR9Voc6nenRNk",
        "name": "Key 2",
        "limit": 40000,  # 40K CU/day
        "description": "Original key 2"
    },
    {
        "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImE4MjMzZGUzLTQ4MjQtNDdmNy1iNTUxLWVhMzNlM2I1NzE2ZiIsIm9yZ0lkIjoiNDcyNDQ1IiwidXNlcklkIjoiNDg2MDEwIiwidHlwZUlkIjoiZjM5MTI5ZWYtNThhYS00MDNlLTkxZGYtMDI4ZWNiMWY1NmUzIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg4NDQ0MTYsImV4cCI6NDkxNDYwNDQxNn0.3IpzWsLcfUtVddECU2-nh9vFiBLMwMHcaR3r7cuFCuk",
        "name": "Key 3",
        "limit": 40000,  # 40K CU/day
        "description": "New key 3 (added 2025-09-26)"
    },
    {
        "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImIwNjhhY2M0LTRhYzMtNGM3NS05MzQxLWVhMzRlN2FlYjU0ZCIsIm9yZ0lkIjoiNDcyNDQ2IiwidXNlcklkIjoiNDg2MDExIiwidHlwZUlkIjoiNDc5MTk3ZmUtNzAxZi00ODE1LWJkMGMtYzYwMzY4NTUwYjIwIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTg4NDQ1NDIsImV4cCI6NDkxNDYwNDU0Mn0.822M36Ie7Pjl4tUSyVeJ-sUNGSm93QR1gHQywj0_z2o",
        "name": "Key 4",
        "limit": 40000,  # 40K CU/day
        "description": "New key 4 (added 2025-09-26)"
    }
]

# Extract just the key strings for compatibility
MORALIS_API_KEY_LIST = [k["key"] for k in MORALIS_API_KEYS]

# Rate limiting configuration
MAX_REQUESTS_PER_KEY_PER_HOUR = 1600  # ~40K per day / 24 hours with buffer
KEY_ROTATION_DELAY = 5  # Seconds to wait after rotating through all keys

# Endpoint costs in Compute Units (CU)
ENDPOINT_COSTS = {
    "getTokenPrice": 3,
    "getMultipleTokenPrices": 3,  # per token
    "getPairsByAddress": 5,
    "getPairStats": 5,
    "getWalletTokenBalances": 10,
    "getWalletHistory": 15,
    "getTokenTransfers": 10,
    "getWalletProfitability": 20,
    "getTopProfitableWallets": 25,
    "getTopTokenHolders": 20,
    "getTokenOwners": 10
}

# Calculate daily CU budget
TOTAL_DAILY_CU = len(MORALIS_API_KEYS) * 40000  # 160,000 CU/day with 4 keys
HOURLY_CU_BUDGET = TOTAL_DAILY_CU // 24  # ~6,666 CU/hour

print(f"Moralis Configuration Loaded:")
print(f"  - {len(MORALIS_API_KEYS)} API keys available")
print(f"  - Total daily CU budget: {TOTAL_DAILY_CU:,} CU")
print(f"  - Hourly CU budget: {HOURLY_CU_BUDGET:,} CU")