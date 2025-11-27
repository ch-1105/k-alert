from app.services.indicator import IndicatorService
import pandas as pd
from loguru import logger

class SignalEngine:
    @staticmethod
    def check_signal(df: pd.DataFrame, strategy):
        """
        Check signals based on strategy configuration.
        Returns a dict with signal details or None.
        """
        if df is None or df.empty:
            return None

        # 1. Calculate Base RSI
        rsi = IndicatorService.calculate_rsi(df, length=strategy.rsi_length)
        if rsi is None:
            return None
            
        signal_type = None
        reason = []
        detail = []
        
        # Current Price (for filters)
        current_price = float(df.iloc[-1]['close']) if 'close' in df.columns else float(df.iloc[-1]['收盘'])

        # --- Filter 1: Trend Filter (MA) ---
        # Default thresholds
        effective_low = strategy.rsi_low
        effective_high = strategy.rsi_high
        trend_status = "Unknown"

        if strategy.enable_trend_filter:
            ma60 = IndicatorService.calculate_ma(df, length=60)
            if ma60:
                if current_price > ma60:
                    trend_status = "Uptrend (Price > MA60)"
                    # Uptrend: Relax buy threshold (easier to buy), strict sell
                    effective_low = strategy.rsi_low + 5 
                    detail.append(f"Trend: Bullish. Adj Low: {effective_low}")
                else:
                    trend_status = "Downtrend (Price < MA60)"
                    # Downtrend: Strict buy threshold (harder to buy), relax sell
                    effective_low = strategy.rsi_low - 5
                    detail.append(f"Trend: Bearish. Adj Low: {effective_low}")
                
                logger.debug(f"Trend Filter: {trend_status}, RSI: {rsi:.2f}, Eff Low: {effective_low}, Eff High: {effective_high}")
            else:
                detail.append("Trend: MA60 N/A")
                logger.debug("Trend Filter: MA60 not available (insufficient data?)")

        # --- Check Base Signal with Effective Thresholds ---
        if rsi < effective_low:
            signal_type = "buy"
            reason.append(f"RSI({rsi:.1f}) < {effective_low}")
        elif rsi > effective_high:
            signal_type = "sell"
            reason.append(f"RSI({rsi:.1f}) > {effective_high}")
        else:
            # Log why it didn't trigger if it was close
            if rsi < strategy.rsi_low + 10: # Only log if somewhat close
                logger.debug(f"No signal. RSI: {rsi:.2f} not < {effective_low} (Base: {strategy.rsi_low})")

        # If no base signal, return early (unless we want to support other signals later)
        if not signal_type:
            return None

        # --- Filter 2: Volatility Filter (Bollinger Bands) ---
        if strategy.enable_volatility_filter:
            bb = IndicatorService.calculate_bollinger_bands(df)
            if bb:
                if signal_type == "buy" and current_price <= bb['lower']:
                    reason.append("Price touched BB Lower Band")
                elif signal_type == "sell" and current_price >= bb['upper']:
                    reason.append("Price touched BB Upper Band")
                else:
                    # If filter is enabled but condition not met, should we suppress?
                    # For now, let's just NOT add the "Strong" tag, but still allow signal.
                    # Or strictly suppress? User requirement implies "Enhancement", so maybe just add info.
                    # "共振信号...报警权重设为高" -> Implies adding weight, not necessarily suppressing.
                    pass
            else:
                detail.append("BB N/A")

        # Construct Result
        return {
            "signal_type": signal_type,
            "triggered": True,
            "reason": " + ".join(reason),
            "detail": "; ".join(detail),
            "rsi": rsi,
            "price": current_price,
            "trend": trend_status
        }
