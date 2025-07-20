# app/services/place_order_service.py
from flask import jsonify, request
from app.utils.logger import logger
import app.utils.shared_state as shared_state

def handle_place_order(req):
    try:
        data = req.get_json()
        mobile = data.get("mobile")

        logger.info(f"Received place_order request | mobile={mobile} | data={data}")

        if not mobile or mobile not in shared_state.clients:
            logger.warning(f"User not logged in or missing mobile: {mobile}")
            return jsonify({"error": "User not logged in"}), 401

        client_data = shared_state.clients[mobile]
        client = client_data["client"]

        required_fields = [
            "exchange_segment", "product", "price", "order_type", "quantity",
            "validity", "trading_symbol", "transaction_type"
        ]
        missing = [field for field in required_fields if field not in data]
        if missing:
            logger.warning(f"Missing fields in order request: {missing}")
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        logger.debug("Placing order with validated data...")

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

        logger.info(f"Order placed successfully | response={response}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Exception in handle_place_order: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
