# Fix trader.py for empty position handling

with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\src\trader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix sync_position to handle empty position
old_sync = '''                    if qty > 0:
                        self.position = qty
                        self.status = TradeStatus.HOLDING
                        # 获取当前价格作为持仓参考
                        current_price = self.fetcher.get_current_price(self.symbol)
                        self.position_entry_price = current_price
                        # 设置止损
                        self.stop_loss_price = current_price * (1 - self.stop_loss_ratio)
                        self.logger.info(f"同步持仓: {self.symbol} x {qty} @ {current_price}")
                    break'''

new_sync = '''                    if qty > 0.0001:  # 大于最小精度才认为有持仓
                        self.position = qty
                        self.status = TradeStatus.HOLDING
                        # 获取当前价格作为持仓参考
                        current_price = self.fetcher.get_current_price(self.symbol)
                        self.position_entry_price = current_price
                        # 设置止损
                        self.stop_loss_price = current_price * (1 - self.stop_loss_ratio)
                        self.logger.info(f"同步持仓: {self.symbol} x {qty} @ {current_price}")
                    else:
                        # 空仓状态
                        self.position = 0
                        self.status = TradeStatus.IDLE
                        self.logger.info(f"同步持仓: 空仓")
                    break'''

content = content.replace(old_sync, new_sync)

with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\src\trader.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
