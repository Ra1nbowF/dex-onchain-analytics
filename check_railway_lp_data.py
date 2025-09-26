"""Check LP data in Railway database"""

import psycopg2
from datetime import datetime, timedelta

# Railway database connection
RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def check_lp_data():
    conn = None
    cur = None
    
    try:
        print("Checking LP Data in Railway Database")
        print("=" * 70)
        
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()
        
        now = datetime.utcnow()
        print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
        
        # 1. Check bsc_liquidity_events (V2 style events)
        print("1. BSC Liquidity Events (bsc_liquidity_events):")
        print("-" * 50)
        cur.execute("SELECT COUNT(*) FROM bsc_liquidity_events")
        count = cur.fetchone()[0]
        print(f"   Total records: {count}")
        
        if count > 0:
            cur.execute("""
                SELECT event_type, provider_address, btcb_amount, usdt_amount, timestamp
                FROM bsc_liquidity_events
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            recent = cur.fetchall()
            print("   Recent events:")
            for r in recent:
                print(f"     {r[4]}: {r[0]} - BTCB: {r[2]:.4f}, USDT: {r[3]:.0f}")
        else:
            print("   [NO DATA]")
        
        # 2. Check bsc_lp_token_transfers
        print("\n2. LP Token Transfers (bsc_lp_token_transfers):")
        print("-" * 50)
        cur.execute("SELECT COUNT(*) FROM bsc_lp_token_transfers")
        count = cur.fetchone()[0]
        print(f"   Total records: {count}")
        
        if count > 0:
            cur.execute("""
                SELECT transfer_type, from_address, to_address, lp_amount, timestamp
                FROM bsc_lp_token_transfers
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            recent = cur.fetchall()
            print("   Recent transfers:")
            for r in recent:
                print(f"     {r[4]}: {r[0]} - Amount: {r[3]:.6f}")
        else:
            print("   [NO DATA]")
        
        # 3. Check bsc_lp_holders
        print("\n3. LP Holders (bsc_lp_holders):")
        print("-" * 50)
        cur.execute("SELECT COUNT(*) FROM bsc_lp_holders")
        count = cur.fetchone()[0]
        print(f"   Total records: {count}")
        
        if count > 0:
            cur.execute("""
                SELECT wallet_address, lp_balance, pool_share_percent, total_value_usd
                FROM bsc_lp_holders
                ORDER BY lp_balance DESC
                LIMIT 5
            """)
            top_holders = cur.fetchall()
            print("   Top holders:")
            for h in top_holders:
                print(f"     {h[0][:10]}...: {h[1]:.4f} LP ({h[2]:.2f}%) - ${h[3]:.0f}")
        else:
            print("   [NO DATA]")
        
        # 4. Check V3 liquidity events
        print("\n4. V3 Liquidity Events (bsc_v3_liquidity_events):")
        print("-" * 50)
        cur.execute("SELECT COUNT(*) FROM bsc_v3_liquidity_events")
        count = cur.fetchone()[0]
        print(f"   Total records: {count}")
        
        if count > 0:
            cur.execute("""
                SELECT event_type, owner_address, position_id, timestamp
                FROM bsc_v3_liquidity_events
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            recent = cur.fetchall()
            print("   Recent V3 events:")
            for r in recent:
                print(f"     {r[3]}: {r[0]} - Position #{r[2]}")
        else:
            print("   [NO DATA]")
        
        # 5. Check multi-pool LP activity
        print("\n5. Multi-Pool LP Activity (multi_pool_lp_activity):")
        print("-" * 50)
        cur.execute("SELECT COUNT(*) FROM multi_pool_lp_activity")
        count = cur.fetchone()[0]
        print(f"   Total records: {count}")
        
        if count > 0:
            cur.execute("""
                SELECT pool_name, transfer_type, COUNT(*) as cnt
                FROM multi_pool_lp_activity
                GROUP BY pool_name, transfer_type
                ORDER BY pool_name, transfer_type
            """)
            summary = cur.fetchall()
            print("   Activity by pool:")
            for s in summary:
                print(f"     {s[0]} - {s[1]}: {s[2]} events")
            
            # Get recent activity
            cur.execute("""
                SELECT pool_name, transfer_type, timestamp
                FROM multi_pool_lp_activity
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            recent = cur.fetchall()
            print("\n   Recent activity:")
            for r in recent:
                print(f"     {r[2]}: {r[0]} - {r[1]}")
        else:
            print("   [NO DATA]")
        
        # 6. Check when BSC monitor last ran
        print("\n6. BSC Pool Metrics (Last Update):")
        print("-" * 50)
        cur.execute("""
            SELECT MAX(timestamp) as last_update,
                   COUNT(*) as total_records,
                   COUNT(DISTINCT DATE(timestamp)) as days_of_data
            FROM bsc_pool_metrics
        """)
        result = cur.fetchone()
        if result[0]:
            last_update = result[0]
            age = (now - last_update).total_seconds() / 60
            print(f"   Last update: {last_update} ({age:.1f} minutes ago)")
            print(f"   Total records: {result[1]}")
            print(f"   Days of data: {result[2]}")
            
            if age > 60:
                print("   [WARNING] BSC monitor may not be running (last update > 1 hour ago)")
            else:
                print("   [OK] BSC monitor is running")
        else:
            print("   [NO DATA]")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY:")
        
        # Check if any LP data exists
        lp_tables = [
            ('bsc_liquidity_events', 'Liquidity Events'),
            ('bsc_lp_token_transfers', 'LP Token Transfers'),
            ('bsc_lp_holders', 'LP Holders'),
            ('bsc_v3_liquidity_events', 'V3 Liquidity Events'),
            ('multi_pool_lp_activity', 'Multi-Pool LP Activity')
        ]
        
        has_data = False
        for table, name in lp_tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            if count > 0:
                has_data = True
                print(f"  [OK] {name}: {count} records")
            else:
                print(f"  [X] {name}: NO DATA")
        
        if not has_data:
            print("\n[ISSUE] No LP data is being collected!")
            print("Possible causes:")
            print("  1. BSC monitor is not deployed or not running")
            print("  2. LP tracking methods are not being called")
            print("  3. The pools have no LP activity")
            print("  4. Configuration issues with pool addresses")
        else:
            print("\n[STATUS] Some LP data is being collected")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_lp_data()