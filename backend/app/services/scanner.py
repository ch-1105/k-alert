from app.services.market_data import MarketDataService
from app.services.indicator import IndicatorService
from app.services.signal import SignalEngine
from app.core.queue import alarm_queue
from app.core.database import SessionLocal
from app.models import UserStock, UserStrategy
from datetime import datetime
from loguru import logger
import time
import random
from app.services.trading_hours import TradingHours, get_market_status

def scan_stocks():
    logger.info("Scanning stocks...")
    
    # Check if market is open - skip scanning during non-trading hours
    if not TradingHours.is_trading_day():
        logger.info(f"Skipping scan - Market is closed (Weekend/Holiday)")
        return
    
    # For non-trading hours on trading days, still allow scanning with historical data
    # but log the market status
    market_status = get_market_status()
    is_trading = TradingHours.is_trading_time()
    
    if not is_trading:
        logger.info(
            f"Market is currently {market_status}. "
            f"Scanning will use historical data only (no real-time prices)."
        )
    
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
                    
                # Calculate change percent
                change_pct = 0.0
                try:
                    # Determine column name
                    close_col = 'close' if 'close' in df.columns else '收盘'
                    
                    if len(df) >= 2:
                        current_close = float(df.iloc[-1][close_col])
                        prev_close = float(df.iloc[-2][close_col])
                        if prev_close != 0:
                            change_pct = (current_close - prev_close) / prev_close * 100
                except Exception as e:
                    logger.warning(f"Failed to calculate change percent: {e}")

                logger.info(f"Stock: {stock.stock_code}, RSI: {rsi:.2f} (Length: {length}), Change: {change_pct:+.2f}%")

                # Check signal
                signal = SignalEngine.check_rsi_threshold(rsi, strategy.rsi_low, strategy.rsi_high)
                
                if signal:
                    # Check cooldown
                    if strategy.last_notify_time:
                        # Calculate minutes since last notify
                        diff = datetime.now() - strategy.last_notify_time
                        minutes_since = diff.total_seconds() / 60
                        
                        cooldown = getattr(strategy, 'cooldown_period', 60)
                        if minutes_since < cooldown:
                            logger.info(f"Skipping alert for {stock.stock_code} due to cooldown ({minutes_since:.1f}/{cooldown}m)")
                            continue
                    
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
                    
                    # Update last notify time
                    strategy.last_notify_time = datetime.now()
                    db.commit()
                
                # Add small delay to be nice to the API
                # Reduced from 3-5s to 0.1-0.5s because we run every 15s globally
                delay = random.uniform(0.1, 0.5)
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Error scanning {stock.stock_code}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Scan failed: {e}")
    finally:
        db.close()
