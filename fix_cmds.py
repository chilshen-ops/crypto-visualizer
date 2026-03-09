# Fix web_ui.py send_cmd to handle all buttons

import re

with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\web_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the send_cmd function
old_func = '''    def send_cmd(self):
        cmd = self.path.split('=')[1] if '=' in self.path else ''
        
        try:
            if cmd == 'close':
                # 执行平仓
                result = trader.sell(reason="用户手动平仓")
                success = result.get('success', False)
            else:
                success = False
        except Exception as e:
            success = False
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({"success": success, "cmd": cmd}).encode('utf-8'))'''

new_func = '''    def send_cmd(self):
        cmd = self.path.split('=')[1] if '=' in self.path else ''
        
        try:
            success = False
            if cmd == 'close':
                # 平仓
                result = trader.sell(reason="用户手动平仓")
                success = result.get('success', False)
            elif cmd == 'start':
                # 开始交易
                if hasattr(trader, 'start_trading'):
                    trader.start_trading()
                success = True
            elif cmd == 'pause':
                # 暂停交易
                if hasattr(trader, 'pause_trading'):
                    trader.pause_trading()
                success = True
            elif cmd == 'stop':
                # 停止交易
                if hasattr(trader, 'stop_trading'):
                    trader.stop_trading()
                success = True
        except Exception as e:
            success = False
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({"success": success, "cmd": cmd}).encode('utf-8'))'''

content = content.replace(old_func, new_func)

with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\web_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
