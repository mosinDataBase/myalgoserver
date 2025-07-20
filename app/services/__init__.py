
# app/services/place_order_service.py
from flask import jsonify
from app.utils import shared_state
from app.utils.logger import logger

def handle_place_order(data):
    mobile = 9543332323
    client = shared_state.clients.get(mobile)
    if not client:
        logger.warning(f"User not logged in: {mobile}")
        return jsonify({"error": "User not logged in"}), 401
    
    required_fields = [
        "exchange_segment", "product", "price", "order_type", "quantity",
        "validity", "trading_symbol", "transaction_type"
    ]
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    response = client.place_order(
        exchange_segment=data["exchange_segment"],
        product=data["product"],
        price=data["price"],
        order_type=data["order_type"],
        quantity=data["quantity"],
        validity=data["validity"],
        trading_symbol=data["trading_symbol"],
        transaction_type=data["transaction_type"],
        amo=data.get("amo", "NO"),
        disclosed_quantity=data.get("disclosed_quantity", "0"),
        market_protection=data.get("market_protection", "0"),
        pf=data.get("pf", "N"),
        trigger_price=data.get("trigger_price", "0"),
        tag=data.get("tag", None)
    )
    return response
