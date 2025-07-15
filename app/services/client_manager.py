from neo_api_client import NeoAPI
from app.utils.shared_state import clients, file_paths, dfs, combined_database
from app.utils.socket_events import on_message
import pandas as pd
from io import StringIO
import urllib.request

def create_client(mobile, password, consumer_key, consumer_secret):
    client = NeoAPI(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        environment='prod',
    )
    clients[mobile] = client
    return client
def verify_otp_and_prepare_data(mobile, otp):
    user_entry = clients.get(mobile)

    # ✅ Fix: extract client from dict if wrapped
    if isinstance(user_entry, dict):
        client = user_entry.get("client")
    else:
        client = user_entry

    if not client:
        raise Exception("Client not found for mobile number.")

    result = client.session_2fa(OTP=otp)
    data = result.get("data", {})

    if not data or "token" not in data:
        raise Exception("OTP verification failed")

    # Set socket handlers
    client.on_message = on_message
    client.on_open = lambda ws: print("✅ WebSocket connected.")
    client.on_close = lambda ws: print("❌ WebSocket connection closed.")
    client.on_error = lambda ws, error: print("[OnError]:", error)

    # ✅ Wrap client in dict for future use
    clients[mobile] = {
        "client": client,
        "token": data["token"],
        "sid": data["sid"]
    }

    segments = ["bse_cm", "cde_fo", "mcx_fo", "nse_cm", "nse_fo"]
    file_paths.clear()
    dfs.clear()

    for seg in segments:
        path = client.scrip_master(seg)
        file_paths.append(path)

    _ = load_master_data()
    return result

def load_master_data():
    global combined_database  # ✅ important!

    required_columns = {"pSymbol", "pExchSeg", "pTrdSymbol", "pSymbolName", "pInstType", "lLotSize", "lExpiryDate"}
    dfs.clear()

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
        except Exception as e:
            print(f"Failed to process: {e}")

    if dfs:
        combined_database = pd.concat(dfs, ignore_index=True)  # ✅ correct replacement
        return True
    return False

