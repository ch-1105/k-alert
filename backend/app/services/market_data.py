import akshare as ak
import pandas as pd
from datetime import datetime
from loguru import logger

class MarketDataService:
    @staticmethod
    def get_real_time_price(stock_code: str, stock_type: str = "stock"):
        """
        Get real-time price for a stock.
        Optimized to fetch only specific stock data.
        """
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching real-time price for {stock_code} (Attempt {attempt + 1})")
                
                # Use minute data as a proxy for real-time if spot is too heavy
                df = None
                
                if stock_type == "etf":
                    try:
                        df = ak.fund_etf_hist_min_em(symbol=stock_code, period='1', adjust='qfq')
                    except:
                        pass
                else:
                    try:
                        df = ak.stock_zh_a_hist_min_em(symbol=stock_code, period='1', adjust='qfq')
                    except:
                        pass
                
                if df is None or df.empty:
                    logger.warning(f"No data found for {stock_code}")
                    return None
                    
                # Get the latest record
                latest = df.iloc[-1]
                price = float(latest['close'])
                
                name = stock_code # Default
                # Try to get name (optional)
                try:
                    if stock_type == "stock":
                        info_df = ak.stock_individual_info_em(symbol=stock_code)
                        name_row = info_df[info_df['item'] == "股票简称"]
                        if not name_row.empty:
                            name = name_row.iloc[0]['value']
                except:
                    pass

                logger.debug(f"Got price for {stock_code}: {price}")
                return {
                    "code": stock_code,
                    "name": name,
                    "price": price,
                    "change_percent": 0.0, 
                    "timestamp": datetime.now()
                }
            except Exception as e:
                logger.error(f"Error fetching data for {stock_code}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None

    @staticmethod
    def get_history_data(stock_code: str, period: str = "daily", stock_type: str = "stock"):
        """
        Get history data for indicator calculation.
        Period: daily, weekly, monthly, 30, 60
        Stock Type: stock, etf
        """
        try:
            logger.info(f"Fetching history for {stock_code} ({stock_type}), period: {period}")
            df = None
            
            # SIMPLIFIED LOGIC: Try standard stock API first, then ETF if it fails or if requested
            # This mimics the "old" behavior where we might have just tried one.
            
            if stock_type == "etf":
                try:
                    if period in ["daily", "weekly", "monthly"]:
                        df = ak.fund_etf_hist_em(symbol=stock_code, period=period, adjust="qfq")
                    else:
                        df = ak.fund_etf_hist_min_em(symbol=stock_code, period=period, adjust="qfq")
                except Exception as e:
                    logger.warning(f"ETF fetch failed for {stock_code}: {e}")
            
            if df is None or df.empty:
                # Fallback or Primary for Stock
                if period in ["daily", "weekly", "monthly"]:
                    df = ak.stock_zh_a_hist(symbol=stock_code, period=period, adjust="qfq")
                else:
                    # Ensure period is string '30', '60'
                    df = ak.stock_zh_a_hist_min_em(symbol=stock_code, period=str(period), adjust="qfq")

            return df
        except Exception as e:
            logger.error(f"Error fetching history for {stock_code}: {e}")
            return None
