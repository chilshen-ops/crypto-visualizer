# Crypto Visualizer - 币安量化交易程序大纲

## 项目概述
- 目标：用户输入自然语言策略 → AI 全权处理交易
- 平台：支持多交易所（币安/OKX/火币）
- 交易品种：现货 Spot（支持多交易所）
- 数据：3分钟/5分钟 K线
- AI：本地 Ollama 模型
- GUI：桌面端可视化
- 交易风格：超短线，快进快出，靠交易量赚钱

---

## 核心原则

### 1. 程序与参数分离
- 参数：全部放在 config.py
- 程序：只负责逻辑，不硬编码

### 2. 交易所适配器模式
- 换交易所 → 只需新增 exchange/xx.py
- 核心程序完全不动
- 统一接口：BaseExchange

### 3. 文档同步
- 修改程序 → 先改大纲 → 记录 CHANGELOG

### 4. 错误处理
- 所有异常捕获，不让程序崩溃
- 错误自动记录 + 告警通知
- 异常后自动重试 + 恢复

### 5. 日志系统
- 分级记录：DEBUG / INFO / WARNING / ERROR
- 分模块记录，便于定位问题
- 交易日志单独存储
- 日志轮转，自动清理旧日志

### 6. 数据备份
- 定时自动备份 data/ 文件夹
- 备份保留天数可配置
- 备份失败告警

### 7. 异步处理
- 多任务并行执行
- 数据获取与交易分离
- 提升响应速度

### 8. 性能监控
- 监控 CPU/内存/网络延迟
- 记录交易响应时间
- 性能异常告警

### 9. 参数校验
- 参数边界检查（止损比例0-1之间等）
- 启动前校验配置完整性
- 防止配置错误导致损失

### 10. 版本管理
- 程序版本号
- 配置版本
- 升级时兼容性检查

## 通知模块 (notifier.py)

### 配置 (NOTIFY_CONFIG)
```python
NOTIFY_CONFIG = {
    "enabled": True,
    "webhook": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    "secret": "",              # 加签密钥（可选）
    "notify_on_trade": True,   # 交易时通知
    "notify_on_error": True,   # 错误时通知
    "notify_on_start": True,   # 启动时通知
    "notify_on_stop": True,    # 停止时通知
}
```

### 接口
```python
class Notifier:
    def __init__(self, config: dict)
    def send(self, msg: str, msg_type: str = "text")      # 发送消息
    def notify_trade(self, trade: dict)                   # 交易通知
    def notify_error(self, error: Exception)              # 错误通知
    def notify_status(self, status: str)                  # 状态通知
    def notify_report(self, report: dict)                  # 报告通知
```

### 消息格式 (Markdown)
使用钉钉 markdown 消息类型：

```json
{
    "msgtype": "markdown",
    "markdown": {
        "title": "交易通知",
        "text": "### 交易通知\n---\n**操作**: 买入\n**币种**: BTCUSDT\n**数量**: 0.01\n**价格**: 45000"
    }
}
```

| 类型 | 格式 |
|------|------|
| 交易 | `### 交易通知\n---\n**操作**: 买入\n**币种**: BTCUSDT\n**数量**: 0.01\n**价格**: 45000` |
| 错误 | `### 错误告警\n---\n**类型**: API超时\n**详情**: 连接币安API失败\n**操作**: 3秒后重试` |
| 状态 | `### 系统状态\n---\n**程序**: 已启动\n**交易对**: BTCUSDT\n**模式**: 测试` |
| 报告 | `### 日报 2026-03-09\n---\n**收益**: +50U (+1.2%)\n**交易**: 5笔\n**胜率**: 80%` |

### 特点
- `###` 标题 → 消息类型清晰
- `---` 分隔线 → 结构分明
- `**加粗**` → 关键信息突出

### 12. 断点续传
- 每次操作保存状态
- 程序重启后恢复
- 防止因崩溃丢失进度

---

## 项目结构

