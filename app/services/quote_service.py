from flask import jsonify, request
import app.utils.shared_state as shared_state
import time
import pandas as pd
from app.utils.socket_events import on_message_live_option_chain_data, on_main_index_message,on_error, on_open, on_close
from app.utils.logger import logger


def get_tokens_for_quotes(symbol, expiry, segment, strike_price):
    logger.debug(f"Fetching tokens for symbol={symbol}, expiry={expiry}, segment={segment}, strike_price={strike_price}")
    
    db_map = {
        "nse_fo": shared_state.nse_fo_database,
        "cde_fo": shared_state.cde_fo_database,
        "mcx_fo": shared_state.mcx_fo_database,
        "nse_cm": shared_state.nse_cm_database,
        "bse_cm": shared_state.bse_cm_database,
    }

    df = db_map.get(segment.lower())
    if df is None or df.empty:
        logger.warning(f"No data found for segment: {segment}")
        return [], pd.DataFrame(), []

    symbol = symbol.strip().upper()
    try:
        expiry = int(expiry)
    except Exception:
        logger.warning(f"Invalid expiry format: {expiry}")
        return [], pd.DataFrame(), []

    df = df.dropna(subset=["pTrdSymbol", "pSymbolName", "dStrikePrice", "pInstType"]).copy()
    df = df[df["pInstType"].isin(["OPTIDX", "OPTSTK"])]
    df = df[df["pSymbolName"].str.upper() == symbol]
    df = df[df["lExpiryDate"].astype(str) == str(expiry)]

    df["dStrikePrice"] = pd.to_numeric(df["dStrikePrice"], errors="coerce") / 100
    df = df.dropna(subset=["dStrikePrice"])

    df_sorted = df.sort_values(by="dStrikePrice")
    lower_df = df_sorted[df_sorted["dStrikePrice"] < strike_price].tail(25)
    upper_df = df_sorted[df_sorted["dStrikePrice"] >= strike_price].head(25)
    selected_df = pd.concat([lower_df, upper_df])

    logger.debug(f"Selected {len(selected_df)} option contracts near strike price.")

    tokens = []
    metaData = []

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
    data = shared_state.socketData.get("data")
    shared_state.socketData["data"] = None
    return {"data": data}



def get_quotes_data(req):
    try:
        data = req.get_json()
        mobile = data.get("mobileNumber")
        symbol = data.get("symbol")
        expiry = data.get("expiry")
        strike_price = float(data.get("strikePrice", 0))
        segment = data.get("segment", "").lower()

        logger.info(f"Quote request received | mobile={mobile} | symbol={symbol} | expiry={expiry} | segment={segment}")

        if not mobile or not symbol or not expiry or segment not in ["nse_fo", "cde_fo", "mcx_fo", "nse_cm", "bse_cm"]:
            logger.warning("Missing or invalid input in quote request")
            return jsonify({"error": "Missing or invalid input"}), 400

        user_data = shared_state.clients.get(mobile)
        if not user_data:
            logger.warning(f"User not logged in: {mobile}")
            return jsonify({"error": "User not logged in"}), 401

        tokens, selected_df, metaData = get_tokens_for_quotes(symbol, expiry, segment, strike_price)
        if not tokens:
            logger.warning(f"No tokens found for symbol={symbol} | expiry={expiry}")
            return jsonify({"error": "Symbol not found", "tokens": []}), 404

        user_client = user_data["client"]
        # user_client.quotes(
        #     instrument_tokens=tokens,
        #     quote_type="",
        #     isIndex=False,
        #     session_token=user_data["token"],
        #     sid=user_data["sid"],
        #     server_id="server1"
        # )

        logger.info(f"Quotes requested from server for {len(tokens)} tokens")
        logger.debug(f"Tokens: {tokens}")

        user_client.subscribe(instrument_tokens=tokens, isIndex=False, isDepth=False)
        # Initialize nested dict if not present
        if mobile not in shared_state.subscribed_tokens:
            shared_state.subscribed_tokens[mobile] = {}
        if "optionsToken" not in shared_state.subscribed_tokens[mobile]:
            shared_state.subscribed_tokens[mobile]["optionsToken"] = []
        for token in tokens:
            if token not in shared_state.subscribed_tokens[mobile]["optionsToken"]:
                shared_state.subscribed_tokens[mobile]["optionsToken"].append(token)
    
        user_client.on_message = lambda message: on_message_live_option_chain_data(message, mobile)
        user_client.on_error = on_error
        user_client.on_close = on_close
        user_client.on_open = on_open

        logger.debug("WebSocket event handlers set")

        return jsonify({
            "message": "Quotes subscription initiated",
            "tokens": tokens,
            "metaData": metaData,
        }), 200

    except Exception as e:
        logger.error(f"Exception in get_quotes_data: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "metaData": metaData if 'metaData' in locals() else [],
            "tokens": tokens if 'tokens' in locals() else []
        }), 500


def subscribe_live_tokens(req):
    try:
        tokens = req.json.get("tokens")
        mobile = req.json.get("mobile")

        logger.info(f"Subscribe request | mobile={mobile} | token count={len(tokens) if tokens else 0}")

        if not tokens or not mobile:
            logger.warning("Missing fields in subscription request")
            return jsonify({"error": "Missing fields"}), 400

        user_data = shared_state.clients.get(mobile)
        if not user_data:
            logger.warning(f"User not logged in: {mobile}")
            return jsonify({"error": "User not logged in"}), 401

        user_data["client"].subscribe(instrument_tokens=tokens)
        logger.debug(f"Subscribed to tokens for user {mobile}")

        timeout, interval, elapsed = 5, 0.05, 0
        while elapsed < timeout:
            if shared_state.socketData.get("data"):
                logger.debug("Initial socket data received")
                break
            time.sleep(interval)
            elapsed += interval

        return jsonify({
            "status": "Subscribed",
            "initialData": shared_state.socketData.get("data")
        }), 200

    except Exception as e:
        logger.error(f"Error during subscription: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500



def get_main_indices(req):
    try:
        data = req.get_json()
        mobile = data.get("mobile") or req.args.get("mobile")

        logger.info(f"get_main_indices request | mobile={mobile}")
        user_data = shared_state.clients.get(mobile)
        if  not mobile or not user_data:
            logger.warning("Missing fields in subscription request")
            return jsonify({"error": "Missing fields"}), 400

        if not user_data:
            logger.warning(f"User not logged in: {mobile}")
            return jsonify({"error": "User not logged in"}), 401

        client = user_data["client"]

        # Predefined index tokens (example: NSE_FO index tokens)
        inst_tokens = [{"instrument_token": "11536", "exchange_segment": "nse_cm"},
                        {"instrument_token": "26000", "exchange_segment": "nse_cm"},
                        {"instrument_token": "26009", "exchange_segment": "nse_cm"},
                        {"instrument_token": "26037", "exchange_segment": "nse_cm"},
                        {"instrument_token": "26074", "exchange_segment": "nse_cm"}
                        ]
        response = client.subscribe(instrument_tokens=inst_tokens, isIndex=False, isDepth=False)
        client.on_message = on_main_index_message
        client.on_error = on_error
        client.on_close = on_close
        client.on_open = on_open

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error fetching main indices: {str(e)}")
        return jsonify({"error": "Failed to fetch indices", "details": str(e)}), 500
