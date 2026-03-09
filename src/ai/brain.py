"""
AI 决策模块 - 使用 Ollama 本地模型进行交易决策
"""
import json
import time
import requests
from typing import Optional, Dict, Any, List
import pandas as pd

from src.fetcher import DataFetcher
from src.analyzer import TechnicalAnalyzer
from src.logger import get_logger
import config


class AIBrain:
    """AI 决策大脑"""
    
    def __init__(self, fetcher: DataFetcher = None, analyzer: TechnicalAnalyzer = None):
        """
        初始化 AI 大脑
        
        Args:
            fetcher: 数据获取器
            analyzer: 技术分析器
        """
        self.fetcher = fetcher
        self.analyzer = analyzer or TechnicalAnalyzer()
        self.logger = get_logger("ai")
        
        # 加载配置
        ai_config = config.AI_CONFIG
        self.model = ai_config.get("model", "llama3")
        self.host = ai_config.get("host", "http://localhost:11434")
        self.confidence_threshold = ai_config.get("confidence_threshold", 0.7)
        self.temperature = ai_config.get("temperature", 0.7)
        self.max_tokens = ai_config.get("max_tokens", 500)
        
        self.last_decision = None
        self.last_decision_time = 0
    
    def set_fetcher(self, fetcher: DataFetcher):
        """设置数据获取器"""
        self.fetcher = fetcher
    
    def analyze(self, symbol: str, interval: str = "3m") -> Dict[str, Any]:
        """
        分析并做出决策
        
        Args:
            symbol: 交易对
            interval: K线周期
            
        Returns:
            决策结果
        """
        if not self.fetcher:
            self.logger.error("未设置数据获取器")
            return {"action": "hold", "reason": "数据获取器未初始化"}
        
        try:
            # 1. 获取数据
            df = self.fetcher.get_klines(symbol, interval, limit=100)
            if df is None or len(df) < 20:
                return {"action": "hold", "reason": "数据不足"}
            
            # 2. 计算指标
            self.analyzer.calculate(df)
            indicators = self.analyzer.get_latest_indicators(df)
            patterns = self.analyzer.detect_patterns(df)
            
            # 3. 构建提示词
            prompt = self._build_prompt(symbol, indicators, patterns)
            
            # 4. 调用 Ollama
            response = self._call_ollama(prompt)
            
            # 5. 解析决策
            decision = self._parse_response(response, indicators, patterns)
            
            self.last_decision = decision
            self.last_decision_time = time.time()
            
            self.logger.info(f"AI 决策: {decision.get('action')} - {decision.get('reason')}")
            
            return decision
            
        except Exception as e:
            self.logger.error(f"AI 分析失败: {e}")
            return {"action": "hold", "reason": f"分析异常: {e}"}
    
    def _build_prompt(self, symbol: str, indicators: Dict, patterns: Dict) -> str:
        """构建提示词"""
        
        # 提取关键指标
        price = indicators.get('price', 0)
        rsi = indicators.get('rsi', 50)
        macd_dif = indicators.get('macd_dif', 0)
        macd_hist = indicators.get('macd_hist', 0)
        kdj_k = indicators.get('kdj_k', 50)
        kdj_j = indicators.get('kdj_j', 50)
        ma5 = indicators.get('ma5', 0)
        ma20 = indicators.get('ma20', 0)
        
        # 提取形态信号
        signals = []
        if patterns.get('kdj_golden_cross'): signals.append("KDJ金叉")
        if patterns.get('kdj_death_cross'): signals.append("KDJ死叉")
        if patterns.get('macd_golden_cross'): signals.append("MACD金叉")
        if patterns.get('macd_death_cross'): signals.append("MACD死叉")
        if patterns.get('rsi_oversold'): signals.append("RSI超卖")
        if patterns.get('rsi_overbought'): signals.append("RSI超买")
        if patterns.get('ma_golden_cross'): signals.append("MA金叉")
        if patterns.get('ma_death_cross'): signals.append("MA死叉")
        
        signal_str = ", ".join(signals) if signals else "无明显信号"
        
        prompt = f"""你是一个专业的数字货币交易分析师。请分析以下数据并给出交易建议。

当前交易对: {symbol}
当前价格: {price}

技术指标:
- RSI(14): {rsi:.2f}
- MACD DIF: {macd_dif:.4f}
- MACD 柱状: {macd_hist:.4f}
- KDJ K: {kdj_k:.2f}
- KDJ J: {kdj_j:.2f}
- MA5: {ma5:.2f}
- MA20: {ma20:.2f}

技术信号: {signal_str}

请给出交易建议，格式如下:
ACTION: buy/sell/hold
REASON: 简短的原因说明
CONFIDENCE: 0.0-1.0 的置信度

只返回这三行，不要其他内容。"""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """调用 Ollama API"""
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                self.logger.error(f"Ollama 请求失败: {response.status_code}")
                return ""
                
        except requests.exceptions.ConnectionError:
            self.logger.error("无法连接到 Ollama，请确保 Ollama 已启动")
            return ""
        except Exception as e:
            self.logger.error(f"Ollama 调用异常: {e}")
            return ""
    
    def _parse_response(self, response: str, indicators: Dict, patterns: Dict) -> Dict[str, Any]:
        """解析 AI 响应"""
        
        # 默认决策
        decision = {
            "action": "hold",
            "reason": "无有效决策",
            "confidence": 0,
            "thinking": "",
            "raw_response": response
        }
        
        if not response:
            decision["reason"] = "AI 无响应"
            return decision
        
        # 保存完整思考过程
        decision["thinking"] = response
        
        # 解析 ACTION
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip().upper()
            if line.startswith('ACTION:'):
                action = line.replace('ACTION:', '').strip().lower()
                if action in ['buy', 'sell', 'hold']:
                    decision['action'] = action
            
            elif line.startswith('REASON:'):
                decision['reason'] = line.replace('REASON:', '').strip()
            
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.replace('CONFIDENCE:', '').strip())
                    decision['confidence'] = min(1.0, max(0.0, confidence))
                except:
                    pass
        
        # 如果置信度低于阈值，改为 hold
        if decision['confidence'] < self.confidence_threshold:
            decision['action'] = 'hold'
            decision['reason'] += f" (置信度{decision['confidence']:.2f}低于阈值)"
        
        return decision
    
    def validate_decision(self, decision: Dict[str, Any], 
                         current_position: bool = False) -> bool:
        """
        验证决策是否合理
        
        Args:
            decision: 决策结果
            current_position: 当前是否有持仓
            
        Returns:
            是否执行决策
        """
        action = decision.get('action', 'hold')
        
        # 有持仓只能卖
        if current_position and action == 'buy':
            self.logger.warning("当前有持仓，忽略买入信号")
            return False
        
        # 无持仓只能买
        if not current_position and action == 'sell':
            self.logger.warning("当前无持仓，忽略卖出信号")
            return False
        
        # 置信度检查
        if decision.get('confidence', 0) < self.confidence_threshold:
            self.logger.info(f"置信度 {decision['confidence']} 低于阈值 {self.confidence_threshold}")
            return False
        
        return True
    
    def get_last_decision(self) -> Optional[Dict]:
        """获取上次决策"""
        return self.last_decision


# 全局 AI 大脑
_brain: Optional[AIBrain] = None


def get_ai_brain(fetcher: DataFetcher = None) -> AIBrain:
    """获取 AI 大脑实例"""
    global _brain
    if _brain is None:
        _brain = AIBrain(fetcher)
    elif fetcher:
        _brain.set_fetcher(fetcher)
    return _brain


def init_ai_brain(fetcher: DataFetcher = None, model: str = None) -> AIBrain:
    """初始化 AI 大脑"""
    global _brain
    if model:
        config.AI_CONFIG['model'] = model
    _brain = AIBrain(fetcher)
    return _brain
