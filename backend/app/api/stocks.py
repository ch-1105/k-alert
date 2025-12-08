from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import UserStock, UserStrategy
from pydantic import BaseModel
from typing import List

router = APIRouter()

from typing import Optional
from app.services.market_data import MarketDataService

class StockCreate(BaseModel):
    stock_code: str
    stock_name: str
    stock_type: str = "stock"

class StockResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    stock_type: str
    
    class Config:
        from_attributes = True

@router.post("/add", response_model=StockResponse)
def add_stock(stock: StockCreate, db: Session = Depends(get_db)):
    # Check if exists
    existing = db.query(UserStock).filter(UserStock.stock_code == stock.stock_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already monitored")
    
    db_stock = UserStock(
        stock_code=stock.stock_code, 
        stock_name=stock.stock_name,
        stock_type=stock.stock_type
    )
    db.add(db_stock)
    
    # Create default strategy
    db_strategy = UserStrategy(
        stock_code=stock.stock_code,
        rsi_low=30.0,
        rsi_high=70.0,
        rsi_period="daily",
        rsi_length=14,
        enable_push=True
    )
    db.add(db_strategy)
    
    db.commit()
    db.refresh(db_stock)
    return db_stock

@router.get("/list", response_model=List[StockResponse])
def list_stocks(db: Session = Depends(get_db)):
    return db.query(UserStock).all()

@router.delete("/delete/{stock_code}")
def delete_stock(stock_code: str, db: Session = Depends(get_db)):
    db.query(UserStock).filter(UserStock.stock_code == stock_code).delete()
    db.commit()
    return {"status": "ok"}

class StockMetrics(BaseModel):
    stock_code: str
    price: float
    change_percent: float
    rsi: Optional[float] = None
    rsi_length: int = 14
    timestamp: str
    market_status: str
    
    class Config:
        from_attributes = True

@router.get("/metrics/{stock_code}", response_model=StockMetrics)
def get_stock_metrics(stock_code: str, db: Session = Depends(get_db)):
    """
    Get real-time metrics for a stock: price, RSI, change percentage.
    """
    from datetime import datetime
    from app.services.indicator import IndicatorService
    from app.services.trading_hours import get_market_status
    
    # Get stock info from database
    stock = db.query(UserStock).filter(UserStock.stock_code == stock_code).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get strategy to determine RSI period and length
    strategy = db.query(UserStrategy).filter_by(stock_code=stock_code).first()
    if not strategy:
        # Use defaults
        rsi_period = "daily"
        rsi_length = 14
    else:
        rsi_period = strategy.rsi_period
        rsi_length = getattr(strategy, 'rsi_length', 14)
    
    # Fetch historical data
    df = MarketDataService.get_history_data(
        stock_code=stock.stock_code, 
        period=rsi_period, 
        stock_type=stock.stock_type
    )
    
    if df is None or df.empty:
        raise HTTPException(status_code=500, detail="Failed to fetch market data")
    
    # Determine column name
    close_col = 'close' if 'close' in df.columns else '收盘'
    open_col = 'open' if 'open' in df.columns else '开盘'
    
    # Get current price (latest close) and opening price
    try:
        current_price = float(df.iloc[-1][close_col])
        current_open = float(df.iloc[-1][open_col])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse price: {e}")
    
    # Calculate change percentage (vs opening price of the day)
    change_pct = 0.0
    if current_open != 0:
        change_pct = (current_price - current_open) / current_open * 100
    
    # Calculate RSI
    rsi_value = None
    try:
        rsi_value = IndicatorService.calculate_rsi(df, length=rsi_length)
    except Exception as e:
        # RSI calculation failed, but still return price data
        pass
    
    # Get market status
    market_status = get_market_status()
    
    return StockMetrics(
        stock_code=stock_code,
        price=current_price,
        change_percent=change_pct,
        rsi=rsi_value,
        rsi_length=rsi_length,
        timestamp=datetime.now().isoformat(),
        market_status=market_status
    )

