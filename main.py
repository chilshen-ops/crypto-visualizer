"""
Crypto Visualizer 主程序
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.notifier import init_notifier
from src.logger import get_logger
from src.trading_loop import init_trading_loop
from src.ui.cli import start_cli


def main():
    """主函数"""
    print("=" * 50)
    print("Crypto Visualizer")
    print("币安量化交易程序 + AI 决策")
    print("=" * 50)
    
    # 初始化日志
    logger = get_logger("main")
    logger.info("程序启动")
    
    # 初始化通知器
    notify_config = config.NOTIFY_CONFIG
    notifier = init_notifier(notify_config)
    logger.info(f"通知器: {'已启用' if notifier.enabled else '已禁用'}")
    
    # 检查 webhook 配置
    if notifier.enabled and notifier.webhook and "YOUR_TOKEN" not in notifier.webhook:
        logger.info("Webhook 已配置")
    else:
        logger.warning("请在 config.py 中配置 webhook token")
    
    # 获取 API 配置（从环境变量）
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    
    # 初始化交易系统
    logger.info("初始化交易系统...")
    trading_loop = init_trading_loop(api_key, api_secret)
    
    # 获取初始状态
    status = trading_loop.get_status()
    logger.info(f"交易对: {status['symbol']}")
    logger.info(f"K线周期: {status['interval']}")
    
    # 测试数据获取
    logger.info("测试数据获取...")
    try:
        price = trading_loop.fetcher.get_current_price(status['symbol'])
        logger.info(f"{status['symbol']} 当前价格: {price}")
        
        # 获取排名前三的币种
        top_symbols = trading_loop.get_top_symbols(3)
        logger.info("推荐的币种:")
        for i, s in enumerate(top_symbols, 1):
            logger.info(f"  {i}. {s['symbol']} (分数: {s['score']})")
            
    except Exception as e:
        logger.error(f"数据获取测试失败: {e}")
    
    # 启动命令行界面
    print("\n启动命令行控制台...")
    start_cli(trading_loop)
    
    logger.info("程序已停止")


if __name__ == "__main__":
    main()