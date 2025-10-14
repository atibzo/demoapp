from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict
from .hist import get_bars_for_date, _slice_upto_hhmm, build_snapshot_at, analyze_snapshot, load_policy_v2, whatif

router = APIRouter(prefix="/api/v2/hist", tags=["hist"])

@router.get("/bars")
def hist_bars(symbol: str, date: str):
    bars = get_bars_for_date(symbol, date)
    if not bars:
        raise HTTPException(status_code=404, detail="No bars recorded for this date.")
    return {"bars": bars}

@router.get("/analyze")
def hist_analyze(symbol: str, date: str, time: str = Query(..., regex=r"^\d{2}:\d{2}$")):
    bars = get_bars_for_date(symbol, date)
    if not bars:
        raise HTTPException(status_code=404, detail="No bars recorded for this date.")
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
