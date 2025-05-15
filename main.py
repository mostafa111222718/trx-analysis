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
        'interval': interval,
        'limit': 500
    }
    response = requests.get(url, params=params)
    
    # 🛠 تغییر چنگیز: بررسی صحت داده
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data
        else:
            raise ValueError("No data received from Binance.")
    else:
        raise ConnectionError("Failed to fetch data from Binance.")

# محاسبه RSI از داده‌های قیمت
def calculate_rsi(data, period=14):
    # 🛠 تغییر چنگیز: بررسی کافی بودن داده‌ها
    if len(data) < period + 1:
        raise ValueError("Not enough data to calculate RSI.")
    closes = [float(entry[4]) for entry in data]
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
    # 🛠 تغییر چنگیز: بررسی کافی بودن داده‌ها
    if len(data) < slow_period + signal_period:
        raise ValueError("Not enough data to calculate MACD.")
    closes = [float(entry[4]) for entry in data]
    fast_ema = [sum(closes[:fast_period]) / fast_period]
    slow_ema = [sum(closes[:slow_period]) / slow_period]

    for i in range(slow_period, len(closes)):
        fast_ema.append((closes[i] * (2 / (fast_period + 1))) + (fast_ema[-1] * (1 - (2 / (fast_period + 1)))))
        slow_ema.append((closes[i] * (2 / (slow_period + 1))) + (slow_ema[-1] * (1 - (2 / (slow_period + 1)))))

    macd = [fast - slow for fast, slow in zip(fast_ema, slow_ema)]
    signal = [sum(macd[i:i + signal_period]) / signal_period for i in range(len(macd) - signal_period + 1)]
    return macd[-1], signal[-1]

# تحلیل روزانه TRX
def get_daily_analysis():
    try:
        data = get_trx_data(interval='1d')
        rsi = calculate_rsi(data)
        macd, signal = calculate_macd(data)

        message = f"📊 تحلیل روزانه TRX:\n"
        message += f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}\n"
        message += f"قیمت فعلی: {float(data[-1][4]):.3f} USDT\n"
        message += f"RSI: {rsi:.2f} {'✅' if rsi < 70 else '❌'}\n"
        message += f"MACD: {macd:.4f} {'صعودی' if macd > signal else 'نزولی'} {'✅' if macd > signal else '❌'}\n"

        ma50 = sum([float(entry[4]) for entry in data[-50:]]) / 50
        ma200 = sum([float(entry[4]) for entry in data[-200:]]) / 200
        message += f"MA50: {ma50:.3f} | MA200: {ma200:.3f}\n"

        if rsi < 30 and macd > signal:
            message += "⚡️ هشدار خرید فعال ✅"
        elif rsi > 70 and macd < signal:
            message += "⚡️ هشدار فروش فعال ❌"
        else:
            message += "هیچ هشدار فعال نیست ❌"

        return message
    except Exception as e:
        return f"❌ خطا در تحلیل روزانه: {str(e)}"  # 🛠 تغییر چنگیز: ارسال خطا

# تحلیل 4 ساعته TRX
def get_4h_analysis():
    try:
        data = get_trx_data(interval='4h')
        rsi = calculate_rsi(data)
        macd, signal = calculate_macd(data)

        message = f"📊 تحلیل 4 ساعته TRX:\n"
        message += f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        message += f"قیمت فعلی: {float(data[-1][4]):.3f} USDT\n"
        message += f"RSI: {rsi:.2f} {'✅' if rsi < 70 else '❌'}\n"
        message += f"MACD: {macd:.4f} {'صعودی' if macd > signal else 'نزولی'} {'✅' if macd > signal else '❌'}\n"

        ma50 = sum([float(entry[4]) for entry in data[-50:]]) / 50
        ma200 = sum([float(entry[4]) for entry in data[-200:]]) / 200
        message += f"MA50: {ma50:.3f} | MA200: {ma200:.3f}\n"

        if rsi < 30 and macd > signal:
            message += "⚡️ هشدار خرید فعال ✅"
        elif rsi > 70 and macd < signal:
            message += "⚡️ هشدار فروش فعال ❌"
        else:
            message += "هیچ هشدار فعال نیست ❌"

        return message
    except Exception as e:
        return f"❌ خطا در تحلیل 4 ساعته: {str(e)}"  # 🛠 تغییر چنگیز: ارسال خطا

# ارسال تحلیل ترکیبی
def send_combined_analysis():
    daily_message = get_daily_analysis()
    h4_message = get_4h_analysis()
    
    combined_message = f"{daily_message}\n\n{'-'*20}\n\n{h4_message}"
    send_message(combined_message)

# اجرای اولیه
send_combined_analysis()

# اجرای مداوم هر 4 ساعت
while True:
    time.sleep(14400)  # 4 ساعت
    send_combined_analysis()
