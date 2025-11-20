class SignalEngine:
    @staticmethod
    def check_rsi_threshold(rsi_value: float, low_threshold: float, high_threshold: float):
        """
        Check if RSI triggers a signal.
        Returns: "buy", "sell", or None
        """
        if rsi_value is None:
            return None
            
        if rsi_value < low_threshold:
            return "buy"
        elif rsi_value > high_threshold:
            return "sell"
        return None
