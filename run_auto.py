"""后台自动交易模式"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange
from src.fetcher import DataFetcher
from src.analyzer import TechnicalAnalyzer
from src.ai.brain import AIBrain
from src.trader import Trader
from src.notifier import get_notifier
from src.constants import TradeStatus

def run_auto_trading():
    print("=" * 60)
    print("Crypto Visualizer - 自动交易模式")
    print("=" * 60)
    
    # 初始化
    api_key = config.SECURITY_CONFIG.get("api_key", "")
    api_secret = config.SECURITY_CONFIG.get("api_secret", "")
    testnet = config.SECURITY_CONFIG.get("testnet_mode", False)
    
    exchange = BinanceExchange(api_key, api_secret, testnet)
    fetcher = DataFetcher(exchange)
    analyzer = TechnicalAnalyzer()
    ai_brain = AIBrain(fetcher, analyzer)
    trader = Trader(exchange, fetcher)
    notifier = get_notifier()
    
    symbol = config.TRADING_CONFIG.get("symbol", "ETHUSDT")
    interval = config.TRADING_CONFIG.get("interval", "3m")
    
    print(f"\n交易对: {symbol}")
    print(f"模式: {'测试网' if testnet else '实盘'}")
    print(f"止损比例: {config.TRADING_CONFIG.get('stop_loss_ratio')*100}%")
    
    # 显示持仓状态
    status = trader.get_status()
    print(f"\n当前状态:")
    print(f"  持仓: {status.get('position')} {symbol}")
    print(f"  持仓价格: {status.get('entry_price')}")
    print(f"  止损价格: {status.get('stop_loss')}")
    print(f"  交易状态: {status.get('status')}")
    
    # 开始自动交易循环
    print(f"\n开始自动交易 (每 {interval} 一次)...")
    print(f"\n开始自动交易 (每 {interval} 一次)...\n")
    
    tick = 0
    try:
        while True:
            tick += 1
            print(f"\n--- 第 {tick} 次执行 ---")
            
            # 1. 获取数据
            df = fetcher.get_klines(symbol, interval, limit=100)
            if df is None or len(df) < 20:
                print("数据获取失败，等待重试...")
                time.sleep(60)
                continue
            
            # 2. 技术分析
            analyzer.calculate(df)
            indicators = analyzer.get_latest_indicators(df)
            patterns = analyzer.detect_patterns(df)
            
            current_price = indicators.get('price', 0)
            print(f"当前价格: {current_price}")
            
            # 3. 检查止损
            if trader.status == TradeStatus.HOLDING:
                if current_price > 0 and current_price <= trader.stop_loss_price:
                    print("触发止损！")
                    trader.sell(reason="止损")
                    if notifier.enabled:
                        notifier.notify_trade({
                            "action": "sell",
                            "symbol": symbol,
                            "price": current_price,
                            "reason": "止损"
                        })
                    continue
            
            # 4. AI 决策
            decision = ai_brain.analyze(symbol, interval)
            action = decision.get('action', 'hold')
            reason = decision.get('reason', '')
            confidence = decision.get('confidence', 0)
            
            print(f"AI 决策: {action} (置信度: {confidence})")
            print(f"原因: {reason}")
            
            # 5. 执行交易
            if action == 'buy' and trader.status == TradeStatus.IDLE:
                print("执行买入...")
                result = trader.buy()
                if result.get('success'):
                    print(f"买入成功: {result}")
                    if notifier.enabled:
                        notifier.notify_trade({
                            "action": "buy",
                            "symbol": symbol,
                            "price": current_price,
                            "reason": reason
                        })
                else:
                    print(f"买入失败: {result.get('reason')}")
            
            elif action == 'sell' and trader.status == TradeStatus.HOLDING:
                print("执行卖出...")
                result = trader.sell(reason=reason)
                if result.get('success'):
                    print(f"卖出成功: {result}")
                    if notifier.enabled:
                        notifier.notify_trade({
                            "action": "sell",
                            "symbol": symbol,
                            "price": current_price,
                            "reason": reason
                        })
                else:
                    print(f"卖出失败: {result.get('reason')}")
            
            elif action == 'hold':
                print("持有等待...")
            
            # 显示持仓状态
            status = trader.get_status()
            print(f"\n持仓状态: {status.get('status')}")
            if status.get('position', 0) > 0:
                print(f"  数量: {status.get('position')}")
                print(f"  价格: {status.get('entry_price')}")
                print(f"  止损: {status.get('stop_loss')}")
            
            # 等待下一个周期
            interval_seconds = {"1m": 60, "3m": 180, "5m": 300, "15m": 900, "1h": 3600}
            wait_time = interval_seconds.get(interval, 180)
            print(f"\n等待 {wait_time} 秒...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n\n程序已停止")

if __name__ == "__main__":
    run_auto_trading()
