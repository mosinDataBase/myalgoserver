import time

def run(api):
    symbol = "NIFTY"
    qty, sl_percent, tgt_percent = 1, 20, 30

    atm = api.get_atm_strike(symbol)
    call_strike = atm + 100
    put_strike = atm - 100

    entry_call = api.get_option_price(symbol, call_strike, "CALL")
    entry_put = api.get_option_price(symbol, put_strike, "PUT")

    api.place_order(symbol, call_strike, "CALL", "SELL", qty)
    api.place_order(symbol, put_strike, "PUT", "SELL", qty)

    entry_total = (entry_call + entry_put) * qty
    sl = -sl_percent / 100 * entry_total
    tgt = tgt_percent / 100 * entry_total

    while True:
        time.sleep(5)
        pnl = ((entry_call - api.get_option_price(symbol, call_strike, "CALL")) +
               (entry_put - api.get_option_price(symbol, put_strike, "PUT"))) * qty
        print(f"[Strangle] PnL: {pnl:.2f}")
        if pnl <= sl or pnl >= tgt:
            api.place_order(symbol, call_strike, "CALL", "BUY", qty)
            api.place_order(symbol, put_strike, "PUT", "BUY", qty)
            print("Strangle exited")
            break
