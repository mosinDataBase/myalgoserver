
import eventlet
eventlet.monkey_patch()

from io import StringIO
from flask_socketio import SocketIO, emit
import urllib.request
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from pprint import pprint
from dotenv import load_dotenv
import os
from neo_api_client import NeoAPI
import pandas as pd
from datetime import datetime, timezone, timedelta
import numpy as np
import time

# python serverapp.py
app = Flask(__name__)
CORS(app)
load_dotenv()
socketio = SocketIO(app, cors_allowed_origins="*")


clients = {}
dfs = []
file_paths = []
combined_database = None
socketData = {"data": None}


def on_message(message):

    global socketData
    socketData["data"] = message
    print('[Res]: ', message)
    socketio.emit("live_data", message)


def on_error(message):
    print('[OnError]: ', message)


def get_and_clear_quotes():
    global socketData
    data = socketData["data"]
    socketData["data"] = None  # Clear after read
    return {"data": data}


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        mobile = data.get("mobileNumber")
        password = data.get("password")
        ucc = data.get("ucc")

        consumerKey = data.get("consumerKey")
        consumerSecret = data.get("consumerSecret")

        if not mobile or not password:
            return jsonify({"error": "Missing mobile number or password"}), 400
        if not consumerKey or not consumerSecret:
            return jsonify({"status": "error", "message": "Missing consumer key or secret"}), 400

        if mobile and password and consumerKey and consumerSecret:
            client = NeoAPI(
                consumer_key=consumerKey,
                consumer_secret=consumerSecret,
                environment='prod',
            )
            print("Client created successfully")
            clients[mobile] = client

            otp = client.login(mobilenumber=mobile, password=password)
            pprint(otp)
            if otp and "data" in otp and otp["data"].get("token"):
                return jsonify({
                    "status": "success",
                    "message": "Login successful",
                    "data": otp["data"]
                })
            else:
                # If OTP response indicates failure
                return jsonify({
                    "status": "fail",
                    "message": "Login failed or invalid response",
                    "details": otp
                }), 401

        else:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

    except Exception as e:
        # Log the exception (you can replace print with logging)
        print(f"Exception during login: {e}")
        return jsonify({"status": "error", "message": "An error occurred during login."}), 500


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    mobile = data.get("mobileNumber")
    otp = data.get("otp")

    if not mobile or not otp:
        return jsonify({"error": "Missing mobile number or OTP"}), 400

    client = clients.get(mobile)

    try:
        result = client.session_2fa(OTP=otp)
        data = result.get("data", {})
        print("OTP Verification Result:", result)
        if not data or "token" not in data:
            return jsonify({"status": "fail", "message": "OTP verification failed"}), 401

        client.on_message = on_message
        client.on_open = lambda ws: print("✅ WebSocket connected.")
        client.on_close = lambda ws: print("❌ WebSocket connection closed.")
        client.on_error = lambda ws, error: print("[OnError]:", error)

        token = result["data"]["token"]
        sid = result["data"]["sid"]
        clients[mobile] = {
            "client": client,
            "token": token,
            "sid": sid
        }

        segments = ["bse_cm", "cde_fo", "mcx_fo", "nse_cm", "nse_fo"]
        global file_paths
        file_paths.clear()
        global dfs
        dfs.clear()

        for seg in segments:
            path = client.scrip_master(seg)
            file_paths.append(path)

        print("File Paths:", file_paths)
        get_master_scrips()
        return jsonify(result), 200

    except Exception as e:
        print("❌ OTP verification failed:", e)

        return jsonify({"status": "fail", "message": "OTP verification failed"}), 401


@app.route('/masterScrips', methods=['GET'])
def get_master_scrips():
    global file_paths, dfs
    # Clear old data
    dfs.clear()

    # Use the first logged-in client (you can improve this later by session/mobile)

    required_columns = {"pSymbol", "pExchSeg",
                        "pTrdSymbol", "pSymbolName", "pInstType", "lLotSize", "lExpiryDate"}

    for file_path in file_paths:
        try:
            with urllib.request.urlopen(file_path) as response:
                content = response.read().decode("utf-8")
                df = pd.read_csv(StringIO(content))

                available = set(df.columns)
                selected = list(required_columns & available)

                if not selected:
                    continue

                selected_df = df[selected]
                seg = file_path.split("/")[-1].split(".")[0]

                # Handle expiry date format
                if "lExpiryDate" in selected_df.columns:
                    if seg in ["nse_fo", "cde_fo"]:
                        selected_df["lExpiryDate"] = pd.to_datetime(
                            selected_df["lExpiryDate"] + 315513000,
                            unit="s", errors="coerce"
                        )
                    else:
                        selected_df["lExpiryDate"] = pd.to_datetime(
                            selected_df["lExpiryDate"],
                            unit="s", errors="coerce"
                        )

                dfs.append(selected_df)
            global combined_database
            combined_database = pd.concat(dfs,   ignore_index=True)
        except Exception as e:
            print(f"❌ Failed to process : {e}")

    # Combine all data
    if not dfs:
        return jsonify({"error": "No valid data found"}), 500

    combined = pd.concat(dfs, ignore_index=True)
    return jsonify(combined.to_dict(orient="records")), 200


