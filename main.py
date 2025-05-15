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
    }
    requests.get(url, params=params)

# گرفتن داده‌ها از Binance API برای TRX (با تایم فریم دلخواه)
def get_trx_data(interval='1d'):
    url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': 'TRXUSDT',
        'interval': interval,  # تایم فریم (1d یا 4h)
        'limit': 500
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

# محاسبه RSI از داده‌های قیمت
def calculate_rsi(data, period=14):
    closes = [float(entry[4]) for entry in data]  # قیمت‌های بسته شدن
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            losses.append(-change)
            gains.append(0)

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    return rsi

# محاسبه MACD از داده‌های قیمت
def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    closes = [float(entry[4]) for entry in data]  # قیمت‌های بسته شدن
    fast_ema = [sum(closes[:fast_period]) / fast_period]
    slow_ema = [sum(closes[:slow_period]) / slow_period]

    # محاسبه MACD
    for i in range(fast_period, len(closes)):
        fast_ema.append((closes[i] * (2 / (fast_period + 1))) + (fast_ema[-1] * (1 - (2 / (fast_period + 1)))))
        slow_ema.append((closes[i] * (2 / (slow_period + 1))) + (slow_ema[-1] * (1 - (2 / (slow_period + 1)))))

    macd = [fast - slow for fast, slow in zip(fast_ema, slow_ema)]
    signal = [sum(macd[i:i + signal_period]) / signal_period for i in range(len(macd) - signal_period + 1)]
    return macd[-1], signal[-1]

# تحلیل روزانه TRX
def get_daily_analysis():
    data = get_trx_data(interval='1d')
    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)

    # ایجاد پیام تحلیل روزانه
    message = f"📊 تحلیل روزانه TRX:\n"
    message += f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}\n"
    message += f"قیمت فعلی: {float(data[-1][4]):.3f} USDT\n"
    message += f"RSI: {rsi:.2f} {'✅' if rsi < 70 else '❌'}\n"
    message += f"MACD: {macd:.4f} {'صعودی' if macd > signal else 'نزولی'} {'✅' if macd > signal else '❌'}\n"

    # وضعیت MA50 و MA200
    ma50 = sum([float(entry[4]) for entry in data[-50:]]) / 50
    ma200 = sum([float(entry[4]) for entry in data[-200:]]) / 200
    message += f"MA50: {ma50:.3f} | MA200: {ma200:.3f}\n"
    
    # هشدار خرید و فروش
    if rsi < 30 and macd > signal:
        message += "⚡️ هشدار خرید فعال ✅"
    elif rsi > 70 and macd < signal:
        message += "⚡️ هشدار فروش فعال ❌"
    else:
        message += "هیچ هشدار فعال نیست ❌"
    
    return message

# تحلیل 4 ساعته TRX
def get_4h_analysis():
    data = get_trx_data(interval='4h')
    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)

    # ایجاد پیام تحلیل 4 ساعته
    message = f"📊 تحلیل 4 ساعته TRX:\n"
    message += f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    message += f"قیمت فعلی: {float(data[-1][4]):.3f} USDT\n"
    message += f"RSI: {rsi:.2f} {'✅' if rsi < 70 else '❌'}\n"
    message += f"MACD: {macd:.4f} {'صعودی' if macd > signal else 'نزولی'} {'✅' if macd > signal else '❌'}\n"

    # وضعیت MA50 و MA200
    ma50 = sum([float(entry[4]) for entry in data[-50:]]) / 50
    ma200 = sum([float(entry[4]) for entry in data[-200:]]) / 200
    message += f"MA50: {ma50:.3f} | MA200: {ma200:.3f}\n"
    
    # هشدار خرید و فروش
    if rsi < 30 and macd > signal:
        message += "⚡️ هشدار خرید فعال ✅"
    elif rsi > 70 and macd < signal:
        message += "⚡️ هشدار فروش فعال ❌"
    else:
        message += "هیچ هشدار فعال نیست ❌"
    
    return message

# ارسال تحلیل روزانه و 4 ساعته
def send_combined_analysis():
    daily_message = get_daily_analysis()
    h4_message = get_4h_analysis()
    
    # ترکیب دو تحلیل در یک پیام
    combined_message = f"{daily_message}\n\n{'-'*20}\n\n{h4_message}"
    send_message(combined_message)

# ارسال تحلیل روزانه و 4 ساعته
send_combined_analysis()

# تنظیم ارسال تحلیل هر 4 ساعت
while True:
    send_combined_analysis()
    time.sleep(14400)  # هر 4 ساعت یک بار اجرا میشه
