# requirements:
# pip install akshare pandas tenacity

import akshare as ak
import pandas as pd
import time
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

# ---- 配置 ----
REQUEST_SLEEP_SECONDS = 0.8   # 两次请求间隔，防止被限流（适当调大）
RETRIES = 3

# ---- 通用重试装饰器（网络/接口偶发错误） ----
@retry(wait=wait_fixed(1), stop=stop_after_attempt(RETRIES), retry=retry_if_exception_type(Exception))
def fetch_stock_minute(symbol: str, period: str = "30") -> pd.DataFrame:
    """
    获取单只沪深A股的分钟级分时/分钟K线（来自新浪/其他源，AkShare封装）。
    symbol 示例: 'sh600519' 或 'sz000001' 或指数 'sh000300' 等
    period: '1','5','15','30','60'
    返回: pandas.DataFrame（含 day, open, high, low, close, volume 等列）
    """
    # ak.stock_zh_a_minute 接口 (注意 symbol 格式与 period 值)。分钟数据通常只覆盖近期。
    df = ak.stock_zh_a_minute(symbol=symbol, period=period)
    # 简单标准化/检查
    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol} period={period}")
    return df

# ---- 测试 / 使用示例 ----
if __name__ == "__main__":
    # 示例1：拉取贵州茅台（600519）30分钟数据（注意使用 sh 或 sz 前缀）
    try:
        stock_symbol = "sh513500"   # 或 "sz000001"
        print(f"Fetching stock {stock_symbol} 30m...")
        stock_df = fetch_stock_minute(stock_symbol, period="30")
        print(stock_df.head())
        stock_df.to_csv(f"{stock_symbol}_30m.csv", index=False)
        time.sleep(REQUEST_SLEEP_SECONDS)
    except Exception as e:
        print("股票接口异常：", e)
