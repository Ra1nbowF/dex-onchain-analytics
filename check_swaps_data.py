"""Check what's in the moralis_swaps_correct table"""

import psycopg2
from datetime import datetime

# Railway database connection
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def check_swaps():
    conn = None
    cur = None
    
    try:
        print("Checking Swap Transactions Data")
        print("=" * 70)
        
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()
        
        # Check if moralis_swaps_correct table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'moralis_swaps_correct'
            )
        """)
        exists = cur.fetchone()[0]
        
        if not exists:
            print("[ERROR] Table 'moralis_swaps_correct' does not exist!")
            
            # Check what swap-related tables we have
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND (table_name LIKE '%swap%' OR table_name LIKE '%trade%')
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            
            print("\nAvailable swap/trade tables:")
            for t in tables:
                print(f"  - {t[0]}")
                
                # Get count for each
                cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
                count = cur.fetchone()[0]
                print(f"    Records: {count}")
        else:
            # Check the data in moralis_swaps_correct
            cur.execute("SELECT COUNT(*) FROM moralis_swaps_correct")
            count = cur.fetchone()[0]
            print(f"Total records in moralis_swaps_correct: {count}")
            
            if count > 0:
                # Check sample data
                cur.execute("""
                    SELECT 
                        bought_name,
                        sold_name,
                        pair_label,
                        exchange_name,
                        block_timestamp
                    FROM moralis_swaps_correct
                    ORDER BY block_timestamp DESC
                    LIMIT 10
                """)
                
                swaps = cur.fetchall()
                print("\nRecent swaps (token names):")
                for s in swaps:
                    print(f"  {s[4]}: {s[0]} <-> {s[1]} on {s[3]}")
                    print(f"    Pair: {s[2]}")
        
        # Check BSC trades table (our actual swap data)
        print("\n" + "=" * 70)
        print("BSC Trades Table (Actual Pool Swaps):")
        
        cur.execute("SELECT COUNT(*) FROM bsc_trades")
        count = cur.fetchone()[0]
        print(f"Total records in bsc_trades: {count}")
        
        if count > 0:
            cur.execute("""
                SELECT 
                    token_in,
                    token_out,
                    amount_in,
                    amount_out,
                    price,
                    value_usd,
                    is_buy,
                    timestamp
                FROM bsc_trades
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            
            trades = cur.fetchall()
            print("\nRecent BSC trades:")
            for t in trades:
                token_in = 'BTCB' if t[0].lower().startswith('0x7130') else 'USDT'
                token_out = 'BTCB' if t[1].lower().startswith('0x7130') else 'USDT'
                action = 'BUY' if t[6] else 'SELL'
                print(f"  {t[7]}: {action} - {t[3]:.4f} {token_out} for {t[2]:.4f} {token_in}")
                print(f"    Value: ${t[5]:.2f} USD")
        
        # Summary
        print("\n" + "=" * 70)
        print("ISSUE IDENTIFIED:")
        print("\nThe dashboard is showing data from 'moralis_swaps_correct' table")
        print("This table either:")
        print("  1. Contains old/test data with wrong token names")
        print("  2. Is populated by Moralis API with general swap data (not our pool)")
        print("\nSOLUTION:")
        print("  Update the dashboard to use 'bsc_trades' table instead")
        print("  This table has actual swap data from our BTCB/USDT pool")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_swaps()