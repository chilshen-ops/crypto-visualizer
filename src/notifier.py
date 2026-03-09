"""
钉钉通知模块
"""
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any
import requests

import config


class Notifier:
    """钉钉通知器"""

    def __init__(self, config_dict: Optional[Dict] = None):
        """
        初始化通知器
        
        Args:
            config_dict: 配置字典，默认从 config.py 读取
        """
        if config_dict is None:
            config_dict = config.NOTIFY_CONFIG
        
        self.enabled = config_dict.get("enabled", True)
        self.webhook = config_dict.get("webhook", "")
        self.secret = config_dict.get("secret", "")
        self.notify_on_trade = config_dict.get("notify_on_trade", True)
        self.notify_on_error = config_dict.get("notify_on_error", True)
        self.notify_on_start = config_dict.get("notify_on_start", True)
        self.notify_on_stop = config_dict.get("notify_on_stop", True)

    def _sign(self) -> str:
        """
        生成加签签名
        
        Returns:
            签名字符串
        """
        if not self.secret:
            return ""
        
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return f"&timestamp={timestamp}&sign={sign}"

    def send(self, text: str, msg_type: str = "text", title: str = "") -> bool:
        """
        发送消息
        
        Args:
            text: 消息内容
            msg_type: 消息类型 (text/markdown)
            title: 标题（markdown 消息使用）
            
        Returns:
            是否发送成功
        """
        if not self.enabled or not self.webhook:
            return False
        
        try:
            # 构建 URL（含签名）
            url = self.webhook
            sign = self._sign()
            if sign:
                url = f"{self.webhook}{sign}"
            
            # 构建消息体
            if msg_type == "markdown":
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": title,
                        "text": text
                    }
                }
            else:
                payload = {
                    "msgtype": "text",
                    "text": {
                        "content": text
                    }
                }
            
            # 发送请求
            response = requests.post(
                url, 
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            result = response.json()
            
            if result.get("errcode") == 0:
                return True
            else:
                print(f"[Notifier] 发送失败: {result}")
                return False
                
        except Exception as e:
            print(f"[Notifier] 发送异常: {e}")
            return False

    def notify_trade(self, trade: Dict[str, Any]) -> bool:
        """
        发送交易通知
        
        Args:
            trade: 交易信息字典
                - action: 买入/卖出
                - symbol: 币种
                - quantity: 数量
                - price: 价格（可选）
                
        Returns:
            是否发送成功
        """
        if not self.notify_on_trade:
            return False
        
        action = trade.get("action", "未知")
        symbol = trade.get("symbol", "")
        quantity = trade.get("quantity", 0)
        price = trade.get("price", 0)
        
        text = f"### 交易通知\n---\n**操作**: {action}\n**币种**: {symbol}\n**数量**: {quantity}"
        if price:
            text += f"\n**价格**: {price}"
        
        return self.send(text, msg_type="markdown", title="交易通知")

    def notify_error(self, error_type: str, details: str, action: str = "") -> bool:
        """
        发送错误通知
        
        Args:
            error_type: 错误类型
            details: 错误详情
            action: 建议操作
            
        Returns:
            是否发送成功
        """
        if not self.notify_on_error:
            return False
        
        text = f"### 错误告警\n---\n**类型**: {error_type}\n**详情**: {details}"
        if action:
            text += f"\n**操作**: {action}"
        
        return self.send(text, msg_type="markdown", title="错误告警")

    def notify_status(self, status: str, symbol: str = "", mode: str = "") -> bool:
        """
        发送状态通知
        
        Args:
            status: 状态描述
            symbol: 交易对
            mode: 模式（测试/实盘）
            
        Returns:
            是否发送成功
        """
        text = f"### 系统状态\n---\n**状态**: {status}"
        if symbol:
            text += f"\n**交易对**: {symbol}"
        if mode:
            text += f"\n**模式**: {mode}"
        
        return self.send(text, msg_type="markdown", title="系统状态")

    def notify_report(self, report: Dict[str, Any]) -> bool:
        """
        发送报告通知
        
        Args:
            report: 报告字典
                - date: 日期
                - profit: 收益
                - trades: 交易次数
                - win_rate: 胜率（可选）
                
        Returns:
            是否发送成功
        """
        date = report.get("date", datetime.now().strftime("%Y-%m-%d"))
        profit = report.get("profit", 0)
        trades = report.get("trades", 0)
        win_rate = report.get("win_rate", 0)
        
        text = f"### 日报 {date}\n---\n**收益**: {profit}"
        if win_rate:
            text += f" (+{win_rate}%)"
        text += f"\n**交易**: {trades}笔"
        if win_rate:
            text += f"\n**胜率**: {win_rate}%"
        
        return self.send(text, msg_type="markdown", title=f"日报 {date}")


# 全局通知器实例
_notifier: Optional[Notifier] = None


def get_notifier() -> Notifier:
    """获取全局通知器实例"""
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier


def init_notifier(config_dict: Dict = None) -> Notifier:
    """初始化通知器"""
    global _notifier
    _notifier = Notifier(config_dict)
    return _notifier
