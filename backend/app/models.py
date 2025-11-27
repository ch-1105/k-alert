from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class UserStock(Base):
    __tablename__ = "user_stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1) # Single user for now
    stock_code = Column(String, index=True)
    stock_name = Column(String)
    stock_type = Column(String, default="stock") # stock, etf
    created_at = Column(DateTime, default=func.now())

class UserStrategy(Base):
    __tablename__ = "user_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    stock_code = Column(String, index=True)
    rsi_low = Column(Float, default=30.0)
    rsi_high = Column(Float, default=70.0)
    rsi_period = Column(String, default="daily") # daily, 60, 30, 4h
    rsi_length = Column(Integer, default=14)
    enable_push = Column(Boolean, default=True)
    enable_trend_filter = Column(Boolean, default=False)
    enable_volatility_filter = Column(Boolean, default=False)
    last_notify_time = Column(DateTime, nullable=True)
    cooldown_period = Column(Integer, default=30) # minutes
    
class UserNotify(Base):
    __tablename__ = "user_notifies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    telegram_id = Column(String, nullable=True)
    email = Column(String, nullable=True)
    notify_rate_limit = Column(Integer, default=30) # seconds
