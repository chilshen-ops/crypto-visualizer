"""
币安交易所适配器
"""
import os
import json
import time
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
import pandas as pd
import requests
from websocket import create_connection, WebSocketApp

# 尝试使用官方库
try:
    from binance.client import Client as BinanceClient
    HAS_BINANCE_LIB = True
except ImportError:
    HAS_BINANCE_LIB = False

from .base import BaseExchange


class BinanceExchange(BaseExchange):
    """币安交易所实现"""

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        """
        初始化币安交易所
        
        Args:
            api_key: API Key
            api_secret: API Secret
            testnet: 是否使用测试网
        """
        self.api_key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET", "")
        self.testnet = testnet
        
        # 优先使用官方库
        if HAS_BINANCE_LIB and self.api_key and self.api_secret:
            try:
                self.client = BinanceClient(self.api_key, self.api_secret)
                self._use_lib = True
            except:
                self._use_lib = False
        else:
            self._use_lib = False
        
        # 设置 API 地址
        if testnet:
            self.base_url = "https://testnet.binance.vision/api"
            self.ws_url = "wss://testnet.binance.vision/ws"
        else:
            self.base_url = "https://api.binance.com/api"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        
        self.ws: Optional[WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self.ws_subscriptions: Dict[str, Callable] = {}
        self._running = False
        self.testnet = testnet
        
        # 设置 API 地址
        if testnet:
            self.base_url = "https://testnet.binance.vision/api"
            self.ws_url = "wss://testnet.binance.vision/ws"
        else:
            self.base_url = "https://api.binance.com/api"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        
        self.ws: Optional[WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self.ws_subscriptions: Dict[str, Callable] = {}
        self._running = False

    # ========== 通用请求方法 ==========
    def _request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """发送 API 请求"""
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        # 签名
        if signed and self.api_secret:
            # 添加 recvWindow
            params["recvWindow"] = 5000
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._sign(query_string)
            params["signature"] = signature
            headers = {"X-MBX-APIKEY": self.api_key}
        else:
            headers = {}
        
        if method == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, params=params, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, params=params, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        result = response.json()
        
        # 检查错误
        if isinstance(result, dict) and result.get("code"):
            raise Exception(f"Binance API Error: {result.get('msg')} (code: {result.get('code')})")
        
        return result

    def _sign(self, message: str) -> str:
        """生成签名"""
        import hmac
        import hashlib
        return hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    # ========== 市场数据 ==========
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对，如 BTCUSDT
            interval: K线周期，如 1m, 3m, 5m, 15m, 1h
            limit: 返回数量
            
        Returns:
            DataFrame，包含 K线数据
        """
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        
        data = self._request("GET", "/v3/klines", params)
        
        # 转换为 DataFrame
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # 转换类型
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df

    def get_ticker(self, symbol: str) -> dict:
        """
        获取实时行情
        
        Args:
            symbol: 交易对
            
        Returns:
            字典，包含价格信息
        """
        params = {"symbol": symbol.upper()}
        return self._request("GET", "/v3/ticker/24hr", params)

    def get_symbols(self) -> List[str]:
        """
        获取交易对列表
        
        Returns:
            交易对列表
        """
        data = self._request("GET", "/v3/exchangeInfo")
        return [s['symbol'] for s in data['symbols'] if s['status'] == 'TRADING']

    # ========== 账户 ==========
    def get_balance(self) -> dict:
        """
        获取账户余额
        
        Returns:
            余额字典
        """
        # 优先使用官方库
        if getattr(self, '_use_lib', False):
            account = self.client.get_account()
            return {
                "balances": [{"asset": b["asset"], "free": b["free"], "locked": b["locked"]} 
                            for b in account["balances"]]
            }
        
        params = {"timestamp": int(time.time() * 1000)}
        return self._request("GET", "/v3/account", params, signed=True)

    # ========== 交易 ==========
    def buy_market(self, symbol: str, quantity: float) -> dict:
        """
        市价买入
        
        Args:
            symbol: 交易对
            quantity: 数量
            
        Returns:
            订单信息
        """
        # 优先使用官方库
        if getattr(self, '_use_lib', False):
            return self.client.order_market_buy(symbol=symbol.upper(), quantity=quantity)
        
        params = {
            "symbol": symbol.upper(),
            "side": "BUY",
            "type": "MARKET",
            "quantity": quantity,
            "timestamp": int(time.time() * 1000)
        }
        return self._request("POST", "/v3/order", params, signed=True)

    def buy_market_all(self, symbol: str, quote_amount: float = None) -> dict:
        """
        市价全仓买入
        
        Args:
            symbol: 交易对
            quote_amount: 使用多少 USDT买入（默认全部）
            
        Returns:
            订单信息
        """
        # 如果指定了金额
        if quote_amount:
            params = {
                "symbol": symbol.upper(),
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": quote_amount,
                "timestamp": int(time.time() * 1000)
            }
        else:
            # 先获取可用 USDT 余额
            balance = self.get_balance()
            usdt_balance = 0
            for bal in balance.get('balances', []):
                if bal.get('asset') == 'USDT':
                    usdt_balance = float(bal.get('free', 0))
                    break
            
            # 使用全部 USDT
            params = {
                "symbol": symbol.upper(),
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": usdt_balance,
                "timestamp": int(time.time() * 1000)
            }
        
        return self._request("POST", "/v3/order", params, signed=True)

    def sell_market(self, symbol: str, quantity: float) -> dict:
        """
        市价卖出
        
        Args:
            symbol: 交易对
            quantity: 数量
            
        Returns:
            订单信息
        """
        # 优先使用官方库
        if getattr(self, '_use_lib', False):
            return self.client.order_market_sell(symbol=symbol.upper(), quantity=quantity)
        
        params = {
            "symbol": symbol.upper(),
            "side": "SELL",
            "type": "MARKET",
            "quantity": quantity,
            "timestamp": int(time.time() * 1000)
        }
        return self._request("POST", "/v3/order", params, signed=True)

    def sell_market_all(self, symbol: str) -> dict:
        """
        市价全仓卖出
        
        Args:
            symbol: 交易对
            
        Returns:
            订单信息
        """
        # 获取当前持仓
        balance = self.get_balance()
        quantity = 0
        
        # 提取交易对的资产（如 BTCUSDT 中的 BTC）
        base_asset = symbol.replace('USDT', '').replace('usdt', '')
        
        for bal in balance.get('balances', []):
            if bal.get('asset') == base_asset:
                quantity = float(bal.get('free', 0))
                break
        
        if quantity <= 0:
            return {"error": "No position to sell"}
        
        params = {
            "symbol": symbol.upper(),
            "side": "SELL",
            "type": "MARKET",
            "quantity": quantity,
            "timestamp": int(time.time() * 1000)
        }
        return self._request("POST", "/v3/order", params, signed=True)

    def set_stop_loss(self, symbol: str, price: float, quantity: float) -> dict:
        """
        设置止损单
        
        Args:
            symbol: 交易对
            price: 止损价格
            quantity: 数量
            
        Returns:
            订单信息
        """
        params = {
            "symbol": symbol.upper(),
            "side": "SELL",
            "type": "STOP_LOSS_LIMIT",
            "quantity": quantity,
            "stopPrice": price,
            "price": price * 0.99,  # 略低于止损价确保成交
            "timeInForce": "GTC",
            "timestamp": int(time.time() * 1000)
        }
        return self._request("POST", "/v3/order", params, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            取消结果
        """
        params = {
            "symbol": symbol.upper(),
            "orderId": order_id,
            "timestamp": int(time.time() * 1000)
        }
        return self._request("DELETE", "/v3/order", params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict:
        """
        查询订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            订单信息
        """
        params = {
            "symbol": symbol.upper(),
            "orderId": order_id,
            "timestamp": int(time.time() * 1000)
        }
        return self._request("GET", "/v3/order", params, signed=True)

    def get_open_orders(self, symbol: str = None) -> List[dict]:
        """
        获取挂单
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            挂单列表
        """
        params = {"timestamp": int(time.time() * 1000)}
        if symbol:
            params["symbol"] = symbol.upper()
        return self._request("GET", "/v3/openOrders", params, signed=True)

    # ========== WebSocket ==========
    def connect_websocket(self):
        """连接 WebSocket"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            return
        
        self.ws = WebSocketApp(
            self.ws_url,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close,
            on_open=self._on_ws_open
        )
        self._running = True
        
        # 启动 WebSocket 线程
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def disconnect_websocket(self):
        """断开 WebSocket"""
        self._running = False
        if self.ws:
            self.ws.close()
            self.ws = None

    def subscribe_kline(self, symbol: str, interval: str, callback: Callable):
        """
        订阅K线
        
        Args:
            symbol: 交易对
            interval: 周期
            callback: 回调函数
        """
        stream = f"{symbol.lower()}@kline_{interval}"
        self.ws_subscriptions[stream] = callback
        
        if self.ws and self._running:
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [stream],
                "id": int(time.time())
            }
            self.ws.send(json.dumps(subscribe_msg))

    def subscribe_ticker(self, symbol: str, callback: Callable):
        """
        订阅行情
        
        Args:
            symbol: 交易对
            callback: 回调函数
        """
        stream = f"{symbol.lower()}@ticker"
        self.ws_subscriptions[stream] = callback
        
        if self.ws and self._running:
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [stream],
                "id": int(time.time())
            }
            self.ws.send(json.dumps(subscribe_msg))

    def _on_ws_message(self, ws, message):
        """WebSocket 消息处理"""
        try:
            data = json.loads(message)
            
            # 处理K线数据
            if 'e' in data and data['e'] == 'kline':
                kline = data['k']
                stream = f"{data['s'].lower()}@kline_{kline['i']}"
                if stream in self.ws_subscriptions:
                    self.ws_subscriptions[stream](kline)
            
            # 处理行情数据
            elif 'e' in data and data['e'] == '24hrTicker':
                stream = f"{data['s'].lower()}@ticker"
                if stream in self.ws_subscriptions:
                    self.ws_subscriptions[stream](data)
                    
        except Exception as e:
            print(f"[Binance] WebSocket 消息解析错误: {e}")

    def _on_ws_error(self, ws, error):
        """WebSocket 错误处理"""
        print(f"[Binance] WebSocket 错误: {error}")

    def _on_ws_close(self, ws, close_status_code, close_msg):
        """WebSocket 关闭处理"""
        print(f"[Binance] WebSocket 已关闭: {close_status_code} - {close_msg}")
        self._running = False

    def _on_ws_open(self, ws):
        """WebSocket 打开处理"""
        print("[Binance] WebSocket 已连接")
        
        # 重新订阅
        for stream in self.ws_subscriptions.keys():
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [stream],
                "id": int(time.time())
            }
            ws.send(json.dumps(subscribe_msg))

    # ========== 便捷方法 ==========
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        ticker = self.get_ticker(symbol)
        return float(ticker.get('lastPrice', 0))

    def get_balance_of(self, asset: str) -> float:
        """获取指定资产余额"""
        balance = self.get_balance()
        for bal in balance.get('balances', []):
            if bal['asset'].upper() == asset.upper():
                return float(bal['free'])
        return 0.0

    def close(self):
        """关闭连接"""
        self.disconnect_websocket()


# 全局实例
_exchange: Optional[BinanceExchange] = None


def get_exchange(api_key: str = "", api_secret: str = "", testnet: bool = True) -> BinanceExchange:
    """获取币安交易所实例"""
    global _exchange
    if _exchange is None:
        _exchange = BinanceExchange(api_key, api_secret, testnet)
    return _exchange


def init_exchange(api_key: str, api_secret: str, testnet: bool = True) -> BinanceExchange:
    """初始化币安交易所"""
    global _exchange
    _exchange = BinanceExchange(api_key, api_secret, testnet)
    return _exchange
