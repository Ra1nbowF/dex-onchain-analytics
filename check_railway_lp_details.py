"""Check detailed LP data in Railway database"""

import psycopg2
from datetime import datetime

# Railway database connection
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def check_lp_details():
    conn = None
    cur = None
    
    try:
        print("Detailed LP Data Analysis")
        print("=" * 70)
        
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()
        
        # 1. Check LP token transfers with all fields
        print("1. LP Token Transfer Details:")
        print("-" * 50)
        cur.execute("""
            SELECT 
                tx_hash,
                from_address,
                to_address,
                lp_amount,
                btcb_amount,
                usdt_amount,
                total_value_usd,
                transfer_type,
                pool_share_percent,
                timestamp
            FROM bsc_lp_token_transfers
            ORDER BY timestamp DESC
            LIMIT 3
        """)
        transfers = cur.fetchall()
        
        for i, t in enumerate(transfers, 1):
            print(f"\nTransfer {i}:")
            print(f"  TX Hash: {t[0][:10]}...")
            print(f"  Type: {t[7]}")
            print(f"  From: {t[1][:10]}...")
            print(f"  To: {t[2][:10]}...")
            print(f"  LP Amount: {t[3]}")
            print(f"  BTCB Amount: {t[4]}")
            print(f"  USDT Amount: {t[5]}")
            print(f"  Total Value USD: ${t[6]}")
            print(f"  Pool Share %: {t[8]}")
            print(f"  Timestamp: {t[9]}")
        
        # 2. Check unique transfer types
        print("\n2. Transfer Types Distribution:")
        print("-" * 50)
        cur.execute("""
            SELECT transfer_type, COUNT(*) as cnt
            FROM bsc_lp_token_transfers
            GROUP BY transfer_type
            ORDER BY cnt DESC
        """)
        types = cur.fetchall()
        for t in types:
            print(f"  {t[0]}: {t[1]} transfers")
        
        # 3. Check if amounts are all zero
        print("\n3. Non-Zero LP Amounts:")
        print("-" * 50)
        cur.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN lp_amount > 0 THEN 1 END) as non_zero,
                   AVG(lp_amount) as avg_amount,
                   MAX(lp_amount) as max_amount
            FROM bsc_lp_token_transfers
        """)
        result = cur.fetchone()
        print(f"  Total transfers: {result[0]}")
        print(f"  Non-zero amounts: {result[1]}")
        print(f"  Average LP amount: {result[2]}")
        print(f"  Max LP amount: {result[3]}")
        
        # 4. Check LP holders details
        print("\n4. LP Holders Details:")
        print("-" * 50)
        cur.execute("""
            SELECT 
                wallet_address,
                lp_balance,
                pool_share_percent,
                btcb_value,
                usdt_value,
                total_value_usd,
                first_provided,
                last_updated
            FROM bsc_lp_holders
            ORDER BY total_value_usd DESC
            LIMIT 3
        """)
        holders = cur.fetchall()
        
        for i, h in enumerate(holders, 1):
            print(f"\nHolder {i}:")
            print(f"  Wallet: {h[0][:10]}...{h[0][-4:]}")
            print(f"  LP Balance: {h[1]}")
            print(f"  Pool Share: {h[2]}%")
            print(f"  BTCB Value: {h[3]}")
            print(f"  USDT Value: {h[4]}")
            print(f"  Total USD: ${h[5]}")
            print(f"  Last Updated: {h[7]}")
        
        # 5. Check distinct addresses involved
        print("\n5. Unique Addresses:")
        print("-" * 50)
        cur.execute("""
            SELECT COUNT(DISTINCT from_address) as unique_from,
                   COUNT(DISTINCT to_address) as unique_to
            FROM bsc_lp_token_transfers
        """)
        result = cur.fetchone()
        print(f"  Unique FROM addresses: {result[0]}")
        print(f"  Unique TO addresses: {result[1]}")
        
        # Check for null address (mints/burns)
        cur.execute("""
            SELECT COUNT(*) 
            FROM bsc_lp_token_transfers 
            WHERE from_address = '0x0000000000000000000000000000000000000000'
        """)
        mints = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) 
            FROM bsc_lp_token_transfers 
            WHERE to_address = '0x0000000000000000000000000000000000000000'
        """)
        burns = cur.fetchone()[0]
        
        print(f"  Mints (from 0x0): {mints}")
        print(f"  Burns (to 0x0): {burns}")
        
        # 6. Summary
        print("\n" + "=" * 70)
        print("ANALYSIS SUMMARY:")
        
        if result[0] == 0 and result[1] == 0:
            print("\n[ISSUE] All LP amounts are 0!")
            print("Possible causes:")
            print("  1. V3 pool doesn't use fungible LP tokens (uses NFTs instead)")
            print("  2. Decoding issue - amounts not being calculated correctly")
            print("  3. Wrong LP token address")
            print("  4. Pool has very small liquidity")
        
        if mints == 40:
            print("\n[PATTERN] All transfers are mints from 0x0")
            print("This suggests V3 liquidity events being tracked as LP transfers")
            print("V3 uses NFT positions, not fungible tokens")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_lp_details()