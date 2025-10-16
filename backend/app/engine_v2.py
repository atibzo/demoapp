from __future__ import annotations
import json, os, math, time, statistics
from typing import Dict, List, Tuple, Optional
from zoneinfo import ZoneInfo
import redis
from kiteconnect.exceptions import TokenException
from .kite import get_kite

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
IST = ZoneInfo("Asia/Kolkata")
def r() -> redis.Redis: return redis.from_url(REDIS_URL, decode_responses=True)
def now_ms() -> int: return int(time.time() * 1000)

def market_open_ist() -> bool:
    """Check if market is currently open in IST"""
    from datetime import datetime
    now = datetime.now(tz=IST)
    if now.weekday() >= 5:  # Weekend
        return False
    minutes = now.hour * 60 + now.minute
    open_m = 9 * 60 + 15   # 09:15
    close_m = 15 * 60 + 30  # 15:30
    return open_m <= minutes <= close_m

# --- policy in Redis (source of truth) ---
def _load_policy_file() -> Dict:
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "policy.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def load_policy() -> Tuple[Dict, int]:
    rd = r()
    raw = rd.get("policy:current")
    rev = int(rd.get("policy:rev") or 0)
    if raw:
        return json.loads(raw), rev
    pf = _load_policy_file()     # first run: hydrate from file
    rd.set("policy:current", json.dumps(pf))
    rd.set("policy:rev", 1)
    return pf, 1

def save_policy(new_body: Dict) -> int:
    rd = r()
    rd.set("policy:current", json.dumps(new_body))
    return int(rd.incr("policy:rev"))

# --- helpers ---
def window_status(pol: Dict) -> str:
    from datetime import datetime
    now = datetime.now(tz=IST)
    hhmm = f"{now.hour:02d}:{now.minute:02d}"
    start = pol.get("entry_window", {}).get("start", "11:00")
    end   = pol.get("entry_window", {}).get("end", "15:10")
    if hhmm < start: return "early"
    if hhmm > end:   return "closed"
    return "ok"

def list_active_symbols() -> List[str]:
    return sorted(list(r().smembers("symbols:active") or []))

def read_snap(sym: str) -> Optional[Dict]:
    raw = r().get(f"snap:{sym}")
    if not raw: return None
    j = json.loads(raw)
    j["_age_s"] = max(0.0, (now_ms() - float(j.get("ts_ms", now_ms()))) / 1000.0)
    return j

# --- simple scoring (bounded factors) ---
def _side(ema9, ema21) -> str: return "long" if (ema9 or 0) >= (ema21 or 0) else "short"
def _regime(atr, price) -> str:
    try:
        rv = (atr or 0) / max(1e-6, (price or 1))
        return "Calm" if rv < 0.006 else ("Hot" if rv > 0.018 else "Normal")
    except: return "Normal"

def _trigger(side, ema9, don_l, don_u):
    if side == "long":
        c = [v for v in [don_u, ema9] if isinstance(v, (int,float))]
        return max(c) if c else None
    c = [v for v in [don_l, ema9] if isinstance(v, (int,float))]
    return min(c) if c else None

def _factors(s: Dict, pol: Dict) -> Dict[str, float]:
    price = s.get("price") or s.get("last_price") or s.get("last_close") or 0
    atr = s.get("atr") or s.get("atr14") or 1.0
    ema9 = s.get("ema9") or 0
    ema21 = s.get("ema21") or 0
    vwap = s.get("vwap") or price
    
    def squash(x, lo, hi):
        try:
            x = max(lo, min(hi, x)); return (x - lo) / (hi - lo)
        except: return 0.0
    
    trend = squash(((ema9 or 0)-(ema21 or 0))/max(1e-6, (atr or 1.0)), -1.0, 1.0)
    pull  = math.exp(-((abs((price or 0)-(ema9 or 0))/max(1e-6,(atr or 1.0))))**2)
    vwd   = abs((price or 0)-(vwap or 0))/max(1e-6,(atr or 1.0))
    vwap_align = 1.0 - squash(vwd, 0.0, 2.0)
    don_l = s.get("donch_lo") or s.get("donchian_lower") or s.get("donchian_lo") or price
    don_u = s.get("donch_hi") or s.get("donchian_upper") or s.get("donchian_hi") or price
    side = _side(ema9, ema21)
    if side == "long":
        prox = 1.0 - squash(abs((don_u or 0)-(price or 0))/max(1e-6,(atr or 1.0)), 0.0, 2.0)
    else:
        prox = 1.0 - squash(abs((price or 0)-(don_l or 0))/max(1e-6,(atr or 1.0)), 0.0, 2.0)
    breakout = max(0.0, prox)
    volx = s.get("vol_mult") or s.get("minute_vol_multiple") or 1.0
    volume = squash(volx, 0.5, 2.0)
    return {"trend":float(trend),"pullback":float(pull),"vwap":float(vwap_align),"breakout":float(breakout),"volume":float(volume)}

