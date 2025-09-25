"""Fix buy/sell volume data for Grafana dashboard"""

import psycopg2

conn = psycopg2.connect('postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway')
cur = conn.cursor()

print("Fixing Buy vs Sell Volume data...")
print("="*60)

# Check if total_value_usd column exists
cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'moralis_swaps_correct'
    AND column_name = 'total_value_usd'
""")

if not cur.fetchone():
    print("Adding total_value_usd column...")
    try:
        cur.execute("""
            ALTER TABLE moralis_swaps_correct
            ADD COLUMN IF NOT EXISTS total_value_usd NUMERIC(20, 2)
        """)
        conn.commit()
        print("[OK] Added total_value_usd column")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to add column: {e}")

# Update total_value_usd based on transaction type
print("\nUpdating total_value_usd values...")
try:
    # For buy transactions, use bought_usd_amount (make positive)
    cur.execute("""
        UPDATE moralis_swaps_correct
        SET total_value_usd = ABS(bought_usd_amount)
        WHERE transaction_type = 'buy'
        AND total_value_usd IS NULL
    """)
    buy_count = cur.rowcount
    print(f"[OK] Updated {buy_count} buy transactions")

    # For sell transactions, use sold_usd_amount (make positive)
    cur.execute("""
        UPDATE moralis_swaps_correct
        SET total_value_usd = ABS(sold_usd_amount)
        WHERE transaction_type = 'sell'
        AND total_value_usd IS NULL
    """)
    sell_count = cur.rowcount
    print(f"[OK] Updated {sell_count} sell transactions")

    conn.commit()

    # Verify the data
    print("\nVerifying data for Grafana query:")
    cur.execute("""
        SELECT
            DATE_TRUNC('hour', block_timestamp) as hour,
            SUM(CASE WHEN transaction_type = 'buy' THEN total_value_usd ELSE 0 END) as buy_vol,
            SUM(CASE WHEN transaction_type = 'sell' THEN total_value_usd ELSE 0 END) as sell_vol
        FROM moralis_swaps_correct
        WHERE block_timestamp > NOW() - INTERVAL '24 hours'
        GROUP BY 1
        ORDER BY 1 DESC
        LIMIT 5
    """)

    print("\nHourly Buy vs Sell Volume (last 5 hours):")
    for hour, buy_vol, sell_vol in cur.fetchall():
        buy_val = float(buy_vol or 0)
        sell_val = float(sell_vol or 0)
        total = buy_val + sell_val
        if total > 0:
            buy_pct = (buy_val / total) * 100
            sell_pct = (sell_val / total) * 100
            print(f"  {hour}: Buy ${buy_val:,.0f} ({buy_pct:.1f}%) | Sell ${sell_val:,.0f} ({sell_pct:.1f}%)")
        else:
            print(f"  {hour}: No volume")

    print("\n" + "="*60)
    print("SUCCESS: Buy vs Sell Volume data fixed for Grafana!")
    print("The dashboard should now show the volume correctly.")

except Exception as e:
    conn.rollback()
    print(f"[ERROR] Failed to update data: {e}")

cur.close()
conn.close()