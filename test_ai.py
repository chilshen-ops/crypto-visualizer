"""测试 AI 决策功能"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange
from src.fetcher import DataFetcher
from src.ai.brain import AIBrain
from src.analyzer import TechnicalAnalyzer

def test_ai():
    print("=" * 50)
    print("测试 AI 决策功能")
    print("=" * 50)
    
    # 1. 初始化
    print("\n[1] 初始化组件...")
    api_key = config.SECURITY_CONFIG.get("api_key", "")
    api_secret = config.SECURITY_CONFIG.get("api_secret", "")
    testnet = config.SECURITY_CONFIG.get("testnet_mode", True)
    
    exchange = BinanceExchange(api_key, api_secret, testnet)
    fetcher = DataFetcher(exchange)
    analyzer = TechnicalAnalyzer()
    ai_brain = AIBrain(fetcher, analyzer)
    
    print(f"    模型: {config.AI_CONFIG.get('model')}")
    print(f"    主机: {config.AI_CONFIG.get('host')}")
    
    # 2. 获取数据
    print("\n[2] 获取 BTCUSDT 数据...")
    symbol = "BTCUSDT"
    interval = "3m"
    df = fetcher.get_klines(symbol, interval, limit=100)
    print(f"    获取到 {len(df)} 条K线数据")
    
    # 3. 计算指标
    print("\n[3] 计算技术指标...")
    analyzer.calculate(df)
    indicators = analyzer.get_latest_indicators(df)
    patterns = analyzer.detect_patterns(df)
    
    print(f"    价格: {indicators.get('price'):.2f}")
    print(f"    RSI: {indicators.get('rsi'):.2f}")
    print(f"    MACD: {indicators.get('macd_dif'):.4f}")
    print(f"    KDJ K: {indicators.get('kdj_k'):.2f}")
    print(f"    MA5: {indicators.get('ma5'):.2f}")
    print(f"    MA20: {indicators.get('ma20'):.2f}")
    
    print("\n    技术信号:")
    if patterns.get('kdj_golden_cross'): print("      - KDJ金叉")
    if patterns.get('macd_golden_cross'): print("      - MACD金叉")
    if patterns.get('rsi_oversold'): print("      - RSI超卖")
    if patterns.get('rsi_overbought'): print("      - RSI超买")
    if not any(patterns.values()): print("      - 无明显信号")
    
    # 4. AI 决策
    print("\n[4] AI 决策中...")
    decision = ai_brain.analyze(symbol, interval)
    
    print(f"\n    决策结果:")
    print(f"      操作: {decision.get('action')}")
    print(f"      原因: {decision.get('reason')}")
    print(f"      置信度: {decision.get('confidence', 0):.2f}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    test_ai()
