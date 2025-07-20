# strategies/straddle.py
import time

def run(api):
    symbol = "NIFTY"
    qty = 1
    sl_percent = 20  # stop loss 20%
    tgt_percent = 30 # target 30%

    atm = api.get_atm_strike(symbol)

    call_price = api.get_option_price(symbol, atm, "CALL")
    put_price = api.get_option_price(symbol, atm, "PUT")

    entry_call = call_price
    entry_put = put_price

    api.place_order(symbol, atm, "CALL", "BUY", qty)
    api.place_order(symbol, atm, "PUT", "BUY", qty)

    while True:
        time.sleep(5)  # avoid API overload
        ltp_call = api.get_option_price(symbol, atm, "CALL")
        ltp_put = api.get_option_price(symbol, atm, "PUT")

        pnl_call = (ltp_call - entry_call) * qty
        pnl_put = (ltp_put - entry_put) * qty
        total_pnl = pnl_call + pnl_put

        entry_total = (entry_call + entry_put) * qty
        sl = -sl_percent / 100 * entry_total
        tgt = tgt_percent / 100 * entry_total

        print(f"[Straddle] PnL: {total_pnl:.2f} | SL: {sl:.2f} | Target: {tgt:.2f}")

        if total_pnl <= sl or total_pnl >= tgt:
            api.place_order(symbol, atm, "CALL", "SELL", qty)
            api.place_order(symbol, atm, "PUT", "SELL", qty)
            print("Straddle exit triggered.")
            break
