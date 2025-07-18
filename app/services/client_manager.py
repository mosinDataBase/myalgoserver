import logging
from neo_api_client import NeoAPI
from app.utils.shared_state import clients,file_paths, dfs, combined_database
from app.utils.socket_events import on_message
import pandas as pd
from io import StringIO
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


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
            file_paths.append((seg, path))  # store tuple: (segment_name, url)
            logger.info(f"[SCRIP FETCHED] Segment: {seg}, URL: {path}")
        except Exception as e:
            logger.error(f"[SCRIP FAIL] Segment: {seg}, Error: {e}")

    
    return result

# def load_master_data():
#     global bse_cm_database, cde_fo_database, mcx_fo_database, nse_cm_database, nse_fo_database
#     required_columns = {"pSymbol", "pExchSeg", "pTrdSymbol", "pSymbolName", "pDesc","pInstType", "lLotSize", "lExpiryDate"}

#     logger.info(f"[LOAD DATA] Starting threaded load from {len(file_paths)} files")
#     print("file_paths: ",file_paths);
#     def process_file(seg, file_path):
#         try:
#             logger.info(f"[THREAD] Loading: {file_path}")
#             with urllib.request.urlopen(file_path) as response:
#                 content = response.read().decode("utf-8")
#                 df = pd.read_csv(StringIO(content))

#                 available = set(df.columns)
#                 selected = list(required_columns & available)
#                 if not selected:
#                     logger.warning(f"[SKIPPED] No required columns in: {file_path}")
#                     return seg, None

#                 selected_df = df[selected]

#                 if "lExpiryDate" in selected_df.columns:
#                     if seg in ["nse_fo", "cde_fo"]:
#                         selected_df["lExpiryDate"] = pd.to_datetime(
#                             selected_df["lExpiryDate"] + 315513000,
#                             unit="s", errors="coerce"
#                         )
#                     else:
#                         selected_df["lExpiryDate"] = pd.to_datetime(
#                             selected_df["lExpiryDate"],
#                             unit="s", errors="coerce"
#                         )

#                 logger.info(f"[THREAD DONE] {seg} rows: {len(selected_df)}")
#                 return seg, selected_df

#         except Exception as e:
#             logger.error(f"[FAILED TO LOAD] {file_path} — Error: {e}")
#             return seg, None

#     with ThreadPoolExecutor(max_workers=min(5, len(file_paths))) as executor:
#         futures = [
#             executor.submit(process_file, seg, url)
#             for seg, url in file_paths
#         ]
#         for future in as_completed(futures):
#             seg, df = future.result()
#             if df is not None:
#                 if seg == "bse_cm":
#                     bse_cm_database = df
#                 elif seg == "cde_fo":
#                     cde_fo_database = df
#                 elif seg == "mcx_fo":
#                     mcx_fo_database = df
#                 elif seg == "nse_cm":
#                     nse_cm_database = df
#                 elif seg == "nse_fo":
#                     nse_fo_database = df

#     all_loaded = all([
#     bse_cm_database is not None and not bse_cm_database.empty,
#     cde_fo_database is not None and not cde_fo_database.empty,
#     mcx_fo_database is not None and not mcx_fo_database.empty,
#     nse_cm_database is not None and not nse_cm_database.empty,
#     nse_fo_database is not None and not nse_fo_database.empty,
#     ])


#     if all_loaded:
#         logger.info(f"[LOAD COMPLETE] At least one segment successfully loaded.")
#         return True
#     else:
#         logger.warning("[NO DATA] No segment databases created.")
#         return False


