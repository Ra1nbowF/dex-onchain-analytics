"""Check buy vs sell volume data collection"""

import psycopg2
from datetime import datetime, timedelta

conn = psycopg2.connect('postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway')
cur = conn.cursor()

print('BUY VS SELL VOLUME DATA CHECK')
print('='*60)

# Check which tables might have buy/sell volume data
tables_to_check = [
    ('moralis_swaps_correct', 'type', 'amount_usd'),
    ('moralis_token_analytics_correct', 'total_buy_volume_24h', 'total_sell_volume_24h'),
    ('moralis_pair_stats_correct', 'buy_volume_24h', 'sell_volume_24h'),
    ('bsc_trades', 'trade_type', 'usd_value'),
    ('bsc_dex_trades', 'amount0_in', 'amount1_in'),
    ('dex_trades', 'token_in', 'value_usd')
]

print('Checking tables for buy/sell volume data:')
print('-'*60)

for table_info in tables_to_check:
    table = table_info[0]
    columns = table_info[1:] if len(table_info) > 1 else []

    try:
        # First check if table has data
        cur.execute(f'SELECT COUNT(*) FROM {table}')
        count = cur.fetchone()[0]

        if count > 0:
            print(f'\n{table}: {count} rows')

            # Check for buy/sell data based on table structure
            if table == 'moralis_swaps_correct':
                # Check swap types
                cur.execute(f"""
                    SELECT type, COUNT(*), SUM(amount_usd)
                    FROM {table}
                    WHERE timestamp > NOW() - INTERVAL '24 hours'
                    GROUP BY type
                """)
                results = cur.fetchall()
                if results:
                    for swap_type, cnt, volume in results:
                        print(f'  {swap_type or "unknown"}: {cnt} trades, ${float(volume or 0):,.2f} volume')
                else:
                    print('  No data in last 24 hours')

            elif table == 'moralis_token_analytics_correct' and len(columns) >= 2:
                # Check if buy/sell volumes are stored
                cur.execute(f'SELECT {columns[0]}, {columns[1]} FROM {table} ORDER BY timestamp DESC LIMIT 1')
                result = cur.fetchone()
                if result:
                    print(f'  Buy Volume 24h: ${float(result[0] or 0):,.2f}')
                    print(f'  Sell Volume 24h: ${float(result[1] or 0):,.2f}')

            elif table == 'moralis_pair_stats_correct' and len(columns) >= 2:
                cur.execute(f'SELECT {columns[0]}, {columns[1]} FROM {table} ORDER BY timestamp DESC LIMIT 1')
                result = cur.fetchone()
                if result:
                    print(f'  Buy Volume 24h: ${float(result[0] or 0):,.2f}')
                    print(f'  Sell Volume 24h: ${float(result[1] or 0):,.2f}')
        else:
            print(f'{table}: EMPTY')

    except Exception as e:
        if 'does not exist' in str(e):
            print(f'{table}: TABLE/COLUMN DOES NOT EXIST')
        else:
            print(f'{table}: ERROR - {str(e)[:100]}')

# Check Grafana query for buy vs sell volume
print('\n' + '='*60)
print('GRAFANA DASHBOARD REQUIREMENT:')
print('For "Buy vs Sell Volume (24h)" chart, Grafana needs:')
print('1. moralis_pair_stats_correct with buy_volume_24h, sell_volume_24h')
print('2. OR moralis_swaps_correct grouped by type (buy/sell)')
print('3. OR bsc_trades with trade_type column')

# Check what the Grafana dashboard is actually querying
print('\nCHECKING ACTUAL DATA:')
cur.execute("""
    SELECT
        SUM(CASE WHEN type = 'buy' THEN amount_usd ELSE 0 END) as buy_volume,
        SUM(CASE WHEN type = 'sell' THEN amount_usd ELSE 0 END) as sell_volume
    FROM moralis_swaps_correct
    WHERE timestamp > NOW() - INTERVAL '24 hours'
""")
result = cur.fetchone()
if result and (result[0] or result[1]):
    print(f'Last 24h from moralis_swaps_correct:')
    print(f'  Buy Volume: ${float(result[0] or 0):,.2f}')
    print(f'  Sell Volume: ${float(result[1] or 0):,.2f}')
else:
    print('No buy/sell data in last 24 hours')

cur.close()
conn.close()