from app.utils import shared_state

def run_strategy(data):
    client = get_client()

    # Example strategy (straddle):
    exchange = data["exchange_segment"]
    symbol = data["symbol"]
    strike_price = data["strike_price"]
    expiry = data["expiry"]
    qty = data["quantity"]

    ce_trading_symbol = f"{symbol}{expiry}C{strike_price}"
    pe_trading_symbol = f"{symbol}{expiry}P{strike_price}"

    ce_order = client.place_order(
        exchange_segment=exchange,
        product="NRML",
        price="0",
        order_type="MKT",
        quantity=str(qty),
        validity="DAY",
        trading_symbol=ce_trading_symbol,
        transaction_type="S",
        amo="NO",
        disclosed_quantity="0",
        market_protection="0",
        pf="N",
        trigger_price="0"
    )

    pe_order = client.place_order(
        exchange_segment=exchange,
        product="NRML",
        price="0",
        order_type="MKT",
        quantity=str(qty),
        validity="DAY",
        trading_symbol=pe_trading_symbol,
        transaction_type="S",
        amo="NO",
        disclosed_quantity="0",
        market_protection="0",
        pf="N",
        trigger_price="0"
    )

    return {"call_order": ce_order, "put_order": pe_order}

from app.utils.strategy_helper import generate_strategy_orders

import app.utils.shared_state as shared_state
from flask import jsonify
from app.utils.logger import logger
def execute_strategy(data):
    """
    Orchestrates strategy execution:
    - Generates order legs
    - Places them via NeoAPI
    """
    mobile =9793928983
    user_data = shared_state.clients.get(mobile)
    if not user_data:
        logger.warning(f"User not logged in: {mobile}")
        return jsonify({"error": "User not logged in"}), 401
    client = user_data()
    order_legs = generate_strategy_orders(data)

    order_responses = []
    for leg in order_legs:
        res = client.place_order(**leg)
        order_responses.append(res)

    return {"status": "success", "orders": order_responses}
