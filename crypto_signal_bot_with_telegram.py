import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
import time
import winsound
import requests

# === შენს ბოტს ეს TOKEN და CHAT_ID ესაჭიროება ===
TELEGRAM_TOKEN = "123456789:AAExampleTokenPlaceholder"  # ჩაანაცვლე ნამდვილი Token-ით
TELEGRAM_CHAT_ID = 1606714980

def send_telegram_message(message_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message_text}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("📩 შეტყობინება გაგზავნილია Telegram-ზე")
        else:
            print("⚠️ Telegram შეცდომა:", response.text)
    except Exception as e:
        print("❌ შეცდომა:", e)

# Binance ბირჟა
exchange = ccxt.binance({'enableRateLimit': True})

symbols = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT',
    'XRP/USDT', 'ADA/USDT', 'LINK/USDT', 'MATIC/USDT'
]

timeframe = '1d'
limit = 120

def fetch_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def analyze_signals(df):
    rsi = RSIIndicator(df['close'], window=14).rsi()
    rsi_now = rsi.iloc[-1]
    rsi_prev = rsi.iloc[-2]
    rsi_change = rsi_now - rsi_prev
    rsi_buy = rsi_now < 30
    rsi_sell = rsi_now > 70

    macd_line = MACD(df['close']).macd()
    signal_line = MACD(df['close']).macd_signal()
    macd_buy = macd_line.iloc[-1] > signal_line.iloc[-1]
    macd_sell = macd_line.iloc[-1] < signal_line.iloc[-1]

    ema_short = EMAIndicator(df['close'], window=9).ema_indicator()
    ema_long = EMAIndicator(df['close'], window=21).ema_indicator()
    ema_buy = ema_short.iloc[-1] > ema_long.iloc[-1]
    ema_sell = ema_short.iloc[-1] < ema_long.iloc[-1]

    rsi_speed = ""
    if rsi_change > 8:
        rsi_speed = "📈 RSI სწრაფად იზრდება"
    elif rsi_change < -8:
        rsi_speed = "📉 RSI სწრაფად იკლებს"

    buy_score = [rsi_buy, macd_buy, ema_buy].count(True)
    sell_score = [rsi_sell, macd_sell, ema_sell].count(True)

    level = "⏸ HOLD"
    alert = None

    if macd_buy and buy_score >= 2:
        level = "🔥 CONFIRMED BUY (MACD + confirmation)"
        alert = "buy"
    elif macd_sell and sell_score >= 2:
        level = "🚨 CONFIRMED SELL (MACD + confirmation)"
        alert = "sell"
    elif buy_score >= 2:
        level = "✅ STRONG BUY"
    elif sell_score >= 2:
        level = "❌ STRONG SELL"

    return {
        "RSI": f"{'BUY' if rsi_buy else 'SELL' if rsi_sell else 'HOLD'} ({rsi_now:.2f})",
        "MACD": "BUY" if macd_buy else "SELL" if macd_sell else "HOLD",
        "EMA": "BUY" if ema_buy else "SELL" if ema_sell else "HOLD",
        "level": level,
        "alert": alert,
        "rsi_speed": rsi_speed
    }

# ==== მთავარი ციკლი ====
print("\n🚀 ბოტი გაშვებულია (24/7, ყოველდღიური გრაფიკი)")

while True:
    print(f"\n🕒 {pd.Timestamp.now()}\n")
    for symbol in symbols:
        try:
            df = fetch_data(symbol)
            result = analyze_signals(df)

            print(f"🔹 {symbol}")
            print(f"RSI: {result['RSI']} | MACD: {result['MACD']} | EMA: {result['EMA']}")
            if result['rsi_speed']:
                print(result['rsi_speed'])
            print(result['level'])
            print("--------------------------------------------------")

            # სიგნალის დრო – ხმის და Telegram შეტყობინება
            if result['alert'] == "buy":
                winsound.Beep(1400, 400)
                time.sleep(0.2)
                winsound.Beep(1200, 400)
                send_telegram_message(f"💹 BUY signal for {symbol}!\n{result['level']}")

            elif result['alert'] == "sell":
                winsound.Beep(700, 400)
                time.sleep(0.2)
                winsound.Beep(500, 400)
                send_telegram_message(f"⚠️ SELL signal for {symbol}!\n{result['level']}")

        except Exception as e:
            print(f"⚠️ შეცდომა {symbol}-ზე:", e)

    print("\n⌛ განახლება 10 წუთში...\n")
    time.sleep(600)


