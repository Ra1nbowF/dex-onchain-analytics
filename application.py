"""Flask API for DEX Analytics - AWS Deployment"""

from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from decimal import Decimal

app = Flask(__name__)

# Database connection from environment
DATABASE_URL = os.environ.get('DATABASE_URL',
    'postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway')

def decimal_default(obj):
    """JSON serializer for Decimal types"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "service": "DEX Analytics API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/swaps",
            "/api/transfers",
            "/api/traders",
            "/api/pool/stats"
        ]
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status
    })

@app.route('/api/swaps')
def get_swaps():
    """Get recent swap transactions"""
    try:
        limit = request.args.get('limit', 50, type=int)

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                tx_hash,
                block_number,
                timestamp,
                trader_address,
                CASE WHEN is_buy THEN 'BUY' ELSE 'SELL' END as type,
                amount_in,
                amount_out,
                price,
                value_usd,
                gas_used
            FROM bsc_trades
            ORDER BY timestamp DESC
            LIMIT %s
        """, (limit,))

        swaps = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            "count": len(swaps),
            "swaps": swaps
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transfers')
def get_transfers():
    """Get recent token transfers"""
    try:
        limit = request.args.get('limit', 50, type=int)
        pool_only = request.args.get('pool_only', 'false').lower() == 'true'

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                tx_hash,
                block_number,
                timestamp,
                from_address,
                to_address,
                token_symbol,
                amount,
                value_usd,
                transfer_type,
                is_pool_related
            FROM bsc_token_transfers
        """

        if pool_only:
            query += " WHERE is_pool_related = true "

        query += " ORDER BY timestamp DESC LIMIT %s"

        cur.execute(query, (limit,))
        transfers = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            "count": len(transfers),
            "transfers": transfers
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/traders')
def get_top_traders():
    """Get top traders by volume"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                trader_address,
                COUNT(*) as total_trades,
                COUNT(CASE WHEN is_buy THEN 1 END) as buy_orders,
                COUNT(CASE WHEN is_buy = false THEN 1 END) as sell_orders,
                COALESCE(SUM(value_usd), 0) as total_volume_usd,
                COALESCE(SUM(CASE WHEN is_buy THEN amount_out ELSE 0 END), 0) as btcb_bought,
                COALESCE(SUM(CASE WHEN is_buy = false THEN amount_in ELSE 0 END), 0) as btcb_sold
            FROM bsc_trades
            GROUP BY trader_address
            ORDER BY total_trades DESC
            LIMIT 20
        """)

        traders = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            "count": len(traders),
            "traders": traders
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pool/stats')
def get_pool_stats():
    """Get pool statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get swap stats
        cur.execute("""
            SELECT
                COUNT(*) as total_swaps,
                COUNT(CASE WHEN is_buy THEN 1 END) as total_buys,
                COUNT(CASE WHEN is_buy = false THEN 1 END) as total_sells,
                COALESCE(SUM(value_usd), 0) as total_volume_usd,
                COALESCE(AVG(price), 0) as avg_price,
                MIN(timestamp) as first_swap,
                MAX(timestamp) as last_swap
            FROM bsc_trades
        """)

        swap_stats = cur.fetchone()

        # Get transfer stats
        cur.execute("""
            SELECT
                COUNT(*) as total_transfers,
                COUNT(CASE WHEN is_pool_related THEN 1 END) as pool_transfers,
                COALESCE(SUM(amount), 0) as total_btcb_transferred
            FROM bsc_token_transfers
        """)

        transfer_stats = cur.fetchone()

        # Get 24h volume
        cur.execute("""
            SELECT
                COALESCE(SUM(value_usd), 0) as volume_24h
            FROM bsc_trades
            WHERE timestamp > NOW() - INTERVAL '24 hours'
        """)

        volume_24h = cur.fetchone()[0]

        cur.close()
        conn.close()

        return jsonify({
            "pool_address": "0x46cf1cf8c69595804ba91dfdd8d6b960c9b0a7c4",
            "swaps": {
                "total": swap_stats[0],
                "buys": swap_stats[1],
                "sells": swap_stats[2],
                "total_volume_usd": float(swap_stats[3]) if swap_stats[3] else 0,
                "avg_price": float(swap_stats[4]) if swap_stats[4] else 0,
                "first_swap": swap_stats[5].isoformat() if swap_stats[5] else None,
                "last_swap": swap_stats[6].isoformat() if swap_stats[6] else None
            },
            "transfers": {
                "total": transfer_stats[0],
                "pool_related": transfer_stats[1],
                "total_btcb": float(transfer_stats[2]) if transfer_stats[2] else 0
            },
            "volume_24h_usd": float(volume_24h) if volume_24h else 0,
            "last_updated": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)