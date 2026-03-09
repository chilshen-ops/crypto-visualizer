import sys

# 读取文件
with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\src\trader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换
old = '''            # 卖出数量
            quantity = quantity or self.position
            
            # 执行卖出
            result = self.exchange.sell_market(self.symbol, quantity)'''

new = '''            # 卖出数量
            quantity = quantity or self.position
            # 确保数量精度正确 (ETH最小0.00001)
            quantity = round(quantity, 5)
            
            # 执行卖出
            result = self.exchange.sell_market(self.symbol, quantity)'''

content = content.replace(old, new)

# 写入
with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\src\trader.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
