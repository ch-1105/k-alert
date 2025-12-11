import pandas as pd
from app.services.signal import SignalEngine
from app.services.indicator import IndicatorService

# Mock Strategy Object
class MockStrategy:
    rsi_low = 30.0
    rsi_high = 70.0
    rsi_length = 6
    enable_trend_filter = True
    enable_volatility_filter = True

def test_signal_logic():
    print("Testing Signal Logic...")
    
    # Create a mock DataFrame
    # Scenario 1: Downtrend (Price < MA60), RSI Low but not strict enough
    # MA60 will be around 100. Price drops to 90.
    data = {
        'close': [100] * 60 + [90] * 10 # 70 points
    }
    df = pd.DataFrame(data)
    
    # Calculate RSI manually to see what we expect
    # RSI of a drop should be low.
    # Let's just mock the RSI calculation or trust the library?
    # Better to create data that results in specific RSI.
    # Alternatively, we can mock IndicatorService.calculate_rsi if we want unit test isolation,
    # but here we want integration test.
    
    # Let's try a simple case where we force values by mocking the service methods
    # because generating exact RSI/MA with small data is tricky.
    
    # Mocking IndicatorService methods for this test run
    original_rsi = IndicatorService.calculate_rsi
    original_ma = IndicatorService.calculate_ma
    original_bb = IndicatorService.calculate_bollinger_bands
    
    try:
        # Case 1: Downtrend, RSI=25 (Threshold 30). 
        # With Trend Filter: Downtrend -> Threshold becomes 30-5=25. 
        # So RSI=25 is NOT < 25. Should NOT trigger.
        IndicatorService.calculate_rsi = lambda df, length=14: 25.0
        IndicatorService.calculate_ma = lambda df, length=60: 100.0 # Price is 90
        IndicatorService.calculate_bollinger_bands = lambda df, length=20, std=2.0: {'lower': 80, 'upper': 120, 'mid': 100}
        
        df_case1 = pd.DataFrame({'close': [90]})
        result = SignalEngine.check_signal(df_case1, MockStrategy())
        print(f"Case 1 (Downtrend, RSI=25, Thresh=25): {result}")
        assert result is None or not result['triggered']
        
        # Case 2: Downtrend, RSI=15. Should trigger.
        IndicatorService.calculate_rsi = lambda df, length=14: 15.0
        result = SignalEngine.check_signal(df_case1, MockStrategy())
        print(f"Case 2 (Downtrend, RSI=15): {result}")
        assert result['triggered']
        assert result['signal_type'] == 'buy'
        assert "Downtrend" in result['trend']
        
        # Case 3: Uptrend (Price > MA60), RSI=33 (Threshold 30).
        # With Trend Filter: Uptrend -> Threshold becomes 30+5=35.
        # RSI=33 < 35. Should trigger.
        IndicatorService.calculate_ma = lambda df, length=60: 80.0 # Price is 90
        IndicatorService.calculate_rsi = lambda df, length=14: 33.0
        result = SignalEngine.check_signal(df_case1, MockStrategy())
        print(f"Case 3 (Uptrend, RSI=33, Thresh=35): {result}")
        assert result['triggered']
        assert "Uptrend" in result['trend']
        
        # Case 4: Volatility Filter. Price touches Lower Band.
        IndicatorService.calculate_bollinger_bands = lambda df, length=20, std=2.0: {'lower': 91, 'upper': 120, 'mid': 100} # Lower=91, Price=90
        IndicatorService.calculate_rsi = lambda df, length=14: 15.0 # Trigger buy
        result = SignalEngine.check_signal(df_case1, MockStrategy())
        print(f"Case 4 (BB Touch): {result}")
        assert "Price touched BB Lower Band" in result['reason']

        print("All tests passed!")
        
    finally:
        # Restore
        IndicatorService.calculate_rsi = original_rsi
        IndicatorService.calculate_ma = original_ma
        IndicatorService.calculate_bollinger_bands = original_bb

if __name__ == "__main__":
    test_signal_logic()
