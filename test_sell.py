import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange

api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")
testnet = config.SECURITY_CONFIG.get("testnet_mode", False)

ex = BinanceExchange(api_key, api_secret, testnet)

# 测试卖出
symbol = "ETHUSDT"
quantity = 0.0127643

print(f"尝试卖出 {quantity} {symbol}...")

try:
    result = ex.sell_market(symbol, quantity)
    print("卖出成功!")
    print(result)
except Exception as e:
    print(f"卖出失败: {e}")
