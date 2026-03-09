import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange

api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")

ex = BinanceExchange(api_key, api_secret, False)
balance = ex.get_balance()

print("当前余额:")
for b in balance.get("balances", []):
    if b.get("asset") in ["ETH", "USDT"]:
        print(f"  {b.get('asset')}: free={b.get('free')}, locked={b.get('locked')}")
