import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange

api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")
testnet = config.SECURITY_CONFIG.get("testnet_mode", False)

print(f"API Key: {api_key[:10]}...")
print(f"Testnet: {testnet}")

ex = BinanceExchange(api_key, api_secret, testnet)

try:
    balance = ex.get_balance()
    print("API 连接成功!")
    print(balance)
except Exception as e:
    print(f"API 错误: {e}")
