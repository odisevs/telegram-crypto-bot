import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
import time
import requests

# ==============================
# TELEGRAM SETTINGS
# ==============================

TELEGRAM_TOKEN = "8510669458:AAFHt51-nrup-h-wm2DFs8syg4TE8WQ4YEk"
TELEGRAM_CHAT_ID = 1606714980


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)


# ==============================
# EXCHANGE
# ==============================

exchange = ccxt.binance({
    'enableRateLimit': True
})

symbols = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "LINK/USDT",
    "MATIC/USDT"
]

timeframe = "1d"
limit = 120


# ==============================
# FETCH DATA
# ==============================

def fetch_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(
        ohlcv,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df


# ==============================
# ANALYZE SIGNALS
# ==============================

def analyze_signals(df):
    # RSI
    rsi = RSIIndicator(df['close'], window=14).rsi()
    rsi_now = rsi.iloc[-1]

    rsi_buy = rsi_now < 30
    rsi_sell = rsi_now > 70

    # MACD
    macd = MACD(df['close'])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()

    macd_buy = macd_line.iloc[-1] > signal_line.iloc[-1]
    macd_sell = macd_line.iloc[-1] < signal_line.iloc[-1]

    # EMA
    ema_short = EMAIndicator(df['close'], window=9).ema_indicator()
    ema_long = EMAIndicator(df['close'], window=21).ema_indicator()

    ema_buy = ema_short.iloc[-1] > ema_long.iloc[-1]
    ema_sell = ema_short.iloc[-1] < ema_long.iloc[-1]

    buy_score = [rsi_buy, macd_buy, ema_buy].count(True)
    sell_score = [rsi_sell, macd_sell, ema_sell].count(True)

    alert = None
    level = "HOLD"

    if macd_buy and buy_score >= 2:
        alert = "BUY"
        level = "🔥 CONFIRMED BUY"

    elif macd_sell and sell_score >= 2:
        alert = "SELL"
        level = "🚨 CONFIRMED SELL"

    elif buy_score >= 2:
        level = "✅ STRONG BUY"

    elif sell_score >= 2:
        level = "❌ STRONG SELL"

    return alert, level, rsi_now


# ==============================
# MAIN LOOP
# ==============================

print("🚀 Crypto Signal Bot started!")

send_telegram_message("✅ Crypto Signal Bot is now ONLINE!")

last_alerts = {}

while True:

    for symbol in symbols:

        try:
            df = fetch_data(symbol)
            alert, level, rsi_value = analyze_signals(df)

            print(symbol, level, f"RSI: {round(rsi_value,2)}")

            # რომ არ დაგისპამოს Telegram
            if alert:

                if last_alerts.get(symbol) != alert:

                    message = f"""
📊 {symbol}

Signal: {level}
RSI: {round(rsi_value,2)}
Timeframe: 1D
"""

                    send_telegram_message(message)

                    last_alerts[symbol] = alert

        except Exception as e:
            print("Error:", symbol, e)

    print("Sleeping 10 minutes...\n")

    time.sleep(600)
