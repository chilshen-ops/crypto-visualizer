# Crypto Visualizer

币安量化交易程序 - AI 驱动的自动交易系统

## 功能特点

- 🤖 **AI 决策**：使用本地 Ollama 模型（gpt-oss:latest）进行交易决策
- 📊 **技术分析**：内置多种技术指标（RSI、MACD、KDJ、布林带、ATR 等）
- 🎯 **智能选币**：自动评分并推荐最优交易币种
- 🔄 **自动交易**：全自动化交易流程，无需人工干预
- 📱 **钉钉通知**：实时推送交易状态、持仓信息、异常告警
- 🛡️ **风险控制**：止损机制、熔断保护、单日亏损限制

## 系统要求

- Python 3.8+
- Ollama（本地运行 AI 模型）
- 币安 API Key

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd crypto-visualizer

# 安装依赖
pip install -r requirements.txt

# 配置 config.py
# - 设置币安 API Key
# - 配置钉钉 Webhook（可选）
# - 调整交易参数
```

## 配置

编辑 `config.py`：

```python
# 交易配置
TRADING_CONFIG = {
    "symbol": "ETHUSDT",        # 交易对
    "interval": "3m",           # K线周期
    "monitor_symbols": ["ETHUSDT", "BTCUSDT"],
    "stop_loss_ratio": 0.05,    # 止损比例 5%
}

# API 配置
SECURITY_CONFIG = {
    "api_key": "你的API Key",
    "api_secret": "你的API Secret",
    "testnet_mode": False,      # 实盘=True, 测试网=False
}

# 钉钉通知
NOTIFY_CONFIG = {
    "enabled": True,
    "webhook": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
}
```

## 使用方法

### 1. 自动交易模式

```bash
python run_auto.py
```

程序将：
- 自动同步当前持仓
- 每 3 分钟分析一次市场
- 根据 AI 决策自动买卖
- 触发止损自动平仓
- 钉钉推送交易通知

### 2. 命令行模式

```bash
python main.py
```

支持命令：
- `start` - 启动自动交易
- `stop` - 停止交易
- `status` - 查看状态
- `buy` - 手动买入
- `sell` - 手动卖出
- `top` - 推荐币种

### 3. 测试

```bash
# 全流程测试
python test_simulation.py

# AI 决策测试
python test_ai.py

# 交易流程测试
python test_trading.py
```

## 项目结构

```
crypto-visualizer/
├── main.py              # 主程序入口
├── run_auto.py          # 自动交易模式
├── config.py            # 配置文件
├── requirements.txt     # 依赖
├── src/
│   ├── notifier.py     # 钉钉通知
│   ├── logger.py       # 日志系统
│   ├── error_handler.py# 错误处理
│   ├── fetcher.py      # 数据获取
│   ├── analyzer.py     # 技术分析
│   ├── scorer.py       # 评分器
│   ├── selector.py     # 选币器
│   ├── trader.py       # 交易执行
│   ├── trading_loop.py # 主循环
│   ├── constants.py    # 常量定义
│   ├── exchange/
│   │   ├── base.py    # 交易所基类
│   │   └── binance.py # 币安适配器
│   ├── ai/
│   │   └── brain.py   # AI 决策
│   └── ui/
│       └── cli.py     # 命令行界面
└── logs/               # 日志目录
```

## AI 决策流程

```
1. 获取K线数据（100条）
2. 计算技术指标（RSI、MACD、KDJ、MA等）
3. 检测技术形态（金叉、死叉、超买超卖）
4. 构建提示词发送给 Ollama
5. 解析 AI 响应（buy/sell/hold + 置信度）
6. 置信度 >= 0.7 时执行交易
```

## 风险提示

⚠️ 量化交易存在风险，请谨慎使用：
- 本程序仅供学习交流
- 实盘交易前请先在测试网充分测试
- 设置合理的止损比例
- 定期检查程序运行状态
- 关注市场异常波动

## 许可证

MIT License
