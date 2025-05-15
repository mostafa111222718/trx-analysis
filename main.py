import requests
import time
from datetime import datetime

TOKEN = '7665819781:AAFqklWxMbzvtWydzfolKwDZFbS2lZ4SjeM'

# لیست ارزهای پشتیبانی شده با نماد کوینکس (تمام با usdt)
SUPPORTED_COINS = {
    'trx': 'trxusdt',
    'btc': 'btcusdt',
    'eth': 'ethusdt',
    'bnb': 'bnbusdt',
    'ada': 'adausdt',
    'doge': 'dogeusdt',
}

def send_message(chat_id, message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {'chat_id': chat_id, 'text': message}
    requests.get(url, params=params)

def get_updates(offset=None):
    url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
    params = {'timeout': 100, 'offset': offset}
    response = requests.get(url, params=params)
    result_json = response.json()
    return result_json['result']

def get_coinex_data(symbol='trxusdt', interval='1d'):
    url = f'https://api.coinex.com/v1/market/kline'
    params = {'market': symbol.lower(), 'type': interval, 'limit': 500}
    response = requests.get(url, params=params)
    data = response.json()
    if data['code'] == 0:
        return data['data']
    else:
        return None

def calculate_rsi(data, period=14):
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
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    closes = [float(entry[4]) for entry in data]
    fast_ema = [sum(closes[:fast_period]) / fast_period]
    slow_ema = [sum(closes[:slow_period]) / slow_period]
    for i in range(fast_period, len(closes)):
        fast_ema.append(closes[i] * (2 / (fast_period + 1)) + fast_ema[-1] * (1 - 2 / (fast_period + 1)))
        slow_ema.append(closes[i] * (2 / (slow_period + 1)) + slow_ema[-1] * (1 - 2 / (slow_period + 1)))
    macd = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal = [sum(macd[i:i + signal_period]) / signal_period for i in range(len(macd) - signal_period + 1)]
    return macd[-1], signal[-1]

def calculate_ma(data, period):
    closes = [float(entry[4]) for entry in data]
    if len(closes) < period:
        return sum(closes) / len(closes)
    return sum(closes[-period:]) / period

def create_analysis_message(data, interval_label, coin_symbol):
    rsi = calculate_rsi(data)
    macd, signal = calculate_macd(data)
    ma50 = calculate_ma(data, 50)
    ma200 = calculate_ma(data, 200)
    price = float(data[-1][4])
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d %H:%M') if interval_label == '4h' else now.strftime('%Y-%m-%d')

    message = f"📊 تحلیل {interval_label} {coin_symbol.upper()}:\n"
    message += f"📅 تاریخ: {date_str}\n"
    message += f"💰 قیمت فعلی: {price:.6f} USDT\n"
    message += f"📈 RSI: {rsi:.2f} {'✅' if rsi < 70 else '❌'}\n"
    message += f"📉 MACD: {macd:.6f} {'صعودی' if macd > signal else 'نزولی'} {'✅' if macd > signal else '❌'}\n"
    message += f"MA50: {ma50:.6f} | MA200: {ma200:.6f}\n"

    if rsi < 30 and macd > signal:
        message += "⚡️ هشدار خرید فعال ✅"
    elif rsi > 70 and macd < signal:
        message += "⚡️ هشدار فروش فعال ❌"
    else:
        message += "هیچ هشدار فعال نیست ❌"
    return message

def send_combined_analysis(chat_id, symbol):
    daily_data = get_coinex_data(symbol, '1d')
    h4_data = get_coinex_data(symbol, '4h')

    if daily_data is None or h4_data is None:
        send_message(chat_id, f"❌ خطا در دریافت داده‌های {symbol.upper()} از CoinEx.")
        return

    daily_message = create_analysis_message(daily_data, 'روزانه', symbol.replace('usdt',''))
    h4_message = create_analysis_message(h4_data, '4 ساعته', symbol.replace('usdt',''))
    combined_message = f"{daily_message}\n\n{'-'*20}\n\n{h4_message}"
    send_message(chat_id, combined_message)

def extract_coin_symbol(text):
    # جداسازی نماد ارز از متن، جستجو در کلمات و بازگرداندن نماد معتبر
    text = text.lower()
    for coin in SUPPORTED_COINS:
        if coin in text:
            return SUPPORTED_COINS[coin]
    return None

def main():
    offset = None
    print("ربات تحلیل رمزارزها شروع به کار کرد...")
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update['update_id'] + 1
                if 'message' in update and 'text' in update['message']:
                    chat_id = update['message']['chat']['id']
                    text = update['message']['text'].strip()
                    symbol = extract_coin_symbol(text)
                    if symbol:
                        send_combined_analysis(chat_id, symbol)
                    else:
                        msg = ("سلام! من ربات تحلیل رمزارز هستم.\n"
                               "لطفا نام یکی از ارزهای زیر را برای تحلیل بفرستید:\n" +
                               "\n".join(SUPPORTED_COINS.keys()))
                        send_message(chat_id, msg)
            time.sleep(1)
        except Exception as e:
            print(f"خطا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
