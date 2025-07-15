from flask import jsonify, request
from app.utils.shared_state import clients, combined_database, socketData
from app.services.client_manager import load_master_data
import time

def get_tokens_for_quotes(symbol, combined_db):
    symbol = symbol.strip().upper()
    df = combined_db.dropna(subset=['pTrdSymbol'])
    matched_rows = df[df['pTrdSymbol'].str.strip().str.upper() == symbol]

    if matched_rows.empty:
        matched_rows = df[df['pSymbolName'].str.strip().str.upper() == symbol]

    result = []
    for _, row in matched_rows.iterrows():
        result.append({
            "instrument_token": str(row.get("pSymbol", "")),
            "exchange_segment": str(row.get("pExchSeg", "")).lower()
        })
    return result

def get_and_clear_quotes():
    data = socketData["data"]
    socketData["data"] = None
    return {"data": data}

def get_quotes_data(req):
    data = req.get_json()
    mobile = data.get("mobileNumber")
    symbol = data.get("symbol")

    if not mobile or not symbol:
        return jsonify({"error": "Missing mobile number or symbol"}), 400

    user_data = clients.get(mobile)
    if not user_data:
        return jsonify({"error": "User not logged in"}), 401

    if combined_database.empty:
        return jsonify({"error": "Master data not loaded"}), 400

    try:
        tokens = get_tokens_for_quotes(symbol, combined_database)
        if not tokens:
            return jsonify({"error": "Symbol not found"}), 404

        user_client = user_data["client"]
        token = user_data["token"]
        sid = user_data["sid"]

        user_client.quotes(
            instrument_tokens=tokens,
            quote_type="",
            isIndex=False,
            session_token=token,
            sid=sid,
            server_id="server1"
        )

        timeout, interval, elapsed = 6, 0.05, 0
        while elapsed < timeout:
            current_data = get_and_clear_quotes()
            if current_data["data"]:
                return jsonify({"type": "quotes", "data": current_data["data"]})
            time.sleep(interval)
            elapsed += interval

        return jsonify({"error": "Quotes response timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def subscribe_live_tokens(req):
    tokens = req.json.get("tokens")
    mobile = req.json.get("mobile")

    if not tokens or not mobile:
        return jsonify({"error": "Missing fields"}), 400

    user_data = clients.get(mobile)
    if not user_data:
        return jsonify({"error": "User not logged in"}), 401

    try:
        client = user_data["client"]
        client.subscribe(instrument_tokens=tokens)

        timeout, interval, elapsed = 5, 0.05, 0
        while elapsed < timeout:
            if socketData["data"]:
                break
            time.sleep(interval)
            elapsed += interval

        return jsonify({"status": "Subscribed", "initialData": socketData["data"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