```
crypto-visualizer/
├── main.py
├── config.py                  # 所有参数配置
├── config_schema.py           # 参数校验规范
├── data/
│   ├── raw/                   # K线原始数据
│   ├── processed/             # 含指标数据
│   ├── trades/                # 交易记录
│   └── backtest/              # 回测结果
├── src/
│   ├── __init__.py
│   ├── constants.py           # 常量定义
│   ├── logger.py              # 日志系统
│   ├── error_handler.py       # 错误处理
│   ├── backup.py             # 数据备份
│   ├── exchange/              # 交易所适配器
│   │   ├── __init__.py
│   │   ├── base.py           # 基类（统一接口）
│   │   ├── binance.py        # 币安实现
│   │   ├── okx.py            # OKX实现
│   │   └── huobi.py          # 火币实现
│   ├── fetcher.py             # 数据获取
│   ├── storage.py             # 数据持久化
│   ├── trader.py              # 交易执行 + 状态机
│   ├── analyzer.py            # 指标计算
│   ├── cache.py               # 缓存
│   ├── backtester.py          # 回测引擎
│   ├── selector.py            # 选币
│   ├── scorer.py              # 评分逻辑
│   ├── notifier.py            # 钉钉通知
│   ├── security.py            # 安全模块
│   ├── ai/
│   │   ├── brain.py
│   │   ├── memory.py
│   │   ├── validator.py
│   │   ├── optimizer.py
│   │   └── controller.py
│   └── ui/
│       ├── dashboard.py
│       └── strategy_input.py
├── prompts/
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

---

## 交易所适配器规范 (exchange/base.py)

```python
from abc import ABC, abstractmethod

class BaseExchange(ABC):
    """交易所统一接口"""

    # ========== 市场数据 ==========
    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        """获取K线"""
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> dict:
        """获取实时行情"""
        pass

    @abstractmethod
    def get_symbols(self) -> list:
        """获取交易对列表"""
        pass

    # ========== 账户 ==========
    @abstractmethod
    def get_balance(self) -> dict:
        """获取余额"""
        pass

    # ========== 交易 ==========
    @abstractmethod
    def buy_market(self, symbol: str, quantity: float) -> dict:
        """市价买入"""
        pass

    @abstractmethod
    def sell_market(self, symbol: str, quantity: float) -> dict:
        """市价卖出"""
        pass

    @abstractmethod
    def set_stop_loss(self, symbol: str, price: float, quantity: float) -> dict:
        """设置止损"""
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """取消订单"""
        pass

    @abstractmethod
    def get_order(self, symbol: str, order_id: int) -> dict:
        """查询订单"""
        pass

    @abstractmethod
    def get_open_orders(self, symbol: str) -> list:
        """获取挂单"""
        pass

    # ========== WebSocket ==========
    @abstractmethod
    def subscribe_kline(self, symbol: str, callback):
        """订阅K线"""
        pass

    @abstractmethod
    def subscribe_ticker(self, symbol: str, callback):
        """订阅行情"""
        pass
```

---

## 配置文件 (config.py)

```python
"""
所有参数配置
"""

# ========== 交易配置 ==========
TRADING_CONFIG = {
    "exchange": "binance",          # 交易所: binance/okx/huobi
    "symbol": "BTCUSDT",           # 交易对
    "interval": "3m",              # K线周期
    "monitor_symbols": [           # 监控币种
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "DOGEUSDT"
    ],
    "stop_loss_ratio": 0.05,       # 止损比例
    "min_position_time": 1,        # 最小持仓K线数
}

# ========== 仓位配置 ==========
POSITION_CONFIG = {
    "full_position_threshold": 1000,
    "position_steps": [0.33, 0.33, 0.34],
    "max_position_ratio": 0.95,
}

# ========== 风控配置 ==========
RISK_CONFIG = {
    "max_consecutive_loss": 3,
    "daily_loss_limit": 0.10,
    "max_position_hours": 24,
}

# ========== AI 配置 ==========
AI_CONFIG = {
    "model": "llama3",
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
    "enabled": False,
    "webhook": "",
    "secret": "",
    "notify_on_trade": True,
    "notify_on_error": True,
}

# ========== 安全配置 ==========
SECURITY_CONFIG = {
    "ui_password": "",
    "encrypt_api_key": True,
    "testnet_mode": True,
}

# ========== 日志配置 ==========
LOG_CONFIG = {
    "level": "INFO",                # DEBUG/INFO/WARNING/ERROR
    "log_dir": "logs",             # 日志目录
    "max_size": 10,                # 单文件最大MB
    "backup_count": 5,             # 保留文件数
    "trade_log_separate": True,    # 交易日志单独文件
}

# ========== 备份配置 ==========
BACKUP_CONFIG = {
    "enabled": False,               # 是否启用
    "interval_hours": 24,          # 备份间隔
    "keep_days": 7,                # 保留天数
    "backup_dir": "backups",       # 备份目录
}

# ========== UI 配置 ==========
UI_CONFIG = {
    "theme": "dark",
    "refresh_interval": 1,
    "log_lines": 100,
}
```

---

## 常量 (constants.py)

```python
class TradeStatus:
    IDLE = "idle"
    OPENING = "opening"
    HOLDING = "holding"
    CLOSING = "closing"

