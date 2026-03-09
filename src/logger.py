"""
日志系统
"""
import os
import sys
import logging
import time
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

import config


class Logger:
    """日志管理器"""
    
    _instances = {}
    
    def __init__(self, name: str, log_dir: str = "logs", level: str = "INFO", 
                 max_size: int = 10, backup_count: int = 5):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
            level: 日志级别
            max_size: 单文件最大MB
            backup_count: 保留文件数
        """
        self.name = name
        self.log_dir = log_dir
        self.level = getattr(logging, level.upper())
        
        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建 logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        self.logger.handlers = []  # 清除已有 handlers
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件 handler（带轮转）
        log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_size * 1024 * 1024, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 控制台 handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def critical(self, msg: str):
        self.logger.critical(msg)


# 全局日志器
_loggers = {}


def get_logger(name: str = "crypto") -> Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        Logger 实例
    """
    if name in _loggers:
        return _loggers[name]
    
    # 从配置读取
    log_config = config.LOG_CONFIG
    logger = Logger(
        name=name,
        log_dir=log_config.get("log_dir", "logs"),
        level=log_config.get("level", "INFO"),
        max_size=log_config.get("max_size", 10),
        backup_count=log_config.get("backup_count", 5)
    )
    _loggers[name] = logger
    return logger


def get_trade_logger() -> Logger:
    """获取交易专用日志器"""
    trade_logger = get_logger("trade")
    trade_logger.info("=" * 50)
    trade_logger.info("交易日志初始化")
    trade_logger.info("=" * 50)
    return trade_logger
