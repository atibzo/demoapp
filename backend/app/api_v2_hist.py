from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List
from .hist import get_bars_for_date, _slice_upto_hhmm, build_snapshot_at, analyze_snapshot, load_policy_v2, whatif, historical_plan

router = APIRouter(prefix="/api/v2/hist", tags=["hist"])

@router.get("/bars")
def hist_bars(symbol: str, date: str, auto_fetch: bool = Query(default=True)):
    """
    Get historical bars for a symbol on a date.
    
    Args:
        symbol: Stock symbol (e.g., NSE:INFY)
        date: Date in YYYY-MM-DD format
        auto_fetch: If True, automatically fetch from Kite API if not cached (default: True)
    
    Returns:
        List of 1-minute bars for the trading day
    """
    from .hist import _fetch_and_cache_historical_bars
    
    # Clean symbol
    symbol = symbol.replace(" ", "").upper()
    
    # Try to get cached bars first
    bars = get_bars_for_date(symbol, date)
    
    # If no cached bars and auto_fetch is enabled, try to fetch from Kite API
    if not bars and auto_fetch:
        bars = _fetch_and_cache_historical_bars(symbol, date)
    
    if not bars:
        raise HTTPException(
            status_code=404,
            detail=f"No bars recorded for {symbol} on {date}. "
                   "Try logging in to Zerodha to fetch historical data."
        )
    
    return {"bars": bars}

@router.get("/analyze")
def hist_analyze(symbol: str, date: str, time: str = Query(..., regex=r"^\d{2}:\d{2}$")):
    """
    Analyze a stock at a specific time on a historical date.
    Auto-fetches data from Kite API if not already cached.
    
    This endpoint works independently - you can analyze ANY stock on ANY date,
    not just stocks that are in the "top algos" universe.
    """
    from .hist import _fetch_and_cache_historical_bars
    
    # Clean symbol
    symbol = symbol.replace(" ", "").upper()
    
    # Try to get cached bars first
    bars = get_bars_for_date(symbol, date)
    
    # If no cached bars, try to fetch from Kite API
    if not bars:
        bars = _fetch_and_cache_historical_bars(symbol, date)
        
    if not bars:
        raise HTTPException(
            status_code=404, 
            detail=f"No historical data available for {symbol} on {date}. "
                   "Make sure you're logged in to Zerodha and the symbol exists."
        )
    
    upto = _slice_upto_hhmm(bars, time)
    if not upto:
        raise HTTPException(status_code=400, detail="No bars up to given time.")
    
    snap = build_snapshot_at(symbol, upto)
    pol  = load_policy_v2()
    out  = analyze_snapshot(snap, pol)
    return out

@router.get("/whatif")
def hist_whatif(symbol: str, date: str, time: str,
                entry: float, stop: float, tp2: float, risk_amt: float, lot: int = 1):
    return whatif(entry, stop, tp2, risk_amt, lot)

@router.get("/plan")
def hist_plan(
    date: str, 
    top: int = Query(10, ge=1, le=100), 
    time: str = "15:10",
    universe_size: int = Query(300, ge=50, le=300, description="Number of stocks to scan (default 300)")
) -> Dict[str, Any]:
    """
    Get top trading opportunities for a historical date.
    Automatically fetches data from Kite API if not cached.
    
    NOW SCANS TOP 300 INTRADAY TRADABLE STOCKS (configurable)!
    
    Args:
        date: Date in YYYY-MM-DD format
        top: Number of top opportunities to return (default 10, max 100)
        time: Time of day in HH:MM format (default 15:10 - near market close)
        universe_size: Number of stocks to scan (default 300, max 300)
    
    Returns:
        Object containing:
        - date: Query date
        - top: Number of results requested
        - time: Analysis time
        - universe_scanned: Number of stocks scanned
        - count: Number of results returned
        - items: List of top trading opportunities ranked by score
    """
    import logging
    log = logging.getLogger(__name__)
    
    try:
        log.info(f"Historical plan: date={date}, time={time}, top={top}, universe_size={universe_size}")
        rows = historical_plan(date, time, top, universe_size)
        
        return {
            "date": date,
            "top": top,
            "time": time,
            "universe_scanned": universe_size,
            "count": len(rows),
            "items": rows
        }
    except Exception as e:
        log.exception(f"Failed to generate historical plan: {e}")
        # Check if it's an authentication error
        if "token" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=401, 
                detail="Zerodha session expired or not authenticated. Please login to fetch historical data."
            )
        # Generic error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate historical plan: {str(e)}"
        )
