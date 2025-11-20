from app.services.market_data import MarketDataService
from app.services.indicator import IndicatorService
from app.services.signal import SignalEngine
from app.core.queue import alarm_queue
from app.core.database import SessionLocal
from app.models import UserStock, UserStrategy
from datetime import datetime
from loguru import logger

def scan_stocks():
    logger.info("Scanning stocks...")
    db = SessionLocal()
    try:
        # Get all monitored stocks
        stocks = db.query(UserStock).all()
        if not stocks:
            logger.info("No stocks to monitor.")
            return

        for stock in stocks:
            try:
                # Get strategy
                strategy = db.query(UserStrategy).filter_by(stock_code=stock.stock_code).first()
                if not strategy:
                    logger.warning(f"No strategy found for {stock.stock_code}, creating default.")
                    strategy = UserStrategy(
                        stock_code=stock.stock_code,
                        rsi_low=30.0,
                        rsi_high=70.0,
                        rsi_period="daily",
                        rsi_length=14,
                        enable_push=True
                    )
                    db.add(strategy)
                    db.commit()
                    db.refresh(strategy)
                    
                # Get data
                # For RSI, we need history.
                df = MarketDataService.get_history_data(stock.stock_code, period=strategy.rsi_period, stock_type=stock.stock_type)
                if df is None or df.empty:
                    logger.warning(f"No history data for {stock.stock_code} (period={strategy.rsi_period}), skipping.")
                    continue
                    
                # Calculate RSI
                # Use configured length or default to 14
                length = getattr(strategy, 'rsi_length', 14)
                rsi = IndicatorService.calculate_rsi(df, length=length)
                if rsi is None:
                    logger.warning(f"Could not calculate RSI for {stock.stock_code}, skipping.")
                    continue
                    
                logger.info(f"Stock: {stock.stock_code}, RSI: {rsi} (Length: {length})")

                # Check signal
                signal = SignalEngine.check_rsi_threshold(rsi, strategy.rsi_low, strategy.rsi_high)
                
                if signal:
                    # Get real-time price for the alert
                    rt_data = MarketDataService.get_real_time_price(stock.stock_code, stock_type=stock.stock_type)
                    price = rt_data['price'] if rt_data else 0
                    
                    # Push to queue
                    alarm_data = {
                        "user_id": stock.user_id,
                        "stock_code": stock.stock_code,
                        "stock_name": stock.stock_name,
                        "reason": f"RSI {signal}",
                        "value": rsi,
                        "threshold": strategy.rsi_low if signal == "buy" else strategy.rsi_high,
                        "price": price,
                        "time": datetime.now().isoformat()
                    }
                    alarm_queue.push_alarm(alarm_data)
                    logger.info(f"Alarm pushed: {alarm_data}")
                
                # Add delay to avoid rate limiting
                import time
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error scanning {stock.stock_code}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Scan failed: {e}")
    finally:
        db.close()
