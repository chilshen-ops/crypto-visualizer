# 常量定义

class TradeStatus:
    IDLE = "idle"
    OPENING = "opening"
    HOLDING = "holding"
    CLOSING = "closing"


class OrderSide:
    BUY = "BUY"
    SELL = "SELL"


class OrderType:
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"


class Interval:
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"


class Indicator:
    MA5 = "MA5"
    MA10 = "MA10"
    MA20 = "MA20"
    RSI = "RSI"
    MACD = "MACD"
    KDJ = "KDJ"
    BOLL = "BOLL"
    ATR = "ATR"
