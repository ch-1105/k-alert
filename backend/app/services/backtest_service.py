import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy
from app.services.market_data import MarketDataService
from loguru import logger

class TPlusOneRsiStrategy(Strategy):
    rsi_lower = 30
    rsi_upper = 70
    rsi_window = 14
    
    last_exit_bar = -100
    cooldown_bars = 5

    def init(self):
        # Calculate RSI
        # self.data.Close is a numpy array. We convert to Series for pandas_ta
        close_series = pd.Series(self.data.Close)
        self.rsi = self.I(ta.rsi, close_series, length=self.rsi_window)

    def next(self):
        # T+1 Validation and Sell Logic
        # In China A-shares, you cannot sell on the same day you bought (T+1).
        for trade in self.trades:
            if len(self.data) - 1 > trade.entry_bar:
                # Sell signal
                if self.rsi[-1] > self.rsi_upper:
                    trade.close()
                    self.last_exit_bar = len(self.data) - 1
        
        # Buy Logic
        # Simple strategy: If no position, buy when RSI < Lower
        # Constraint 1: Single position (handled by if not self.position)
        # Constraint 2: Cooldown period (to avoid whipsaws)
        if not self.position:
            # Check cooldown
            if (len(self.data) - 1 - self.last_exit_bar) > self.cooldown_bars:
                if self.rsi[-1] < self.rsi_lower:
                    self.buy()

class BacktestService:
    @staticmethod
    def run_backtest(stock_code: str, rsi_lower: float = 30, rsi_upper: float = 70, period: str = "daily"):
        """
        Run a backtest for a specific stock using T+1 RSI Strategy.
        """
        logger.info(f"Starting backtest for {stock_code}. Lower: {rsi_lower}, Upper: {rsi_upper}")
        
        # 1. Fetch History Data
        # Default to daily for backtesting usually
        df = MarketDataService.get_history_data(stock_code, period=period)
        
        if df is None or df.empty:
            logger.warning("No data for backtest.")
            return None
            
        # 2. Normalize Data for Backtesting.py
        # Needs: Open, High, Low, Close, Volume. Index: Datetime.
        
        # Copy to avoid setting on view
        df = df.copy()
        
        # Handle date index
        # Handle date index - handle various AkShare column names
        if '日期' in df.columns:
            df['Date'] = pd.to_datetime(df['日期'])
        elif 'date' in df.columns:
            df['Date'] = pd.to_datetime(df['date'])
        elif 'day' in df.columns:
            df['Date'] = pd.to_datetime(df['day'])
        elif '时间' in df.columns:
            df['Date'] = pd.to_datetime(df['时间'])
        else:
            # If index is already datetime? AkShare usually returns RangeIndex with a date col.
            pass
            
        if 'Date' in df.columns:
            df.set_index('Date', inplace=True)
            
        # Map Columns
        col_map = {
            '开盘': 'Open', 'open': 'Open',
            '最高': 'High', 'high': 'High',
            '最低': 'Low', 'low': 'Low',
            '收盘': 'Close', 'close': 'Close',
            '成交量': 'Volume', 'volume': 'Volume'
        }
        df.rename(columns=col_map, inplace=True)
        
        # Ensure required columns exist
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required):
            logger.error(f"Missing columns for backtest. Have: {df.columns}")
            return None
            
        # Convert to numeric
        for col in required:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df.dropna(subset=['Open', 'Close'], inplace=True)
        
        if df.empty:
            return None

        # 3. Configure Strategy
        # Strategy classes in Backtesting.py use class attributes for params.
        # We subclass dynamically or just set them on the class (since requests are serial or we spawn new classes).
        # To be safe regarding concurrency (though this is single threaded usually in FastAPI unless async), 
        # let's create a subclass dynamically to avoid race conditions if global class attrs are changed.
        
        class DynamicStrategy(TPlusOneRsiStrategy):
            pass
            
        DynamicStrategy.rsi_lower = rsi_lower
        DynamicStrategy.rsi_upper = rsi_upper
        
        # 4. Run Backtest
        # cash=100000, commission=0.0003 (approx A-share fees + tax, maybe 0.001 safer)
        bt = Backtest(df, DynamicStrategy, cash=100000, commission=0.001)
        stats = bt.run()
        
        # 5. Process Results
        try:
            trades_df = stats['_trades']
            trades_list = []
            if not trades_df.empty:
                # Convert trades to list of dicts
                # Columns: Size, EntryBar, ExitBar, EntryPrice, ExitPrice, PnL, ReturnPct, EntryTime, ExitTime, Duration
                trades_df['EntryTime'] = trades_df['EntryTime'].astype(str)
                trades_df['ExitTime'] = trades_df['ExitTime'].astype(str)
                trades_list = trades_df.to_dict(orient='records')

            return {
                "stock_code": stock_code,
                "return_pct": float(stats['Return [%]']),
                "win_rate": float(stats['Win Rate [%]']),
                "sharpe_ratio": float(stats['Sharpe Ratio']) if not pd.isna(stats['Sharpe Ratio']) else 0,
                "max_drawdown": float(stats['Max. Drawdown [%]']),
                "total_trades": int(stats['# Trades']),
                "trades": trades_list
            }
        except Exception as e:
            logger.error(f"Error processing backtest stats: {e}")
            return None
