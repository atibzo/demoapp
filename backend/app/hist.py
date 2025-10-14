from __future__ import annotations
import json, math, datetime as dt, statistics
from typing import List, Dict, Any, Tuple, Optional

try:
    import redis  # redis-py
except Exception:
    redis = None

# -------- Redis helpers -------------------------------------------------------

def _get_redis() -> Optional["redis.Redis"]:
    if redis is None: 
        return None
    # docker-compose service name is "redis"
    return redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

def _bars_key(symbol: str, date_yyyy_mm_dd: str) -> str:
    return f"bars:{symbol}:{date_yyyy_mm_dd}"

def _snap_key(symbol: str, date_yyyy_mm_dd: str, hhmm: str) -> str:
    return f"snap:{symbol}:{date_yyyy_mm_dd}:{hhmm}"

# bulk writer for backfill
def write_bars_for_date(symbol: str, date_yyyy_mm_dd: str, bars: List[Dict[str, Any]]) -> int:
    """
    Overwrite bars:<SYM>:<DATE> with a full day of 1-min bars.
    Each item: {"ts": ISO8601, "o": float, "h": float, "l": float, "c": float, "v": int}
    """
    r = _get_redis()
    if not r: 
        return 0
    key = _bars_key(symbol, date_yyyy_mm_dd)
    # replace atomically
    pipe = r.pipeline()
    pipe.delete(key)
    if bars:
        pipe.rpush(key, *[json.dumps(b) for b in bars])
    pipe.expire(key, 14 * 24 * 3600)
    pipe.execute()
    return len(bars)


# -------- Public recording API (called by ticker) -----------------------------

def record_minute_bar(symbol: str, bar: Dict[str, Any]) -> None:
    """
    bar = {"ts": ISO8601, "o": float, "h": float, "l": float, "c": float, "v": int}
    Appends to a Redis list. Harmless no-op if redis isn't available.
    """
    r = _get_redis()
    if not r: 
        return
    ts = bar.get("ts")
    if not ts:
        # attach now in IST-ish for robustness
        ts = dt.datetime.utcnow().isoformat()
        bar["ts"] = ts
    date = bar["ts"][:10]
    key = _bars_key(symbol, date)
    r.rpush(key, json.dumps(bar))
    # keep at least 14 days; adjust to your taste
    r.expire(key, 14 * 24 * 3600)

# -------- Utilities -----------------------------------------------------------

def _parse_iso(ts: str) -> dt.datetime:
    # tolerant parse (no timezone)
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return dt.datetime.fromisoformat(ts.split(".")[0])

def _hhmm(d: dt.datetime) -> str:
    return f"{d.hour:02d}:{d.minute:02d}"

# -------- Bars loading --------------------------------------------------------

def get_bars_for_date(symbol: str, date_yyyy_mm_dd: str) -> List[Dict[str, Any]]:
    """Return list[bar] or [] if not recorded."""
    r = _get_redis()
    if not r:
        return []
    key = _bars_key(symbol, date_yyyy_mm_dd)
    raw = r.lrange(key, 0, -1)
    bars = [json.loads(x) for x in raw]
    # normalize numeric fields
    for b in bars:
        for k in ("o","h","l","c"):
            if k in b: b[k] = float(b[k])
        if "v" in b: b["v"] = int(b["v"])
    return bars

def _slice_upto_hhmm(bars: List[Dict[str,Any]], hhmm: str) -> List[Dict[str,Any]]:
    if not bars: return []
    end_ix = 0
    for i, b in enumerate(bars):
        t = _hhmm(_parse_iso(b["ts"]))
        if t <= hhmm:
            end_ix = i
        else:
            break
    return bars[:end_ix+1]

# -------- Indicators (pure-python; no numpy) ---------------------------------

def ema(values: List[float], length: int) -> List[float]:
    if length <= 1 or not values: 
        return values[:]
    k = 2.0/(length+1)
    out = []
    ema_prev = values[0]
    for i, v in enumerate(values):
        if i == 0:
            out.append(v)
        else:
            ema_prev = v*k + ema_prev*(1-k)
            out.append(round(ema_prev, 6))
    return out

