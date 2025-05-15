@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message", {}).get("text", "").lower().strip()
    print("Message received:", message)  # برای دیباگ

    if not message:
        return 'ok'

    parts = message.split()
    
    # استخراج symbol و interval از پیام
    symbol = None
    interval = '1d'
    
    for part in parts:
        if part in SYMBOLS and symbol is None:
            symbol = part
        if part in ['1d', '4h']:
            interval = part

    # اگر symbol معتبر بود، تحلیل همان ارز را انجام بده
    if symbol:
        result = analyze(symbol, interval)
        send_message(result)
    else:
        # اگر هیچ symbol معتبری نبود، همه ارزها تحلیل شوند
        full = ""
        for s in SYMBOLS:
            result_1d = analyze(s, '1d')
            result_4h = analyze(s, '4h')
            combined = f"{result_1d}\n{'-'*20}\n{result_4h}\n{'='*40}\n"
            if len(full) + len(combined) < 4000:
                full += combined
            else:
                send_message(full)
                full = combined
        if full:
            send_message(full)

    return 'ok'