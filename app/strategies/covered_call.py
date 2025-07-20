import time

def run(api):
    symbol = "RELIANCE"
    qty, sl_percent, tgt_percent = 1, 20, 30

    ltp = api.get_ltp(symbol)
    strike = round((ltp + 50) / 10) * 10

    entry_price = api.get_option_price(symbol, strike, "CALL")
    api.place_order(symbol, strike, "CALL", "SELL", qty)

    sl = -sl_percent / 100 * entry_price * qty
    tgt = tgt_percent / 100 * entry_price * qty

    while True:
        time.sleep(5)
        pnl = (entry_price - api.get_option_price(symbol, strike, "CALL")) * qty
        print(f"[Covered Call] PnL: {pnl:.2f}")
        if pnl <= sl or pnl >= tgt:
            api.place_order(symbol, strike, "CALL", "BUY", qty)
            print("Covered Call exited")
            break
