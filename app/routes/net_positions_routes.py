# app/routes/net_positions_routes.py

from flask import Blueprint, request, jsonify
from app.utils.shared_state import clients

net_positions_bp = Blueprint("net_positions", __name__)

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
            except Exception as e:
                print("WebSocket subscribe failed:", e)

        return jsonify({
            "status": "success",
            "positions": positions
        }), 200

    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500
