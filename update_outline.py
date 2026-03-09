# Update crypto-outline.md version

with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\crypto-outline.md', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-03-09 | 初始版本 |
| v1.1 | 2026-03-09 | 新增钉钉通知模块设计 |

---

## 持久化文件'''

new = '''| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-03-09 | 初始版本 |
| v1.1 | 2026-03-09 | 新增钉钉通知模块设计 |
| v1.2 | 2026-03-09 | 修复API签名问题、使用官方库、全仓买卖、空仓判断 |

---

## 持久化文件'''

content = content.replace(old, new)

with open(r'C:\Users\Sin\.openclaw\workspace\crypto-visualizer\crypto-outline.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("大纲已更新!")
