import requests
import time
from datetime import datetime

TOKEN = '7665819781:AAFqklWxMbzvtWydzfolKwDZFbS2lZ4SjeM'
CHAT_ID = '5451942674'

# ارسال پیام به تلگرام
def send_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.get(url, params=params)

# گرفتن داده‌ها از CoinEx API برای TRX
def get_trx_data(interval='1d'):
    url = 'https://api.coinex.com/v1/market/kline'
    interval_map = {'1d': '1day', '4h': '4hour'}
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
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# محاسبه MACD
def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    closes = [float(entry[2]) for entry in data]
    def ema(prices, period):
        ema_vals = [sum(prices[:period]) / period]
        multiplier = 2 / (period + 1)
        for price in prices[period:]:
            ema_vals.append((price - ema_vals[-1]) * multiplier + ema_vals[-1])
        return ema_vals
    fast_ema = ema(closes, fast_period)
    slow_ema = ema(closes, slow_period)
    macd = [f - s for f, s in zip(fast_ema[-len(slow_ema):], slow_ema)]
    signal = ema(macd, signal_period)
    return macd[-1], signal[-1]

# ساخت پیام تحلیل
def build_analysis(interval, name):
    data = get_trx_data(interval)
    if data is None:
        return f"❌ خطا در تحلیل {name}: دریافت اطلاعات ناموفق بود."
    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)
    ma50 = sum([float(entry[2]) for entry in data[-50:]]) / 50
    ma200 = sum([float(entry[2]) for entry in data[-200:]]) / 200
    price = float(data[-1][2])
    time_str = datetime.now().strftime('%Y-%m-%d') if interval == '1d' else datetime.now().strftime('%Y-%m-%d %H:%M')
    
    message = f"📊 تحلیل {'روزانه' if interval == '1d' else '4 ساعته'} TRX:\n"
    message += f"📅 تاریخ: {time_str}\n"
    message += f"قیمت فعلی: {price:.3f} USDT\n"
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

# ارسال تحلیل ترکیبی
def send_combined_analysis():
    daily_msg = build_analysis('1d', 'روزانه')
    h4_msg = build_analysis('4h', '4 ساعته')
    full_msg = f"{daily_msg}\n\n{'-'*20}\n\n{h4_msg}"
    send_message(full_msg)

# بررسی دستورات جدید
def check_commands(last_update_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {'offset': last_update_id + 1}
    response = requests.get(url, params=params).json()
    if not response['ok']:
        return last_update_id
    for update in response['result']:
        update_id = update['update_id']
        if 'message' in update and 'text' in update['message']:
            text = update['message']['text'].lower()
            if 'trx' in text:
                send_combined_analysis()
        last_update_id = update_id
    return last_update_id

# حلقه اصلی
if __name__ == "__main__":
    last_update_id = 0
    last_sent = 0
    while True:
        now = time.time()
        if now - last_sent >= 14400:  # هر ۴ ساعت
            send_combined_analysis()
            last_sent = now
        last_update_id = check_commands(last_update_id)
        time.sleep(5)