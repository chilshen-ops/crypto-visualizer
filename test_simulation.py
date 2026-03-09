"""全流程模拟测试"""
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
from src.constants import TradeStatus

def test_full_simulation():
    print("=" * 60)
    print("全流程模拟测试")
    print("=" * 60)
    
    # 1. 初始化系统
    print("\n[1] 初始化交易系统...")
    api_key = config.SECURITY_CONFIG.get("api_key", "")
    api_secret = config.SECURITY_CONFIG.get("api_secret", "")
    testnet = config.SECURITY_CONFIG.get("testnet_mode", True)
    
    exchange = BinanceExchange(api_key, api_secret, testnet)
    fetcher = DataFetcher(exchange)
    analyzer = TechnicalAnalyzer()
    scorer = Scorer(analyzer)
    selector = SymbolSelector(fetcher, scorer)
    trader = Trader(exchange, fetcher)
    
    print(f"    模式: {'测试网' if testnet else '实盘'}")
    print(f"    交易对: {config.TRADING_CONFIG.get('symbol')}")
    print(f"    K线周期: {config.TRADING_CONFIG.get('interval')}")
    print(f"    仓位比例: {config.POSITION_CONFIG.get('max_position_ratio')*100}%")
    
    # 2. 选币
    print("\n[2] 选币测试...")
    symbols = config.TRADING_CONFIG.get("monitor_symbols")
    top = selector.get_top_symbols(symbols, top_n=3)
    best_symbol = top[0]['symbol'] if top else "BTCUSDT"
    print(f"    最佳币种: {best_symbol} (分数: {top[0]['score']})")
    
    # 3. 获取数据
    print("\n[3] 获取数据...")
    df = fetcher.get_klines(best_symbol, "3m", limit=100)
    print(f"    获取 {len(df)} 条 K线")
    
    # 4. 技术分析
    print("\n[4] 技术分析...")
    analyzer.calculate(df)
    indicators = analyzer.get_latest_indicators(df)
    patterns = analyzer.detect_patterns(df)
    print(f"    价格: {indicators.get('price'):.2f}")
    print(f"    RSI: {indicators.get('rsi'):.2f}")
    print(f"    MACD: {indicators.get('macd_dif'):.4f}")
    
    # 5. AI 决策
    print("\n[5] AI 决策...")
    from src.ai.brain import AIBrain
    ai_brain = AIBrain(fetcher, analyzer)
    decision = ai_brain.analyze(best_symbol, "3m")
    print(f"    决策: {decision.get('action')}")
    print(f"    原因: {decision.get('reason')}")
    print(f"    置信度: {decision.get('confidence', 0):.2f}")
    
    # 6. 模拟交易
    print("\n[6] 模拟交易...")
    action = decision.get('action', 'hold')
    
    if action == 'buy' and trader.status == TradeStatus.IDLE:
        print(f"    模拟买入信号: {best_symbol}")
        print(f"    当前状态: {trader.status}")
        print(f"    可交易: {trader.can_trade()}")
        print("    ⚠️ 实际买入已禁用（模拟模式）")
    
    elif action == 'buy' and trader.status == TradeStatus.HOLDING:
        print(f"    已有持仓，建议持有")
        print(f"    当前状态: {trader.status}")
    
    elif action == 'sell' and trader.status == TradeStatus.HOLDING:
        print(f"    模拟卖出信号: {best_symbol}")
        print("    ⚠️ 实际卖出已禁用（模拟模式）")
    
    elif action == 'hold' or (action == 'buy' and trader.status != TradeStatus.IDLE):
        print(f"    建议持有")
        print(f"    当前状态: {trader.status}")
    
    # 7. 风控检查
    print("\n[7] 风控检查...")
    can_trade = trader.can_trade()
    print(f"    可交易: {can_trade}")
    print(f"    连续亏损: {trader.consecutive_loss} / {trader.max_consecutive_loss}")
    print(f"    持仓时间: {trader.position_time} 根K线")
    
    # 8. 状态汇总
    print("\n[8] 系统状态...")
    status = trader.get_status()
    print(f"    交易状态: {status.get('status')}")
    print(f"    持仓数量: {status.get('position')}")
    print(f"    持仓价格: {status.get('entry_price')}")
    print(f"    止损价格: {status.get('stop_loss')}")
    print(f"    今日盈亏: {status.get('daily_pnl')}")
    
    # 9. 通知测试
    print("\n[9] 通知测试...")
    from src.notifier import get_notifier
    notifier = get_notifier()
    print(f"    通知启用: {notifier.enabled}")
    print(f"    Webhook: {'已配置' if notifier.webhook else '未配置'}")
    
    print("\n" + "=" * 60)
    print("全流程模拟测试完成!")
    print("=" * 60)
    
    return {
        "symbol": best_symbol,
        "decision": action,
        "can_trade": can_trade,
        "status": status
    }

if __name__ == "__main__":
    test_full_simulation()
