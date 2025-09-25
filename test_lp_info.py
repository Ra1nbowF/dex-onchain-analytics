"""Get basic LP token information"""

import asyncio
from web3 import Web3
import json

LP_TOKEN_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BTCB_ADDRESS = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"

# Minimal ERC20 ABI for basic functions
ERC20_ABI = json.loads('[{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')

async def check_lp_info():
    # Connect to BSC
    w3 = Web3(Web3.HTTPProvider("https://bsc.publicnode.com"))

    if not w3.is_connected():
        print("Failed to connect to BSC")
        return

    print(f"Connected to BSC. Latest block: {w3.eth.block_number}")
    print("=" * 50)

    # Get LP token contract
    lp_contract = w3.eth.contract(
        address=Web3.to_checksum_address(LP_TOKEN_ADDRESS),
        abi=ERC20_ABI
    )

    # Get BTCB and USDT contracts
    btcb_contract = w3.eth.contract(
        address=Web3.to_checksum_address(BTCB_ADDRESS),
        abi=ERC20_ABI
    )

    usdt_contract = w3.eth.contract(
        address=Web3.to_checksum_address(USDT_ADDRESS),
        abi=ERC20_ABI
    )

    try:
        # Get LP token info
        print("\nLP Token Information:")
        print(f"Address: {LP_TOKEN_ADDRESS}")

        try:
            name = lp_contract.functions.name().call()
            print(f"Name: {name}")
        except:
            print("Name: Unable to fetch")

        try:
            symbol = lp_contract.functions.symbol().call()
            print(f"Symbol: {symbol}")
        except:
            print("Symbol: Unable to fetch")

        try:
            decimals = lp_contract.functions.decimals().call()
            print(f"Decimals: {decimals}")
        except:
            decimals = 18
            print(f"Decimals: {decimals} (assumed)")

        try:
            total_supply = lp_contract.functions.totalSupply().call() / 10**decimals
            print(f"Total Supply: {total_supply:.6f}")
        except:
            print("Total Supply: Unable to fetch")

        # Get pool reserves (tokens held by the LP contract)
        print("\nPool Reserves:")

        try:
            btcb_balance = btcb_contract.functions.balanceOf(Web3.to_checksum_address(LP_TOKEN_ADDRESS)).call() / 10**18
            print(f"BTCB: {btcb_balance:.6f}")
        except Exception as e:
            print(f"BTCB: Unable to fetch - {e}")

        try:
            usdt_balance = usdt_contract.functions.balanceOf(Web3.to_checksum_address(LP_TOKEN_ADDRESS)).call() / 10**18
            print(f"USDT: {usdt_balance:.2f}")
        except Exception as e:
            print(f"USDT: Unable to fetch - {e}")

        # Calculate pool value
        btcb_price = 70000  # Approximate
        if 'btcb_balance' in locals() and 'usdt_balance' in locals():
            total_value = (btcb_balance * btcb_price) + usdt_balance
            print(f"\nEstimated Pool Value: ${total_value:,.2f}")

            if 'total_supply' in locals() and total_supply > 0:
                lp_price = total_value / total_supply
                print(f"LP Token Price: ${lp_price:.2f}")

    except Exception as e:
        print(f"Error: {e}")

asyncio.run(check_lp_info())