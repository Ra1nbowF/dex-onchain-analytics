"""Update Railway database with new tables - simple version"""

import psycopg2
from psycopg2 import sql

# Railway database URL
RAILWAY_DATABASE_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def update_railway():
    conn = None
    cur = None
    
    try:
        print("Connecting to Railway database...")
        conn = psycopg2.connect(RAILWAY_DATABASE_URL)
        cur = conn.cursor()
        print("[OK] Connected")
        
        # 1. Create V3 liquidity events table
        print("\nCreating V3 liquidity events table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bsc_v3_liquidity_events (
                id SERIAL PRIMARY KEY,
                tx_hash VARCHAR(66) NOT NULL,
                block_number BIGINT NOT NULL,
                event_type VARCHAR(20) NOT NULL,
                owner_address VARCHAR(42),
                position_id BIGINT,
                tick_lower INTEGER,
                tick_upper INTEGER,
                liquidity NUMERIC(40, 0),
                amount0 NUMERIC(40, 18),
                amount1 NUMERIC(40, 18),
                timestamp TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()
        print("[OK] V3 table created")
        
        # Add constraint if not exists
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE bsc_v3_liquidity_events 
                ADD CONSTRAINT bsc_v3_liquidity_events_unique 
                UNIQUE(tx_hash, event_type, owner_address);
            EXCEPTION
                WHEN duplicate_table THEN NULL;
                WHEN duplicate_object THEN NULL;
            END $$;
        """)
        conn.commit()
        
        # 2. Create multi-pool table
        print("\nCreating multi-pool LP activity table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS multi_pool_lp_activity (
                id SERIAL PRIMARY KEY,
                pool_address VARCHAR(42) NOT NULL,
                pool_name VARCHAR(50) NOT NULL,
                pool_version VARCHAR(10) NOT NULL,
                tx_hash VARCHAR(66) NOT NULL,
                block_number BIGINT NOT NULL,
                from_address VARCHAR(42),
                to_address VARCHAR(42),
                transfer_type VARCHAR(20) NOT NULL,
                lp_amount NUMERIC(40, 18),
                timestamp TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()
        print("[OK] Multi-pool table created")
        
        # Add constraint
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE multi_pool_lp_activity 
                ADD CONSTRAINT multi_pool_lp_activity_unique 
                UNIQUE(tx_hash, pool_address);
            EXCEPTION
                WHEN duplicate_table THEN NULL;
                WHEN duplicate_object THEN NULL;
            END $$;
        """)
        conn.commit()
        
        # 3. Create indexes
        print("\nCreating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_v3_liquidity_timestamp ON bsc_v3_liquidity_events(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_v3_liquidity_owner ON bsc_v3_liquidity_events(owner_address)",
            "CREATE INDEX IF NOT EXISTS idx_v3_liquidity_type ON bsc_v3_liquidity_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_multi_pool_timestamp ON multi_pool_lp_activity(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_multi_pool_address ON multi_pool_lp_activity(pool_address)",
            "CREATE INDEX IF NOT EXISTS idx_multi_pool_type ON multi_pool_lp_activity(transfer_type)",
            "CREATE INDEX IF NOT EXISTS idx_multi_pool_name ON multi_pool_lp_activity(pool_name)"
        ]
        
        for idx in indexes:
            cur.execute(idx)
        conn.commit()
        print("[OK] Indexes created")
        
        # 4. Create view
        print("\nCreating summary view...")
        cur.execute("""
            CREATE OR REPLACE VIEW multi_pool_lp_summary AS
            SELECT 
                pool_name,
                pool_version,
                transfer_type,
                COUNT(*) as event_count,
                SUM(lp_amount) as total_lp_amount,
                MAX(timestamp) as last_activity
            FROM multi_pool_lp_activity
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY pool_name, pool_version, transfer_type
            ORDER BY pool_name, transfer_type
        """)
        conn.commit()
        print("[OK] View created")
        
        # 5. Verify tables
        print("\nVerifying tables...")
        tables = [
            'bsc_v3_liquidity_events',
            'multi_pool_lp_activity',
            'bsc_liquidity_events',
            'bsc_lp_token_transfers',
            'bsc_lp_holders',
            'bsc_pool_metrics'
        ]
        
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count} records")
        
        print("\n[SUCCESS] Railway database updated!")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        if conn:
            conn.rollback()
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("\nConnection closed")

if __name__ == "__main__":
    update_railway()