import time
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# Telegram ბოტის კონფიგურაცია
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

# მონეტების სიები (CoinGecko ფორმატით)
symbols = [
    ("bitcoin","BTC/USDT"),
    ("ethereum","ETH/USDT"),
    ("solana","SOL/USDT"),
    ("binancecoin","BNB/USDT"),
    ("ripple","XRP/USDT"),
    ("cardano","ADA/USDT"),
    ("chainlink","LINK/USDT"),
    ("polygon","MATIC/USDT")
]

def fetch_coingecko_data(coin_id):
    # CoinGecko API URL
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
    try:
        response = requests.get(url)
        data = response.json()
        prices = data.get("prices", [])
        return prices
    except Exception as e:
        print("Coingecko fetch error:", e)
        return []

def build_dataframe(prices):
    df = pd.DataFrame(prices, columns=["timestamp","price"])
    df["close"] = df["price"]  # close ფასი
    return df

def analyze_signals(df):
    # RSI
    rsi = RSIIndicator(df["close"], window=14).rsi()
    rsi_now = rsi.iloc[-1]
    rsi_prev = rsi.iloc[-2]
    rsi_change = rsi_now - rsi_prev
    rsi_buy = rsi_now < 30
    rsi_sell = rsi_now > 70

    # MACD
    macd = MACD(df["close"])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    macd_buy = macd_line.iloc[-1] > signal_line.iloc[-1]
    macd_sell = macd_line.iloc[-1] < signal_line.iloc[-1]

    # EMA
    ema_short = EMAIndicator(df["close"], window=9).ema_indicator()
    ema_long = EMAIndicator(df["close"], window=21).ema_indicator()
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

print("Crypto Signal Bot with CoinGecko started!")
send_telegram_message("📡 Crypto Signal Bot (CoinGecko) ONLINE!")

last_alerts = {}

while True:
    for coin_id, symbol in symbols:
        prices = fetch_coingecko_data(coin_id)
        if not prices:
            continue

        df = build_dataframe(prices)
        alert, level, rsi_now = analyze_signals(df)

        print(f"{symbol} → {level}, RSI: {round(rsi_now,2)}")

        if alert:
            if last_alerts.get(symbol) != alert:
                msg = f"""
📊 {symbol}
Signal: {level}
RSI: {round(rsi_now,2)}
(Source: CoinGecko)
"""
                send_telegram_message(msg)
                last_alerts[symbol] = alert

    print("Sleeping 10 minutes...\n")
    time.sleep(600)

