"""
数据获取模块
"""
import time
from typing import Optional, List, Dict, Any
import pandas as pd

from .exchange.base import BaseExchange
from .logger import get_logger
from .error_handler import handle_error


class DataFetcher:
    """数据获取器"""
    
    def __init__(self, exchange: BaseExchange):
        """
        初始化数据获取器
        
        Args:
            exchange: 交易所实例
        """
        self.exchange = exchange
        self.logger = get_logger("fetcher")
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 60  # 缓存有效期（秒）
    
    @handle_error("获取K线数据", notify=True, retry=True)
    def get_klines(self, symbol: str, interval: str = "3m", 
                   limit: int = 100, use_cache: bool = True) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: K线周期
            limit: 数量
            use_cache: 是否使用缓存
            
        Returns:
            DataFrame
        """
        cache_key = f"klines_{symbol}_{interval}_{limit}"
        
        # 检查缓存
        if use_cache and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                self.logger.debug(f"使用缓存: {cache_key}")
                return cached_data
        
        # 获取数据
        df = self.exchange.get_klines(symbol, interval, limit)
        
        # 更新缓存
        if use_cache:
            self.cache[cache_key] = (df, time.time())
        
        self.logger.info(f"获取 {symbol} {interval} K线 {len(df)} 条")
        return df
    
    def get_recent_klines(self, symbol: str, interval: str = "3m", 
                          minutes: int = 60) -> pd.DataFrame:
        """
        获取最近N分钟的K线
        
        Args:
            symbol: 交易对
            interval: K线周期
            minutes: 分钟数
            
        Returns:
            DataFrame
        """
        # 估算需要的K线数量
        interval_map = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "1h": 60}
        interval_minutes = interval_map.get(interval, 3)
        limit = max(10, minutes // interval_minutes + 10)
        
        return self.get_klines(symbol, interval, limit)
    
    @handle_error("获取行情", notify=True)
    def get_ticker(self, symbol: str, use_cache: bool = True) -> Dict:
        """
        获取实时行情
        
        Args:
            symbol: 交易对
            use_cache: 是否使用缓存
            
        Returns:
            行情字典
        """
        cache_key = f"ticker_{symbol}"
        
        if use_cache and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < 5:  # 行情缓存5秒
                return cached_data
        
        ticker = self.exchange.get_ticker(symbol)
        
        if use_cache:
            self.cache[cache_key] = (ticker, time.time())
        
        return ticker
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        ticker = self.get_ticker(symbol)
        return float(ticker.get('lastPrice', 0))
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        获取多个币种价格
        
        Args:
            symbols: 交易对列表
            
        Returns:
            价格字典 {symbol: price}
        """
        prices = {}
        for symbol in symbols:
            try:
                prices[symbol] = self.get_current_price(symbol)
            except Exception as e:
                self.logger.warning(f"获取 {symbol} 价格失败: {e}")
                prices[symbol] = 0
        return prices
    
    @handle_error("获取交易对列表", notify=False)
    def get_symbols(self) -> List[str]:
        """获取可交易的交易对列表"""
        symbols = self.exchange.get_symbols()
        # 过滤 USDT 交易对
        usdt_symbols = [s for s in symbols if s.endswith('USDT')]
        self.logger.info(f"获取到 {len(usdt_symbols)} 个 USDT 交易对")
        return usdt_symbols
    
    def get_balance(self) -> Dict:
        """获取账户余额"""
        return self.exchange.get_balance()
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.logger.info("缓存已清空")
    
    def get_market_stats(self, symbol: str) -> Dict[str, Any]:
        """
        获取市场统计数据
        
        Args:
            symbol: 交易对
            
        Returns:
            统计字典
        """
        ticker = self.get_ticker(symbol)
        
        return {
            "symbol": symbol,
            "price": float(ticker.get('lastPrice', 0)),
            "change_24h": float(ticker.get('priceChange', 0)),
            "change_pct_24h": float(ticker.get('priceChangePercent', 0)),
            "high_24h": float(ticker.get('highPrice', 0)),
            "low_24h": float(ticker.get('lowPrice', 0)),
            "volume_24h": float(ticker.get('volume', 0)),
            "quote_volume_24h": float(ticker.get('quoteVolume', 0)),
            "trades_24h": int(ticker.get('count', 0)),
        }
