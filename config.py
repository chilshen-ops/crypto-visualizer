"""
所有参数配置
"""

# ========== 交易配置 ==========
TRADING_CONFIG = {
    "exchange": "binance",        # 交易所: binance/okx/huobi
    "symbol": "ETHUSDT",          # 交易对
    "interval": "3m",             # K线周期
    "monitor_symbols": [          # 监控币种
        "ETHUSDT", "BTCUSDT", "BNBUSDT", "SOLUSDT", "DOGEUSDT"
    ],
    "stop_loss_ratio": 0.05,      # 止损比例
    "min_position_time": 1,       # 最小持仓K线数
}

# ========== 仓位配置 ==========
POSITION_CONFIG = {
    "full_position_threshold": 1000,
    "position_steps": [0.33, 0.33, 0.34],
    "max_position_ratio": 1.0,  # 全仓 100%
}

# ========== 风控配置 ==========
RISK_CONFIG = {
    "max_consecutive_loss": 3,
    "daily_loss_limit": 0.10,
    "max_position_hours": 24,
}

# ========== AI 配置 ==========
AI_CONFIG = {
    "model": "gpt-oss:latest",
    "host": "http://localhost:11434",
    "confidence_threshold": 0.7,
    "temperature": 0.7,
    "max_tokens": 500,
}

# ========== 评分配置 ==========
SCORER_CONFIG = {
    "kdj_gold_cross_score": 10,
    "rsi_oversold_score": 10,
    "macd_gold_cross_score": 10,
    "trend_up_score": 5,
    "volatility_penalty": -5,
}

# ========== 网络配置 ==========
NETWORK_CONFIG = {
    "retry_times": 3,
    "retry_delay": 2,
    "timeout": 10,
    "ws_heartbeat": 30,
}

# ========== 通知配置 ==========
NOTIFY_CONFIG = {
    "enabled": True,
    "webhook": "https://oapi.dingtalk.com/robot/send?access_token=53abfe6c43d0b1f4d5388e1e3ddc12e616c39c19131da6ce1b74563728fdb5ab",
    "secret": "",                 # 加签密钥（可选）
    "notify_on_trade": True,      # 交易时通知
    "notify_on_error": True,      # 错误时通知
    "notify_on_start": True,      # 启动时通知
    "notify_on_stop": True,       # 停止时通知
}

# ========== 安全配置 ==========
SECURITY_CONFIG = {
    "api_key": "d2g8wRHiLFznhGgrRFAPRoDkoS64ZccTj5CPwSJcG0F9aV7SheL6hlDaNsdxvFGh",
    "api_secret": "PZyGnfHKsEoBGXmmETIO7mWz0gHj5mdfiWJNTGHJRlqFFXPQzTGQb4JCV8GU9xNU",
    "ui_password": "",
    "encrypt_api_key": True,
    "testnet_mode": False,  # 实盘模式
}

# ========== 日志配置 ==========
LOG_CONFIG = {
    "level": "INFO",              # DEBUG/INFO/WARNING/ERROR
    "log_dir": "logs",            # 日志目录
    "max_size": 10,               # 单文件最大MB
    "backup_count": 5,            # 保留文件数
    "trade_log_separate": True,   # 交易日志单独文件
}

# ========== 备份配置 ==========
BACKUP_CONFIG = {
    "enabled": False,             # 是否启用
    "interval_hours": 24,         # 备份间隔
    "keep_days": 7,               # 保留天数
    "backup_dir": "backups",      # 备份目录
}

# ========== UI 配置 ==========
UI_CONFIG = {
    "theme": "dark",
    "refresh_interval": 1,
    "log_lines": 100,
}


def get_config(key: str):
    """获取配置"""
    for config in [TRADING_CONFIG, POSITION_CONFIG, RISK_CONFIG, AI_CONFIG,
                  SCORER_CONFIG, NETWORK_CONFIG, NOTIFY_CONFIG, SECURITY_CONFIG,
                  LOG_CONFIG, BACKUP_CONFIG, UI_CONFIG]:
        if key in config:
            return config[key]
    return None


def get_all_configs():
    """获取所有配置"""
    return {
        "trading": TRADING_CONFIG,
        "position": POSITION_CONFIG,
        "risk": RISK_CONFIG,
        "ai": AI_CONFIG,
        "scorer": SCORER_CONFIG,
        "network": NETWORK_CONFIG,
        "notify": NOTIFY_CONFIG,
        "security": SECURITY_CONFIG,
        "log": LOG_CONFIG,
        "backup": BACKUP_CONFIG,
        "ui": UI_CONFIG,
    }
