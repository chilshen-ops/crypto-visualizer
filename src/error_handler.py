"""
错误处理模块
"""
import traceback
import sys
import time
from typing import Optional, Callable, Any
from functools import wraps

from .logger import get_logger
from .notifier import get_notifier


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, notifier=None):
        """
        初始化错误处理器
        
        Args:
            notifier: 通知器实例
        """
        self.logger = get_logger("error")
        self.notifier = notifier
        self.error_count = 0
        self.last_error_time = 0
        self.error_cooldown = 60  # 错误通知冷却时间（秒）
    
    def handle_error(self, error: Exception, context: str = "", 
                     notify: bool = True, retry: bool = False,
                     retry_func: Optional[Callable] = None,
                     max_retries: int = 3,
                     retry_delay: int = 2) -> Any:
        """
        处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            notify: 是否发送通知
            retry: 是否重试
            retry_func: 重试函数
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            
        Returns:
            重试结果或 None
        """
        self.error_count += 1
        error_msg = f"{context}: {str(error)}" if context else str(error)
        
        # 记录日志
        self.logger.error(error_msg)
        self.logger.error(traceback.format_exc())
        
        # 发送通知（带冷却）
        current_time = time.time()
        if notify and self.notifier and (current_time - self.last_error_time) > self.error_cooldown:
            self.notifier.notify_error(
                error_type=context or type(error).__name__,
                details=error_msg[:200],
                action=f"重试 {max_retries} 次" if retry else "请检查"
            )
            self.last_error_time = current_time
        
        # 重试机制
        if retry and retry_func:
            for i in range(max_retries):
                self.logger.info(f"重试 {i+1}/{max_retries}...")
                time.sleep(retry_delay)
                try:
                    result = retry_func()
                    self.logger.info("重试成功")
                    return result
                except Exception as e:
                    self.logger.warning(f"重试失败: {e}")
            
            self.logger.error(f"重试 {max_retries} 次后仍失败")
        
        return None
    
    def safe_call(self, func: Callable, default: Any = None, 
                  context: str = "", notify: bool = True) -> Any:
        """
        安全调用函数
        
        Args:
            func: 要调用的函数
            default: 失败时的默认返回值
            context: 错误上下文
            notify: 是否发送通知
            
        Returns:
            函数返回值或默认值
        """
        try:
            return func()
        except Exception as e:
            self.handle_error(e, context=context, notify=notify)
            return default
    
    def reset_error_count(self):
        """重置错误计数"""
        self.error_count = 0


# 全局错误处理器
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def init_error_handler(notifier=None) -> ErrorHandler:
    """初始化错误处理器"""
    global _error_handler
    _error_handler = ErrorHandler(notifier)
    return _error_handler


def handle_error(context: str = "", notify: bool = True, retry: bool = False):
    """
    装饰器：自动处理错误
    
    Usage:
        @handle_error("获取K线数据", notify=True, retry=True)
        def get_data():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retry_func = lambda: func(*args, **kwargs)
                return handler.handle_error(
                    e, 
                    context=context, 
                    notify=notify,
                    retry=retry,
                    retry_func=retry_func
                )
        return wrapper
    return decorator
