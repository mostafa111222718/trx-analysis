import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

TOKEN = '7665819781:AAFqklWxMbzvtWydzfolKwDZFbS2lZ4SjeM'
CHAT_ID = '5451942674'
SYMBOLS = ['trx', 'btc', 'eth', 'doge', 'ada', 'usdt']

def send_message(text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, data=data)

def get_data(symbol, interval='1d'):
    url = 'https://api.coinex.com/v1/market/kline'
    params = {'market': f'{symbol}usdt', 'type': '1day' if interval == '1d' else '4hour', 'limit': 500}
    r = requests.get(url, params=params).json()
    return r['data'] if r['code'] == 0 else None

def calculate_rsi(data, period=14):
    closes = [float(x[2]) for x in data]
    gains, losses = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    return 100 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))

def calculate_macd(data, fast=12, slow=26, signal=9):
    closes = [float(x[2]) for x in data]
    def ema(vals, p):
        ema_list = [sum(vals[:p]) / p]
        k = 2 / (p + 1)
        for val in vals[p:]:
            ema_list.append(val * k + ema_list[-1] * (1 - k))
        return ema_list
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    macd_line = [f - s for f, s in zip(fast_ema[-len(slow_ema):], slow_ema)]
    signal_line = ema(macd_line, signal)
    return macd_line[-1], signal_line[-1]

def analyze(symbol, interval='1d'):
    data = get_data(symbol, interval)
    if not data or len(data) < 200:
        return f"❌ خطا در تحلیل {symbol.upper()} ({interval}): داده کافی نیست یا دریافت نشد."

    price = float(data[-1][2])
    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)
    ma50 = sum([float(x[2]) for x in data[-50:]]) / 50
    ma200 = sum([float(x[2]) for x in data[-200:]]) / 200

    msg = f"📊 تحلیل {'روزانه' if interval == '1d' else '4 ساعته'} {symbol.upper()}:\n"
    msg += f"📅 تاریخ: {datetime