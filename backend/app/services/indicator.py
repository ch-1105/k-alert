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
