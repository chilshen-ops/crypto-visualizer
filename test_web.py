"""Test web UI"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
print("Testing imports...")
try:
    import config
    print("config OK")
except Exception as e:
    print(f"config Error: {e}")

try:
    from src.exchange.binance import BinanceExchange
    print("binance OK")
except Exception as e:
    print(f"binance Error: {e}")

try:
    from src.fetcher import DataFetcher
    print("fetcher OK")
except Exception as e:
    print(f"fetcher Error: {e}")

try:
    from src.trader import Trader
    print("trader OK")
except Exception as e:
    print(f"trader Error: {e}")

print("\nTesting API...")
try:
    api_key = config.SECURITY_CONFIG.get("api_key", "")
    api_secret = config.SECURITY_CONFIG.get("api_secret", "")
    testnet = config.SECURITY_CONFIG.get("testnet_mode", False)
    
    exchange = BinanceExchange(api_key, api_secret, testnet)
    fetcher = DataFetcher(exchange)
    trader = Trader(exchange, fetcher)
    
    status = trader.get_status()
    print(f"Status: {status}")
except Exception as e:
    print(f"API Error: {e}")
    import traceback
    traceback.print_exc()
