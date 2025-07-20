# app/routes/place_order_routes.py

from flask import Blueprint, request, jsonify
from app.services.place_order_service import handle_place_order

place_order_bp = Blueprint("place_order", __name__)

@place_order_bp.route("/placeOrder", methods=["POST"])
def place_order():
    try:
        data = request.json
        response = handle_place_order(data)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