def rsi(values: List[float], length: int=14) -> List[float]:
    if len(values) < length+1: 
        return [50.0]*len(values)
    gains, losses = [], []
    rsis = [50.0]*(length)  # warmup
    for i in range(1, len(values)):
        delta = values[i]-values[i-1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
        if i >= length:
            avg_gain = sum(gains[-length:])/length
            avg_loss = sum(losses[-length:])/length
            rs = (avg_gain / avg_loss) if avg_loss > 0 else 999.0
            rsis.append(100 - (100/(1+rs)))
    while len(rsis) < len(values): rsis.append(rsis[-1])
    return [round(x,2) for x in rsis]

def atr(bars: List[Dict[str,Any]], length: int=14) -> List[float]:
    if len(bars) < 2: 
        return [0.0]*len(bars)
    trs = []
    for i in range(len(bars)):
        if i==0:
            trs.append(bars[0]["h"] - bars[0]["l"])
            continue
        h, l, pc = bars[i]["h"], bars[i]["l"], bars[i-1]["c"]
        tr = max(h-l, abs(h-pc), abs(l-pc))
        trs.append(tr)
    out = []
    alpha = 1.0/length
    s = trs[0]
    for i, tr in enumerate(trs):
        if i==0:
            s = tr
        else:
            s = alpha*tr + (1-alpha)*s
        out.append(round(s, 6))
    return out

def vwap_series(bars: List[Dict[str,Any]]) -> List[float]:
    cum_pv = 0.0
    cum_v = 0.0
    out = []
    for b in bars:
        tp = (b["h"] + b["l"] + b["c"]) / 3.0
        v = b.get("v", 0)
        cum_pv += tp * v
        cum_v += v
        out.append(round(cum_pv / cum_v, 6) if cum_v>0 else b["c"])
    return out

def donchian(values_high: List[float], values_low: List[float], length: int=20) -> Tuple[List[float],List[float]]:
    up, dn = [], []
    for i in range(len(values_high)):
        lo = max(0, i-length+1)
        up.append(max(values_high[lo:i+1]))
        dn.append(min(values_low[lo:i+1]))
    return up, dn

def bbands(values: List[float], length: int=20, dev: float=2.0) -> Tuple[List[float],List[float],List[float]]:
    ma, up, dn = [], [], []
    for i in range(len(values)):
        lo = max(0, i-length+1)
        window = values[lo:i+1]
        mean = sum(window)/len(window)
        st = math.sqrt(sum((x-mean)**2 for x in window)/len(window))
        ma.append(mean); up.append(mean+dev*st); dn.append(mean-dev*st)
    return ma, up, dn

# -------- Policy defaults -----------------------------------------------------

DEFAULT_POLICY = {
    "weights": {"trend":1.0,"pullback":1.0,"vwap":1.0,"breakout":1.0,"volume":1.0},
    "thresholds": {
        "min_volx": 1.4,
        "vwap_reversion_max_dev": 0.6,  # in ATR
        "atr_mult_sl": 1.2,
        "rr_target": 1.6,
        "tp1_atr": 0.75,
        "tp2_atr": 1.5,
        "entry_chase_atr": 0.15,
        "stop_vwap_offset_atr": 0.5,
    },
    "entry_window": {"start":"11:00","end":"15:10"},
}

# Optional: pull v2 policy if your code has it, else fallback
def load_policy_v2() -> Dict[str,Any]:
    try:
        # circular import guard
        from .main import get_policy_v2_body  # helper we add below
        p = get_policy_v2_body()
        if isinstance(p, dict): 
            return p
    except Exception:
        pass
    return DEFAULT_POLICY

# -------- Snapshot + Analyze --------------------------------------------------

def build_snapshot_at(symbol: str, bars: List[Dict[str,Any]]) -> Dict[str,Any]:
    if not bars: 
        return {}
    c = [b["c"] for b in bars]
    h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]
    v = [b.get("v",0) for b in bars]

    ema9  = ema(c, 9)
    ema21 = ema(c, 21)
    rsi14 = rsi(c, 14)
    atr14 = atr(bars, 14)
    vwap  = vwap_series(bars)
    don_u, don_d = donchian(h, l, 20)
    bb_m, bb_u, bb_d = bbands(c, 20, 2.0)

    vol_med = statistics.median(v) if v else 0.0
    volx = (v[-1] / vol_med) if vol_med>0 else 0.0
    last = bars[-1]
    snap = {
        "symbol": symbol,
        "ts": last["ts"],
        "price": last["c"],
        "ema9": ema9[-1], "ema21": ema21[-1],
        "rsi14": rsi14[-1],
        "atr": atr14[-1],
        "vwap": vwap[-1],
        "minute_vol_multiple": round(volx, 2),
        "don_u": don_u[-1], "don_d": don_d[-1],
        "bb_m": bb_m[-1], "bb_u": bb_u[-1], "bb_d": bb_d[-1],
        "source": "historical"
    }
    return snap

