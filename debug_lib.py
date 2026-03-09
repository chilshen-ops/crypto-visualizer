import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from binance.client import Client

api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")

client = Client(api_key, api_key, api_secret)

# 打印库使用的签名方式
import hashlib
import hmac

# 模拟库的做法
params = {
    "symbol": "ETHUSDT",
    "side": "SELL", 
    "type": "MARKET",
    "quantity": 0.0127643,
    "timestamp": 1773038000000
}

# Binance 库的做法
query_string = "&".join([f"{k}={v}" for k,v in params.items()])
print(f"Query: {query_string}")

signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
print(f"Signature: {signature}")
