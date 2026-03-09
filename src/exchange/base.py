"""
交易所适配器基类
定义统一接口，所有交易所实现需继承此类
"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseExchange(ABC):
    """交易所统一接口"""

    # ========== 市场数据 ==========
    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """获取K线"""
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> dict:
        """获取实时行情"""
        pass

    @abstractmethod
    def get_symbols(self) -> list:
        """获取交易对列表"""
        pass

    # ========== 账户 ==========
    @abstractmethod
    def get_balance(self) -> dict:
        """获取余额"""
        pass

    # ========== 交易 ==========
    @abstractmethod
    def buy_market(self, symbol: str, quantity: float) -> dict:
        """市价买入"""
        pass

    @abstractmethod
    def sell_market(self, symbol: str, quantity: float) -> dict:
        """市价卖出"""
        pass

    @abstractmethod
    def set_stop_loss(self, symbol: str, price: float, quantity: float) -> dict:
        """设置止损"""
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """取消订单"""
        pass

    @abstractmethod
    def get_order(self, symbol: str, order_id: int) -> dict:
        """查询订单"""
        pass

    @abstractmethod
    def get_open_orders(self, symbol: str = None) -> list:
        """获取挂单"""
        pass

    # ========== WebSocket ==========
    @abstractmethod
    def subscribe_kline(self, symbol: str, interval: str, callback):
        """订阅K线"""
        pass

    @abstractmethod
    def subscribe_ticker(self, symbol: str, callback):
        """订阅行情"""
        pass

    @abstractmethod
    def connect_websocket(self):
        """连接WebSocket"""
        pass

    @abstractmethod
    def disconnect_websocket(self):
        """断开WebSocket"""
        pass

    # ========== 辅助方法 ==========
    def parse_klines(self, raw_data: list) -> pd.DataFrame:
        """
        解析K线数据为DataFrame
        子类可重写以适应不同交易所格式
        """
        df = pd.DataFrame(raw_data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df
