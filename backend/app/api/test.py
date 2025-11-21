from fastapi import APIRouter, HTTPException
from app.services.market_data import MarketDataService
from pydantic import BaseModel
import akshare as ak
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class TestFetchRequest(BaseModel):
    symbol: str
    period: str = "daily"
    stock_type: str = "stock"

async def fetch_logic(symbol: str, period: str, stock_type: str):
    try:
        logger.info(f"Test fetch request: symbol={symbol}, period={period}, type={stock_type}")
        
        # 1. Test AkShare Version
        version = getattr(ak, "__version__", "unknown")
        
        # 2. Fetch Data
        df = MarketDataService.get_history_data(
            stock_code=symbol, 
            period=period, 
            stock_type=stock_type
        )
        
        if df is None or df.empty:
            return {
                "status": "warning",
                "message": "Data fetched successfully but is empty.",
                "akshare_version": version,
                "data": None
            }
            
        # Convert tail to dict
        tail_data = df.tail().to_dict(orient="records")
        
        return {
            "status": "success",
            "message": f"Successfully fetched {len(df)} rows.",
            "akshare_version": version,
            "columns": list(df.columns),
            "sample_data": tail_data
        }
    except Exception as e:
        logger.error(f"Test fetch failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "type": str(type(e))
        }

@router.post("/fetch")
async def test_fetch_data_post(request: TestFetchRequest):
    """
    Test fetching data for a specific stock/ETF (POST).
    """
    return await fetch_logic(request.symbol, request.period, request.stock_type)

@router.get("/fetch")
async def test_fetch_data_get(symbol: str, period: str = "daily", stock_type: str = "stock"):
    """
    Test fetching data for a specific stock/ETF (GET).
    """
    return await fetch_logic(symbol, period, stock_type)
@router.get("/diagnose")
async def diagnose_symbol(symbol: str):
    """
    Try multiple AkShare functions to see what works for this symbol.
    """
    results = {}
    
    # 1. Try Stock Daily
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        results["stock_daily"] = f"Success: {len(df)} rows" if df is not None and not df.empty else "Empty"
    except Exception as e:
        results["stock_daily"] = f"Error: {str(e)}"

    # 2. Try Stock Min (30)
    try:
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="30", adjust="qfq")
        results["stock_min_30"] = f"Success: {len(df)} rows" if df is not None and not df.empty else "Empty"
    except Exception as e:
        results["stock_min_30"] = f"Error: {str(e)}"

    # 3. Try ETF Daily
    try:
        df = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq")
        results["etf_daily"] = f"Success: {len(df)} rows" if df is not None and not df.empty else "Empty"
    except Exception as e:
        results["etf_daily"] = f"Error: {str(e)}"

    # 4. Try ETF Min (30)
    try:
        df = ak.fund_etf_hist_min_em(symbol=symbol, period="30", adjust="qfq")
        results["etf_min_30"] = f"Success: {len(df)} rows" if df is not None and not df.empty else "Empty"
    except Exception as e:
        results["etf_min_30"] = f"Error: {str(e)}"
        
    return {
        "symbol": symbol,
        "akshare_version": getattr(ak, "__version__", "unknown"),
        "results": results
    }
