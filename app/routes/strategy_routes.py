from flask import Blueprint, request, jsonify
from app.services.strategy_service import run_strategy
from app.services.strategy_service import execute_strategy

strategy_bp = Blueprint("strategy", __name__)

@strategy_bp.route("/run", methods=["POST"])
def run_strategy_endpoint():
    try:
        data = request.json
        result = run_strategy(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@strategy_bp.route("/execute", methods=["POST"])
def run_strategy():
    try:
        data = request.json
        result = execute_strategy(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
