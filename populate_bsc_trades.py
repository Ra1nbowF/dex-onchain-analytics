"""Populate bsc_trades table with recent swap data from BTCB/USDT pool"""

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import psycopg2
from datetime import datetime
import json

# Connect to BSC
rpc_url = "https://bsc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

# BSC is a POA chain, need to inject middleware
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Railway database connection
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

print("Fetching swap events from BTCB/USDT pool...")
print("=" * 70)

# Pool and token addresses
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"
BTCB_ADDRESS = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"

# V3 Swap event signature (BSC PancakeSwap V3 specific)
SWAP_TOPIC = "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83"

# Get recent blocks
current_block = w3.eth.block_number
from_block = current_block - 5000  # Last ~4 hours

# Fetch swap logs
swap_logs = w3.eth.get_logs({
    'fromBlock': from_block,
    'toBlock': current_block,
    'address': Web3.to_checksum_address(POOL_ADDRESS),
    'topics': [SWAP_TOPIC]
})

print(f"Found {len(swap_logs)} swap events")

if swap_logs:
    conn = None
    cur = None

    try:
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()

        # Clear existing data
        cur.execute("DELETE FROM bsc_trades")
        print("Cleared existing bsc_trades data")

        swaps_inserted = 0

        for log in swap_logs[-100:]:  # Process last 100 swaps
            try:
                # Get block timestamp
                block = w3.eth.get_block(log['blockNumber'])
                timestamp = datetime.fromtimestamp(block['timestamp'])

                # Topic[0] = event signature
                # Topic[1] = sender address (indexed)
                # Topic[2] = recipient address (indexed)

                sender = "0x" + log['topics'][1].hex()[-40:]
                recipient = "0x" + log['topics'][2].hex()[-40:]

                # Data contains: amount0, amount1 (and possibly more parameters)
                data_hex = log['data'].hex() if isinstance(log['data'], bytes) else log['data'][2:]

                if len(data_hex) < 128:
                    continue  # Skip if not enough data

                # Decode amounts (int256 values, can be negative)
                amount0_hex = data_hex[0:64]
                amount1_hex = data_hex[64:128]

                # Convert to signed integers
                amount0_raw = int(amount0_hex, 16)
                if amount0_raw > 2**255:
                    amount0_raw = amount0_raw - 2**256

                amount1_raw = int(amount1_hex, 16)
                if amount1_raw > 2**255:
                    amount1_raw = amount1_raw - 2**256

                # Convert to decimals (both tokens have 18 decimals)
                amount0 = abs(amount0_raw) / 10**18  # BTCB
                amount1 = abs(amount1_raw) / 10**18  # USDT

                # Determine trade direction
                # BTCB is token0, USDT is token1
                # If amount0 is negative, BTCB goes OUT (user SELLS BTCB)
                # If amount0 is positive, BTCB comes IN (user BUYS BTCB)
                # If amount1 is negative, USDT goes OUT (user BUYS with USDT)
                # If amount1 is positive, USDT comes IN (user SELLS for USDT)

                if amount0_raw < 0:
                    # BTCB going out, USDT coming in = SELLING BTCB for USDT
                    is_buy = False
                    token_in = BTCB_ADDRESS
                    token_out = USDT_ADDRESS
                    amount_in = amount0
                    amount_out = amount1
                else:
                    # BTCB coming in, USDT going out = BUYING BTCB with USDT
                    is_buy = True
                    token_in = USDT_ADDRESS
                    token_out = BTCB_ADDRESS
                    amount_in = amount1
                    amount_out = amount0

                # Calculate price and value
                if amount0 > 0:
                    price = amount1 / amount0  # USDT per BTCB
                else:
                    price = 0

                # Estimate value in USD (USDT ≈ $1)
                value_usd = amount1

                # Get gas used from transaction receipt
                tx_receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
                gas_used = tx_receipt['gasUsed']

                # Insert into database
                cur.execute("""
                    INSERT INTO bsc_trades (
                        tx_hash, block_number, trader_address,
                        token_in, token_out, amount_in, amount_out,
                        price, value_usd, gas_used, slippage, is_buy, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    log['transactionHash'].hex(),
                    log['blockNumber'],
                    recipient,  # Use recipient as trader
                    token_in.lower(),
                    token_out.lower(),
                    amount_in,
                    amount_out,
                    price,
                    value_usd,
                    gas_used,
                    0,  # Slippage calculation would need expected price
                    is_buy,
                    timestamp
                ))

                swaps_inserted += 1

                if swaps_inserted <= 5:
                    action = "BUY" if is_buy else "SELL"
                    print(f"  {timestamp}: {action} {amount_out:.6f} {'BTCB' if is_buy else 'USDT'} for {amount_in:.2f} {'USDT' if is_buy else 'BTCB'}")

            except Exception as e:
                print(f"Error processing swap: {e}")
                continue

        conn.commit()
        print(f"\nSuccessfully inserted {swaps_inserted} swap transactions into bsc_trades")

        # Verify data
        cur.execute("SELECT COUNT(*) FROM bsc_trades")
        count = cur.fetchone()[0]
        print(f"Total records in bsc_trades: {count}")

    except Exception as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    print("\n[SUCCESS] Dashboard should now show swap data!")
    print("Refresh your Grafana dashboard to see the Recent Swap Transactions.")

else:
    print("No swap events found in the specified range")
    print("The pool might have low activity.")