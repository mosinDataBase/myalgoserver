from flask import Blueprint, request, jsonify
from app.services.quote_service import get_quotes_data, subscribe_live_tokens,get_main_indices

quotes_bp = Blueprint("quotes", __name__)

@quotes_bp.route("/symbol", methods=["POST"])
def get_quotes():
    return get_quotes_data(request)

@quotes_bp.route("/livedata", methods=["POST"])
def subscribe():
    return subscribe_live_tokens(request)

@quotes_bp.route("/getMainIndices", methods=["POST"])
def getMainIndices():
    return get_main_indices(request)
