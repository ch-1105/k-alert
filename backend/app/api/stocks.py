from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from app.core.database import get_db
from app.models import UserStock, UserStrategy
from app.services.indicator import IndicatorService
from pydantic import BaseModel
from typing import List

router = APIRouter()

from typing import Optional, Dict, Any
from app.services.market_data import MarketDataService
from app.services.backtest_service import BacktestService

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

class BacktestRequest(BaseModel):
    stock_code: str
    rsi_lower: float = 30.0
    rsi_upper: float = 70.0
    period: str = "daily"

@router.post("/backtest")
def run_backtest_endpoint(req: BacktestRequest):
    """
    Run backtest for a stock.
    """
    result = BacktestService.run_backtest(req.stock_code, req.rsi_lower, req.rsi_upper, req.period)
    if not result:
        raise HTTPException(status_code=400, detail="Backtest failed or no data available")
    return result

@router.get("/kline/{stock_code}")
def get_kline_data(stock_code: str, period: str = "daily", stock_type: str = "stock"):
    """
    Get K-line data for TradingView charts.
    """
    df = MarketDataService.get_history_data(stock_code, period=period, stock_type=stock_type)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No data found")
        
    # Format for lightweight-charts
    # expected: { time: '2019-04-11', open: 80.01, high: 96.63, low: 76.6, close: 88.65 }
    
    data = []
    
    # helper to parse row
    # AkShare columns can vary slightly
    
    # Normalize col names for easier access (copy paste from backtest logic or similar)
    col_map = {
        '日期': 'time', 'date': 'time',
        '开盘': 'open', 'open': 'open',
        '最高': 'high', 'high': 'high',
        '最低': 'low', 'low': 'low',
        '收盘': 'close', 'close': 'close',
        '成交量': 'volume', 'volume': 'volume'
    }
    
    # Rename columns that exist
    df = df.rename(columns={k:v for k,v in col_map.items() if k in df.columns})
    
    # Ensure date/time is string 'YYYY-MM-DD'
    if 'time' in df.columns:
        # If it's datetime object
        if pd.api.types.is_datetime64_any_dtype(df['time']):
            df['time'] = df['time'].dt.strftime('%Y-%m-%d')
        else:
             # assume string, try to slice if it has time?
             # For daily, YYYY-MM-DD is needed.
             pass
    

    # Convert to list of dicts
    # Filter only needed columns
    needed = ['time', 'open', 'high', 'low', 'close', 'volume']
    # Check intersection
    available = [c for c in needed if c in df.columns]
    
    if len(available) < 5:
        # Missing essential OHLC
        raise HTTPException(status_code=500, detail=f"Data format error, missing columns. Found: {df.columns}")
    
    # Calculate markers based on RSI
    markers = []
    try:
        # We need a dataframe with 'close' for RSI calc
        # We already have df with 'close' (renamed)
        rsi_series = IndicatorService.calculate_rsi_series(df, length=14)
        
        # Identify signals
        # Buy: RSI < 30
        # Sell: RSI > 70 (optional, mainly focus on buy as per alert logic)
        
        for i in range(len(df)):
            if i < 14: continue
            
            rsi_val = rsi_series.iloc[i]
            row_time = df.iloc[i]['time']
            
            if pd.isna(rsi_val): continue
            
            if rsi_val < 30:
                markers.append({
                    "time": row_time,
                    "position": "belowBar",
                    "color": "#e91e63", # Pink/Red
                    "shape": "arrowUp",
                    "text": f"B:{int(rsi_val)}"
                })
            elif rsi_val > 70:
                markers.append({
                    "time": row_time,
                    "position": "aboveBar",
                    "color": "#2196F3", # Blue
                    "shape": "arrowDown",
                    "text": f"S:{int(rsi_val)}"
                })
                
    except Exception as e:
        # If calculation fails, just no markers
        pass
    
    # to_dict('records')
    records = df[available].to_dict(orient='records')
    
    return {
        "kline": records,
        "markers": markers
    }

