from __future__ import annotations

import os
import json
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Iterable

from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from kiteconnect.exceptions import TokenException

from .utils import rid
from .rl import redis_client, token_bucket
from .models import APIResponse, Policy, HintIn
from .kite import get_kite
from .engine import plan, minute_snapshot
from . import llm
from .api_v2 import router as api_v2_router
from .api_v2_hist import router as api_v2_hist_router

# ---------- Config ----------
IST = ZoneInfo("Asia/Kolkata")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")
TICKER_HEARTBEAT_MAX_AGE = int(os.getenv("TICKER_HEARTBEAT_MAX_AGE", "15"))
DEFAULT_UNIVERSE_LIMIT = int(os.getenv("UNIVERSE_LIMIT", "300"))
DEBUG_ENABLED = os.getenv("DEBUG_ENABLED", "1") == "1"

# ---------- Logging ----------
log = logging.getLogger("intraday_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ---------- Time helpers ----------
def ist_now() -> datetime:
    return datetime.now(tz=IST)


def is_market_open(ts: datetime | None = None) -> bool:
    d = ts or ist_now()
    if d.weekday() >= 5:
        return False
    minutes = d.hour * 60 + d.minute
    open_m = 9 * 60 + 15
    close_m = 15 * 60 + 30  # inclusive is intentional
    return open_m <= minutes <= close_m


# --- Historical analysis helpers ---
from .hist import (  # noqa: E402
    get_bars_for_date,
    _slice_upto_hhmm,
    build_snapshot_at,
    analyze_snapshot,
    whatif,
    load_policy_v2,
)


# ---------- Normalization ----------
def _clean_symbol(s: str) -> str:
    # "NSE: ABB" -> "NSE:ABB"
    return (s or "").replace(" ", "").upper()


def _b2s(x: Any) -> Any:
    return x.decode("utf-8") if isinstance(x, (bytes, bytearray)) else x


def _smembers_str(values: Iterable[Any]) -> List[str]:
    return [str(_b2s(v)) for v in (values or [])]


def _get_int(v: Any, default: int) -> int:
    try:
        if v is None:
            return default
        if isinstance(v, (bytes, bytearray)):
            v = v.decode()
        return int(v)
    except Exception:
        return default


def _json_loads_or(obj: Any, fallback: Any) -> Any:
    try:
        if obj is None:
            return fallback
        if isinstance(obj, (bytes, bytearray)):
            obj = obj.decode("utf-8")
        return json.loads(obj)
    except Exception:
        return fallback


# ---------- App & CORS ----------
app = FastAPI(title="Intraday Co-Pilot API")

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        t0 = time.perf_counter()
        request_id = rid()
        try:
            response = await call_next(request)
            dt = int(1000 * (time.perf_counter() - t0))
            log.info(
                "rid=%s %s %s qp=%s status=%s dur_ms=%s",
                request_id,
                request.method,
                request.url.path,
                str(request.query_params),
                response.status_code,
                dt,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            dt = int(1000 * (time.perf_counter() - t0))
            log.exception("rid=%s unhandled path=%s qp=%s dur_ms=%s", request_id, request.url.path, str(request.query_params), dt)
            raise


app.add_middleware(AccessLogMiddleware)

# ---------- Include API v2 Routers ----------
app.include_router(api_v2_router, prefix="/api/v2")
app.include_router(api_v2_hist_router)  # already has prefix

# ---------- Redis ----------
try:
    r = redis_client(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
except Exception as e:
    log.error(f"Failed to connect to Redis: {e}")
    raise


# Allow hist.py to reuse the same policy you edit via /api/policy
def get_policy_v2_body() -> Dict[str, Any] | None:
    try:
        import pathlib
        p = pathlib.Path(__file__).with_name("policy.json")
        return json.loads(p.read_text())
    except Exception:
        return None


# ---------- Root ----------
@app.get("/")
def root():
    return RedirectResponse(url="/docs")


# ---------- Health ----------
@app.get("/healthz")
def healthz():
    try:
        ok = bool(r.ping())
    except Exception:
        ok = False
    return {"redis": ok, "time": ist_now().isoformat()}


# ---------- Session / OAuth ----------
@app.get("/api/session")
def api_session():
    ks = get_kite()

    zerodha_ok = bool(getattr(ks, "access_token", None))
    if zerodha_ok:
        try:
            ks.kite.profile()
        except TokenException:
            zerodha_ok = False
        except Exception:
            pass

    now_s = int(time.time())
    try:
        alive_raw = r.get("ticker:alive")
    except Exception:
        alive_raw = None
    alive = _get_int(alive_raw, 0)
    ticker_live = (now_s - alive) < TICKER_HEARTBEAT_MAX_AGE

    try:
        subs_raw = r.scard("symbols:active")
    except Exception:
        subs_raw = 0
    subs = int(subs_raw or 0)

    limit = _get_int(r.get("cfg:universe_limit"), DEFAULT_UNIVERSE_LIMIT)

    mo = is_market_open()
    mode = "LIVE" if mo and ticker_live else ("WAITING" if mo and not ticker_live else "HISTORICAL")

    return {
        "zerodha": zerodha_ok,
        "llm": True,
        "ticker": bool(ticker_live),
        "stale_count": 0,
        "subscribed_count": subs,
        "universe_limit": limit,
        "market_open": mo,
        "server_time_ist": ist_now().isoformat(),
        "mode": mode,
    }


@app.get("/kite/login_url")
def kite_login_url():
    return {"login_url": get_kite().login_url()}


@app.get("/callback")
def kite_callback(request_token: str):
    get_kite().exchange_for_token(request_token)
    return RedirectResponse(url=f"{FRONTEND_URL}/auth/redirect?ok=1")


@app.post("/logout")
def logout():
    from .kite import SESSION_PATH
    try:
        if os.path.exists(SESSION_PATH):
            os.remove(SESSION_PATH)
    except Exception:
        pass
    return {"ok": True}


# ---------- Plan / Live ----------
@app.get("/api/plan")
def api_plan(top: int = 30):
    ok, wait = token_bucket("plan", 10, 3.0)
    if not ok:
        raise HTTPException(status_code=429, detail="rate limited", headers={"Retry-After": str(int(round(wait)))})
    try:
        syms = _smembers_str(r.smembers("symbols:active"))
    except Exception:
        syms = []
    rows = plan(syms, top_n=top)
    return {"ok": True, "request_id": rid(), "duration_ms": 0, "data": rows}


@app.get("/api/live")
def api_live(symbols: str):
    ok, wait = token_bucket("live", 20, 5.0)
    if not ok:
        raise HTTPException(status_code=429, detail="rate limited", headers={"Retry-After": str(int(round(wait)))})
    out: Dict[str, Any] = {}
    for s in [x for x in (symbols or "").split(",") if x.strip()]:
        cs = _clean_symbol(s)
        try:
            out[cs] = minute_snapshot(cs)
        except Exception:
            log.exception("minute_snapshot failed symbol=%s", cs)
            out[cs] = {"error": "stale_or_missing"}
    return {"ok": True, "request_id": rid(), "duration_ms": 0, "data": out}


# ---------- Bars (charts work off-hours) ----------
@app.get("/api/bars")
def api_bars(symbol: str = Query(...), limit: int = Query(120, ge=1, le=480)):
    symbol = _clean_symbol(symbol)
    try:
        rows = r.lrange(f"bars:{symbol}", 0, max(0, limit - 1)) or []
        bars = [_json_loads_or(x, None) for x in rows]
        bars = [b for b in bars if b is not None]
    except Exception:
        bars = []
    snap_raw = r.get(f"snap:{symbol}")
    indicators = _json_loads_or(snap_raw, {})
    return {"ok": True, "request_id": rid(), "duration_ms": 0, "data": {"bars": bars, "indicators": indicators}}


# ---------- AI Tooltip ----------
@app.post("/api/hint")
def api_hint(body: HintIn):
    ok, wait = token_bucket("hint", 10, 2.0)
    if not ok:
        raise HTTPException(status_code=429, detail="rate limited", headers={"Retry-After": str(int(round(wait)))})
    try:
        text = llm.hint(body.metric, body.context)
    except Exception:
        log.exception("llm.hint failed metric=%s", body.metric)
        text = ""
    return {"ok": True, "request_id": rid(), "duration_ms": 0, "data": {"hint": text}}


# ---------- Journal ----------
@app.get("/api/journal")
def api_journal():
    """
    Returns trading journal entries. Currently returns empty list.
    TODO: Implement actual journal storage and retrieval.
    """
    return {"ok": True, "request_id": rid(), "duration_ms": 0, "data": []}

# ---------- Config (pinned & active universe limit) ----------
@app.get("/api/config")
def api_get_config():
    try:
        pinned = sorted(_smembers_str(r.smembers("cfg:pinned")))
    except Exception:
        pinned = []
    limit = _get_int(r.get("cfg:universe_limit"), DEFAULT_UNIVERSE_LIMIT)
    return {"pinned": pinned, "universe_limit": limit}


@app.post("/api/config")
def api_set_config(
    pinned: List[str] | None = Body(default=None),
    universe_limit: int | None = Body(default=None),
):
    if pinned is not None:
        try:
            r.delete("cfg:pinned")
            if pinned:
                r.sadd("cfg:pinned", *[p.strip() for p in pinned if p.strip()])
        except Exception:
            log.exception("failed updating cfg:pinned")
    if universe_limit is not None:
        try:
            r.set("cfg:universe_limit", int(universe_limit))
        except Exception:
            log.exception("failed setting cfg:universe_limit")
    return {"ok": True}


# ---------- Analyze (LLM) ----------
@app.get("/api/analyze")
def api_analyze(symbol: str):
    """
    Deterministic JSON verdict for the given symbol.
    Uses the latest live snapshot if available; otherwise runs on {}.
    """
    raw = symbol
    symbol = _clean_symbol(symbol)
    log.info("analyze start symbol_raw=%r symbol=%r", raw, symbol)

    try:
        snap = minute_snapshot(symbol)
    except Exception:
        log.exception("minute_snapshot failed symbol=%s", symbol)
        snap = {}

    try:
        out = llm.analyze(symbol, snap)
    except Exception:
        log.exception("llm.analyze failed symbol=%s", symbol)
        out = {"decision": "skip", "bands": [1.0, 1.0], "confidence": 0.5, "checks": {}}

    return {"ok": True, "request_id": rid(), "duration_ms": 0, "data": out}


# ---------- Policy ----------
@app.get("/api/policy")
def api_policy_get():
    import pathlib
    p = pathlib.Path(__file__).with_name("policy.json")
    try:
        return json.loads(p.read_text())
    except FileNotFoundError:
        raise HTTPException(404, "policy.json not found")


@app.post("/api/policy")
def api_policy_post(obj: Policy):
    import pathlib
    p = pathlib.Path(__file__).with_name("policy.json")
    p.write_text(json.dumps(obj.model_dump(), indent=2))
    return {"ok": True}


# ---------- Historical (day + minute) ----------
@app.get("/api/v2/hist/bars")
def hist_bars(symbol: str = Query(...), date: str = Query(..., description="YYYY-MM-DD")):
    symbol = _clean_symbol(symbol)
    bars = get_bars_for_date(symbol, date)
    if not bars:
        raise HTTPException(status_code=404, detail="No bars recorded for this date.")
    return {"ok": True, "request_id": rid(), "data": {"bars": bars}}


@app.get("/api/v2/hist/analyze")
def hist_analyze(
    symbol: str = Query(...),
    date: str = Query(..., description="YYYY-MM-DD"),
    time_: str = Query(..., alias="time", pattern=r"^\d{2}:\d{2}$"),
):
    symbol = _clean_symbol(symbol)
    bars = get_bars_for_date(symbol, date)
    if not bars:
        raise HTTPException(status_code=404, detail="No bars recorded for this date.")
    upto = _slice_upto_hhmm(bars, time_)
    if not upto:
        raise HTTPException(status_code=400, detail="No bars up to given time.")
    snap = build_snapshot_at(symbol, upto)
    pol = load_policy_v2()
    out = analyze_snapshot(snap, pol)
    return {"ok": True, "request_id": rid(), "data": out}


@app.get("/api/v2/hist/whatif")
def hist_whatif(
    symbol: str = Query(...),
    date: str = Query(...),
    time_: str = Query(..., alias="time"),
    entry: float = Query(...),
    stop: float = Query(...),
    tp2: float = Query(...),
    risk_amt: float = Query(...),
    lot: int = Query(1, ge=1),
):
    res = whatif(entry, stop, tp2, risk_amt, lot)
    return {"ok": True, "request_id": rid(), "data": res}

# ---------- Historical backfill (one day, 1-min) ----------
from datetime import datetime as _dt
from zoneinfo import ZoneInfo as _Z
from .hist import write_bars_for_date  # we added this

def _split_symbol(sym: str) -> tuple[str,str]:
    s = _clean_symbol(sym)
    if ":" in s:
        ex, ts = s.split(":", 1)
        return ex, ts
    return "NSE", s

def _find_token(exchange: str, tradingsymbol: str) -> int | None:
    # 1) try Redis map populated by the ticker
    try:
        ts_full = f"{exchange}:{tradingsymbol}"
        tok = r.hget("inst:sym2token", ts_full)
        if tok:
            return int(tok)
    except Exception:
        pass
    # 2) fall back to scanning instruments from Kite
    try:
        ks = get_kite().kite
        inst = ks.instruments(exchange)
        # try exact match
        for it in inst:
            if str(it.get("tradingsymbol","")).upper() == tradingsymbol:
                return int(it.get("instrument_token"))
        # try ignoring suffixes like -BE/-BZ
        base = tradingsymbol.split("-")[0]
        for it in inst:
            ts = str(it.get("tradingsymbol","")).upper()
            if ts.split("-")[0] == base:
                return int(it.get("instrument_token"))
    except Exception:
        pass
    return None

@app.post("/api/v2/hist/backfill")
def hist_backfill(symbol: str = Query(..., description="EXCH:SYMBOL, e.g. NSE:INFY"),
                  date: str   = Query(..., description="YYYY-MM-DD")):
    """
    Fetch one trading day's 1-min bars from Kite and store under bars:<SYM>:<DATE>.
    Requires valid Zerodha session.
    """
    symbol = _clean_symbol(symbol)
    ex, ts = _split_symbol(symbol)
    tok = _find_token(ex, ts)
    if tok is None:
        raise HTTPException(status_code=404, detail=f"instrument token not found for {symbol}")

    # build time range in IST
    try:
        ist = IST
        start_ist = _dt.fromisoformat(f"{date}T09:15:00").replace(tzinfo=ist)
        end_ist   = _dt.fromisoformat(f"{date}T15:30:00").replace(tzinfo=ist)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid date; expected YYYY-MM-DD")

    ks = get_kite().kite
    try:
        data = ks.historical_data(
            instrument_token=tok,
            from_date=start_ist,
            to_date=end_ist,
            interval="minute",
            continuous=False,
            oi=False,
        )
    except TokenException as te:
        raise HTTPException(status_code=401, detail=f"Kite token invalid: {te}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Kite historical_data error: {e}")

    if not data:
        raise HTTPException(status_code=404, detail="no historical bars returned")

    # map to our shape and write
    bars = []
    for d in data:
        # Zerodha returns naive times in local tz or UTC depending on lib; handle both
        # Prefer ISO with IST offset for consistency with our reader
        # d keys: date, open, high, low, close, volume
        dt_obj = d.get("date")
        if isinstance(dt_obj, str):
            ts_iso = _dt.fromisoformat(dt_obj).astimezone(IST).replace(second=0, microsecond=0).isoformat()
        else:
            # assume datetime-like
            ts_iso = (dt_obj.astimezone(IST) if getattr(dt_obj, "tzinfo", None) else dt_obj.replace(tzinfo=IST)).replace(second=0, microsecond=0).isoformat()

        bars.append({
            "ts": ts_iso,
            "o": float(d.get("open", 0.0)),
            "h": float(d.get("high", 0.0)),
            "l": float(d.get("low", 0.0)),
            "c": float(d.get("close", 0.0)),
            "v": int(d.get("volume", 0)),
        })

    wrote = write_bars_for_date(symbol, date, bars)
    return {"ok": True, "symbol": symbol, "date": date, "count": wrote}



# ---------- Optional debug ----------
if DEBUG_ENABLED:

    @app.get("/debug/state")
    def debug_state():
        try:
            subs = _smembers_str(r.smembers("symbols:active"))
        except Exception:
            subs = []
        try:
            hb = _get_int(r.get("ticker:alive"), 0)
        except Exception:
            hb = 0
        return {
            "pinned": _smembers_str(r.smembers("cfg:pinned") or []),
            "universe_limit": _get_int(r.get("cfg:universe_limit"), DEFAULT_UNIVERSE_LIMIT),
            "symbols_active": subs,
            "ticker_alive": hb,
        }


