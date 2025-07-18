# app/routes/net_positions_routes.py
import logging
from flask import Blueprint, request, jsonify
from app.utils.shared_state import clients
from app.utils.socket_events import on_message,on_error,on_open,on_close

net_positions_bp = Blueprint("net_positions", __name__)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
@net_positions_bp.route("/positions", methods=["POST"])
def get_net_positions():
    try:
        data = request.get_json()
        mobile = data.get("mobile")

        if not mobile:
            return jsonify({"error": "Missing mobile number"}), 400

        user_data = clients.get(mobile)
        if not user_data:
            return jsonify({"error": "User not logged in"}), 401

        client = user_data.get("client")
        result = client.positions()

        if result.get("stat", "").lower() != "ok":
            return jsonify({
                "error": "Failed to fetch net positions",
                "details": result
            }), 500

        positions = result.get("data", [])

        # 🔍 Filter active positions for live market subscription
        active_tokens = []
        for pos in positions:
            try:
                buy_qty = int(pos.get("flBuyQty") or 0)
                sell_qty = int(pos.get("flSellQty") or 0)
                net_qty = buy_qty - sell_qty
                if net_qty != 0:
                    active_tokens.append({
                        "instrument_token": pos.get("tok"),
                        "exchange_segment": pos.get("exSeg")
                    })
            except Exception:
                continue  # skip if parsing error
            
        # 🔌 Subscribe to live feed for active tokens only
        if active_tokens:
            try:
                client.subscribe(instrument_tokens=active_tokens, isIndex=False, isDepth=False)
               
             # Set socket handlers
                client.on_message = on_message  # called when message is received from websocket
                client.on_error = on_error  # called when any error or exception occurs in code or websocket
                client.on_close = on_close  # called when websocket connection is closed
                client.on_open = on_open  # called when websocket successfully connects

            except Exception as e:
                print("WebSocket subscribe failed:", e)

        return jsonify({
            "status": "success",
            "positions": positions
        }), 200

    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500
