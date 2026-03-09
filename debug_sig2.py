import sys
import os
import time
import hmac
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")

print(f"API Key: {api_key}")
print(f"API Secret: {api_secret}")
print(f"Secret length: {len(api_secret)}")

# 测试不同签名方式
symbol = "ETHUSDT"
quantity = 0.0127643
timestamp = int(time.time() * 1000)

# 方式1: 不带 recvWindow
params1 = {
    "symbol": symbol.upper(),
    "side": "SELL",
    "type": "MARKET",
    "quantity": quantity,
    "timestamp": timestamp
}
query1 = "&".join([f"{k}={v}" for k, v in sorted(params1.items())])
sig1 = hmac.new(api_secret.encode(), query1.encode(), hashlib.sha256).hexdigest()
print(f"\n方式1 (无recvWindow):")
print(f"Query: {query1}")
print(f"Signature: {sig1}")

# 方式2: 使用 urlencoded 参数顺序
params2 = f"symbol={symbol.upper()}&side=SELL&type=MARKET&quantity={quantity}&timestamp={timestamp}"
sig2 = hmac.new(api_secret.encode(), params2.encode(), hashlib.sha256).hexdigest()
print(f"\n方式2 (原始顺序):")
print(f"Query: {params2}")
print(f"Signature: {sig2}")

# 方式3: 检查是否是 Secret 读取问题 - 直接硬编码测试
test_secret = "PZyGnfHKsEoBGXmmETIO7mWz0gHj5mdfiWJNTGHJRlqFFXPQzTGQb4JCV8GU9xNU"
sig3 = hmac.new(test_secret.encode(), query1.encode(), hashlib.sha256).hexdigest()
print(f"\n方式3 (硬编码Secret):")
print(f"Signature: {sig3}")