def _score_conf(factors: Dict[str,float], pol: Dict, regime: str, fresh_ok: bool, liq_ok: bool) -> Tuple[float,float]:
    w = pol.get("weights", {})
    num = (w.get("trend",1)*factors["trend"] + w.get("pullback",0.6)*factors["pullback"] +
           w.get("vwap",0.8)*factors["vwap"] + w.get("breakout",0.7)*factors["breakout"] +
           w.get("volume",0.6)*factors["volume"])
    den = (w.get("trend",1)+w.get("pullback",0.6)+w.get("vwap",0.8)+w.get("breakout",0.7)+w.get("volume",0.6))
    score = 100.0 * num / max(1e-6, den)
    
    # Better confidence calculation: base confidence from factors
    caps = pol.get("regime_caps", {"Calm":0.9,"Normal":0.8,"Hot":0.6})
    regime_cap = float(caps.get(regime, 0.8))
    
    # Base confidence from normalized factors (0..1 range)
    base_conf = num / max(1e-6, den)  # This gives 0..1 range since factors are 0..1
    
    # Apply regime cap
    conf = min(base_conf, regime_cap)
    
    # Apply penalties instead of hard caps
    if not fresh_ok:
        conf *= 0.3  # Significant penalty for stale data
    if not liq_ok:
        conf *= 0.7  # Moderate penalty for liquidity issues (not a hard cap)
    
    # Ensure confidence is in valid range
    conf = max(0.0, min(1.0, float(conf)))
    
    return float(score), float(conf)

def _universe_soft_reason(sym: str, pol: Dict) -> Optional[str]:
    """
    Check if a symbol is suitable for intraday trading in Top Algos.
    Uses strict filtering to ensure only high-liquidity, intraday-suitable stocks.
    
    Returns:
        Reason string if not suitable, None if suitable
    """
    from .universe import get_non_intraday_reason
    
    mode = (pol.get("universe", {}).get("mode") or "strict").lower()
    if mode == "off": 
        return None
    
    # Check custom exclude patterns from policy
    pats = pol.get("universe", {}).get("exclude_patterns", [])
    if any(pat in sym for pat in pats):
        return "non_intraday" if mode in ("strict", "soft") else None
    
    # Use comprehensive intraday check from universe module
    reason = get_non_intraday_reason(sym)
    if reason:
        # In strict mode, block completely
        # In soft mode, show but mark as blocked
        return reason if mode in ("strict", "soft") else None
    
    return None

def plan(top_n: int = 10) -> Tuple[List[Dict], Dict]:
    pol, rev = load_policy()
    staleness = int(pol.get("staleness_s", 10))
    wstatus = window_status(pol)
    rows, ages = [], []

    for sym in list_active_symbols():
        s = read_snap(sym)
        if not s: continue
        ages.append(s["_age_s"])
        price, atr, ema9, ema21 = s.get("price") or s.get("last_price"), s.get("atr"), s.get("ema9"), s.get("ema21")
        don_l, don_u = s.get("donch_lo") or s.get("donchian_lower"), s.get("donch_hi") or s.get("donchian_upper")
        side = _side(ema9, ema21)
        regime = _regime(atr, price)
        factors = _factors(s, pol)
        fresh_ok = s["_age_s"] <= staleness
        liq_reason = _universe_soft_reason(sym, pol)
        liq_ok = liq_reason is None
        score, conf = _score_conf(factors, pol, regime, fresh_ok, liq_ok)
        trig = _trigger(side, ema9, don_l, don_u)
        d_bps = None if trig is None or not price else round(abs(trig-price)/price*10000.0, 1)

        readiness, block_reason = "Wait", None
        if not fresh_ok: readiness, block_reason = "Stale", "stale"
        elif wstatus != "ok": readiness, block_reason = "Blocked", f"window:{wstatus}"
        elif not liq_ok: readiness, block_reason = "Blocked", liq_reason
        elif d_bps is not None: readiness = "Ready" if d_bps <= 20 else ("Near" if d_bps <= 60 else "Wait")

        rows.append({
            "symbol": sym, "side": side, "score": round(score,1), "confidence": round(conf,2),
            "age_s": round(s["_age_s"],1), "regime": regime, "delta_trigger_bps": d_bps,
            "readiness": readiness, "block_reason": block_reason,
            "checks": {"VWAPΔ": factors["vwap"] >= 0.5, "VolX": (s.get("vol_mult") or 1.0) >= 1.0, "Liquidity": liq_ok}
        })

    rows.sort(key=lambda x: x["score"], reverse=True)
    p95 = (statistics.quantiles(ages, n=20)[-1] if ages else 0.0)
    return rows[:top_n], {"rev": rev, "snapshot_p95_age_s": p95, "window_status": wstatus}