class OrderSide:
    BUY = "BUY"
    SELL = "SELL"

class OrderType:
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"

class Interval:
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"

class Indicator:
    MA5 = "MA5"
    MA10 = "MA10"
    MA20 = "MA20"
    RSI = "RSI"
    MACD = "MACD"
    KDJ = "KDJ"
    BOLL = "BOLL"
    ATR = "ATR"
```

---

## 核心机制

### 1. 交易流程（状态机）
```
[空闲] → AI判断买入 → [开仓中] → 挂止损单 → [持仓中]
                                              ↓
[空仓中] ← AI判断卖出 ← [平仓中] ← 止损成交/手动平仓/止盈
         ↓
    [熔断检测] → 连续亏损 → 暂停
```

### 1.1 买入流程
```
1. AI发出买入信号
2. 市价买入
3. 立即挂止损单（跌5%）
4. 开始监听止盈信号
```

### 1.2 卖出流程（三种情况）
```
A. 止损卖出：价格跌到止损价 → 自动卖出
B. 止盈卖出：AI判断达到止盈点 → 手动卖出
C. 手动卖出：一键平仓 / 人工干预
```

### 1.3 持仓期间
```
- 每周期检查：是否触发止盈？
- 币种切换：需要用户确认，不自动切换
```

### 1.4 币种切换
```
- 币种由用户决定，不自动切换
- 用户可在监控区查看各币种评分
- 需要换币时，用户手动选择
```

### 2. 多币监控 + 评分选币
- 监控多个币种
- scorer.score_symbol() 评分
- selector.select_best_symbol() 选最优

### 3. AI 决策流程（每周期触发）

```python
# 决策流程
def on_tick():
    # 1. 获取当前币数据
    klines = exchange.get_klines(CURRENT_SYMBOL, interval)
    indicators = analyzer.calculate(klines)
    
    # 2. AI 决策（针对当前持仓币）
    decision = brain.analyze(
        indicators=indicators,
        strategy=strategy,
        position=current_position
    )
    
    # 3. 验证
    if validator.validate(decision):
        # 4. 执行
        if decision.action == "buy" and not has_position:
            trader.buy()
        elif decision.action == "sell" and has_position:
            trader.sell()
    
    # 5. 通知 + 更新UI
    notifier.send(decision)
    ui.update()

# 用户决定换币时
def change_symbol(new_symbol):
    # 先平仓当前持仓
    if has_position:
        trader.sell()
    # 切换交易对
    CURRENT_SYMBOL = new_symbol
```

### 4. 风控规则
- 止损：买入后立即挂止损单
- 状态机：持仓禁买、空仓禁卖
- 熔断：连续亏损3次 / 单日超限
- 最大持仓时间：防止一直持仓
- 最小持仓时间：避免频繁买卖

### 5. 异常处理
- 网络断开：重连 + 恢复状态
- 订单失败：重试 + 记录
- 止损未成交：追单 / 告警
- 异常后状态恢复：检查持仓状态

### 4. AI 决策
```
触发 → fetcher → analyzer → scorer → selector 
    → brain → validator → trader → notifier → UI
```

---

## 换交易所流程

```python
# 1. 新建 exchange/okx.py，实现 BaseExchange
# 2. config.py 改 exchange: "okx"
# 3. 程序完全不用动！
```

---

## UI

| 区域 | 内容 |
|------|------|
| 持仓/收益 | 当前状态 |
| 监控区 | 多币评分列表 |
| AI建议 | 决策理由 |
| 控制 | 开始/暂停/停止/一键平仓 |
| 配置 | 交易所/Ollama/API/钉钉 |

---

## 文档

- 大纲: crypto-outline.md
- 参数: config.py
- 常量: constants.py
- API: docs/API.md
- 变更: docs/CHANGELOG.md

---

## 依赖

```
python-binance  # 或 python-okx
pandas
numpy
matplotlib
plotly
requests
websockets
cryptography
```

---

## 大纲版本管理

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-03-09 | 初始版本 |
| v1.1 | 2026-03-09 | 新增钉钉通知模块设计 |

---

## 持久化文件

- crypto-outline.md - 完整大纲
- MEMORY.md - 记忆恢复
- PROJECT_STATE.md - 项目进度
- HEARTBEAT.md - 定时任务

1. 换交易所 → 只需在 exchange/ 新建文件
2. 程序不动 → 核心逻辑隔离
3. 参数分离 → config.py 统一管理
4. 修改先改大纲 → 保持同步
