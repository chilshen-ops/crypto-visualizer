import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from binance.client import Client

api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")
testnet = config.SECURITY_CONFIG.get("testnet_mode", False)

print(f"API Key: {api_key[:10]}...")

try:
    client = Client(api_key, api_secret)
    
    # 测试获取账户
    account = client.get_account()
    print("获取账户成功!")
    
    # 测试卖出
    symbol = "ETHUSDT"
    quantity = 0.012
    
    print(f"\n尝试卖出 {quantity} {symbol}...")
    order = client.order_market_sell(
        symbol=symbol,
        quantity=quantity
    )
    print("卖出成功!")
    print(order)
    
except Exception as e:
    print(f"错误: {e}")
