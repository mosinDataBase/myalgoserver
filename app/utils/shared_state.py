import pandas as pd

clients = {}
subscribed_tokens ={}
dfs = []
file_paths = []
combined_database = pd.DataFrame()
socketData = {"data": None}

# Initialize segment-specific databases as empty DataFrames
bse_cm_database = pd.DataFrame()
cde_fo_database = pd.DataFrame()
mcx_fo_database = pd.DataFrame()
nse_cm_database = pd.DataFrame()
nse_fo_database = pd.DataFrame()
