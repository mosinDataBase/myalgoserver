# app/utils/expiry_utils.py

import pandas as pd
from app.utils import shared_state


def get_unique_expiries(symbol: str, segment: str) -> list:
    db_map = {
        "nse_fo": shared_state.nse_fo_database,
        "cde_fo": shared_state.cde_fo_database,
        "mcx_fo": shared_state.mcx_fo_database,
        "nse_cm": shared_state.nse_cm_database,
        "bse_cm": shared_state.bse_cm_database,
    }

    df = db_map.get(segment.lower())
    if df is None or df.empty:
        return []

    symbol = symbol.strip().upper()

    # ✅ Ensure required columns exist
    if "pSymbolName" not in df.columns or "lExpiryDate" not in df.columns:
        return []

    # ✅ Filter by symbol
    df_filtered = df[df["pSymbolName"].str.upper() == symbol]

    # ✅ Drop missing expiry values and get unique list
    expiries = df_filtered["lExpiryDate"].dropna().unique().tolist()

    # ✅ Optionally sort (if values are strings like '25/07/2024', or datetime)
    try:
        expiries = sorted(expiries, key=lambda x: pd.to_datetime(x, dayfirst=True))
    except Exception:
        expiries = sorted(expiries)

    return expiries
