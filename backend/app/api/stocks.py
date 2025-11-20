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
