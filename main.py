import requests
import time
from datetime import datetime

# توکن و chat_id شما
TOKEN = '7665819781:AAFqklWxMbzvtWydzfolKwDZFbS2lZ4SjeM'
CHAT_ID = '5451942674'

def send_message(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.get(url, params=params)

def get_trx_data(symbol, interval='1d'):
    url = 'https://api.coinex.com/v1/market/kline'
    interval_map = {
        '1d': '1day',
        '4h': '4hour'
    }
    params = {
        'market': symbol.lower() + 'usdt',
        'type': interval_map.get(interval, '1day'),
        'limit': 500
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data['code'] != 0:
        return None
    return data['data']

def calculate_rsi(data, period=14):
    closes = [float(entry[2]) for entry in data]
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    closes = [float(entry[2]) for entry in data]
    def ema(prices, period):
        ema_vals = [sum(prices[:period]) / period]
        k = 2 / (period + 1)
        for price in prices[period:]:
            ema_vals.append(price * k + ema_vals[-1] * (1 - k))
        return ema_vals
    fast = ema(closes, fast_period)
    slow = ema(closes, slow_period)
    macd_line = [f - s for f, s in zip(fast[-len(slow):], slow)]
    signal_line = ema(macd_line, signal_period)
    return macd_line[-1], signal_line[-1]

def analyze(symbol, interval):
    data = get_trx_data(symbol, interval)
    if data is None or len(data) < 200:
        return f"❌ خطا در تحلیل {symbol.upper()} ({interval}): داده کافی نیست یا دریافت نشد."

    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)
    ma50 = sum([float(entry[2]) for entry in data[-50:]]) / 50
    ma200 = sum([float(entry[2]) for entry in data[-200:]]) / 200
    price = float(data[-1][2])

    if interval == '1d':
        title = f"📊 تحلیل روزانه {symbol.upper()}"
        date = datetime.now().strftime('%Y-%m-%d')
    else:
        title = f"📊 تحلیل 4 ساعته {symbol.upper()}"
        date = datetime.now().strftime('%Y-%m-%d %H:%M')

    msg = f"{title}:\n📅 تاریخ: {date}\nقیمت فعلی: {price:.3f} USDT\n"
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

def send_all_analysis():
    symbols = ['trx', 'btc', 'eth', 'doge', 'ada', 'usdt']
    combined = ""
    for symbol in symbols:
        daily = analyze(symbol, '1d')
        h4 = analyze(symbol, '4h')
        combined += f"{daily}\n\n{'-'*20}\n\n{h4}\n\n{'='*40}\n\n"
    send_message(combined.strip())

# اجرای یک‌باره برای تست
send_all_analysis()

# اجرای خودکار هر 4 ساعت
# while True:
#     send_all_analysis()
#     time.sleep(14400)