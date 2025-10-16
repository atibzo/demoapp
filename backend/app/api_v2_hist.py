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

@router.get("/debug/lookup")
def debug_instrument_lookup(symbol: str, show_matches: bool = False):
    """
    Debug endpoint to test instrument lookup.
    Shows detailed information about how a symbol is resolved.
    
    Args:
        symbol: Stock symbol to lookup (e.g., BSE:BHEL, NSE:INFY, BHEL)
        show_matches: If True, show all similar matches found (default: False)
    
    Returns:
        Detailed lookup information including:
        - parsed_exchange: The exchange extracted from symbol
        - parsed_symbol: The trading symbol extracted
        - token: The instrument token found (or null)
        - found_exchange: The exchange where it was found (or null)
        - cache_status: Information about instrument cache
        - search_attempts: List of exchanges tried
        - variations_tried: Symbol variations attempted
        - similar_matches: (if show_matches=true) List of similar symbols found
    """
    from .hist import _find_instrument_token_robust, _INSTRUMENTS_CACHE, _INSTRUMENTS_CACHE_TIME
    from .kite import get_kite
    import logging
    import time
    
    log = logging.getLogger(__name__)
    
    # Get Kite session
    kite_session = get_kite()
    if not kite_session.access_token:
        raise HTTPException(
            status_code=401,
            detail="Not logged in to Zerodha. Please login first."
        )
    
    ks = kite_session.kite
    if not ks:
        raise HTTPException(
            status_code=500,
            detail="Kite session not initialized properly."
        )
    
    # Parse symbol
    symbol = symbol.replace(" ", "").upper()
    if ":" in symbol:
        parts = symbol.split(":", 1)
        parsed_exchange = parts[0] if len(parts) == 2 else "NSE"
        parsed_symbol = parts[1] if len(parts) == 2 else symbol
    else:
        parsed_exchange = "NSE"
        parsed_symbol = symbol
    
    # Get cache status
    cache_age = None
    if _INSTRUMENTS_CACHE_TIME:
        cache_age = int(time.time() - _INSTRUMENTS_CACHE_TIME)
    
    cache_info = {
        "cached_exchanges": list(_INSTRUMENTS_CACHE.keys()),
        "cache_age_seconds": cache_age,
        "cache_counts": {k: len(v) for k, v in _INSTRUMENTS_CACHE.items()},
        "cache_is_empty": len(_INSTRUMENTS_CACHE) == 0
    }
    
    # Perform lookup
    log.info(f"[DEBUG] Looking up {symbol} -> exchange:{parsed_exchange}, symbol:{parsed_symbol}")
    token, found_exchange = _find_instrument_token_robust(ks, symbol)
    
    # Build variations that would be tried
    variations = list(dict.fromkeys([
        parsed_symbol,
        f"{parsed_symbol}-EQ",
        f"{parsed_symbol}-BE",
        parsed_symbol.replace("-EQ", ""),
        parsed_symbol.replace("-BE", ""),
    ]))
    
    result = {
        "input_symbol": symbol,
        "parsed_exchange": parsed_exchange,
        "parsed_symbol": parsed_symbol,
        "token": token,
        "found_exchange": found_exchange,
        "success": token is not None,
        "cache_status": cache_info,
        "variations_tried": variations,
        "exchanges_searched": [parsed_exchange, "BSE" if parsed_exchange == "NSE" else "NSE"],
    }
    
    # If found, try to get more details from cache
    if token and found_exchange and found_exchange in _INSTRUMENTS_CACHE:
        for inst in _INSTRUMENTS_CACHE[found_exchange]:
            if inst.get("instrument_token") == token:
                result["instrument_details"] = {
                    "tradingsymbol": inst.get("tradingsymbol"),
                    "name": inst.get("name"),
                    "exchange": inst.get("exchange"),
                    "instrument_type": inst.get("instrument_type"),
                    "segment": inst.get("segment"),
                    "tick_size": inst.get("tick_size"),
                    "lot_size": inst.get("lot_size"),
                }
                break
    
    # If requested, show similar matches for debugging
    if show_matches and parsed_exchange in _INSTRUMENTS_CACHE:
        similar = []
        search_prefix = parsed_symbol[:3] if len(parsed_symbol) >= 3 else parsed_symbol
        
        for inst in _INSTRUMENTS_CACHE[parsed_exchange]:
            inst_sym = str(inst.get("tradingsymbol", "")).upper()
            if search_prefix in inst_sym:
                similar.append({
                    "symbol": inst_sym,
                    "token": inst.get("instrument_token"),
                    "name": inst.get("name", ""),
                })
                if len(similar) >= 20:  # Limit to 20 matches
                    break
        
        result["similar_matches"] = similar
        result["similar_count"] = len(similar)
    
    return result


@router.post("/debug/cache/refresh")
def debug_refresh_cache(exchange: str = None):
    """
    Manually refresh the instruments cache.
    Useful if you suspect the cache is stale or corrupted.
    
    Args:
        exchange: Specific exchange to refresh (NSE, BSE, ALL) or None for all
    
    Returns:
        Status of cache refresh operation
    """
    from .hist import _INSTRUMENTS_CACHE, warm_instruments_cache
    from .kite import get_kite
    import logging
    import time
    
    log = logging.getLogger(__name__)
    
    # Get Kite session
    kite_session = get_kite()
    if not kite_session.access_token:
        raise HTTPException(
            status_code=401,
            detail="Not logged in to Zerodha. Please login first."
        )
    
    ks = kite_session.kite
    if not ks:
        raise HTTPException(
            status_code=500,
            detail="Kite session not initialized properly."
        )
    
    try:
        # Clear the cache for the requested exchange
        if exchange and exchange != "ALL":
            log.info(f"[DEBUG] Clearing cache for {exchange}")
            _INSTRUMENTS_CACHE.pop(exchange, None)
        else:
            log.info(f"[DEBUG] Clearing entire instruments cache")
            _INSTRUMENTS_CACHE.clear()
        
        # Warm the cache
        success = warm_instruments_cache(ks)
        
        # Get updated status
        cache_status = {
            "cached_exchanges": list(_INSTRUMENTS_CACHE.keys()),
            "cache_counts": {k: len(v) for k, v in _INSTRUMENTS_CACHE.items()}
        }
        
        return {
            "success": success,
            "message": "Cache refreshed successfully" if success else "Cache refresh failed",
            "cache_status": cache_status
        }
        
    except Exception as e:
        log.error(f"[DEBUG] Error refreshing cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh cache: {str(e)}"
        )
