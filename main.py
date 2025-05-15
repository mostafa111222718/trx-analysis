import requests
import time
from datetime import datetime
from flask import Flask, request

# =============== پیکربندی ===============
TOKEN = 'توکن_ربات_تلگرام_اینجا'
CHAT_ID = 'آی‌دی_چت_اینجا'

# =============== ارسال پیام به تلگرام ===============
def send_message(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {
        'chat_id': CHAT_ID,
        'text': message
    }
    requests.get(url, params=params)

# =============== گرفتن داده از KuCoin ===============
def get_price_data(symbol='TRX-USDT', interval='1day', limit=200):
    url = 'https://api.kucoin.com/api/v1/market/candles'
    params = {
        'symbol': symbol,
        'type': interval,
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f'خطا در دریافت داده‌های {symbol} از KuCoin.')
    data = response.json()['data']
    data.reverse()
    return data[:limit]

# =============== محاسبه RSI ===============
def calculate_rsi(data, period=14):
    closes = [float(item[2]) for item in data]
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(0, change))
        losses.append(max(0, -change))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =============== محاسبه MACD ===============
def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    closes = [float(item[2]) for item in data]
    def ema(values, period):
        ema_vals = [sum(values[:period]) / period]
        k = 2 / (period + 1)
        for price in values[period:]:
            ema_vals.append(price * k + ema_vals[-1] * (1 - k))
        return ema_vals
    fast = ema(closes, fast_period)
    slow = ema(closes, slow_period)
    macd = [f - s for f, s in zip(fast[-len(slow):], slow)]
    signal = ema(macd, signal_period)
    return macd[-1], signal[-1]

# =============== ساخت پیام تحلیل ===============
def build_analysis_message(symbol, interval='1day'):
    try:
        data = get_price_data(symbol.replace("USDT", "-USDT"), interval=interval)
    except:
        return f"❌ خطا در دریافت داده‌های {symbol} از KuCoin."

    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)
    closes = [float(item[2]) for item in data]
    ma50 = sum(closes[-50:]) / 50
    ma200 = sum(closes[-200:]) / 200
    price = float(data[-1][2])

    msg = f"📊 تحلیل {'روزانه' if interval == '1day' else '4 ساعته'} {symbol}:\n"
    msg += f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    msg += f"قیمت فعلی: {price:.3f} USDT\n"
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

# =============== ارسال هر ۴ ساعت ===============
def periodic_analysis():
    while True:
        daily = build_analysis_message('TRXUSDT', '1day')
        h4 = build_analysis_message('TRXUSDT', '4hour')
        send_message(f"{daily}\n\n{'-'*20}\n\n{h4}")
        time.sleep(14400)  # هر 4 ساعت

# =============== پاسخ به پیام‌ها در تلگرام ===============
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    update = request.json
    if 'message' in update:
        text = update['message'].get('text', '').lower()
        chat_id = update['message']['chat']['id']
        if text in ['trx', 'btc', 'eth']:
            symbol = text.upper() + 'USDT'
            msg = build_analysis_message(symbol, '1day') + "\n\n" + build_analysis_message(symbol, '4hour')
            url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
            params = {'chat_id': chat_id, 'text': msg}
            requests.get(url, params=params)
    return '', 200

# اگر می‌خوای برنامه لوکال اجرا بشه:
# periodic_analysis()

# اگر روی هاست (مثل Replit) هستی، از وب‌هوک استفاده کن:
if __name__ == '__main__':
    app.run(port=5000)