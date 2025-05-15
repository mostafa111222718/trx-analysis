import requests
import time
from datetime import datetime

# توکن ربات و chat_id
TOKEN = '7665819781:AAFqklWxMbzvtWydzfolKwDZFbS2lZ4SjeM'
CHAT_ID = '5451942674'

# ارسال پیام به تلگرام
def send_message(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.get(url, params=params)

# گرفتن داده‌ها از CoinEx API
def get_trx_data(interval='1d'):
    url = 'https://api.coinex.com/v1/market/kline'
    interval_map = {
        '1d': '1day',
        '4h': '4hour'
    }
    params = {
        'market': 'trxusdt',
        'type': interval_map.get(interval, '1day'),
        'limit': 500
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data['code'] != 0:
        return None
    return data['data']

# محاسبه RSI
def calculate_rsi(data, period=14):
    closes = [float(entry[2]) for entry in data]
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-change)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# محاسبه MACD
def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    closes = [float(entry[2]) for entry in data]
    fast_ema = [sum(closes[:fast_period]) / fast_period]
    slow_ema = [sum(closes[:slow_period]) / slow_period]
    for i in range(fast_period, len(closes)):
        fast_ema.append((closes[i] * (2 / (fast_period + 1))) + (fast_ema[-1] * (1 - (2 / (fast_period + 1)))))
    for i in range(slow_period, len(closes)):
        slow_ema.append((closes[i] * (2 / (slow_period + 1))) + (slow_ema[-1] * (1 - (2 / (slow_period + 1)))))
    macd = [f - s for f, s in zip(fast_ema[-len(slow_ema):], slow_ema)]
    signal = [sum(macd[i:i + signal_period]) / signal_period for i in range(len(macd) - signal_period + 1)]
    return macd[-1], signal[-1]

# تحلیل روزانه
def get_daily_analysis():
    data = get_trx_data(interval='1d')
    if data is None or len(data) < 200:
        return "❌ تحلیل روزانه: داده کافی برای محاسبه MA200 وجود ندارد."
    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)
    ma50 = sum([float(entry[2]) for entry in data[-50:]]) / 50
    ma200 = sum([float(entry[2]) for entry in data[-200:]]) / 200
    message = f"📊 تحلیل روزانه TRX:\n"
    message += f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}\n"
    message += f"قیمت فعلی: {float(data[-1][2]):.3f} USDT\n"
    message += f"RSI: {rsi:.2f} {'✅' if rsi < 70 else '❌'}\n"
    message += f"MACD: {macd:.4f} {'صعودی' if macd > signal else 'نزولی'} {'✅' if macd > signal else '❌'}\n"
    message += f"MA50: {ma50:.3f} | MA200: {ma200:.3f}\n"
    if rsi < 30 and macd > signal:
        message += "⚡️ هشدار خرید فعال ✅"
    elif rsi > 70 and macd < signal:
        message += "⚡️ هشدار فروش فعال ❌"
    else:
        message += "هیچ هشدار فعال نیست ❌"
    return message

# تحلیل ۴ ساعته
def get_4h_analysis():
    data = get_trx_data(interval='4h')
    if data is None or len(data) < 200:
        return "❌ تحلیل ۴ ساعته: داده کافی برای محاسبه MA200 وجود ندارد."
    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)
    ma50 = sum([float(entry[2]) for entry in data[-50:]]) / 50
    ma200 = sum([float(entry[2]) for entry in data[-200:]]) / 200
    message = f"📊 تحلیل 4 ساعته TRX:\n"
    message += f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    message += f"قیمت فعلی: {float(data[-1][2]):.3f} USDT\n"
    message += f"RSI: {rsi:.2f} {'✅' if rsi < 70 else '❌'}\n"
    message += f"MACD: {macd:.4f} {'صعودی' if macd > signal else 'نزولی'} {'✅' if macd > signal else '❌'}\n"
    message += f"MA50: {ma50:.3f} | MA200: {ma200:.3f}\n"
    if rsi < 30 and macd > signal:
        message += "⚡️ هشدار خرید فعال ✅"
    elif rsi > 70 and macd < signal:
        message += "⚡️ هشدار فروش فعال ❌"
    else:
        message += "هیچ هشدار فعال نیست ❌"
    return message

# ترکیب و ارسال تحلیل‌ها
def send_combined_analysis():
    daily_message = get_daily_analysis()
    h4_message = get_4h_analysis()
    combined_message = f"{daily_message}\n\n{'-'*20}\n\n{h4_message}"
    send_message(combined_message)

# اجرای خودکار هر ۴ ساعت
while True:
    send_combined_analysis()
    time.sleep(14400)  # 4 ساعت