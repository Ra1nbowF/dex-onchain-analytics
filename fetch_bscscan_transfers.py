"""Fetch token transfers from BscScan API for BTCB and USDT"""

import requests
import psycopg2
from datetime import datetime
import time
import os

# BscScan API configuration
BSCSCAN_API_KEY = "YOUR_API_KEY_HERE"  # You need to get this from BscScan
BSCSCAN_API_URL = "https://api.bscscan.com/api"

# Token addresses
BTCB_ADDRESS = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"
POOL_ADDRESS = "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4"

# Railway database connection
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def fetch_token_transfers(token_address, token_name):
    """Fetch ERC20 token transfer events from BscScan"""

    print(f"\nFetching {token_name} transfers...")
    print("-" * 50)

    transfers = []

    # Get transfers TO the pool
    params = {
        'module': 'account',
        'action': 'tokentx',
        'contractaddress': token_address,
        'address': POOL_ADDRESS,
        'page': 1,
        'offset': 100,
        'sort': 'desc',
        'apikey': BSCSCAN_API_KEY
    }

    try:
        response = requests.get(BSCSCAN_API_URL, params=params)
        data = response.json()

        if data['status'] == '1' and data['result']:
            print(f"Found {len(data['result'])} transfers involving the pool")

            for tx in data['result']:
                transfers.append({
                    'tx_hash': tx['hash'],
                    'block_number': int(tx['blockNumber']),
                    'timestamp': datetime.fromtimestamp(int(tx['timeStamp'])),
                    'from_address': tx['from'].lower(),
                    'to_address': tx['to'].lower(),
                    'value': int(tx['value']) / 10**int(tx['tokenDecimal']),
                    'token_address': token_address.lower(),
                    'token_name': token_name,
                    'token_symbol': tx['tokenSymbol'],
                    'gas_used': int(tx['gasUsed']) if 'gasUsed' in tx else 0,
                    'is_pool_related': True
                })
        else:
            print(f"No transfers found or API error: {data.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"Error fetching {token_name} transfers: {e}")

    # Also get recent token transfers (not just pool-related)
    time.sleep(0.5)  # Rate limiting

    params = {
        'module': 'account',
        'action': 'tokentx',
        'contractaddress': token_address,
        'startblock': 0,
        'endblock': 99999999,
        'page': 1,
        'offset': 50,
        'sort': 'desc',
        'apikey': BSCSCAN_API_KEY
    }

    try:
        response = requests.get(BSCSCAN_API_URL, params=params)
        data = response.json()

        if data['status'] == '1' and data['result']:
            print(f"Found {len(data['result'])} recent {token_name} transfers")

            for tx in data['result']:
                # Check if this transfer involves the pool
                is_pool = (tx['from'].lower() == POOL_ADDRESS.lower() or
                          tx['to'].lower() == POOL_ADDRESS.lower())

                transfers.append({
                    'tx_hash': tx['hash'],
                    'block_number': int(tx['blockNumber']),
                    'timestamp': datetime.fromtimestamp(int(tx['timeStamp'])),
                    'from_address': tx['from'].lower(),
                    'to_address': tx['to'].lower(),
                    'value': int(tx['value']) / 10**int(tx['tokenDecimal']),
                    'token_address': token_address.lower(),
                    'token_name': token_name,
                    'token_symbol': tx['tokenSymbol'],
                    'gas_used': int(tx['gasUsed']) if 'gasUsed' in tx else 0,
                    'is_pool_related': is_pool
                })

    except Exception as e:
        print(f"Error fetching recent transfers: {e}")

    return transfers

def store_transfers(transfers):
    """Store transfers in the database"""

    if not transfers:
        print("No transfers to store")
        return

    conn = None
    cur = None

    try:
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()

        # Insert transfers (table already exists with specific schema)
        inserted = 0
        for transfer in transfers:
            try:
                # Calculate USD value
                if transfer['token_name'] == 'BTCB':
                    value_usd = transfer['value'] * 70000  # Approximate BTC price
                else:  # USDT
                    value_usd = transfer['value']

                # Determine transfer type
                if transfer['from_address'] == POOL_ADDRESS.lower():
                    transfer_type = 'OUT'
                elif transfer['to_address'] == POOL_ADDRESS.lower():
                    transfer_type = 'IN'
                else:
                    transfer_type = 'TRANSFER'

                cur.execute("""
                    INSERT INTO bsc_token_transfers (
                        tx_hash, block_number, timestamp, token_address, token_symbol,
                        from_address, to_address, amount, value_usd, is_pool_related,
                        transfer_type, gas_used
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    transfer['tx_hash'],
                    transfer['block_number'],
                    transfer['timestamp'],
                    transfer['token_address'],
                    transfer['token_symbol'],
                    transfer['from_address'],
                    transfer['to_address'],
                    transfer['value'],
                    value_usd,
                    transfer['is_pool_related'],
                    transfer_type,
                    transfer['gas_used']
                ))

                if cur.rowcount > 0:
                    inserted += 1

            except Exception as e:
                print(f"Error inserting transfer: {e}")
                continue

        conn.commit()
        print(f"Successfully inserted {inserted} new transfers")

        # Show statistics
        cur.execute("""
            SELECT
                token_symbol,
                COUNT(*) as count,
                COUNT(CASE WHEN is_pool_related THEN 1 END) as pool_related,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM bsc_token_transfers
            GROUP BY token_symbol
        """)

        print("\nTransfer Statistics:")
        print("-" * 50)
        for row in cur.fetchall():
            print(f"{row[0]}: {row[1]} total, {row[2]} pool-related")
            print(f"  Range: {row[3]} to {row[4]}")

    except Exception as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def main():
    print("=" * 70)
    print("Fetching BTCB Token Transfers from BscScan")
    print("=" * 70)

    # Check if API key is set
    if BSCSCAN_API_KEY == "YOUR_API_KEY_HERE":
        print("\n[ERROR] Please set your BscScan API key in the script!")
        print("Get your free API key from: https://bscscan.com/apis")
        print("\nAlternatively, using blockchain method...")

        # Alternative: fetch without API (limited)
        fetch_transfers_no_api()
        return

    # Fetch transfers for BTCB only (relevant for BTCB/USDT pool)
    all_transfers = []

    btcb_transfers = fetch_token_transfers(BTCB_ADDRESS, "BTCB")
    all_transfers.extend(btcb_transfers)

    # Store in database
    if all_transfers:
        print(f"\nTotal BTCB transfers collected: {len(all_transfers)}")
        store_transfers(all_transfers)
    else:
        print("\nNo transfers collected")

def fetch_transfers_no_api():
    """Alternative method: fetch from blockchain directly - BTCB only"""
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware

    print("\nFetching BTCB transfers directly from blockchain...")

    # Connect to BSC
    rpc_url = "https://bsc.publicnode.com"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # ERC20 Transfer event signature
    TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

    current_block = w3.eth.block_number
    from_block = current_block - 10000  # Last ~8 hours for more BTCB data

    transfers = []

    # Only fetch BTCB transfers
    print(f"\nFetching BTCB transfers...")

    # Get Transfer events
    logs = w3.eth.get_logs({
        'fromBlock': from_block,
        'toBlock': current_block,
        'address': Web3.to_checksum_address(BTCB_ADDRESS),
        'topics': [TRANSFER_TOPIC]
    })

    print(f"Found {len(logs)} BTCB transfer events")

    # Process last 100 BTCB transfers
    for log in logs[-100:]:  # Process last 100 BTCB transfers
        # Topics: [signature, from, to]
        from_addr = "0x" + log['topics'][1].hex()[-40:]
        to_addr = "0x" + log['topics'][2].hex()[-40:]

        # Check if pool-related
        is_pool = (from_addr.lower() == POOL_ADDRESS.lower() or
                  to_addr.lower() == POOL_ADDRESS.lower())

        # Decode amount
        amount_hex = log['data'].hex() if isinstance(log['data'], bytes) else log['data'][2:]
        amount = int(amount_hex, 16) / 10**18 if amount_hex else 0

        # Get block timestamp
        block = w3.eth.get_block(log['blockNumber'])
        timestamp = datetime.fromtimestamp(block['timestamp'])

        transfers.append({
            'tx_hash': log['transactionHash'].hex(),
            'block_number': log['blockNumber'],
            'timestamp': timestamp,
            'from_address': from_addr.lower(),
            'to_address': to_addr.lower(),
            'value': amount,
            'token_address': BTCB_ADDRESS.lower(),
            'token_name': 'BTCB',
            'token_symbol': 'BTCB',
            'gas_used': 0,  # Would need receipt for this
            'is_pool_related': is_pool
        })

    if transfers:
        print(f"\nCollected {len(transfers)} transfers")
        store_transfers(transfers)
    else:
        print("\nNo transfers found")

if __name__ == "__main__":
    main()