import akshare as ak
import pandas as pd

try:
    print("Fetching 30m data for 600519...")
    df = ak.stock_zh_a_hist_min_em(symbol="600519", period="30", adjust="qfq")
    print(df.head())
    print(df.columns)
except Exception as e:
    print(f"Error: {e}")
