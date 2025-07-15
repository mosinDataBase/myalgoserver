def calculate_positions_summary(data):
    positions_summary = []

    for item in data:
        try:
            lot_size = float(item.get("lotSz", 1))
            multiplier = float(item.get("multiplier", 1))
            precision = int(item.get("precision", 2))

            cf_buy_qty = float(item.get("cfBuyQty", 0))
            cf_sell_qty = float(item.get("cfSellQty", 0))
            fl_buy_qty = float(item.get("flBuyQty", 0))
            fl_sell_qty = float(item.get("flSellQty", 0))

            total_buy_qty = (cf_buy_qty + fl_buy_qty) / lot_size
            total_sell_qty = (cf_sell_qty + fl_sell_qty) / lot_size
            net_qty = total_buy_qty - total_sell_qty

            buy_amt = float(item.get("buyAmt", 0)) + float(item.get("cfBuyAmt", 0))
            sell_amt = float(item.get("sellAmt", 0)) + float(item.get("cfSellAmt", 0))

            gen_num = float(item.get("genNum", 1))
            gen_den = float(item.get("genDen", 1))
            prc_num = float(item.get("prcNum", 1))
            prc_den = float(item.get("prcDen", 1))

            ratio = multiplier * (gen_num / gen_den) * (prc_num / prc_den)

            buy_avg_price = (buy_amt / (total_buy_qty * ratio)) if total_buy_qty > 0 else 0
            sell_avg_price = (sell_amt / (total_sell_qty * ratio)) if total_sell_qty > 0 else 0
            avg_price = buy_avg_price if total_buy_qty > total_sell_qty else sell_avg_price if total_sell_qty > total_buy_qty else 0

            ltp = avg_price  # Placeholder LTP
            pnl = (sell_amt - buy_amt) + (net_qty * ltp * ratio)

            positions_summary.append({
                "symbol": item.get("sym"),
                "exchange": item.get("exSeg", "").split("_")[0].upper(),
                "buyQty": round(total_buy_qty, 2),
                "sellQty": round(total_sell_qty, 2),
                "netQty": round(net_qty, 2),
                "avgPrice": round(avg_price, precision),
                "pnl": round(pnl, 2)
            })

        except Exception as e:
            continue

    return positions_summary