def analyze(symbol: str) -> Dict:
    pol, rev = load_policy()
    sym = symbol.replace(" ", "").upper()
    s = read_snap(sym)
    if not s:
        return {"decision":"WAIT","score":0.0,"confidence":0.0,"bands":[1.0, 1.0],"action":{},"risk":{"atr":0.0,"rr":0.0,"delta_trigger_bps":0.0},"why":{"trend":0,"pullback":0,"vwap":0,"breakout":0,"volume":0,"checks":{}},"meta":{"age_s":None,"regime":"Normal","liquidity_ok":False}}
    price, atr, ema9, ema21, vwap = s.get("price") or s.get("last_price"), s.get("atr") or s.get("atr14"), s.get("ema9"), s.get("ema21"), s.get("vwap")
    don_l, don_u = s.get("donch_lo") or s.get("donchian_lower") or s.get("donchian_lo"), s.get("donch_hi") or s.get("donchian_upper") or s.get("donchian_hi")
    side = _side(ema9, ema21); regime = _regime(atr, price)
    factors = _factors(s, pol)
    fresh_ok = s["_age_s"] <= int(pol.get("staleness_s", 10))
    liq_ok = _universe_soft_reason(sym, pol) is None
    score, conf = _score_conf(factors, pol, regime, fresh_ok, liq_ok)

    # bracket
    b = pol.get("bracket", {})
    entry_chase = float(b.get("entry_chase_atr", 0.15)); tp1_atr = float(b.get("tp1_atr", 0.75))
    tp2_atr = float(b.get("tp2_atr", 1.5)); stop_off = float(b.get("stop_vwap_offset_atr", 0.5))
    trig = _trigger(side, ema9, don_l, don_u)
    action = {}
    delta_trigger_bps = 0.0
    if trig is not None and atr and price:
      delta_trigger_bps = abs(trig - price) / max(1e-6, price) * 10000.0
      if side == "long":
        action = {"trigger": round(trig,2), "entry_range":[round(trig,2), round(trig+entry_chase*atr,2)], "stop": round((vwap or price)-stop_off*atr,2), "tp1": round(trig+tp1_atr*atr,2), "tp2": round(trig+tp2_atr*atr,2), "invalid_if":"1-min close below EMA21"}
      else:
        action = {"trigger": round(trig,2), "entry_range":[round(trig-entry_chase*atr,2), round(trig,2)], "stop": round((vwap or price)+stop_off*atr,2), "tp1": round(trig-tp1_atr*atr,2), "tp2": round(trig-tp2_atr*atr,2), "invalid_if":"1-min close above EMA21"}
    
    # Calculate risk:reward ratio
    rr = 0.0
    if action and action.get("stop") and action.get("tp2"):
        entry_mid = sum(action["entry_range"]) / 2.0 if action.get("entry_range") else action.get("trigger", 0)
        risk_amt = abs(entry_mid - action["stop"])
        reward_amt = abs(action["tp2"] - entry_mid)
        rr = reward_amt / max(1e-6, risk_amt)

    return {
      "decision": "BUY" if (action and side=="long") else ("SELL" if (action and side=="short") else "WAIT"),
      "score": round(score,2), "confidence": round(conf,2),
      "bands": [round(don_l or price, 2), round(don_u or price, 2)],
      "action": action,
      "risk": {
          "atr": round(atr or 0.0, 2),
          "rr": round(rr, 2),
          "delta_trigger_bps": round(delta_trigger_bps, 1)
      },
      "why": {**factors, "checks":{"VWAPΔ": factors["vwap"]>=0.5, "VolX": (s.get("vol_mult") or s.get("minute_vol_multiple") or 1.0)>=1.0}},
      "meta": {"age_s": round(s["_age_s"],1), "regime": regime, "liquidity_ok": liq_ok, "source": "live"}
    }

def session_status() -> Dict:
    pol, rev = load_policy()
    rd = r()
    hb = rd.get("ticker:heartbeat")
    ticker = bool(hb and (now_ms() - int(hb)) < 15000)

    # Validate Zerodha token by calling profile() when an access_token exists.
    try:
        ks = get_kite()
        zerodha_ok = bool(getattr(ks, "access_token", None))
        if zerodha_ok:
            try:
                ks.kite.profile()
            except TokenException:
                zerodha_ok = False
            except Exception:
                # Non-auth errors shouldn't flip login status
                pass
    except Exception:
        zerodha_ok = False

    llm = bool(os.environ.get("OPENAI_API_KEY"))
    ages = []
    for sym in rd.smembers("symbols:active") or []:
        s = read_snap(sym)
        if s:
            ages.append(s["_age_s"])
    p95 = (statistics.quantiles(ages, n=20)[-1] if ages else 0.0)

    return {
        "zerodha": zerodha_ok,
        "ticker": ticker,
        "llm": llm,
        "logged_in": zerodha_ok,
        "market_open": market_open_ist(),
        "window_status": window_status(pol),
        "degraded": bool(p95 and p95 > pol.get("staleness_s", 10)),
        "snapshot_p95_age_s": round(p95 or 0.0, 1),
        "time_ist": time.strftime("%H:%M:%S", time.localtime()),
        "rev": rev,
    }
