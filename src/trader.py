"""
交易执行模块 - 负责买卖操作和状态管理
"""
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd

from .exchange.base import BaseExchange
from .fetcher import DataFetcher
from .logger import get_logger, get_trade_logger
from .notifier import get_notifier
from .constants import TradeStatus, OrderSide
import config


class Trader:
    """交易执行器"""
    
    def __init__(self, exchange: BaseExchange, fetcher: DataFetcher):
        """
        初始化交易器
        
        Args:
            exchange: 交易所实例
            fetcher: 数据获取器
        """
        self.exchange = exchange
        self.fetcher = fetcher
        self.logger = get_logger("trader")
        self.trade_logger = get_trade_logger()
        self.notifier = get_notifier()
        
        # 加载配置
        trading_config = config.TRADING_CONFIG
        self.symbol = trading_config.get("symbol", "BTCUSDT")
        self.interval = trading_config.get("interval", "3m")
        self.stop_loss_ratio = trading_config.get("stop_loss_ratio", 0.05)
        self.min_position_time = trading_config.get("min_position_time", 1)
        
        position_config = config.POSITION_CONFIG
        self.max_position_ratio = position_config.get("max_position_ratio", 0.95)
        
        risk_config = config.RISK_CONFIG
        self.max_consecutive_loss = risk_config.get("max_consecutive_loss", 3)
        self.daily_loss_limit = risk_config.get("daily_loss_limit", 0.10)
        
        # 交易状态
        self.status = TradeStatus.IDLE
        self.position = 0.0  # 持仓数量
        self.position_entry_price = 0.0  # 持仓价格
        self.position_time = 0  # 持仓K线数
        self.stop_loss_price = 0.0  # 止损价格
        self.consecutive_loss = 0  # 连续亏损次数
        self.daily_trades: List[Dict] = []  # 今日交易记录
        self.daily_pnl = 0.0  # 今日盈亏
        
        # 启动时同步持仓状态
        self.sync_position()
    
    def sync_position(self):
        """同步持仓状态 - 启动时从交易所获取当前持仓"""
        try:
            if not self.exchange or not self.fetcher:
                self.logger.warning("交易所或数据获取器未初始化，跳过持仓同步")
                return
            
            # 获取账户余额
            balance = self.exchange.get_balance()
            base_asset = self.symbol.replace('USDT', '').replace('usdt', '')
            
            for bal in balance.get('balances', []):
                if bal.get('asset') == base_asset:
                    qty = float(bal.get('free', 0)) + float(bal.get('locked', 0))
                    if qty > 0:
                        self.position = qty
                        self.status = TradeStatus.HOLDING
                        # 获取当前价格作为持仓参考
                        current_price = self.fetcher.get_current_price(self.symbol)
                        self.position_entry_price = current_price
                        # 设置止损
                        self.stop_loss_price = current_price * (1 - self.stop_loss_ratio)
                        self.logger.info(f"同步持仓: {self.symbol} x {qty} @ {current_price}")
                    break
                    
        except Exception as e:
            self.logger.error(f"同步持仓失败: {e}")
    
    def can_trade(self) -> bool:
        """
        检查是否可以交易
        
        Returns:
            是否可以交易
        """
        # 检查是否在熔断中
        if self.consecutive_loss >= self.max_consecutive_loss:
            self.logger.warning(f"连续亏损 {self.consecutive_loss} 次，熔断中")
            return False
        
        # 持仓时间限制已取消
        # if self.status == TradeStatus.HOLDING and self.position_time < self.min_position_time:
        #     self.logger.info(f"持仓时间不足，最小 {self.min_position_time} 根K线")
        #     return False
        
        return True
    
    def buy(self, quantity: float = None) -> Dict[str, Any]:
        """
        买入
        
        Args:
            quantity: 数量（默认全仓）
            
        Returns:
            交易结果
        """
        if self.status != TradeStatus.IDLE:
            self.logger.warning(f"当前状态 {self.status}，无法买入")
            return {"success": False, "reason": "状态错误"}
        
        try:
            self.status = TradeStatus.OPENING
            self.logger.info(f"开始买入 {self.symbol}")
            
            # 获取当前价格
            current_price = self.fetcher.get_current_price(self.symbol)
            
            # 计算买入数量
            if quantity is None:
                balance = self.exchange.get_balance()
                # 获取 USDT 余额
                usdt_balance = 0
                for bal in balance.get('balances', []):
                    if bal['asset'] == 'USDT':
                        usdt_balance = float(bal['free'])
                        break
                
                # 计算可买入数量
                quantity = (usdt_balance * self.max_position_ratio) / current_price
            
            # 执行买入
            result = self.exchange.buy_market(self.symbol, quantity)
            
            if result.get('orderId'):
                self.logger.info(f"买入成功，数量: {quantity}, 价格: {current_price}")
                self.trade_logger.info(f"BUY {self.symbol} {quantity} @ {current_price}")
                
                # 设置止损
                self.stop_loss_price = current_price * (1 - self.stop_loss_ratio)
                self.logger.info(f"止损价设置为: {self.stop_loss_price}")
                
                # 更新状态
                self.position = quantity
                self.position_entry_price = current_price
                self.position_time = 0
                self.status = TradeStatus.HOLDING
                
                # 发送通知
                self.notifier.notify_trade({
                    "action": "买入",
                    "symbol": self.symbol,
                    "quantity": quantity,
                    "price": current_price
                })
                
                return {
                    "success": True,
                    "order_id": result.get('orderId'),
                    "quantity": quantity,
                    "price": current_price,
                    "stop_loss": self.stop_loss_price
                }
            else:
                self.logger.error(f"买入失败: {result}")
                self.status = TradeStatus.IDLE
                return {"success": False, "error": result}
                
        except Exception as e:
            self.logger.error(f"买入异常: {e}")
            self.status = TradeStatus.IDLE
            return {"success": False, "error": str(e)}
    
    def sell(self, quantity: float = None, reason: str = "手动") -> Dict[str, Any]:
        """
        卖出
        
        Args:
            quantity: 数量（默认全仓）
            reason: 卖出原因
            
        Returns:
            交易结果
        """
        if self.status != TradeStatus.HOLDING:
            self.logger.warning(f"当前状态 {self.status}，无持仓可卖")
            return {"success": False, "reason": "无持仓"}
        
        try:
            self.status = TradeStatus.CLOSING
            self.logger.info(f"开始卖出 {self.symbol}")
            
            # 获取当前价格
            current_price = self.fetcher.get_current_price(self.symbol)
            
            # 卖出数量
            quantity = quantity or self.position
            
            # 执行卖出
            result = self.exchange.sell_market(self.symbol, quantity)
            
            if result.get('orderId'):
                # 计算盈亏
                pnl = (current_price - self.position_entry_price) * quantity
                pnl_pct = (current_price - self.position_entry_price) / self.position_entry_price * 100
                
                self.logger.info(f"卖出成功，数量: {quantity}, 价格: {current_price}, 盈亏: {pnl} ({pnl_pct:.2f}%)")
                self.trade_logger.info(f"SELL {self.symbol} {quantity} @ {current_price} PnL: {pnl}")
                
                # 记录交易
                self.daily_trades.append({
                    "time": datetime.now(),
                    "side": "SELL",
                    "symbol": self.symbol,
                    "quantity": quantity,
                    "price": current_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "reason": reason
                })
                
                # 更新连续亏损/盈利计数
                if pnl < 0:
                    self.consecutive_loss += 1
                else:
                    self.consecutive_loss = 0
                
                self.daily_pnl += pnl
                
                # 更新状态
                self.position = 0
                self.position_entry_price = 0
                self.position_time = 0
                self.stop_loss_price = 0
                self.status = TradeStatus.IDLE
                
                # 发送通知
                self.notifier.notify_trade({
                    "action": "卖出",
                    "symbol": self.symbol,
                    "quantity": quantity,
                    "price": current_price
                })
                
                return {
                    "success": True,
                    "order_id": result.get('orderId'),
                    "quantity": quantity,
                    "price": current_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct
                }
            else:
                self.logger.error(f"卖出失败: {result}")
                self.status = TradeStatus.HOLDING
                return {"success": False, "error": result}
                
        except Exception as e:
            self.logger.error(f"卖出异常: {e}")
            self.status = TradeStatus.HOLDING
            return {"success": False, "error": str(e)}
    
    def check_stop_loss(self) -> bool:
        """
        检查是否触发止损
        
        Returns:
            是否触发止损
        """
        if self.status != TradeStatus.HOLDING or self.stop_loss_price <= 0:
            return False
        
        try:
            current_price = self.fetcher.get_current_price(self.symbol)
            
            if current_price <= self.stop_loss_price:
                self.logger.warning(f"触发止损！当前价格: {current_price}, 止损价格: {self.stop_loss_price}")
                self.sell(reason="止损")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查止损失败: {e}")
            return False
    
    def update_position_time(self):
        """更新持仓时间"""
        if self.status == TradeStatus.HOLDING:
            self.position_time += 1
            self.logger.debug(f"持仓时间: {self.position_time} 根K线")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前交易状态
        
        Returns:
            状态字典
        """
        return {
            "status": self.status,
            "symbol": self.symbol,
            "position": self.position,
            "entry_price": self.position_entry_price,
            "current_price": self.fetcher.get_current_price(self.symbol) if self.status == TradeStatus.HOLDING else 0,
            "stop_loss": self.stop_loss_price,
            "position_time": self.position_time,
            "consecutive_loss": self.consecutive_loss,
            "daily_pnl": self.daily_pnl,
            "can_trade": self.can_trade()
        }
    
    def reset_daily(self):
        """重置每日统计"""
        self.daily_trades = []
        self.daily_pnl = 0.0
        self.logger.info("每日统计已重置")
    
    def emergency_close(self):
        """紧急平仓"""
        if self.status == TradeStatus.HOLDING:
            self.logger.warning("执行紧急平仓")
            self.sell(reason="紧急平仓")


# 全局交易器
_trader: Optional[Trader] = None


def get_trader(exchange: BaseExchange = None, fetcher: DataFetcher = None) -> Trader:
    """获取交易器实例"""
    global _trader
    if _trader is None:
        if exchange and fetcher:
            _trader = Trader(exchange, fetcher)
    return _trader


def init_trader(exchange: BaseExchange, fetcher: DataFetcher) -> Trader:
    """初始化交易器"""
    global _trader
    _trader = Trader(exchange, fetcher)
    return _trader
