import psycopg2

conn = psycopg2.connect('postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway')
conn.autocommit = True
cur = conn.cursor()

print('BUY VS SELL VOLUME (24H) ANALYSIS')
print('='*60)

# Check buy vs sell breakdown
cur.execute("""
    SELECT
        transaction_type,
        COUNT(*) as trade_count,
        SUM(CASE
            WHEN transaction_type = 'buy' THEN bought_usd_amount
            WHEN transaction_type = 'sell' THEN sold_usd_amount
            ELSE 0
        END) as volume_usd
    FROM moralis_swaps_correct
    WHERE block_timestamp > NOW() - INTERVAL '24 hours'
    GROUP BY transaction_type
    ORDER BY transaction_type
""")

results = cur.fetchall()
total_buy_volume = 0
total_sell_volume = 0

print('Last 24 hours trading activity:')
for tx_type, count, volume in results:
    if tx_type == 'buy':
        total_buy_volume = float(volume or 0)
        print(f'  BUY:  {count:,} trades, ${total_buy_volume:,.2f}')
    elif tx_type == 'sell':
        total_sell_volume = float(volume or 0)
        print(f'  SELL: {count:,} trades, ${total_sell_volume:,.2f}')

total = total_buy_volume + total_sell_volume
if total > 0:
    buy_pct = (total_buy_volume / total) * 100
    sell_pct = (total_sell_volume / total) * 100
    print(f'\nVolume split:')
    print(f'  Buy:  {buy_pct:.1f}%')
    print(f'  Sell: {sell_pct:.1f}%')
    print(f'  Total 24h Volume: ${total:,.2f}')
else:
    print('\nNo trading volume in last 24 hours')

# Check if data exists but older
cur.execute("""
    SELECT
        COUNT(*) as total_trades,
        MIN(block_timestamp) as oldest,
        MAX(block_timestamp) as newest
    FROM moralis_swaps_correct
""")
count, oldest, newest = cur.fetchone()
print(f'\nTotal data in moralis_swaps_correct:')
print(f'  Total trades: {count}')
print(f'  Data range: {oldest} to {newest}')

cur.close()
conn.close()