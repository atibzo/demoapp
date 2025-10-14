from __future__ import annotations
from typing import Literal, Optional, Dict, List
from pydantic import BaseModel

Side = Literal["long", "short"]
Regime = Literal["Calm", "Normal", "Hot"]
WindowStatus = Literal["ok", "early", "closed"]

class PlanRowV2(BaseModel):
    symbol: str
    side: Side
    score: float
    confidence: float
    age_s: float
    regime: Regime
    delta_trigger_bps: Optional[float] = None
    readiness: Literal["Ready", "Near", "Wait", "Stale", "Blocked"]
    block_reason: Optional[str] = None
    checks: Dict[str, bool]

class AnalyzeResponseV2(BaseModel):
    decision: Literal["BUY", "SELL", "WAIT"]
    score: float
    confidence: float
    bands: Dict[str, Optional[float]]
    action: Dict[str, object]
    why: Dict[str, object]
    meta: Dict[str, object]

class Policy(BaseModel):
    rev: int
    body: Dict[str, object]

class SessionStatusV2(BaseModel):
    zerodha: bool
    ticker: bool
    llm: bool
    logged_in: bool
    market_open: bool
    window_status: WindowStatus
    degraded: bool
    snapshot_p95_age_s: float
    time_ist: str
    rev: int