def get_tokens_for_quotes(security_identifier, combined_database):
    security_identifier = security_identifier.strip().upper()
    dff = combined_database.dropna(subset=['pTrdSymbol'])
    print("Security Identifier:", security_identifier)
    matched_rows = dff[
        dff['pTrdSymbol'].astype(str).str.strip(
        ).str.upper() == security_identifier
    ]
    # Match trading symbol
    if matched_rows.empty:
        matched_rows = dff[
            dff['pSymbolName'].astype(str).str.strip(
            ).str.upper() == security_identifier
        ]
    print("Matched Rows:", matched_rows)
    result = []
    for _, row in matched_rows.iterrows():
        result.append({
            "instrument_token": str(row.get("pSymbol", "")),
            "exchange_segment": str(row.get("pExchSeg", "")).lower()
        })
    print("Result:", result)
    return result


@app.route('/quotes', methods=['POST'])
def get_quotes():
    data = request.get_json()
    mobile = data.get("mobileNumber")
    symbol = data.get("symbol")  # single security identifier

    if not mobile or not symbol:
        return jsonify({"error": "Missing mobile number or symbol"}), 400

    user_data = clients.get(mobile)
    if not user_data:
        return jsonify({"error": "User not logged in"}), 401
    client = user_data["client"]
    token = user_data["token"]
    sid = user_data["sid"]
    if combined_database is None:
        return jsonify({"error": "Master data not loaded yet. Please verify OTP first."}), 400

    try:
        instrument_tokens = get_tokens_for_quotes(symbol, combined_database)
        print("Instrument Tokens:", instrument_tokens)
        if not instrument_tokens:
            return jsonify({"error": "Symbol not found in master database"}), 404

        quotes = client.quotes(
            instrument_tokens=instrument_tokens,
            quote_type="",            # or 'ltp', 'full', etc.
            isIndex=False,
            session_token=token,
            sid=sid,
            server_id="server1"
        )

        timeout = 6
        poll_interval = 0.05
        elapsed = 0
        quotesData = None

        while elapsed < timeout:
            current_data = get_and_clear_quotes()
            if current_data["data"]:  # Wait until populated
                quotesData = current_data
                break
            time.sleep(poll_interval)
            elapsed += poll_interval

        if not quotesData["data"]:
            return jsonify({"error": "Quotes response timed out"}), 504
        print("quotes are :", quotesData)
        return jsonify(
            {
                "type": "quotes",
                "data": quotesData["data"]

            }
        ), 200

    except Exception as e:
        print("❌ Error fetching quotes:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/symbols', methods=['GET'])
def get_all_symbols():
    global combined_database
    if combined_database is None:
        return jsonify({"error": "Master data not loaded yet. Please verify OTP first."}), 400

    try:

        symbols = combined_database.dropna(
            subset=["pSymbolName", "pTrdSymbol"])
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
        print("❌ Error fetching symbol list:", e)
        return jsonify({"error": "Failed to extract symbols", "details": str(e)}), 500


@app.route('/livedata', methods=['POST'])
def subscribe_tokens():

    # Frontend sends: [{"instrument_token": "11536", "exchange_segment": "nse_cm"}, ...]
    tokens = request.json.get("tokens")
    mobile = request.json.get("mobile")

    if not all([tokens, mobile]):
        return {"error": "Missing required fields"}, 400
    user_data = clients.get(mobile)
    if not user_data:
        return jsonify({"error": "User not logged in"}), 401
    # Start live subscription
    try:
        client = user_data["client"]
        client.subscribe(instrument_tokens=tokens)

          # Wait briefly for the first socket push
        timeout = 5
        poll_interval = 0.05
        elapsed = 0
        while elapsed < timeout:
            if socketData["data"]:  # WebSocket must populate this
                break
            time.sleep(poll_interval)
            elapsed += poll_interval

    except Exception as e:
        return {"error": str(e)}, 500
    return {"status": "Subscribed", "initialData": socketData["data"]}, 200


if __name__ == '__main__':
    print("Starting server...")
    socketio.run(app, host="0.0.0.0", port=10000, debug=True)


