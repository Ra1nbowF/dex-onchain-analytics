import asyncio
import aiohttp
from bsc_pool_monitor import BSCPoolMonitor

async def test():
    monitor = BSCPoolMonitor()
    await monitor.initialize()

    # Test with longer range
    print("Fetching LP token transfers (7 days)...")
    transfers = await monitor.fetch_lp_token_transfers(hours=168)
    print(f"Found {len(transfers)} LP transfers in last 7 days")

    # Also test regular trades
    print("\nFetching swap trades...")
    trades = await monitor.fetch_recent_trades(hours=24)
    print(f"Found {len(trades)} trades in last 24 hours")

    # Check pool reserves
    print("\nFetching pool reserves...")
    reserves = await monitor.fetch_pool_reserves()
    if reserves:
        print(f"BTCB Reserve: {reserves.get('btcb_reserve', 0):.4f}")
        print(f"USDT Reserve: {reserves.get('usdt_reserve', 0):.2f}")
        print(f"TVL: ${reserves.get('tvl', 0):,.2f}")

    # Get LP token total supply
    print("\nFetching LP token supply...")
    supply = await monitor.get_lp_total_supply()
    print(f"LP Token Total Supply: {supply:.6f}")

    await monitor.cleanup()

if __name__ == "__main__":
    asyncio.run(test())