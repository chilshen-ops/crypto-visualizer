"""检查账户持仓"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange

api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")
testnet = config.SECURITY_CONFIG.get("testnet_mode", False)

print(f"模式: {'测试网' if testnet else '实盘'}")
print(f"API Key: {api_key[:10]}...")

exchange = BinanceExchange(api_key, api_secret, testnet)
balance = exchange.get_balance()

print("\n账户余额:")
for bal in balance.get("balances", []):
    free = float(bal.get("free", 0))
    locked = float(bal.get("locked", 0))
    if free > 0 or locked > 0:
        print(f"  {bal.get('asset')}: free={free}, locked={locked}")
