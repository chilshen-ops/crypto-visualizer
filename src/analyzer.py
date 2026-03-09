"""
指标计算模块
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from .logger import get_logger


class TechnicalAnalyzer:
    """技术指标分析器"""
    
    def __init__(self):
        self.logger = get_logger("analyzer")
    
    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算所有指标
        
        Args:
            df: K线数据
            
        Returns:
            指标字典
        """
        if df is None or len(df) < 20:
            return {}
        
        return {
            "ma": self.calculate_ma(df),
            "ema": self.calculate_ema(df),
            "rsi": self.calculate_rsi(df),
            "macd": self.calculate_macd(df),
            "kdj": self.calculate_kdj(df),
            "bollinger": self.calculate_bollinger(df),
            "atr": self.calculate_atr(df),
        }
    
    def calculate_ma(self, df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> Dict[str, pd.Series]:
        """
        计算移动平均线
        
        Args:
            df: K线数据
            periods: 周期列表
            
        Returns:
            MA 字典
        """
        result = {}
        for period in periods:
            col = f"ma{period}"
            df[col] = df['close'].rolling(window=period).mean()
            result[col] = df[col]
        return result
    
    def calculate_ema(self, df: pd.DataFrame, periods: list = [12, 26]) -> Dict[str, pd.Series]:
        """
        计算指数移动平均线
        
        Args:
            df: K线数据
            periods: 周期列表
            
        Returns:
            EMA 字典
        """
        result = {}
        for period in periods:
            col = f"ema{period}"
            df[col] = df['close'].ewm(span=period, adjust=False).mean()
            result[col] = df[col]
        return result
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算 RSI 相对强弱指标
        
        Args:
            df: K线数据
            period: 周期
            
        Returns:
            RSI Series
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        df['rsi'] = rsi
        return rsi
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, 
                       slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        计算 MACD 指标
        
        Args:
            df: K线数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            MACD 字典
        """
        # 计算 EMA
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        # DIF (MACD 线)
        df['macd_dif'] = ema_fast - ema_slow
        
        # DEA (信号线)
        df['macd_dea'] = df['macd_dif'].ewm(span=signal, adjust=False).mean()
        
        # MACD 柱状图
        df['macd_hist'] = (df['macd_dif'] - df['macd_dea']) * 2
        
        return {
            "dif": df['macd_dif'],
            "dea": df['macd_dea'],
            "hist": df['macd_hist'],
        }
    
    def calculate_kdj(self, df: pd.DataFrame, period: int = 9) -> Dict[str, pd.Series]:
        """
        计算 KDJ 随机指标
        
        Args:
            df: K线数据
            period: 周期
            
        Returns:
            KDJ 字典
        """
        low_n = df['low'].rolling(window=period).min()
        high_n = df['high'].rolling(window=period).max()
        
        # K 值
        df['kdj_k'] = 100 * (df['close'] - low_n) / (high_n - low_n)
        
        # D 值
        df['kdj_d'] = df['kdj_k'].rolling(window=3).mean()
        
        # J 值
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        return {
            "k": df['kdj_k'],
            "d": df['kdj_d'],
            "j": df['kdj_j'],
        }
    
    def calculate_bollinger(self, df: pd.DataFrame, period: int = 20, 
                           std_dev: float = 2) -> Dict[str, pd.Series]:
        """
        计算布林带指标
        
        Args:
            df: K线数据
            period: 周期
            std_dev: 标准差倍数
            
        Returns:
            布林带字典
        """
        df['bb_mid'] = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        df['bb_upper'] = df['bb_mid'] + std_dev * std
        df['bb_lower'] = df['bb_mid'] - std_dev * std
        
        # 计算 %B
        df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 计算带宽
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        
        return {
            "upper": df['bb_upper'],
            "mid": df['bb_mid'],
            "lower": df['bb_lower'],
            "percent": df['bb_percent'],
            "width": df['bb_width'],
        }
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算 ATR 平均真实波幅
        
        Args:
            df: K线数据
            period: 周期
            
        Returns:
            ATR Series
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        df['atr'] = atr
        return atr
    
    def get_latest_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取最新的指标值
        
        Args:
            df: K线数据（已计算指标）
            
        Returns:
            最新指标字典
        """
        if df is None or len(df) == 0:
            return {}
        
        latest = df.iloc[-1]
        
        return {
            "price": latest.get('close', 0),
            "ma5": latest.get('ma5', 0),
            "ma10": latest.get('ma10', 0),
            "ma20": latest.get('ma20', 0),
            "rsi": latest.get('rsi', 50),
            "macd_dif": latest.get('macd_dif', 0),
            "macd_dea": latest.get('macd_dea', 0),
            "macd_hist": latest.get('macd_hist', 0),
            "kdj_k": latest.get('kdj_k', 50),
            "kdj_d": latest.get('kdj_d', 50),
            "kdj_j": latest.get('kdj_j', 50),
            "bb_upper": latest.get('bb_upper', 0),
            "bb_mid": latest.get('bb_mid', 0),
            "bb_lower": latest.get('bb_lower', 0),
            "atr": latest.get('atr', 0),
        }
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        检测常见形态
        
        Args:
            df: K线数据
            
        Returns:
            形态检测结果
        """
        if df is None or len(df) < 5:
            return {}
        
        patterns = {}
        
        # 金叉/死叉
        if 'ma5' in df.columns and 'ma10' in df.columns:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # MA5 上穿 MA10 = 金叉
            patterns['ma_golden_cross'] = (
                prev['ma5'] <= prev['ma10'] and 
                latest['ma5'] > latest['ma10']
            )
            
            # MA5 下穿 MA10 = 死叉
            patterns['ma_death_cross'] = (
                prev['ma5'] >= prev['ma10'] and 
                latest['ma5'] < latest['ma10']
            )
        
        # KDJ 金叉/死叉
        if 'kdj_k' in df.columns and 'kdj_d' in df.columns:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            patterns['kdj_golden_cross'] = (
                prev['kdj_k'] <= prev['kdj_d'] and 
                latest['kdj_k'] > latest['kdj_d']
            )
            
            patterns['kdj_death_cross'] = (
                prev['kdj_k'] >= prev['kdj_d'] and 
                latest['kdj_k'] < latest['kdj_d']
            )
        
        # RSI 超买超卖
        if 'rsi' in df.columns:
            rsi = df.iloc[-1]['rsi']
            patterns['rsi_oversold'] = rsi < 30
            patterns['rsi_overbought'] = rsi > 70
            patterns['rsi_neutral'] = 30 <= rsi <= 70
        
        # MACD 金叉/死叉
        if 'macd_dif' in df.columns and 'macd_dea' in df.columns:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            patterns['macd_golden_cross'] = (
                prev['macd_dif'] <= prev['macd_dea'] and 
                latest['macd_dif'] > latest['macd_dea']
            )
            
            patterns['macd_death_cross'] = (
                prev['macd_dif'] >= prev['macd_dea'] and 
                latest['macd_dif'] < latest['macd_dea']
            )
        
        return patterns


# 全局分析器实例
_analyzer: Optional[TechnicalAnalyzer] = None


def get_analyzer() -> TechnicalAnalyzer:
    """获取技术分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TechnicalAnalyzer()
    return _analyzer
