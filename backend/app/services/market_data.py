import akshare as ak
import pandas as pd
from datetime import datetime
from loguru import logger
import time
from functools import wraps
from http.client import RemoteDisconnected
from requests.exceptions import ConnectionError, Timeout
from app.services.trading_hours import TradingHours, get_market_status

def retry_on_connection_error(max_retries=3, base_delay=3):
    """
    Decorator to retry function on connection errors with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will be multiplied for exponential backoff)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, RemoteDisconnected, Timeout, Exception) as e:
                    # Only retry on connection-related errors
                    error_type = type(e).__name__
                    is_connection_error = any([
                        isinstance(e, (ConnectionError, RemoteDisconnected, Timeout)),
                        'Connection' in str(e),
                        'Remote end closed' in str(e),
                        'timed out' in str(e).lower()
                    ])
                    
                    if not is_connection_error or retries >= max_retries - 1:
                        # Not a connection error or out of retries
                        raise
                    
                    retries += 1
                    delay = base_delay * (2 ** (retries - 1))  # Exponential backoff: 3s, 6s, 12s
                    logger.warning(
                        f"Connection error in {func.__name__}: {error_type}: {str(e)[:100]}. "
                        f"Retrying {retries}/{max_retries} in {delay}s..."
                    )
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            raise Exception(f"Failed after {max_retries} retries")
        
        return wrapper
    return decorator

class MarketDataService:
    @staticmethod
    def _get_stock_with_prefix(stock_code: str) -> str:
        """
        Add prefix to stock code for Sina API (sh/sz).
        """
        if stock_code.startswith(('6', '5', '9')):
            return f"sh{stock_code}"
        elif stock_code.startswith(('0', '3', '1')):
            return f"sz{stock_code}"
        elif stock_code.startswith(('4', '8')):
            return f"bj{stock_code}"
        return stock_code

    @staticmethod
    @retry_on_connection_error(max_retries=3, base_delay=3)
    def get_real_time_price(stock_code: str, stock_type: str = "stock"):
        """
        Get real-time price for a stock.
        Optimized to fetch only specific stock data.
        Uses retry decorator to handle connection errors.
        Skips API calls entirely during non-trading hours.
        """
        # Check trading hours - skip API call if market is closed
        is_trading = TradingHours.is_trading_time()
        
        if not is_trading:
            market_status = get_market_status()
            logger.info(
                f"Skipping real-time API call for {stock_code}. "
                f"Market is currently {market_status}. "
                f"Real-time data is only available during trading hours."
            )
            return None
        
        # Market is open, proceed with API call
        logger.info(f"Fetching real-time price for {stock_code} (Market: {get_market_status()})")
        
        symbol = MarketDataService._get_stock_with_prefix(stock_code)
        df = None
        
        try:
            # Use minute data (period='1') to get latest price
            df = ak.stock_zh_a_minute(symbol=symbol, period='1')
        except Exception as e:
            logger.warning(f"Real-time fetch failed for {symbol}: {e}")
            pass
        
        if df is None or df.empty:
            logger.warning(f"No data found for {stock_code} despite market being open")
            return None
            
        # Get the latest record
        # Columns: day, open, high, low, close, volume
        latest = df.iloc[-1]
        price = float(latest['close'])
        
        name = stock_code # Default
        # Try to get name (optional) - keeping old method for now or could use new API if available
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

    @staticmethod
    @retry_on_connection_error(max_retries=3, base_delay=3)
    def get_history_data(stock_code: str, period: str = "daily", stock_type: str = "stock"):
        """
        Get history data for indicator calculation.
        Period: daily, weekly, monthly, 1, 5, 15, 30, 60
        Stock Type: stock, etf
        Uses retry decorator to handle connection errors.
        Note: Historical data is available regardless of trading hours.
        """
        logger.info(f"Fetching history for {stock_code} ({stock_type}), period: {period}")
        symbol = MarketDataService._get_stock_with_prefix(stock_code)
        df = None
        
        try:
            if period in ["daily", "weekly", "monthly"]:
                # For daily data, use stock_zh_a_daily
                try:
                    df = ak.stock_zh_a_daily(symbol=symbol)
                except Exception as e:
                    # Fallback for ETFs if Sina API fails
                    if stock_type == "etf":
                        # logger.warning(f"Sina API failed for ETF {stock_code}, trying EastMoney fallback: {e}")
                        try:
                            df = ak.fund_etf_hist_em(symbol=stock_code, period=period, adjust="qfq")
                        except Exception as e2:
                            logger.error(f"EastMoney fallback also failed for {stock_code}: {e2}")
                            raise e
                    else:
                        raise e

            elif str(period) in ["1", "5", "15", "30", "60"]:
                # For minute data: 1, 5, 15, 30, 60
                # Ensure period is string
                df = ak.stock_zh_a_minute(symbol=symbol, period=str(period))
            else:
                logger.error(f"Unsupported period: {period} for {stock_code}. Supported: daily, weekly, monthly, 1, 5, 15, 30, 60")
                return None
                
            if df is not None and not df.empty:
                logger.info(f"Successfully fetched {len(df)} rows for {stock_code}")
            else:
                logger.warning(f"No data returned for {stock_code}")
                
            return df
            
        except Exception as e:
            logger.error(f"Error fetching history for {stock_code}: {e}")
            return None
