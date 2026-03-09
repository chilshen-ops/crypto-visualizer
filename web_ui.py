"""简单的Web可视化界面"""
import http.server
import socketserver
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PORT = 5001

# 先加载配置获取状态
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange
from src.fetcher import DataFetcher
from src.trader import Trader

# 初始化
api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")
testnet = config.SECURITY_CONFIG.get("testnet_mode", False)

exchange = BinanceExchange(api_key, api_secret, testnet)
fetcher = DataFetcher(exchange)
trader = Trader(exchange, fetcher)
status = trader.get_status()

symbol = config.TRADING_CONFIG.get("symbol", "ETHUSDT")
current_price = 0
if status.get("position", 0) > 0:
    current_price = fetcher.get_current_price(symbol)

HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Crypto Visualizer</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #1a1a2e; color: #eee; }
        h1 { text-align: center; color: #00d4ff; }
        .card { background: #16213e; border-radius: 10px; padding: 20px; margin: 10px 0; }
        .label { color: #888; font-size: 14px; }
        .value { font-size: 24px; font-weight: bold; color: #00ff88; }
        .price { font-size: 36px; color: #ffd700; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    </style>
</head>
<body>
    <h1>Crypto Visualizer</h1>
    <div class="card">
        <div class="label">SYMBOL</div>
        <div class="price" id="price">Loading...</div>
    </div>
    <div class="grid">
        <div class="card">
            <div class="label">Status</div>
            <div class="value" id="status">-</div>
        </div>
        <div class="card">
            <div class="label">Position</div>
            <div class="value" id="position">-</div>
        </div>
    </div>
    <div class="card">
        <div class="label">Entry Price</div>
        <div class="value" id="entry">-</div>
    </div>
    <script>
    function update() {
        fetch('/api/status').then(r=>r.json()).then(d=>{
            document.getElementById('price').innerText = '$' + d.current_price;
            document.getElementById('status').innerText = d.status;
            document.getElementById('position').innerText = d.position;
            document.getElementById('entry').innerText = '$' + d.entry_price;
        });
    }
    update();
    setInterval(update, 10000);
    </script>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            status = trader.get_status()
            symbol = config.TRADING_CONFIG.get("symbol", "ETHUSDT")
            current_price = 0
            if status.get("position", 0) > 0:
                try:
                    current_price = fetcher.get_current_price(symbol)
                except:
                    current_price = status.get("entry_price", 0)
            
            data = json.dumps({
                "symbol": symbol,
                "status": status.get("status", "unknown"),
                "position": str(status.get("position", 0)),
                "entry_price": str(status.get("entry_price", 0)),
                "current_price": str(current_price),
                "stop_loss": str(status.get("stop_loss", 0)),
                "daily_pnl": str(status.get("daily_pnl", 0)),
                "last_update": datetime.now().strftime("%H:%M:%S")
            })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(data.encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
    
    def log_message(self, format, *args):
        pass  # 禁用日志

print("=" * 50)
print("Crypto Visualizer Web")
print(f"http://localhost:{PORT}")
print("=" * 50)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
