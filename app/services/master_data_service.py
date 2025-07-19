import pandas as pd
import urllib.request
from io import StringIO
from app.utils.logger import logger
from app.utils import shared_state
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_master_data():
    logger.info(f"[LOAD DATA] Starting threaded load from {len(shared_state.file_paths)} files")
    print("in load_master_data file_paths: ", shared_state.file_paths)

    def process_file(seg, file_path):
        try:
            logger.info(f"[THREAD] Loading: {file_path}")
            with urllib.request.urlopen(file_path) as response:
                content = response.read().decode("utf-8")
                df = pd.read_csv(StringIO(content))

                # Clean column names
                df.columns = df.columns.str.strip().str.replace(";", "", regex=False)
                print(f"[DEBUG] {seg} loaded with shape: {df.shape}")
                return seg, df

        except Exception as e:
            logger.error(f"[FAILED TO LOAD] {file_path} — Error: {e}")
            return seg, None

    # Run file loads in threads
    with ThreadPoolExecutor(max_workers=min(5, len(shared_state.file_paths))) as executor:
        futures = [
            executor.submit(process_file, seg, url)
            for seg, url in shared_state.file_paths
        ]
        for future in as_completed(futures):
            seg, df = future.result()
            if df is not None:
                if seg == "bse_cm":
                    shared_state.bse_cm_database = df
                elif seg == "cde_fo":
                    shared_state.cde_fo_database = df
                elif seg == "mcx_fo":
                    shared_state.mcx_fo_database = df
                elif seg == "nse_cm":
                    shared_state.nse_cm_database = df
                elif seg == "nse_fo":
                    shared_state.nse_fo_database = df

    all_loaded = all([
        shared_state.bse_cm_database is not None and not shared_state.bse_cm_database.empty,
        shared_state.cde_fo_database is not None and not shared_state.cde_fo_database.empty,
        shared_state.mcx_fo_database is not None and not shared_state.mcx_fo_database.empty,
        shared_state.nse_cm_database is not None and not shared_state.nse_cm_database.empty,
        shared_state.nse_fo_database is not None and not shared_state.nse_fo_database.empty,
    ])


    if all_loaded:
        logger.info(f"[LOAD COMPLETE] All segment databases successfully loaded.")
        return True
    else:
        logger.warning("[NO DATA] One or more segment databases not loaded.")
        return False
