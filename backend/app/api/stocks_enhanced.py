from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from app.core.database import get_db
from app.models import UserStock, UserStrategy
from app.services.indicator import IndicatorService
from app.services.market_data import MarketDataService
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()

# ... existing code (keep all existing endpoints) ...

@router.get("/kline-enhanced/{stock_code}")
def get_kline_enhanced(stock_code: str, period: str = "daily", stock_type: str = "stock"):
    """
    Get enhanced K-line data with all indicators for advanced charting.
    Returns: kline, markers, ma5, ma10, ma20, ma60, boll, volume, rsi, macd
    """
    from datetime import datetime
    
    # Get stock info
    df = MarketDataService.get_history_data(stock_code, period=period, stock_type=stock_type)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No data found")
    
    # Normalize column names
    col_map = {
        '日期': 'time', 'date': 'time',
        '开盘': 'open', 'open': 'open',
        '最高': 'high', 'high': 'high',
        '最低': 'low', 'low': 'low',
        '收盘': 'close', 'close': 'close',
        '成交量': 'volume', 'volume': 'volume'
    }
    
    df = df.rename(columns={k:v for k,v in col_map.items() if k in df.columns})
    
    # Ensure time is string YYYY-MM-DD or handle datetime
    if 'time' in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df['time']):
            # For minute data, format as YYYY-MM-DD HH:MM
            if period in ['1', '5', '15', '30', '60']:
                df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M')
            else:
                df['time'] = df['time'].dt.strftime('%Y-%m-%d')
    
    # Convert to numeric
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['open', 'close'])
    
    if df.empty:
        raise HTTPException(status_code=500, detail="Data processing failed")
    
    # Prepare response
    response = {}
    
    # 1. Basic OHLCV
    kline_data = df[['time', 'open', 'high', 'low', 'close', 'volume']].to_dict(orient='records')
    response['kline'] = kline_data
    
    # 2. Calculate indicators
    try:
        # RSI
        rsi_series = IndicatorService.calculate_rsi_series(df, length=14)
        rsi_data = []
        for i, (idx, val) in enumerate(rsi_series.items()):
            if pd.notna(val):
                rsi_data.append({
                    'time': df.iloc[i]['time'],
                    'value': float(val)
                })
        response['rsi'] = rsi_data
        
        # MA lines
        for ma_len in [5, 10, 20, 60]:
            ma_series = IndicatorService.calculate_ma_series(df, length=ma_len)
            ma_data = []
            for i, (idx, val) in enumerate(ma_series.items()):
                if pd.notna(val):
                    ma_data.append({
                        'time': df.iloc[i]['time'],
                        'value': float(val)
                    })
            response[f'ma{ma_len}'] = ma_data
        
        # Bollinger Bands
        boll = IndicatorService.calculate_bollinger_bands_series(df, length=20, std=2.0)
        if boll is not None:
            boll_upper_data = []
            boll_mid_data = []
            boll_lower_data = []
            for i in range(len(df)):
                if i < len(boll):
                    row = boll.iloc[i]
                    time_val = df.iloc[i]['time']
                    if pd.notna(row.iloc[2]):  # upper
                        boll_upper_data.append({'time': time_val, 'value': float(row.iloc[2])})
                    if pd.notna(row.iloc[1]):  # mid
                        boll_mid_data.append({'time': time_val, 'value': float(row.iloc[1])})
                    if pd.notna(row.iloc[0]):  # lower
                        boll_lower_data.append({'time': time_val, 'value': float(row.iloc[0])})
            
            response['boll_upper'] = boll_upper_data
            response['boll_mid'] = boll_mid_data
            response['boll_lower'] = boll_lower_data
        
        # MACD
        macd_dict = IndicatorService.calculate_macd_series(df)
        if macd_dict:
            # macd_dict has 'macd', 'signal', 'histogram' as Series
            macd_data = []
            signal_data = []
            hist_data = []
            
            for i in range(len(df)):
                time_val = df.iloc[i]['time']
                if i < len(macd_dict['macd']):
                    if pd.notna(macd_dict['macd'].iloc[i]):
                        macd_data.append({'time': time_val, 'value': float(macd_dict['macd'].iloc[i])})
                    if pd.notna(macd_dict['signal'].iloc[i]):
                        signal_data.append({'time': time_val, 'value': float(macd_dict['signal'].iloc[i])})
                    if pd.notna(macd_dict['histogram'].iloc[i]):
                        hist_data.append({'time': time_val, 'value': float(macd_dict['histogram'].iloc[i])})
            
            response['macd'] = macd_data
            response['macd_signal'] = signal_data
            response['macd_histogram'] = hist_data
        
        # Volume (formatted for histogram)
        volume_data = []
        for i in range(len(df)):
            volume_data.append({
                'time': df.iloc[i]['time'],
                'value': float(df.iloc[i]['volume']),
                'color': '#26a69a' if df.iloc[i]['close'] >= df.iloc[i]['open'] else '#ef5350'
            })
        response['volume'] = volume_data
        
        # Calculate markers (buy/sell signals)
        markers = []
        for i in range(len(df)):
            if i < 14: continue
            
            rsi_val = rsi_series.iloc[i]
            row_time = df.iloc[i]['time']
            
            if pd.isna(rsi_val): continue
            
            if rsi_val < 30:
                markers.append({
                    "time": row_time,
                    "position": "belowBar",
                    "color": "#e91e63",
                    "shape": "arrowUp",
                    "text": f"B:{int(rsi_val)}"
                })
            elif rsi_val > 70:
                markers.append({
                    "time": row_time,
                    "position": "aboveBar",
                    "color": "#2196F3",
                    "shape": "arrowDown",
                    "text": f"S:{int(rsi_val)}"
                })
        
        response['markers'] = markers
        
    except Exception as e:
        # If indicator calculation fails, still return basic kline
        print(f"Indicator calculation error: {e}")
        pass
    
    return response
