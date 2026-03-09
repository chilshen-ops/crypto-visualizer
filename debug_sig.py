import sys
import os
import time
import hmac
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange

api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")
testnet = config.SECURITY_CONFIG.get("testnet_mode", False)

symbol = "ETHUSDT"
quantity = 0.0127643
timestamp = int(time.time() * 1000)

# 模拟签名生成
params = {
    "symbol": symbol.upper(),
    "side": "SELL",
    "type": "MARKET",
    "quantity": quantity,
    "timestamp": timestamp,
    "recvWindow": 5000
}

# 按字母顺序排序
query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
print(f"Query string: {query_string}")

# 生成签名
signature = hmac.new(
    api_secret.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print(f"Signature: {signature}")

# 直接用 requests 测试
import requests

url = "https://api.binance.com/api/v3/order"
headers = {"X-MBX-APIKEY": api_key}

# 发送请求
params["signature"] = signature

print(f"\n发送请求...")
response = requests.post(url, params=params, headers=headers, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
