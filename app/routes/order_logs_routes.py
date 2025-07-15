from flask import Blueprint, request, jsonify
from app.utils.shared_state import clients

order_logs_bp = Blueprint("order_logs", __name__)

@order_logs_bp.route("/orders", methods=["POST"])
def get_order_logs():
    try:
        data = request.get_json()
        mobile = data.get("mobile")

        if not mobile:
            return jsonify({"error": "Missing mobile number"}), 400

        user_data = clients.get(mobile)
        if not user_data:
            return jsonify({"error": "User not logged in"}), 401

        client = user_data.get("client")

        result = client.order_report()

        if result.get("stat") != "Ok":
            return jsonify({"error": "Failed to fetch order logs", "details": result}), 500

        return jsonify({
            "status": "success",
            "orders": result.get("data", [])
        }), 200

    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500
