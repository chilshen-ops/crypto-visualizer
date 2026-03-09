"""
命令行界面
"""
import os
import sys
import time
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..trading_loop import TradingLoop
from ..logger import get_logger


class CLI:
    """命令行界面"""
    
    def __init__(self, trading_loop: TradingLoop):
        """
        初始化 CLI
        
        Args:
            trading_loop: 交易循环实例
        """
        self.trading_loop = trading_loop
        self.logger = get_logger("cli")
        self.running = False
        self.input_thread: Optional[threading.Thread] = None
    
    def start(self):
        """启动 CLI"""
        self.running = True
        self._print_welcome()
        self._print_help()
        
        # 启动输入监听
        self.input_thread = threading.Thread(target=self._listen_input, daemon=True)
        self.input_thread.start()
        
        # 主循环显示状态
        self._main_loop()
    
    def stop(self):
        """停止 CLI"""
        self.running = False
        print("\nCLI 已退出")
    
    def _print_welcome(self):
        """打印欢迎信息"""
        print("=" * 50)
        print("  Crypto Visualizer - 命令行控制台")
        print("=" * 50)
    
    def _print_help(self):
        """打印帮助信息"""
        print("\n可用命令:")
        print("  status    - 显示当前状态")
        print("  start     - 启动交易")
        print("  stop      - 停止交易")
        print("  pause     - 暂停交易")
        print("  resume    - 恢复交易")
        print("  buy       - 手动买入")
        print("  sell      - 手动卖出")
        print("  symbol    - 切换交易对")
        print("  top       - 显示推荐币种")
        print("  help      - 显示帮助")
        print("  exit      - 退出程序")
    
    def _listen_input(self):
        """监听用户输入"""
        while self.running:
            try:
                cmd = input("\n> ").strip().lower()
                if not cmd:
                    continue
                
                self._handle_command(cmd)
                
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(f"输入错误: {e}")
    
    def _handle_command(self, cmd: str):
        """处理命令"""
        parts = cmd.split()
        action = parts[0]
        
        if action == "help":
            self._print_help()
        
        elif action == "status":
            self._show_status()
        
        elif action == "start":
            self.trading_loop.start()
            print("交易已启动")
        
        elif action == "stop":
            self.trading_loop.stop()
            print("交易已停止")
        
        elif action == "pause":
            self.trading_loop.pause()
            print("交易已暂停")
        
        elif action == "resume":
            self.trading_loop.resume()
            print("交易已恢复")
        
        elif action == "buy":
            quantity = float(parts[1]) if len(parts) > 1 else None
            result = self.trading_loop.manual_buy(quantity)
            if result.get("success"):
                print(f"买入成功: {result}")
            else:
                print(f"买入失败: {result.get('reason')}")
        
        elif action == "sell":
            quantity = float(parts[1]) if len(parts) > 1 else None
            result = self.trading_loop.manual_sell(quantity)
            if result.get("success"):
                print(f"卖出成功: {result}")
            else:
                print(f"卖出失败: {result.get('reason')}")
        
        elif action == "symbol":
            if len(parts) > 1:
                new_symbol = parts[1].upper()
                success = self.trading_loop.change_symbol(new_symbol)
                if success:
                    print(f"已切换交易对: {new_symbol}")
                else:
                    print("切换失败，当前有持仓")
            else:
                print("用法: symbol <币种>")
        
        elif action == "top":
            n = int(parts[1]) if len(parts) > 1 else 3
            top_list = self.trading_loop.get_top_symbols(n)
            print(f"\n推荐币种 (Top {n}):")
            for i, item in enumerate(top_list, 1):
                print(f"  {i}. {item['symbol']} - 分数: {item['score']}")
                reasons = item.get('reasons', [])
                if reasons:
                    print(f"     原因: {', '.join(reasons[:3])}")
        
        elif action == "exit":
            self.running = False
            self.trading_loop.stop()
            print("正在退出...")
        
        else:
            print(f"未知命令: {cmd}")
            print("输入 'help' 查看可用命令")
    
    def _show_status(self):
        """显示状态"""
        status = self.trading_loop.get_status()
        
        print("\n" + "=" * 40)
        print("  当前状态")
        print("=" * 40)
        
        print(f"运行状态: {'运行中' if status['running'] else '已停止'}")
        print(f"暂停状态: {'已暂停' if status['paused'] else '正常'}")
        print(f"交易对: {status['symbol']}")
        print(f"周期: {status['interval']}")
        
        trader = status.get('trader', {})
        print(f"\n持仓状态:")
        print(f"  状态: {trader.get('status', 'idle')}")
        print(f"  数量: {trader.get('position', 0)}")
        print(f"  开仓价: {trader.get('entry_price', 0)}")
        print(f"  当前价: {trader.get('current_price', 0)}")
        print(f"  止损价: {trader.get('stop_loss', 0)}")
        print(f"  持仓时间: {trader.get('position_time', 0)} 根K线")
        
        print(f"\n风控:")
        print(f"  连续亏损: {trader.get('consecutive_loss', 0)} 次")
        print(f"  今日盈亏: {trader.get('daily_pnl', 0)} USDT")
        print(f"  可交易: {'是' if trader.get('can_trade') else '否'}")
        
        print("=" * 40)
    
    def _main_loop(self):
        """主循环 - 显示实时状态"""
        last_status = ""
        
        while self.running:
            try:
                status = self.trading_loop.get_status()
                trader = status.get('trader', {})
                
                # 构建状态栏
                status_bar = (
                    f"交易对: {status['symbol']} | "
                    f"状态: {trader.get('status', 'idle')} | "
                    f"持仓: {trader.get('position', 0)} | "
                    f"盈亏: {trader.get('daily_pnl', 0)}"
                )
                
                # 只有状态变化时才打印
                if status_bar != last_status:
                    # 清除上一行
                    print(f"\r{status_bar}", end="")
                    last_status = status_bar
                
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"CLI 主循环异常: {e}")
                time.sleep(2)


def start_cli(trading_loop: TradingLoop):
    """启动命令行界面"""
    cli = CLI(trading_loop)
    try:
        cli.start()
    except KeyboardInterrupt:
        cli.stop()
