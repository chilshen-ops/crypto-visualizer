import re

# Read file
with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\web_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace control panel buttons
old = '''<div class="controls">
                <button class="btn btn-close" onclick="sendCmd('close')">一键平仓</button>
            </div>'''

new = '''<div class="controls">
                <button class="btn btn-start" onclick="sendCmd('start')">开始</button>
                <button class="btn btn-stop" onclick="sendCmd('pause')">暂停</button>
                <button class="btn btn-stop" onclick="sendCmd('stop')">停止</button>
                <button class="btn btn-close" onclick="sendCmd('close')">一键平仓</button>
            </div>'''

content = content.replace(old, new)

# Add more config items
old_config = '''<div class="config-item">
                    <span class="config-label">止损比例: </span>
                    <span class="config-value" id="config-stop-loss">5%</span>
                </div>
                <div class="config-item">
                    <span class="config-label">模式: </span>
                    <span class="config-value" id="config-mode">实盘</span>
                </div>
            </div>
        </div>
        
        <!-- 日志 -->'''

new_config = '''<div class="config-item">
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
        
        <!-- 日志 -->'''

content = content.replace(old_config, new_config)

# Write file
with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\web_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
