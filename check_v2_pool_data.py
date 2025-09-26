"""Check if V2 pool (WBNB/USDT) would have LP data"""

import psycopg2
from datetime import datetime

# Railway database connection
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def check_v2_pool():
    conn = None
    cur = None
    
    try:
        print("Checking for V2 Pool Data (WBNB/USDT)")
        print("=" * 70)
        print("V2 Pool Address: 0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae")
        print("V2 pools have fungible LP tokens (same address as pool)")
        print()
        
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()
        
        # Check if multi-pool monitor has collected any V2 data
        print("1. Multi-Pool LP Activity:")
        print("-" * 50)
        
        # Check for WBNB/USDT pool specifically
        cur.execute("""
            SELECT COUNT(*) 
            FROM multi_pool_lp_activity 
            WHERE pool_address = '0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae'
               OR pool_name LIKE '%WBNB%'
        """)
        v2_count = cur.fetchone()[0]
        print(f"   WBNB/USDT V2 pool records: {v2_count}")
        
        if v2_count > 0:
            cur.execute("""
                SELECT pool_name, pool_version, transfer_type, COUNT(*) as cnt
                FROM multi_pool_lp_activity
                WHERE pool_name LIKE '%WBNB%'
                GROUP BY pool_name, pool_version, transfer_type
            """)
            results = cur.fetchall()
            print("\n   Activity breakdown:")
            for r in results:
                print(f"     {r[0]} ({r[1]}): {r[2]} - {r[3]} events")
        else:
            print("   [NO DATA] Multi-pool monitor not collecting V2 data")
        
        # Check current pool being monitored
        print("\n2. Current BSC Pool Monitor (V3 BTCB/USDT):")
        print("-" * 50)
        cur.execute("""
            SELECT 
                pool_address,
                COUNT(*) as metrics_count,
                MAX(timestamp) as last_update
            FROM bsc_pool_metrics
            GROUP BY pool_address
        """)
        pools = cur.fetchall()
        
        for p in pools:
            print(f"   Pool: {p[0]}")
            print(f"   Metrics: {p[1]} records")
            print(f"   Last update: {p[2]}")
            
            if p[0].lower() == '0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4':
                print("   [INFO] This is the V3 BTCB/USDT pool")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY:")
        print()
        print("Current situation:")
        print("  - BSC monitor is tracking V3 BTCB/USDT pool")
        print("  - V3 pools use NFT positions (not fungible LP tokens)")
        print("  - That's why LP amounts are 0")
        print()
        print("To get real LP data:")
        print("  1. Deploy bsc_multi_pool_monitor.py")
        print("  2. It will track WBNB/USDT V2 pool")
        print("  3. V2 pools have real LP token transfers")
        print()
        print("Deployment needed:")
        print("  - Add bsc_multi_pool_monitor.py to collector.py")
        print("  - Or run it as a separate service")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_v2_pool()