import akshare as ak
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fetch(symbol, period, type="stock"):
    logger.info(f"Testing fetch for {symbol} ({type}), period={period}")
    try:
        start_time = time.time()
        if type == "etf":
            if period in ["30", "60"]:
                df = ak.fund_etf_hist_min_em(symbol=symbol, period=period, adjust="qfq")
            else:
                df = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq")
        else:
            if period in ["30", "60"]:
                df = ak.stock_zh_a_hist_min_em(symbol=symbol, period=period, adjust="qfq")
            else:
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        
        duration = time.time() - start_time
        if df is not None and not df.empty:
            logger.info(f"Success! Fetched {len(df)} rows in {duration:.2f}s")
            print(df.tail())
        else:
            logger.warning("Fetched empty data")
    except Exception as e:
        logger.error(f"Failed: {e}")

if __name__ == "__main__":
    print("Testing Stock 600519 (Moutai)...")
    test_fetch("600519", "30", "stock")
    
    print("\nWaiting 5 seconds...")
    time.sleep(5)
    
    print("\nTesting ETF 588200...")
    test_fetch("588200", "30", "etf")
