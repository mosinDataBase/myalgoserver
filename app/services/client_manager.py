import logging
from neo_api_client import NeoAPI
from app.utils.shared_state import clients, file_paths, dfs, combined_database
from app.utils.socket_events import on_message
import pandas as pd
from io import StringIO
import urllib.request

# ✅ Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def create_client(mobile, password, consumer_key, consumer_secret):
    logger.info(f"[CREATE CLIENT] Creating client for mobile: {mobile}")
    client = NeoAPI(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        environment='prod',
    )
    clients[mobile] = client
    logger.info(f"[CLIENT STORED] Client created and stored for {mobile}")
    return client

def verify_otp_and_prepare_data(mobile, otp):
    logger.info(f"[VERIFY OTP] Verifying OTP for: {mobile}")
    user_entry = clients.get(mobile)

    if isinstance(user_entry, dict):
        client = user_entry.get("client")
    else:
        client = user_entry

    if not client:
        logger.error(f"[ERROR] No client found for mobile {mobile}")
        raise Exception("Client not found for mobile number.")

    result = client.session_2fa(OTP=otp)
    data = result.get("data", {})

    if not data or "token" not in data:
        logger.error(f"[OTP FAIL] OTP verification failed for {mobile}")
        raise Exception("OTP verification failed")

    logger.info(f"[OTP SUCCESS] Token received for {mobile}")

    # Set socket handlers
    client.on_message = on_message
    client.on_open = lambda ws: logger.info(f"[WS OPEN] WebSocket connected for {mobile}")
    client.on_close = lambda ws: logger.warning(f"[WS CLOSED] WebSocket connection closed for {mobile}")
    client.on_error = lambda ws, error: logger.error(f"[WS ERROR] Error: {error}")

    clients[mobile] = {
        "client": client,
        "token": data["token"],
        "sid": data["sid"]
    }

    segments = ["bse_cm", "cde_fo", "mcx_fo", "nse_cm", "nse_fo"]
    file_paths.clear()
    dfs.clear()

    logger.info(f"[SCRIP LOAD] Starting to fetch scrip masters for: {segments}")

    for seg in segments:
        try:
            path = client.scrip_master(seg)
            file_paths.append(path)
            logger.info(f"[SCRIP FETCHED] Segment: {seg}, URL: {path}")
        except Exception as e:
            logger.error(f"[SCRIP FAIL] Segment: {seg}, Error: {e}")

    success = load_master_data()
    logger.info(f"[MASTER DATA] Loaded: {success}")
    return result

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import urllib.request
import pandas as pd

def load_master_data():
    global combined_database
    required_columns = {"pSymbol", "pExchSeg", "pTrdSymbol", "pSymbolName", "pInstType", "lLotSize", "lExpiryDate"}
    dfs.clear()

    logger.info(f"[LOAD DATA] Starting threaded load from {len(file_paths)} files")

    def process_file(file_path):
        try:
            logger.info(f"[THREAD] Loading: {file_path}")
            with urllib.request.urlopen(file_path) as response:
                content = response.read().decode("utf-8")
                df = pd.read_csv(StringIO(content))

                available = set(df.columns)
                selected = list(required_columns & available)
                if not selected:
                    logger.warning(f"[SKIPPED] No required columns in: {file_path}")
                    return None

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

                logger.info(f"[THREAD DONE] {seg} rows: {len(selected_df)}")
                return selected_df

        except Exception as e:
            logger.error(f"[FAILED TO LOAD] {file_path} — Error: {e}")
            return None

    with ThreadPoolExecutor(max_workers=min(5, len(file_paths))) as executor:
        futures = [executor.submit(process_file, fp) for fp in file_paths]
        for future in as_completed(futures):
            df = future.result()
            if df is not None:
                dfs.append(df)

    if dfs:
        combined_database = pd.concat(dfs, ignore_index=True)
        logger.info(f"[COMBINED DB] Total rows: {len(combined_database)}")
        return True

    logger.warning("[NO DATA] No valid dataframes created.")
    return False

