from flask import jsonify
from app.utils.shared_state import combined_database
from app.services.client_manager import load_master_data

def load_master_scrips():
    success = load_master_data()
    if success:
        return jsonify(combined_database.to_dict(orient="records")), 200
    return jsonify({"error": "Failed to load master data"}), 500

def get_symbol_list():
    if combined_database.empty:
        return jsonify({"error": "Master data not loaded"}), 400

    try:
        symbols = combined_database.dropna(subset=["pSymbolName", "pTrdSymbol"])
        symbols = symbols.drop_duplicates(subset=["pTrdSymbol"])
        symbol_list = [
            {
                "name": row["pSymbolName"].strip().upper(),
                "symbol": row["pTrdSymbol"].strip().upper()
            }
            for _, row in symbols.iterrows()
        ]
        return jsonify({"symbols": symbol_list}), 200
    except Exception as e:
        return jsonify({"error": "Failed to extract symbols", "details": str(e)}), 500
