"""
主循环 - 定时执行交易策略
"""
import time
import threading
from typing import Optional, Dict, Any
from datetime import datetime

from .exchange.binance import BinanceExchange
from .fetcher import DataFetcher
from .analyzer import TechnicalAnalyzer
from .scorer import Scorer
from .selector import SymbolSelector
from .trader import Trader
from .ai.brain import AIBrain
from .logger import get_logger, get_trade_logger
from .notifier import get_notifier
from .constants import TradeStatus
import config


class TradingLoop:
    """交易主循环"""
    
    def __init__(self):
        self.logger = get_logger("loop")
        self.trade_logger = get_trade_logger()
        
        # 组件
        self.exchange: Optional[BinanceExchange] = None
        self.fetcher: Optional[DataFetcher] = None
        self.analyzer: Optional[TechnicalAnalyzer] = None
        self.scorer: Optional[Scorer] = None
        self.selector: Optional[SymbolSelector] = None
        self.trader: Optional[Trader] = None
        self.ai_brain: Optional[AIBrain] = None
        self.notifier = get_notifier()
        
        # 状态
        self.running = False
        self.paused = False
        self.loop_thread: Optional[threading.Thread] = None
        
        # 配置
        trading_config = config.TRADING_CONFIG
        self.symbol = trading_config.get("symbol", "BTCUSDT")
        self.interval = trading_config.get("interval", "3m")
        self.monitor_symbols = trading_config.get("monitor_symbols", ["BTCUSDT"])
        
        # K线周期对应的秒数
        self.interval_seconds = {
            "1m": 60,
            "3m": 180,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
        }
    
    def initialize(self, api_key: str = "", api_secret: str = ""):
        """初始化所有组件"""
        self.logger.info("初始化交易系统...")
        
        # 交易所
        testnet = config.SECURITY_CONFIG.get("testnet_mode", True)
        self.exchange = BinanceExchange(api_key, api_secret, testnet)
        self.logger.info(f"交易所已初始化 (测试网: {testnet})")
        
        # 数据获取
        self.fetcher = DataFetcher(self.exchange)
        
        # 技术分析
        self.analyzer = TechnicalAnalyzer()
        
        # 评分
        self.scorer = Scorer(self.analyzer)
        
        # 选币
        self.selector = SymbolSelector(self.fetcher, self.scorer)
        
        # 交易
        self.trader = Trader(self.exchange, self.fetcher)
        
        # AI
        self.ai_brain = AIBrain(self.fetcher, self.analyzer)
        
        self.logger.info("交易系统初始化完成")
        
        # 发送启动通知
        if self.notifier.enabled:
            self.notifier.notify_status("已启动", self.symbol, "测试" if testnet else "实盘")
    
    def start(self):
        """启动交易循环"""
        if self.running:
            self.logger.warning("交易循环已在运行")
            return
        
        self.running = True
        self.paused = False
        
        # 启动循环线程
        self.loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.loop_thread.start()
        
        self.logger.info("交易循环已启动")
    
    def stop(self):
        """停止交易循环"""
        self.running = False
        
        if self.loop_thread:
            self.loop_thread.join(timeout=10)
        
        # 紧急平仓
        if self.trader and self.trader.status == TradeStatus.HOLDING:
            self.logger.warning("执行紧急平仓")
            self.trader.emergency_close()
        
        # 发送停止通知
        if self.notifier.enabled:
            self.notifier.notify_status("已停止", self.symbol, "")
        
        self.logger.info("交易循环已停止")
    
    def pause(self):
        """暂停交易"""
        self.paused = True
        self.logger.info("交易已暂停")
    
    def resume(self):
        """恢复交易"""
        self.paused = False
        self.logger.info("交易已恢复")
    
    def _run_loop(self):
        """主循环"""
        self.logger.info("进入交易主循环")
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(5)
                    continue
                
                # 获取K线周期对应的等待时间
                wait_time = self.interval_seconds.get(self.interval, 180)
                
                # 执行交易逻辑
                self._execute_tick()
                
                # 等待下一个周期
                for _ in range(wait_time):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"交易循环异常: {e}")
                time.sleep(10)  # 异常后等待10秒
    
    def _execute_tick(self):
        """执行一次交易"""
        if not self.trader:
            return
        
        # 更新持仓时间
        self.trader.update_position_time()
        
        # 检查止损
        if self.trader.status == TradeStatus.HOLDING:
            if self.trader.check_stop_loss():
                self.logger.info("止损已触发")
                return
        
        # 检查是否可以交易
        if not self.trader.can_trade():
            return
        
        # 获取AI决策
        decision = self.ai_brain.analyze(self.symbol, self.interval)
        
        action = decision.get('action', 'hold')
        reason = decision.get('reason', '')
        
        self.logger.info(f"AI 决策: {action} - {reason}")
        
        # 保存AI决策到trader供UI显示
        if self.trader:
            self.trader.last_ai_action = action
            self.trader.last_ai_reason = reason
            self.trader.last_ai_confidence = decision.get('confidence', '')
            self.trader.last_ai_thinking = decision.get('thinking', reason)
            self.trader.is_running = self.running
        
        # 验证并执行决策
        has_position = self.trader.status == TradeStatus.HOLDING
        
        if action == 'buy' and not has_position:
            # 买入
            result = self.trader.buy()
            if result.get('success'):
                self.logger.info(f"买入成功: {result}")
        
        elif action == 'sell' and has_position:
            # 卖出
            result = self.trader.sell(reason=reason)
            if result.get('success'):
                self.logger.info(f"卖出成功: {result}")
        
        elif action == 'hold':
            # 持有
            if has_position:
                status = self.trader.get_status()
                self.logger.debug(f"持仓中: 价格 {status.get('current_price')}, "
                               f"盈亏 {status.get('daily_pnl')}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "running": self.running,
            "paused": self.paused,
            "symbol": self.symbol,
            "interval": self.interval,
            "trader": self.trader.get_status() if self.trader else {},
        }
    
    def get_recommendation(self) -> Dict[str, Any]:
        """获取当前推荐"""
        if not self.selector:
            return {}
        
        # 评估当前币种
        return self.selector.evaluate_current_symbol(self.symbol)
    
    def get_top_symbols(self, top_n: int = 3) -> list:
        """获取排名前N的币种"""
        if not self.selector:
            return []
        
        return self.selector.get_top_symbols(self.monitor_symbols, top_n)
    
    def change_symbol(self, new_symbol: str):
        """切换交易对"""
        if self.trader and self.trader.status == TradeStatus.HOLDING:
            self.logger.warning("当前有持仓，请先平仓")
            return False
        
        self.symbol = new_symbol
        self.trader.symbol = new_symbol
        self.logger.info(f"切换交易对: {new_symbol}")
        
        if self.notifier.enabled:
            self.notifier.notify_status("切换交易对", new_symbol, "")
        
        return True
    
    def manual_buy(self, quantity: float = None) -> Dict:
        """手动买入"""
        if self.trader:
            return self.trader.buy(quantity)
        return {"success": False, "reason": "交易器未初始化"}
    
    def manual_sell(self, quantity: float = None) -> Dict:
        """手动卖出"""
        if self.trader:
            return self.trader.sell(quantity, reason="手动")
        return {"success": False, "reason": "交易器未初始化"}
    
    def force_stop_loss(self) -> Dict:
        """手动触发止损"""
        if self.trader:
            return self.trader.sell(reason="手动止损")
        return {"success": False, "reason": "交易器未初始化"}


# 全局交易循环
_trading_loop: Optional[TradingLoop] = None


def get_trading_loop() -> TradingLoop:
    """获取交易循环实例"""
    global _trading_loop
    if _trading_loop is None:
        _trading_loop = TradingLoop()
    return _trading_loop


def init_trading_loop(api_key: str = "", api_secret: str = "") -> TradingLoop:
    """初始化交易循环"""
    global _trading_loop
    _trading_loop = TradingLoop()
    _trading_loop.initialize(api_key, api_secret)
    return _trading_loop
