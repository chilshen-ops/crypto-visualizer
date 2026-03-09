"""
评分模块 - 对币种进行技术分析评分
"""
from typing import Dict, Any, Optional
import pandas as pd

from .analyzer import TechnicalAnalyzer, get_analyzer
from .logger import get_logger
import config


class Scorer:
    """评分器"""
    
    def __init__(self, analyzer: TechnicalAnalyzer = None):
        """
        初始化评分器
        
        Args:
            analyzer: 技术分析器
        """
        self.analyzer = analyzer or get_analyzer()
        self.logger = get_logger("scorer")
        
        # 加载配置
        scorer_config = config.SCORER_CONFIG
        self.kdj_gold_cross_score = scorer_config.get("kdj_gold_cross_score", 10)
        self.rsi_oversold_score = scorer_config.get("rsi_oversold_score", 10)
        self.macd_gold_cross_score = scorer_config.get("macd_gold_cross_score", 10)
        self.trend_up_score = scorer_config.get("trend_up_score", 5)
        self.volatility_penalty = scorer_config.get("volatility_penalty", -5)
    
    def score_symbol(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        对币种进行评分
        
        Args:
            df: K线数据（包含指标）
            
        Returns:
            评分结果
        """
        if df is None or len(df) < 20:
            return {"score": 0, "reasons": ["数据不足"]}
        
        score = 0
        reasons = []
        
        # 获取最新指标
        indicators = self.analyzer.get_latest_indicators(df)
        patterns = self.analyzer.detect_patterns(df)
        
        # 1. KDJ 金叉 (+10)
        if patterns.get('kdj_golden_cross', False):
            score += self.kdj_gold_cross_score
            reasons.append("KDJ金叉")
        
        # 2. RSI 超卖反弹 (+10)
        if patterns.get('rsi_oversold', False):
            score += self.rsi_oversold_score
            reasons.append("RSI超卖")
        
        # 3. RSI 中性偏多 (+5)
        rsi = indicators.get('rsi', 50)
        if 40 <= rsi < 60:
            score += 3
            reasons.append("RSI中性偏多")
        
        # 4. MACD 金叉 (+10)
        if patterns.get('macd_golden_cross', False):
            score += self.macd_gold_cross_score
            reasons.append("MACD金叉")
        
        # 5. 趋势向上 (+5)
        if indicators.get('ma5', 0) > indicators.get('ma20', 0):
            score += self.trend_up_score
            reasons.append("MA5>MA20趋势向上")
        
        # 6. 价格在均线之上 (+3)
        if indicators.get('price', 0) > indicators.get('ma5', 0):
            score += 3
            reasons.append("价格>MA5")
        
        # 7. 波动性惩罚
        if 'atr' in df.columns and 'close' in df.columns:
            latest = df.iloc[-1]
            atr = latest.get('atr', 0)
            close = latest.get('close', 1)
            volatility = atr / close if close > 0 else 0
            
            if volatility > 0.05:  # 波动过大
                score += self.volatility_penalty
                reasons.append("波动过大")
        
        # 8. MACD 柱状图转正 (+5)
        if indicators.get('macd_hist', 0) > 0:
            score += 5
            reasons.append("MACD柱状图转正")
        
        # 9. KDJ J 值超卖反弹 (+5)
        kdj_j = indicators.get('kdj_j', 50)
        if kdj_j < 20:
            score += 5
            reasons.append("KDJ J值超卖")
        
        # 10. 布林带下轨反弹 (+5)
        if 'bb_lower' in df.columns and 'close' in df.columns:
            latest = df.iloc[-1]
            if latest['close'] < latest['bb_lower']:
                score += 5
                reasons.append("布林带下轨")
        
        return {
            "score": score,
            "reasons": reasons,
            "indicators": indicators,
            "patterns": patterns,
        }
    
    def rank_symbols(self, data: Dict[str, pd.DataFrame]) -> list:
        """
        对多个币种排序
        
        Args:
            data: {symbol: df} 字典
            
        Returns:
            排序后的列表 [{symbol, score, reasons}, ...]
        """
        results = []
        
        for symbol, df in data.items():
            try:
                result = self.score_symbol(df)
                results.append({
                    "symbol": symbol,
                    "score": result["score"],
                    "reasons": result.get("reasons", []),
                })
            except Exception as e:
                self.logger.warning(f"评分 {symbol} 失败: {e}")
                results.append({
                    "symbol": symbol,
                    "score": -999,
                    "reasons": [f"错误: {e}"],
                })
        
        # 按分数降序排列
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results


# 全局评分器
_scorer: Optional[Scorer] = None


def get_scorer() -> Scorer:
    """获取评分器实例"""
    global _scorer
    if _scorer is None:
        _scorer = Scorer()
    return _scorer
