from flask import Flask, request
import requests
import time
from datetime import datetime
import threading

app = Flask(__name__)

TOKEN = '7665819781:AAFqklWxMbzvtWydzfolKwDZFbS2lZ4SjeM'
CHAT_ID = '5451942674'
SYMBOLS = ['trx', 'btc', 'eth', 'doge', 'ada', 'usdt']

def send_message(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.get(url, params=params)

def get_data(symbol, interval='1d'):
    url = 'https://api.coinex.com/v1/market/kline'
    interval_map = {'1d': '1day', '4h': '4hour'}
    params = {
        'market': f'{symbol}usdt',
        'type': interval_map.get(interval, '1day'),
        'limit': 500
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data['code'] != 0 or not data['data']:
        return None
    return data['data']

def calculate_rsi(data, period=14):
    closes = [float(entry[2]) for entry in data]
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            losses.append(-change)
            gains.append(0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data, fast=12, slow=26, signal=9):
    closes = [float(entry[2]) for entry in data]
    fast_ema = [sum(closes[:fast]) / fast]
    slow_ema = [sum(closes[:slow]) / slow]
    for i in range(slow, len(closes)):
        fast_ema.append((closes[i] * (2 / (fast + 1))) + (fast_ema[-1] * (1 - (2 / (fast + 1)))))
        slow_ema.append((closes[i] * (2 / (slow + 1))) + (slow_ema[-1] * (1 - (2 / (slow + 1)))))
    macd = [f - s for f, s in zip(fast_ema[-len(slow_ema):], slow_ema)]
    signal_line = [sum(macd[i:i + signal]) / signal for i in range(len(macd) - signal + 1)]
    return macd[-1], signal_line[-1]

def get_analysis(symbol, interval='1d'):
    data = get_data(symbol, interval)
    if data is None or len(data) < 200:
        return f"❌ خطا در تحلیل {symbol.upper()} ({interval}): داده کافی نیست یا دریافت نشد."
    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)
    close = float(data[-1][2])
    ma50 = sum([float(d[2]) for d in data[-50:]]) / 50
    ma200 = sum([float(d[2]) for d in data[-200:]]) / 200
    msg = f"📊 تحلیل {'روزانه' if interval == '1d' else '4 ساعته'} {symbol.upper()}:\n"
    msg += f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M') if interval != '1d' else datetime.now().strftime('%Y-%m-%d')}\n"
    msg += f"قیمت فعلی: {close:.3f} USD\n"
    msg += f"RSI: {rsi:.2f} {'✅' if rsi < 70 else '❌'}\n"
    msg += f"MACD: {macd:.4f} {'صعودی' if macd > signal else 'نزولی'} {'✅' if macd > signal else '❌'}\n"
    msg += f"MA50: {ma50:.3f} | MA200: {ma200:.3f}\n"
    if rsi < 30 and macd > signal:
        msg += "⚡️ هشدار خرید فعال ✅"
    elif rsi > 70 and macd < signal:
        msg += "⚡️ هشدار فروش فعال ❌"
    else:
        msg += "هیچ هشدار فعال نیست ❌"
    return msg

def full_analysis(symbol):
    msg1 = get_analysis(symbol, '1d')
    msg2 = get_analysis(symbol, '4h')
    return f"{msg1}\n{'-'*20}\n{msg2}"

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    if "message" in data and "text" in data["message"]:
        text = data["message"]["text"].strip().lower()
        if text in SYMBOLS:
            analysis = full_analysis(text)
            send_message(analysis)
        else:
            send_message("لطفاً فقط نام یکی از این ارزها را وارد کنید: trx, btc, eth, doge, ada, usdt")
    return {"ok": True}

# تابع تحلیل خودکار جداگانه
def auto_send_loop():
    while True:
        for symbol in SYMBOLS:
            message = full_analysis(symbol)
            send_message(message)
            time.sleep(1)
        time.sleep(14400)

if __name__ == "__main__":
    # اجرای Flask در یک ترد
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()
    # اجرای تحلیل خودکار
    auto_send_loop()