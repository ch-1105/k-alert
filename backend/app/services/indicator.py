import pandas as pd
import pandas_ta as ta

class IndicatorService:
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, length: int = 6) -> float:
        """
        Calculate RSI. Assumes df has 'close' or '收盘' column.
        """
        # AkShare dataframe usually has Chinese columns
        if '收盘' in df.columns:
            close = df['收盘']
        elif 'close' in df.columns:
            close = df['close']
        else:
            raise ValueError("DataFrame must contain 'close' or '收盘' column")
            
        # Ensure close is numeric
        close = pd.to_numeric(close, errors='coerce')
            
        rsi = ta.rsi(close, length=length)
        if rsi is None or rsi.empty:
            return None
        return float(rsi.iloc[-1])

    @staticmethod
    def calculate_rsi_series(df: pd.DataFrame, length: int = 6) -> pd.Series:
        """
        Calculate RSI and return the full Series.
        """
        if '收盘' in df.columns:
            close = df['收盘']
        elif 'close' in df.columns:
            close = df['close']
        else:
            raise ValueError("DataFrame must contain 'close' or '收盘' column")
            
        close = pd.to_numeric(close, errors='coerce')
        rsi = ta.rsi(close, length=length)
        return rsi

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
        if '收盘' in df.columns:
            close = df['收盘']
        elif 'close' in df.columns:
            close = df['close']
        else:
            raise ValueError("DataFrame must contain 'close' or '收盘' column")
        
        close = pd.to_numeric(close, errors='coerce')
            
        macd = ta.macd(close, fast=fast, slow=slow, signal=signal)
        if macd is None or macd.empty:
            return None
        # macd returns 3 columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        # We return the last row as a dict
        return macd.iloc[-1].to_dict()

    @staticmethod
    def calculate_ma(df: pd.DataFrame, length: int = 60) -> float:
        """
        Calculate Moving Average (Simple).
        """
        if '收盘' in df.columns:
            close = df['收盘']
        elif 'close' in df.columns:
            close = df['close']
        else:
            return None
            
        close = pd.to_numeric(close, errors='coerce')
        ma = ta.sma(close, length=length)
        
        if ma is None or ma.empty:
            return None
        return float(ma.iloc[-1])

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, length: int = 20, std: float = 2.0):
        """
        Calculate Bollinger Bands.
        Returns dict with 'upper', 'mid', 'lower'.
        """
        if '收盘' in df.columns:
            close = df['收盘']
        elif 'close' in df.columns:
            close = df['close']
        else:
            return None
            
        close = pd.to_numeric(close, errors='coerce')
        # bbands returns 5 columns: BBL, BBM, BBU, BBB, BBP
        bb = ta.bbands(close, length=length, std=std)
        
        if bb is None or bb.empty:
            return None
            
        # Get the last row
        last_row = bb.iloc[-1]
        
        # Column names depend on length and std, e.g., BBL_20_2.0
        # pandas_ta returns columns in order: BBL, BBM, BBU, BBB, BBP
        # We use positional access to avoid KeyError on name mismatch
        
        return {
            "lower": float(last_row.iloc[0]),
            "mid": float(last_row.iloc[1]),
            "upper": float(last_row.iloc[2])
        }

    @staticmethod
    def calculate_ma_series(df: pd.DataFrame, length: int = 60) -> pd.Series:
        """
        Calculate Moving Average and return the full Series.
        """
        if '收盘' in df.columns:
            close = df['收盘']
        elif 'close' in df.columns:
            close = df['close']
        else:
            return pd.Series()
            
        close = pd.to_numeric(close, errors='coerce')
        ma = ta.sma(close, length=length)
        return ma if ma is not None else pd.Series()

    @staticmethod
    def calculate_bollinger_bands_series(df: pd.DataFrame, length: int = 20, std: float = 2.0):
        """
        Calculate Bollinger Bands and return the full DataFrame.
        """
        if '收盘' in df.columns:
            close = df['收盘']
        elif 'close' in df.columns:
            close = df['close']
        else:
            return None
            
        close = pd.to_numeric(close, errors='coerce')
        bb = ta.bbands(close, length=length, std=std)
        return bb

    @staticmethod
    def calculate_macd_series(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        Calculate MACD and return dict with Series for 'macd', 'signal', 'histogram'.
        """
        if '收盘' in df.columns:
            close = df['收盘']
        elif 'close' in df.columns:
            close = df['close']
        else:
            return None
        
        close = pd.to_numeric(close, errors='coerce')
        macd_df = ta.macd(close, fast=fast, slow=slow, signal=signal)
        
        if macd_df is None or macd_df.empty:
            return None
        
        # macd returns DataFrame with columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        # Extract as: macd line, histogram, signal line
        return {
            'macd': macd_df.iloc[:, 0],      # MACD line
            'histogram': macd_df.iloc[:, 1], # Histogram
            'signal': macd_df.iloc[:, 2]     # Signal line
        }

