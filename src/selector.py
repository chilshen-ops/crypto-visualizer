"""
选币模块 - 从多个监控币种中选出最优币
"""
from typing import List, Dict, Any, Optional
import pandas as pd

from .fetcher import DataFetcher
from .scorer import Scorer, get_scorer
from .logger import get_logger
import config


class SymbolSelector:
    """选币器"""
    
    def __init__(self, fetcher: DataFetcher = None, scorer: Scorer = None):
        """
        初始化选币器
        
        Args:
            fetcher: 数据获取器
            scorer: 评分器
        """
        self.fetcher = fetcher
        self.scorer = scorer or get_scorer()
        self.logger = get_logger("selector")
        
        # 加载配置
        trading_config = config.TRADING_CONFIG
        self.monitor_symbols = trading_config.get("monitor_symbols", 
            ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
        self.interval = trading_config.get("interval", "3m")
    
    def set_fetcher(self, fetcher: DataFetcher):
        """设置数据获取器"""
        self.fetcher = fetcher
    
    def select_best_symbol(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        选出最优币种
        
        Args:
            symbols: 币种列表（默认使用配置的监控列表）
            
        Returns:
            最优币种信息
        """
        symbols = symbols or self.monitor_symbols
        
        if not symbols:
            self.logger.warning("没有监控的币种")
            return {}
        
        if not self.fetcher:
            self.logger.error("未设置数据获取器")
            return {}
        
        self.logger.info(f"开始选币，候选币种: {symbols}")
        
        # 获取所有币种的K线数据
        data = {}
        for symbol in symbols:
            try:
                df = self.fetcher.get_klines(symbol, self.interval, limit=100)
                if df is not None and len(df) >= 20:
                    data[symbol] = df
            except Exception as e:
                self.logger.warning(f"获取 {symbol} 数据失败: {e}")
        
        if not data:
            self.logger.warning("没有获取到有效数据")
            return {}
        
        # 评分排序
        ranked = self.scorer.rank_symbols(data)
        
        if ranked:
            best = ranked[0]
            self.logger.info(f"最优币种: {best['symbol']} (分数: {best['score']})")
            return best
        else:
            self.logger.warning("评分失败")
            return {}
    
    def get_top_symbols(self, symbols: List[str] = None, top_n: int = 3) -> List[Dict]:
        """
        获取排名前N的币种
        
        Args:
            symbols: 币种列表
            top_n: 返回数量
            
        Returns:
            排名前N的币种列表
        """
        symbols = symbols or self.monitor_symbols
        
        if not self.fetcher:
            return []
        
        # 获取数据
        data = {}
        for symbol in symbols:
            try:
                df = self.fetcher.get_klines(symbol, self.interval, limit=100)
                if df is not None and len(df) >= 20:
                    data[symbol] = df
            except Exception as e:
                self.logger.warning(f"获取 {symbol} 数据失败: {e}")
        
        if not data:
            return []
        
        # 评分排序
        ranked = self.scorer.rank_symbols(data)
        
        return ranked[:top_n]
    
    def evaluate_current_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        评估当前持仓币种
        
        Args:
            symbol: 币种
            
        Returns:
            评估结果
        """
        if not self.fetcher:
            return {}
        
        try:
            df = self.fetcher.get_klines(symbol, self.interval, limit=100)
            if df is None or len(df) < 20:
                return {}
            
            return self.scorer.score_symbol(df)
        except Exception as e:
            self.logger.warning(f"评估 {symbol} 失败: {e}")
            return {}


# 全局选币器
_selector: Optional[SymbolSelector] = None


def get_selector(fetcher: DataFetcher = None) -> SymbolSelector:
    """获取选币器实例"""
    global _selector
    if _selector is None:
        _selector = SymbolSelector(fetcher)
    elif fetcher:
        _selector.set_fetcher(fetcher)
    return _selector
