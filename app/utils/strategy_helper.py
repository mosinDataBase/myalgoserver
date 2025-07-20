def generate_strategy_orders(config):
    """
    Builds order legs based on strategy logic (from YouTube video).
    Example: Short Straddle at ATM strike.
    """
    spot_price = float(config["spot_price"])
    strike_step = int(config.get("strike_step", 50))
    atm_strike = round(spot_price / strike_step) * strike_step
    lot_size = int(config.get("lot_size", 50))
    expiry = config["expiry"]
    symbol = config["symbol"]
    exchange_segment = config.get("exchange_segment", "nse_fo")

    base_order = {
        "exchange_segment": exchange_segment,
        "product": "NRML",
        "order_type": "MKT",
        "quantity": str(lot_size),
        "validity": "DAY",
        "amo": "NO",
        "disclosed_quantity": "0",
        "market_protection": "0",
        "pf": "N",
        "trigger_price": "0",
        "tag": "strategy_auto"
    }

    ce_leg = {
        **base_order,
        "trading_symbol": f"{symbol}{expiry}C{atm_strike}",
        "transaction_type": "S",  # Sell Call
        "price": "0"
    }

    pe_leg = {
        **base_order,
        "trading_symbol": f"{symbol}{expiry}P{atm_strike}",
        "transaction_type": "S",  # Sell Put
        "price": "0"
    }

    return [ce_leg, pe_leg]
