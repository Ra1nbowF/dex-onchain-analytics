#!/usr/bin/env python3
"""
Verify Railway deployment will work with dashboards
"""

import psycopg2
import sys

RAILWAY_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def verify_deployment():
    print("="*70)
    print("Railway Deployment Verification for Dashboards")
    print("="*70)

    try:
        conn = psycopg2.connect(RAILWAY_URL)
        cur = conn.cursor()

        # Dashboard requirements
        dashboard_tables = {
            "moralis-rich-data-dashboard": [
                "moralis_swaps_correct",
                "moralis_holders",
                "moralis_historical_holders_correct",
                "moralis_transfers"
            ],
            "moralis-corrected-dashboard": [
                "moralis_swaps_correct",
                "moralis_holder_stats_correct",
                "moralis_pair_stats_correct",
                "moralis_token_analytics_correct",
                "moralis_historical_holders_correct",
                "moralis_top_gainers"
            ],
            "bsc-dashboard-fixed": [
                "bsc_pool_metrics",
                "token_distribution"
            ]
        }

        all_good = True

        for dashboard, tables in dashboard_tables.items():
            print(f"\n[Dashboard: {dashboard}]")
            dashboard_ok = True

            for table in tables:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    )
                """, (table,))
                exists = cur.fetchone()[0]

                if exists:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    status = "[OK]" if count > 0 else "[EMPTY]"
                    print(f"  {status} {table}: {count} rows")
                    if count == 0:
                        dashboard_ok = False
                else:
                    print(f"  [MISSING] {table}")
                    dashboard_ok = False
                    all_good = False

            if dashboard_ok and all_good:
                print(f"  Status: Ready (all tables exist)")
            elif not dashboard_ok and all_good:
                print(f"  Status: Tables exist but need data")
            else:
                print(f"  Status: Missing tables")

        # Check if monitors are configured correctly
        print("\n" + "="*70)
        print("Monitor Configuration:")
        print("  bsc_pool_monitor.py -> bsc_pool_metrics, token_distribution")
        print("  moralis_final_monitor.py -> moralis_*_correct tables")

        # Summary
        print("\n" + "="*70)
        if all_good:
            print("[SUCCESS] All required tables exist!")
            print("\nDeployment Steps:")
            print("1. git add railway.json railway_monitor.py")
            print("2. git commit -m 'Deploy BSC and Moralis monitors to Railway'")
            print("3. git push origin main")
            print("\nRailway will automatically:")
            print("- Build and deploy from GitHub")
            print("- Run railway_monitor.py")
            print("- Connect to Railway PostgreSQL")
            print("- Start populating tables for dashboards")
        else:
            print("[ERROR] Some tables are missing!")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_deployment()