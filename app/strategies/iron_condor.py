import time

def run(api):
    symbol = "NIFTY"
    qty, sl_percent, tgt_percent = 1, 20, 30

    atm = api.get_atm_strike(symbol)
    legs = [
        {"strike": atm + 100, "type": "CALL", "action": "SELL"},
        {"strike": atm + 200, "type": "CALL", "action": "BUY"},
        {"strike": atm - 100, "type": "PUT", "action": "SELL"},
        {"strike": atm - 200, "type": "PUT", "action": "BUY"}
    ]

    entries = {}
    for leg in legs:
        api.place_order(symbol, leg["strike"], leg["type"], leg["action"], qty)
        entries[f"{leg['type']}_{leg['strike']}"] = api.get_option_price(symbol, leg["strike"], leg["type"])

    entry_total = sum(v for v in entries.values()) * qty
    sl = -sl_percent / 100 * entry_total
    tgt = tgt_percent / 100 * entry_total

    while True:
        time.sleep(5)
        pnl = 0
        for leg in legs:
            key = f"{leg['type']}_{leg['strike']}"
            current_price = api.get_option_price(symbol, leg["strike"], leg["type"])
            change = (entries[key] - current_price) if leg["action"] == "SELL" else (current_price - entries[key])
            pnl += change * qty

        print(f"[Iron Condor] PnL: {pnl:.2f}")
        if pnl <= sl or pnl >= tgt:
            for leg in legs:
                exit_action = "BUY" if leg["action"] == "SELL" else "SELL"
                api.place_order(symbol, leg["strike"], leg["type"], exit_action, qty)
            print("Iron Condor exited")
            break