def analyze_snapshot(snap: Dict[str,Any], policy: Dict[str,Any]) -> Dict[str,Any]:
    if not snap: 
        return {}
    th = policy.get("thresholds", {})
    w  = policy.get("weights", {})

    price = snap["price"]; atrv = max(snap["atr"], 1e-6)
    # Bias by EMA cross
    long_bias = snap["ema9"] > snap["ema21"]
    side = "BUY" if long_bias else "SELL"

    # Factors (simple, deterministic)
    f_trend = 1.0 if long_bias else -1.0
    f_vwap  = 1.0 if (long_bias and price>=snap["vwap"]) or ((not long_bias) and price<=snap["vwap"]) else -1.0
    # Pullback: prefer price within 0.4–0.8 ATR from VWAP
    dev_atr = abs(price - snap["vwap"]) / atrv
    f_pull  = 1.0 - min(abs(dev_atr-0.6)/0.6, 1.0)  # peak at 0.6×ATR
    # Breakout: closeness to Donchian boundary in direction of bias
    if long_bias:
        dist = max(snap["don_u"] - price, 0.0) / atrv
    else:
        dist = max(price - snap["don_d"], 0.0) / atrv
    f_break = 1.0 - min(dist/1.0, 1.0)
    # Volume factor
    f_vol = min(snap["minute_vol_multiple"]/ (th.get("min_volx",1.4)), 1.2)  # capped

    score = (
        w.get("trend",1.0)*f_trend +
        w.get("vwap",1.0)*f_vwap +
        w.get("pullback",1.0)*f_pull +
        w.get("breakout",1.0)*f_break +
        w.get("volume",1.0)*f_vol
    )
    # Confidence squashed to 0..1
    confidence = 1/(1+math.exp(-score))

    # Checks
    checks = {
        "VWAPΔ": dev_atr <= th.get("vwap_reversion_max_dev", 0.6),
        "VolX":  snap["minute_vol_multiple"] >= th.get("min_volx", 1.4),
    }

    # Bracket
    entry_chase = th.get("entry_chase_atr", 0.15)
    stop_off    = th.get("stop_vwap_offset_atr", 0.5)
    tp1_atr     = th.get("tp1_atr", 0.75)
    tp2_atr     = th.get("tp2_atr", 1.5)

    if long_bias:
        trigger = max(price, snap["don_u"])
        entry_lo, entry_hi = price - entry_chase*atrv, trigger
        stop   = min(snap["vwap"] - stop_off*atrv, price - th.get("atr_mult_sl",1.2)*atrv)
        tp1    = price + tp1_atr*atrv
        tp2    = price + tp2_atr*atrv
        invalid_if = "1-min close below EMA21"
    else:
        trigger = min(price, snap["don_d"])
        entry_lo, entry_hi = trigger, price + entry_chase*atrv
        stop   = max(snap["vwap"] + stop_off*atrv, price + th.get("atr_mult_sl",1.2)*atrv)
        tp1    = price - tp1_atr*atrv
        tp2    = price - tp2_atr*atrv
        invalid_if = "1-min close above EMA21"

    rr = abs((tp2 - price) / (price - stop)) if price!=stop else 0.0
    delta_trigger_bps = ( (trigger - price) / price ) * 1e4

    return {
        "decision": side,
        "confidence": round(confidence, 2),
        "bands": [round(entry_lo,2), round(entry_hi,2)],
        "action": {
            "trigger": round(trigger,2),
            "entry_range": [round(entry_lo,2), round(entry_hi,2)],
            "stop": round(stop,2),
            "tp1": round(tp1,2), "tp2": round(tp2,2),
            "invalid_if": invalid_if
        },
        "risk": {
            "atr": round(atrv, 4),
            "rr": round(rr, 2),
            "delta_trigger_bps": round(delta_trigger_bps, 1),
        },
        "why": {
            "trend": round(f_trend,2), "pullback": round(f_pull,2),
            "vwap": round(f_vwap,2), "breakout": round(f_break,2),
            "volume": round(f_vol,2),
            "checks": checks
        },
        "meta": {"age_s": 0, "regime": "Normal", "source": "historical"}
    }

# -------- What-if sizing ------------------------------------------------------

def whatif(entry: float, stop: float, tp2: float, risk_amt: float, lot: int=1) -> Dict[str,Any]:
    per_share = abs(entry - stop)
    qty = 0 if per_share<=0 else int(risk_amt // per_share)
    if lot>1 and qty>0: 
        qty = (qty//lot)*lot
    notional = qty * entry
    rr = 0.0 if per_share<=0 else abs((tp2 - entry)/per_share)
    return {
        "qty": qty, "notional": round(notional,2), "r": 1.0, "rr": round(rr,2),
        "fees": 0, "slip_mult_atr": 0.0, "expectancy": None
    }
