import akshare as ak
import pandas as pd

symbol = "588200"

print(f"Testing daily data for {symbol}...")
try:
    df_daily = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
    print(f"Daily data shape: {df_daily.shape if df_daily is not None else 'None'}")
    if df_daily is not None and not df_daily.empty:
        print(df_daily.tail())
except Exception as e:
    print(f"Daily data failed: {e}")

print(f"\nTesting minute data (30) for {symbol}...")
try:
    df_min = ak.stock_zh_a_hist_min_em(symbol=symbol, period="30", adjust="qfq")
    print(f"Minute data shape: {df_min.shape if df_min is not None else 'None'}")
    if df_min is not None and not df_min.empty:
        print(df_min.tail())
except Exception as e:
    print(f"Minute data failed: {e}")

print(f"\nTesting ETF daily data for {symbol}...")
try:
    df_etf = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq")
    print(f"ETF Daily data shape: {df_etf.shape if df_etf is not None else 'None'}")
    if df_etf is not None and not df_etf.empty:
        print(df_etf.tail())
except Exception as e:
    print(f"ETF Daily data failed: {e}")
