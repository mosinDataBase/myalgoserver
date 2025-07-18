from flask import Blueprint, jsonify

from flask import jsonify
from app.services.master_data_service import load_master_data
from app.utils.shared_state import nse_cm_database


master_bp = Blueprint("master", __name__)

@master_bp.route("/refreshdata", methods=["POST"])
def refresh_master_data():
    success = load_master_data()
    print("master data loaded status: ",success)

    nse_cm_trimmed = []
    if success and nse_cm_database is not None and not nse_cm_database.empty:
        nse_cm_trimmed = nse_cm_database[
            ["pSymbol", "pSymbolName", "pDesc", "pInstType"]
        ].dropna().to_dict(orient="records")

    return jsonify({
        "success": success,
        "nse_cm_symbols": nse_cm_trimmed
    })
