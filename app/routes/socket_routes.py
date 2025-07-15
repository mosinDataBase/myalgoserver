# app/routes/socket_routes.py

from flask import Blueprint, request, jsonify
from app.utils.shared_state import clients

socket_bp = Blueprint("socket", __name__)

@socket_bp.route("/unsubscribe", methods=["POST"])
def unsubscribe_ws():
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
        tokens = []

        for pos in result.get("data", []):
            try:
                buy_qty = int(pos.get("flBuyQty") or 0)
                sell_qty = int(pos.get("flSellQty") or 0)
                net_qty = buy_qty - sell_qty
                if net_qty != 0:
                    tokens.append({
                        "instrument_token": pos.get("tok"),
                        "exchange_segment": pos.get("exSeg")
                    })
            except Exception:
                continue

        if tokens:
            try:
                client.un_subscribe(tokens, isIndex=False, isDepth=False)
            except Exception as e:
                print("Unsubscribe error:", e)

        return jsonify({"status": "success", "unsubscribed_tokens": len(tokens)}), 200

    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500
