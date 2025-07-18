from flask import Blueprint, request, jsonify
from app.utils.shared_state import nse_fo_database, clients,cde_fo_database,nse_cm_database, mcx_fo_database, bse_cm_database
import re
import json
from flask import Response

symbol_search_bp = Blueprint('symbol_search', __name__)

@symbol_search_bp.route("/search_symbol", methods=["POST"])
def search_symbol():
    
    data = request.get_json()
    query = data.get("q", "").strip().lower()
    segment = data.get("segment", "").lower()
    mobile = data.get("phone")
    print("query and segment:", query, segment)

    if not query or segment not in ["nse_fo", "cde_fo", "mcx_fo", "nse_cm","bse_cm"]:
        return jsonify({"error": "Invalid query or segment"}), 400

    try:

        user_entry = clients.get(mobile)

        if isinstance(user_entry, dict):
            client = user_entry.get("client")
        else:
            client = user_entry

        # Optional: Test call to verify session
        resData = client.search_scrip(exchange_segment=segment, symbol=query)

        if segment == "nse_cm":
            filtered_data = []
            for item in resData:
                p_symbol_name = (item.get("pSymbolName") or "").strip().lower()
                if item.get("pGroup") is None and p_symbol_name == query:
                    filtered_data.append(item)
        elif segment == "nse_fo":
            filtered_data = [item for item in resData if item.get("pOptionType") is not None]
        else:
            filtered_data = resData

        print("resData",resData)
    except Exception as e:
        print("Exception when calling scrip search api -> search_scrip:", e)
    return  Response(json.dumps(filtered_data, default=str), mimetype='application/json')


