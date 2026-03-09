"""完整的Web可视化界面 - 增强版"""
import http.server
import socketserver
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.exchange.binance import BinanceExchange
from src.fetcher import DataFetcher
from src.trader import Trader
from src.analyzer import TechnicalAnalyzer
from src.scorer import Scorer
from src.selector import SymbolSelector

# 初始化
api_key = config.SECURITY_CONFIG.get("api_key", "")
api_secret = config.SECURITY_CONFIG.get("api_secret", "")
testnet = config.SECURITY_CONFIG.get("testnet_mode", False)

exchange = BinanceExchange(api_key, api_secret, testnet)
fetcher = DataFetcher(exchange)
trader = Trader(exchange, fetcher)
analyzer = TechnicalAnalyzer()
scorer = Scorer()
selector = SymbolSelector(fetcher, scorer)

PORT = 5001

# 内存日志
log_messages = []
ai_thinking = ""

HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Crypto Visualizer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
        }
        .header {
            background: rgba(0,0,0,0.3);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
        }
        .header h1 { color: #00d4ff; font-size: 20px; }
        .header .status { color: #00ff88; font-size: 12px; }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 15px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .card {
            background: rgba(22, 33, 62, 0.8);
            border-radius: 12px;
            padding: 15px;
            backdrop-filter: blur(10px);
        }
        
        .card.full-width { grid-column: 1 / -1; }
        
        .card h2 {
            color: #00d4ff;
            font-size: 14px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #333;
        }
        
        /* 持仓状态 */
        .position-info {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }
        
        .info-item { text-align: center; }
        .info-item .label { color: #888; font-size: 11px; margin-bottom: 3px; }
        .info-item .value { font-size: 16px; font-weight: bold; }
        .value.price { color: #ffd700; }
        .value.profit { color: #00ff88; }
        .value.loss { color: #ff4444; }
        .value.holding { color: #ffd700; }
        .value.idle { color: #00d4ff; }
        
        /* AI决策 */
        .ai-decision {
            padding: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }
        
        .ai-action { font-size: 20px; font-weight: bold; margin-bottom: 8px; }
        .action-buy { color: #00ff88; }
        .action-sell { color: #ff4444; }
        .action-hold { color: #ffd700; }
        
        .ai-reason { color: #aaa; font-size: 12px; line-height: 1.4; }
        .ai-confidence { color: #00d4ff; font-size: 11px; margin-top: 8px; }
        
        /* AI思考过程 */
        .ai-thinking {
            margin-top: 10px;
            padding: 10px;
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
            font-size: 11px;
            color: #888;
            max-height: 80px;
            overflow-y: auto;
        }
        
        /* 控制按钮 */
        .controls { display: flex; gap: 8px; flex-wrap: wrap; }
        .btn {
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-start { background: #00ff88; color: #000; }
        .btn-stop { background: #ff4444; color: #fff; }
        .btn-close { background: #00d4ff; color: #000; }
        
        /* 监控区 */
        .coin-list { max-height: 200px; overflow-y: auto; }
        .coin-item {
            display: grid;
            grid-template-columns: 70px 70px 50px 1fr;
            padding: 8px;
            border-bottom: 1px solid #333;
            font-size: 12px;
            align-items: center;
        }
        .coin-item:hover { background: rgba(255,255,255,0.05); }
        .coin-symbol { font-weight: bold; color: #00d4ff; }
        .coin-price { color: #ffd700; }
        .coin-score { padding: 2px 6px; border-radius: 3px; font-size: 10px; text-align: center; }
        .score-high { background: #00ff88; color: #000; }
        .score-mid { background: #ffd700; color: #000; }
        .score-low { background: #ff4444; color: #fff; }
        
        /* 配置 */
        .config-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            font-size: 11px;
        }
        .config-item { padding: 6px; background: rgba(0,0,0,0.2); border-radius: 4px; }
        .config-label { color: #888; }
        .config-value { color: #00ff88; }
        
        /* 日志 */
        .log-area {
            max-height: 150px;
            overflow-y: auto;
            background: rgba(0,0,0,0.3);
            padding: 8px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 10px;
            color: #aaa;
        }
        .log-entry { margin-bottom: 3px; border-bottom: 1px solid #222; padding-bottom: 2px; }
        .log-time { color: #666; margin-right: 5px; }
        
        .time { text-align: center; color: #666; font-size: 11px; margin-top: 10px; }
        
        /* 刷新按钮 */
        .refresh-btn {
            background: #333;
            color: #00d4ff;
            border: 1px solid #00d4ff;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Crypto Visualizer</h1>
        <div>
            <button class="refresh-btn" onclick="update()">刷新</button>
            <span class="status" id="status-badge">● 运行中</span>
        </div>
    </div>
    
    <div class="container">
        <!-- 持仓状态 -->
        <div class="card full-width">
            <h2>持仓状态 <button class="refresh-btn" onclick="update()" style="float:right;margin-top:-3px;">↻</button></h2>
            <div class="position-info">
                <div class="info-item">
                    <div class="label">交易对</div>
                    <div class="value" id="symbol">-</div>
                </div>
                <div class="info-item">
                    <div class="label">状态</div>
                    <div class="value" id="status">-</div>
                </div>
                <div class="info-item">
                    <div class="label">持仓数量</div>
                    <div class="value" id="position">-</div>
                </div>
                <div class="info-item">
                    <div class="label">当前价格</div>
                    <div class="value price" id="current-price">-</div>
                </div>
                <div class="info-item">
                    <div class="label">持仓均价</div>
                    <div class="value" id="entry-price">-</div>
                </div>
                <div class="info-item">
                    <div class="label">止损价</div>
                    <div class="value" id="stop-loss">-</div>
                </div>
                <div class="info-item">
                    <div class="label">盈亏</div>
                    <div class="value" id="pnl">-</div>
                </div>
                <div class="info-item">
                    <div class="label">USDT余额</div>
                    <div class="value" id="usdt-balance">-</div>
                </div>
            </div>
        </div>
        
        <!-- AI决策 -->
        <div class="card">
            <h2>AI决策</h2>
            <div class="ai-decision">
                <div class="ai-action" id="ai-action">-</div>
                <div class="ai-reason" id="ai-reason">等待分析...</div>
                <div class="ai-confidence" id="ai-confidence">-</div>
                <div class="ai-thinking" id="ai-thinking">AI思考过程将显示在这里...</div>
            </div>
        </div>
        
        <!-- 控制 -->
        <div class="card">
            <h2>控制面板</h2>
            <div class="controls">
                <button class="btn btn-start" onclick="sendCmd('start')">开始</button>
                <button class="btn btn-stop" onclick="sendCmd('pause')">暂停</button>
                <button class="btn btn-stop" onclick="sendCmd('stop')">停止</button>
                <button class="btn btn-close" onclick="sendCmd('close')">一键平仓</button>
            </div>
            <div style="margin-top:10px;font-size:11px;color:#888;">
                运行状态: <span id="running-status">运行中</span>
            </div>
        </div>
        
        <!-- 多币监控 -->
        <div class="card full-width">
            <h2>多币监控 <button class="refresh-btn" onclick="updateCoins()">↻</button></h2>
            <div class="coin-list" id="coin-list">
                <div style="color:#666;text-align:center;padding:20px;">加载中...</div>
            </div>
        </div>
        
        <!-- 配置 -->
        <div class="card">
            <h2>系统配置</h2>
            <div class="config-grid">
                <div class="config-item">
                    <span class="config-label">交易所: </span>
                    <span class="config-value">Binance</span>
                </div>
                <div class="config-item">
                    <span class="config-label">交易对: </span>
                    <span class="config-value" id="config-symbol">ETHUSDT</span>
                </div>
                <div class="config-item">
                    <span class="config-label">K线周期: </span>
                    <span class="config-value" id="config-interval">3m</span>
                </div>
                <div class="config-item">
                    <span class="config-label">AI模型: </span>
                    <span class="config-value">gpt-oss:latest</span>
                </div>
                <div class="config-item">
                    <span class="config-label">止损比例: </span>
                    <span class="config-value" id="config-stop-loss">5%</span>
                </div>
                <div class="config-item">
                    <span class="config-label">模式: </span>
                    <span class="config-value" id="config-mode">实盘</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Ollama: </span>
                    <span class="config-value">localhost:11434</span>
                </div>
                <div class="config-item">
                    <span class="config-label">钉钉: </span>
                    <span class="config-value">已配置</span>
                </div>
            </div>
        </div>
        
        <!-- 日志 -->
        <div class="card">
            <h2>交易日志 <button class="refresh-btn" onclick="update()">↻</button></h2>
            <div class="log-area" id="log-area">
                <div class="log-entry"><span class="log-time">--:--:--</span> 系统初始化...</div>
            </div>
        </div>
    </div>
    
    <div class="time">最后更新: <span id="last-update">-</span></div>
    
    <script>
    let logData = [];
    let aiThinkData = "";
    
    function sendCmd(cmd) {
        if(cmd === 'close') {
            if(!confirm('确定要平仓吗?')) return;
        }
        fetch('/api/cmd?cmd=' + cmd).then(r=>r.json()).then(d=>{
            addLog('发送命令: ' + cmd + ' -> ' + (d.success?'成功':'失败'));
            setTimeout(update, 1000);
        });
    }
    
    function addLog(msg) {
        const time = new Date().toTimeString().slice(0,8);
        logData.unshift({time, msg});
        if(logData.length > 100) logData.pop();
        const logHtml = logData.map(l => 
            '<div class="log-entry"><span class="log-time">'+l.time+'</span>'+l.msg+'</div>'
        ).join('');
        document.getElementById('log-area').innerHTML = logHtml;
    }
    
    function updateCoins() {
        fetch('/api/coins').then(r=>r.json()).then(d=>{
            if(d.error) {
                addLog('获取监控列表失败');
                return;
            }
            if(d.coins && d.coins.length > 0) {
                const coinsHtml = d.coins.map(c => 
                    '<div class="coin-item">' +
                        '<div class="coin-symbol">'+c.symbol+'</div>' +
                        '<div class="coin-price">$'+c.price+'</div>' +
                        '<div class="coin-score '+(c.score>=70?'score-high':(c.score>=50?'score-mid':'score-low'))+'">'+c.score+'</div>' +
                        '<div style="color:#666;font-size:10px;">'+(c.reason||'')+'</div>' +
                    '</div>'
                ).join('');
                document.getElementById('coin-list').innerHTML = coinsHtml;
            }
        });
    }
    
    function update() {
        fetch('/api/status').then(r=>r.json()).then(d=>{
            if(d.error) {
                addLog('获取状态失败: ' + d.error);
                return;
            }
            
            // 持仓状态
            document.getElementById('symbol').innerText = d.symbol;
            document.getElementById('status').innerText = d.status.toUpperCase();
            document.getElementById('status').className = 'value ' + (d.status === 'holding' ? 'holding' : 'idle');
            document.getElementById('position').innerText = d.position > 0 ? d.position + ' ' + d.symbol.replace('USDT','') : '-';
            document.getElementById('current-price').innerText = d.current_price > 0 ? '$' + d.current_price : '-';
            document.getElementById('entry-price').innerText = d.entry_price > 0 ? '$' + d.entry_price : '-';
            document.getElementById('stop-loss').innerText = d.stop_loss > 0 ? '$' + d.stop_loss : '-';
            document.getElementById('usdt-balance').innerText = '$' + d.usdt_balance;
            
            // 盈亏
            const pnl = d.position > 0 ? (d.current_price - d.entry_price) * d.position : 0;
            const pnlEl = document.getElementById('pnl');
            pnlEl.innerText = pnl > 0 ? '+$' + pnl.toFixed(2) : (pnl < 0 ? '-$' + Math.abs(pnl).toFixed(2) : '$0');
            pnlEl.className = 'value ' + (pnl > 0 ? 'profit' : (pnl < 0 ? 'loss' : ''));
            
            // AI决策
            const actionEl = document.getElementById('ai-action');
            actionEl.innerText = d.ai_action || '-';
            actionEl.className = 'ai-action action-' + (d.ai_action || 'hold');
            document.getElementById('ai-reason').innerText = d.ai_reason || '等待分析...';
            document.getElementById('ai-confidence').innerText = d.ai_confidence ? '置信度: ' + d.ai_confidence : '';
            
            // AI思考过程
            const thinkEl = document.getElementById('ai-thinking');
            if(d.ai_thinking) {
                thinkEl.innerText = d.ai_thinking;
            } else {
                thinkEl.innerText = '暂无思考过程...';
            }
            
            // 配置
            document.getElementById('config-symbol').innerText = d.symbol;
            document.getElementById('config-interval').innerText = d.interval;
            document.getElementById('config-mode').innerText = d.testnet ? '测试' : '实盘';
            
            // 时间
            document.getElementById('last-update').innerText = d.last_update;
            
            // 添加日志
            if(d.ai_action) {
                addLog('AI决策: ' + d.ai_action + ' (' + d.ai_confidence + ')');
            }
            
        }).catch(e=>addLog('API错误: ' + e));
        
        // 更新监控列表
        updateCoins();
    }
    
    // 初始加载
    update();
    // 每5秒刷新
    setInterval(update, 5000);
    </script>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.send_status()
        elif self.path == '/api/coins':
            self.send_coins()
        elif self.path.startswith('/api/cmd'):
            self.send_cmd()
        else:
            self.send_html()
    
    def send_html(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML.encode('utf-8'))
    
    def send_status(self):
        try:
            global log_messages, ai_thinking
            
            status = trader.get_status()
            symbol = config.TRADING_CONFIG.get("symbol", "ETHUSDT")
            
            # 获取当前价格和余额
            current_price = 0
            usdt_balance = 0
            try:
                if status.get("position", 0) > 0:
                    current_price = fetcher.get_current_price(symbol)
                balance = exchange.get_balance()
                for b in balance.get("balances", []):
                    if b.get("asset") == "USDT":
                        usdt_balance = float(b.get("free", 0))
                        break
            except:
                pass
            
            data = json.dumps({
                "symbol": symbol,
                "status": status.get("status", "unknown"),
                "position": status.get("position", 0),
                "entry_price": status.get("entry_price", 0),
                "current_price": current_price,
                "stop_loss": status.get("stop_loss", 0),
                "usdt_balance": usdt_balance,
                "ai_action": status.get("ai_action", ""),
                "ai_reason": status.get("ai_reason", ""),
                "ai_confidence": status.get("ai_confidence", ""),
                "ai_thinking": status.get("ai_thinking", ""),
                "interval": config.TRADING_CONFIG.get("interval", "3m"),
                "testnet": config.SECURITY_CONFIG.get("testnet_mode", False),
                "last_update": datetime.now().strftime("%H:%M:%S")
            })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(data.encode('utf-8'))
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def send_coins(self):
        try:
            coins = []
            monitor_symbols = config.TRADING_CONFIG.get("monitor_symbols", ["BTCUSDT", "ETHUSDT"])
            
            for sym in monitor_symbols[:6]:
                try:
                    price = fetcher.get_current_price(sym)
                    klines = fetcher.get_klines(sym, config.TRADING_CONFIG.get("interval", "3m"), 50)
                    if klines is not None and len(klines) > 0:
                        data = analyzer.calculate(klines)
                        score_data = scorer.score_symbol(data)
                        coins.append({
                            "symbol": sym,
                            "price": str(round(price, 2)),
                            "score": int(score_data.get("total_score", 0)),
                            "reason": ", ".join(score_data.get("reasons", [])[:2])
                        })
                except:
                    pass
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"coins": coins}).encode('utf-8'))
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def send_cmd(self):
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
        self.wfile.write(json.dumps({"success": success, "cmd": cmd}).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

print("=" * 50)
print("Crypto Visualizer Dashboard")
print(f"http://localhost:{PORT}")
print("=" * 50)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
