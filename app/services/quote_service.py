from flask import jsonify, request
import app.utils.shared_state as shared_state
import time
import re
import pandas as pd
from app.utils.socket_events import on_message_live_option_chain_data,on_error,on_open,on_close

def get_tokens_for_quotes(symbol, segment, strike_price):
    db_map = {
        "nse_fo": shared_state.nse_fo_database,
        "cde_fo": shared_state.cde_fo_database,
        "mcx_fo": shared_state.mcx_fo_database,
        "nse_cm": shared_state.nse_cm_database,
        "bse_cm": shared_state.bse_cm_database,
    }

    df = db_map.get(segment.lower())
    if df is None or df.empty:
        return [], pd.DataFrame(), []

    symbol = symbol.strip().upper()
    df = df.dropna(subset=["pTrdSymbol", "pSymbolName", "dStrikePrice", "pInstType"]).copy()

    # 🔸 Only Options
    df = df[df["pInstType"].isin(["OPTIDX", "OPTSTK"])]

    # 🔸 Match trade symbol like BANKNIFTYxxxx
    pattern = f"^{re.escape(symbol)}\\d+"
    df = df[df["pTrdSymbol"].str.upper().str.match(pattern)]

    # 🔸 Ensure numeric strike
    df["dStrikePrice"] = pd.to_numeric(df["dStrikePrice"], errors="coerce") / 100
    df = df.dropna(subset=["dStrikePrice"])

    # 🔸 Sort and select ±25 strikes
    df_sorted = df.sort_values(by="dStrikePrice")
    lower_df = df_sorted[df_sorted["dStrikePrice"] < strike_price].tail(25)
    upper_df = df_sorted[df_sorted["dStrikePrice"] >= strike_price].head(25)
    selected_df = pd.concat([lower_df, upper_df])

    tokens = []
    metaData = []  # ✅ Initialize before using

    for _, row in selected_df.iterrows():
        tokens.append({
            "instrument_token": str(row.get("pSymbol", "")),
            "exchange_segment": str(row.get("pExchSeg", "")).lower()
        })

        metaData.append({
            "strikePrice": row.get("dStrikePrice", 0),
            "optionType": row.get("pOptionType", ""),
            "expiry": row.get("lExpiryDate", ""),
            "tradingSymbol": row.get("pTrdSymbol", ""),
            "symbolName": row.get("pSymbolName", ""),
            "exchangeSegment": row.get("pExchSeg", "").lower(),
            "lotSize": row.get("iLotSize", row.get("lLotSize", 0)),
            "openInterest": row.get("dOpenInterest", 0),
            "instrumentType": row.get("pInstType", "")
        })

    return tokens, selected_df, metaData



def get_and_clear_quotes():
    # Return and reset the shared quotes safely
    data = shared_state.socketData.get("data")
    shared_state.socketData["data"] = None
    return {"data": data}


def get_quotes_data(req):
    try:
        data = req.get_json()
        mobile = data.get("mobileNumber")
        symbol = data.get("symbol")
        strike_price = float(data.get("strikePrice", 0))
        segment = data.get("segment", "").lower()

        if not mobile or not symbol or segment not in ["nse_fo", "cde_fo", "mcx_fo", "nse_cm", "bse_cm"]:
            return jsonify({"error": "Missing or invalid input"}), 400

        user_data = shared_state.clients.get(mobile)
        if not user_data:
            return jsonify({"error": "User not logged in"}), 401

        tokens, selected_df,metaData = get_tokens_for_quotes(symbol, segment, strike_price)
        if not tokens:
            return jsonify({"error": "Symbol not found", "tokens": []}), 404

        user_client = user_data["client"]
        user_client.quotes(
            instrument_tokens=tokens,
            quote_type="",
            isIndex=False,
            session_token=user_data["token"],
            sid=user_data["sid"],
            server_id="server1"
        )
        print("tokens are: ",tokens)
        user_client.subscribe(instrument_tokens=tokens, isIndex=False, isDepth=False)
        user_client.on_message = on_message_live_option_chain_data  # called when message is received from websocket
        user_client.on_error = on_error  # called when any error or exception occurs in code or websocket
        user_client.on_close = on_close  # called when websocket connection is closed
        user_client.on_open = on_open  # called when websocket successfully connects

        # timeout, interval, elapsed = 6, 0.05, 0
        # while elapsed < timeout:
        #     current_data = get_and_clear_quotes()
        #     if current_data["data"]:
        #         return jsonify({
        #             "type": "quotes",
        #             "data": current_data["data"],
        #            "metaData": metaData,
        #         })
        #     time.sleep(interval)
        #     elapsed += interval

        # If timeout
        return jsonify({
            "error": "Quotes response timed out",
            "tokens": tokens,
            "metaData": metaData,
           
        }), 504

    except Exception as e:
        return jsonify({
            "error": str(e),
            "metaData": metaData,
            "tokens": tokens if 'tokens' in locals() else []
        }), 500


def subscribe_live_tokens(req):
    try:
        tokens = req.json.get("tokens")
        mobile = req.json.get("mobile")

        if not tokens or not mobile:
            return jsonify({"error": "Missing fields"}), 400

        user_data = shared_state.clients.get(mobile)
        if not user_data:
            return jsonify({"error": "User not logged in"}), 401

        user_data["client"].subscribe(instrument_tokens=tokens)

        timeout, interval, elapsed = 5, 0.05, 0
        while elapsed < timeout:
            if shared_state.socketData.get("data"):
                break
            time.sleep(interval)
            elapsed += interval

        return jsonify({
            "status": "Subscribed",
            "initialData": shared_state.socketData.get("data")
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
