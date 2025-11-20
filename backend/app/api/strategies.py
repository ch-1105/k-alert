from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import UserStrategy
from pydantic import BaseModel

router = APIRouter()

class StrategyUpdate(BaseModel):
    stock_code: str
    rsi_low: float
    rsi_high: float
    rsi_period: str = "daily"
    rsi_length: int = 14
    enable_push: bool

@router.get("/{stock_code}")
def get_strategy(stock_code: str, db: Session = Depends(get_db)):
    strategy = db.query(UserStrategy).filter(UserStrategy.stock_code == stock_code).first()
    if not strategy:
        # Return default
        return {"rsi_low": 30, "rsi_high": 70, "rsi_period": "daily", "rsi_length": 14, "enable_push": True}
    return strategy

@router.post("/update")
def update_strategy(strategy: StrategyUpdate, db: Session = Depends(get_db)):
    db_strategy = db.query(UserStrategy).filter(UserStrategy.stock_code == strategy.stock_code).first()
    if not db_strategy:
        db_strategy = UserStrategy(
            stock_code=strategy.stock_code,
            rsi_low=strategy.rsi_low,
            rsi_high=strategy.rsi_high,
            rsi_period=strategy.rsi_period,
            rsi_length=strategy.rsi_length,
            enable_push=strategy.enable_push
        )
        db.add(db_strategy)
    else:
        db_strategy.rsi_low = strategy.rsi_low
        db_strategy.rsi_high = strategy.rsi_high
        db_strategy.rsi_period = strategy.rsi_period
        db_strategy.rsi_length = strategy.rsi_length
        db_strategy.enable_push = strategy.enable_push
    
    db.commit()
    return {"status": "ok"}
