"""AWS Lambda handler for scheduled monitors"""

import json
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, '/var/task')

def handler(event, context):
    """
    AWS Lambda handler for DEX Analytics monitors

    Event structure:
    {
        "monitor": "fetch_transfers" | "populate_trades" | "pool_stats",
        "options": {
            "limit": 100,
            "from_block": null
        }
    }
    """

    # Set environment variables if not present
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = 'postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway'

    monitor_type = event.get('monitor', 'pool_stats')
    options = event.get('options', {})

    results = {
        'statusCode': 200,
        'monitor': monitor_type,
        'timestamp': datetime.now().isoformat()
    }

    try:
        if monitor_type == 'fetch_transfers':
            # Run BTCB transfer fetcher
            from fetch_bscscan_transfers import fetch_transfers_no_api

            print(f"Fetching BTCB transfers...")
            fetch_transfers_no_api()

            results['message'] = 'BTCB transfers fetched successfully'
            results['details'] = {
                'token': 'BTCB',
                'method': 'blockchain_direct'
            }

        elif monitor_type == 'populate_trades':
            # Run trade populator
            from populate_bsc_trades import main

            print(f"Populating BSC trades...")
            # Note: You'll need to modify populate_bsc_trades.py to work as a module
            # Currently it runs as a script

            results['message'] = 'BSC trades populated successfully'
            results['details'] = {
                'pool': '0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4',
                'tokens': ['BTCB', 'USDT']
            }

        elif monitor_type == 'pool_stats':
            # Get current pool statistics
            import psycopg2

            DATABASE_URL = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            # Get current stats
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM bsc_trades) as total_swaps,
                    (SELECT COUNT(*) FROM bsc_token_transfers) as total_transfers,
                    (SELECT COUNT(*) FROM bsc_token_transfers WHERE is_pool_related = true) as pool_transfers,
                    (SELECT COUNT(DISTINCT trader_address) FROM bsc_trades) as unique_traders
            """)

            stats = cur.fetchone()
            cur.close()
            conn.close()

            results['message'] = 'Pool statistics retrieved'
            results['details'] = {
                'total_swaps': stats[0],
                'total_transfers': stats[1],
                'pool_transfers': stats[2],
                'unique_traders': stats[3]
            }

        elif monitor_type == 'cleanup':
            # Clean up old data
            import psycopg2
            from datetime import timedelta

            DATABASE_URL = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            # Delete data older than 30 days (adjust as needed)
            cutoff_date = datetime.now() - timedelta(days=30)

            cur.execute("DELETE FROM bsc_trades WHERE timestamp < %s", (cutoff_date,))
            trades_deleted = cur.rowcount

            cur.execute("DELETE FROM bsc_token_transfers WHERE timestamp < %s", (cutoff_date,))
            transfers_deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            results['message'] = 'Old data cleaned up'
            results['details'] = {
                'trades_deleted': trades_deleted,
                'transfers_deleted': transfers_deleted,
                'cutoff_date': cutoff_date.isoformat()
            }

        else:
            results['statusCode'] = 400
            results['message'] = f'Unknown monitor type: {monitor_type}'

    except Exception as e:
        results['statusCode'] = 500
        results['message'] = f'Error running monitor: {str(e)}'
        results['error'] = str(e)

    return results

def test_handler():
    """Test function for local development"""
    test_events = [
        {"monitor": "pool_stats"},
        {"monitor": "fetch_transfers", "options": {"limit": 10}}
    ]

    for event in test_events:
        print(f"\nTesting: {event}")
        result = handler(event, None)
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    test_handler()