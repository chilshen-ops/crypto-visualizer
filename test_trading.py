"""测试完整交易流程"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange
from src.fetcher import DataFetcher
from src.analyzer import TechnicalAnalyzer
from src.selector import SymbolSelector
from src.scorer import Scorer
from src.trader import Trader

def test_full_flow():
    print("=" * 60)
    print("测试完整交易流程")
    print("=" * 60)
    
    # 1. 初始化
    print("\n[1] 初始化组件...")
    api_key = config.SECURITY_CONFIG.get("api_key", "")
    api_secret = config.SECURITY_CONFIG.get("api_secret", "")
    testnet = config.SECURITY_CONFIG.get("testnet_mode", True)
    
    exchange = BinanceExchange(api_key, api_secret, testnet)
    fetcher = DataFetcher(exchange)
    analyzer = TechnicalAnalyzer()
    scorer = Scorer(analyzer)
    selector = SymbolSelector(fetcher, scorer)
    trader = Trader(exchange, fetcher)
    
    print("    ✅ 全部组件初始化完成")
    
    # 2. 测试选币器
    print("\n[2] 测试选币器...")
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    top = selector.get_top_symbols(symbols, top_n=3)
    print(f"    推荐币种 (前{len(top)}个):")
    for i, s in enumerate(top, 1):
        print(f"      {i}. {s['symbol']} (分数: {s['score']})")
        if s.get('reasons'):
            print(f"         原因: {', '.join(s['reasons'][:3])}")
    
    # 3. 测试交易员状态
    print("\n[3] 测试交易员状态...")
    status = trader.get_status()
    print(f"    状态: {status.get('status')}")
    print(f"    持仓: {status.get('position')}")
    print(f"    能否交易: {status.get('can_trade')}")
    
    # 4. 测试买入前检查
    print("\n[4] 测试买入前检查...")
    can_buy = trader.can_trade()
    print(f"    可以买入: {can_buy}")
    
    # 5. 测试手动买入（测试网模式下尝试）
    print("\n[5] 测试手动买入...")
    print("    (跳过实际买入，仅测试逻辑)")
    
    # 6. 测试风控
    print("\n[6] 测试风控配置...")
    risk = config.RISK_CONFIG
    print(f"    最大连续亏损: {risk.get('max_consecutive_loss')} 次")
    print(f"    日亏损限制: {risk.get('daily_loss_limit')*100}%")
    
    # 7. 测试止损计算
    print("\n[7] 测试止损计算...")
    test_price = 50000
    stop_loss_ratio = config.TRADING_CONFIG.get('stop_loss_ratio', 0.05)
    stop_price = test_price * (1 - stop_loss_ratio)
    print(f"    买入价格: {test_price}")
    print(f"    止损比例: {stop_loss_ratio*100}%")
    print(f"    止损价格: {stop_price}")
    
    print("\n" + "=" * 60)
    print("完整交易流程测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_flow()
