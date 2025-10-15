from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List
from .hist import get_bars_for_date, _slice_upto_hhmm, build_snapshot_at, analyze_snapshot, load_policy_v2, whatif, historical_plan

router = APIRouter(prefix="/api/v2/hist", tags=["hist"])

@router.get("/bars")
def hist_bars(symbol: str, date: str, auto_fetch: bool = Query(default=True)):
    """
    Get historical bars for a symbol on a date.
    
    UNIVERSAL: Works with ANY NSE/BSE stock, even those not suitable for intraday trading.
    This endpoint does NOT filter by intraday-suitability - it's for data retrieval and analysis.
    
    Args:
        symbol: Stock symbol (e.g., NSE:INFY, NSE:BHEL-EQ, NSE:SOMETHING-BE)
        date: Date in YYYY-MM-DD format
        auto_fetch: If True, automatically fetch from Kite API if not cached (default: True)
    
    Returns:
        List of 1-minute bars for the trading day
    """
    from .hist import _fetch_and_cache_historical_bars
    from .kite import get_kite
    import logging
    
    log = logging.getLogger(__name__)
    log.info(f"hist_bars called: symbol={symbol}, date={date}, auto_fetch={auto_fetch}")
    
    # Clean symbol
    symbol = symbol.replace(" ", "").upper()
    
    # Try to get cached bars first
    bars = get_bars_for_date(symbol, date)
    
    # If no cached bars and auto_fetch is enabled, try to fetch from Kite API
    if not bars and auto_fetch:
        # Check authentication first
        kite_session = get_kite()
        if not kite_session.access_token:
            raise HTTPException(
                status_code=401,
                detail="Not logged in to Zerodha. Please login to fetch historical data."
            )
        
        bars = _fetch_and_cache_historical_bars(symbol, date)
    
    if not bars:
        raise HTTPException(
            status_code=404,
            detail=f"No bars recorded for {symbol} on {date}. "
                   "Check backend logs for details. Possible causes: (1) Not logged in, (2) Market was closed, (3) Invalid symbol."
        )
    
    return {"bars": bars}

@router.get("/analyze")
def hist_analyze(symbol: str, date: str, time: str = Query(..., regex=r"^\d{2}:\d{2}$")):
    """
    Analyze a stock at a specific time on a historical date.
    Auto-fetches data from Kite API if not already cached.
    
    UNIVERSAL ANALYZER: Works with ANY NSE/BSE stock on ANY date, regardless of:
    - Whether it's in the Top Algos universe
    - Whether it's suitable for intraday trading
    - The series (EQ, BE, BZ, etc.)
    
    This is for ANALYSIS purposes - you can analyze any stock to understand its behavior,
    even if it's not suitable for actual intraday trading.
    """
    from .hist import _fetch_and_cache_historical_bars
    from .kite import get_kite
    import logging
    
    log = logging.getLogger(__name__)
    log.info(f"[HIST_ANALYZE] Called with symbol={symbol}, date={date}, time={time}")
    
    # Clean symbol
    symbol = symbol.replace(" ", "").upper()
    log.info(f"[HIST_ANALYZE] Cleaned symbol: {symbol}")
    
    # Try to get cached bars first
    bars = get_bars_for_date(symbol, date)
    log.info(f"[HIST_ANALYZE] Cache lookup: {'HIT' if bars else 'MISS'} ({len(bars) if bars else 0} bars)")
    
    # If no cached bars, try to fetch from Kite API
    if not bars:
        log.info(f"[HIST_ANALYZE] No cached data, attempting to fetch from Kite API")
        
        # Check authentication first
        kite_session = get_kite()
        if not kite_session.access_token:
            log.error(f"[HIST_ANALYZE] Not authenticated with Zerodha")
            raise HTTPException(
                status_code=401,
                detail="Not logged in to Zerodha. Please login to fetch historical data."
            )
        
        log.info(f"[HIST_ANALYZE] Zerodha authenticated, fetching data...")
        bars = _fetch_and_cache_historical_bars(symbol, date)
        log.info(f"[HIST_ANALYZE] Fetch result: {len(bars) if bars else 0} bars")
        
    if not bars:
        log.error(f"[HIST_ANALYZE] No data available after cache check and fetch attempt")
        raise HTTPException(
            status_code=404, 
            detail=f"No historical data available for {symbol} on {date}. "
                   f"Possible reasons: (1) Market was closed, (2) Invalid symbol, "
                   f"(3) Date is in the future, (4) Symbol not traded on this date. "
                   f"Please verify the symbol format (NSE:SYMBOL) and that the date is a valid trading day."
        )
    
    upto = _slice_upto_hhmm(bars, time)
    if not upto:
        log.error(f"[HIST_ANALYZE] No bars found up to time {time}")
        raise HTTPException(status_code=400, detail=f"No bars available up to time {time}. Market might not have opened by then.")
    
    log.info(f"[HIST_ANALYZE] Building snapshot from {len(upto)} bars up to {time}")
    snap = build_snapshot_at(symbol, upto)
    pol  = load_policy_v2()
    out  = analyze_snapshot(snap, pol)
    log.info(f"[HIST_ANALYZE] Analysis complete: {out.get('decision', 'N/A')} with confidence {out.get('confidence', 'N/A')}")
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
    universe_size: int = Query(300, ge=50, le=600, description="Number of stocks to scan (default 300, max 600)")
) -> Dict[str, Any]:
    """
    Get top trading opportunities for a historical date.
    Automatically fetches data from Kite API if not cached.
    
    NOW SCANS UP TO 600 INTRADAY TRADABLE STOCKS!
    Uses ultra-robust instrument lookup that works with ANY valid NSE/BSE stock.
    
    Args:
        date: Date in YYYY-MM-DD format
        top: Number of top opportunities to return (default 10, max 100)
        time: Time of day in HH:MM format (default 15:10 - near market close)
        universe_size: Number of stocks to scan (default 300, max 600)
    
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
