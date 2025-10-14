from __future__ import annotations
from typing import Any, Dict, List
import os, json, math, time
from .rl import redis_client


# ---------- helpers ----------
def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _safe(n, dflt: float = 0.0) -> float:
    try:
        f = float(n)
        # NaN check
        return dflt if f != f else f
    except Exception:
        return dflt

def _window_score(x: float, lo: float, hi: float) -> float:
    """
    Returns 0..1 for x fitting an ideal window [lo, hi] with a soft falloff.
    Inside the window gives >= 0.6 with a center bonus toward 1.0.
    """
    if hi <= lo:
        return 0.0
    if x < lo:
        # linear falloff below lo
        return max(0.0, 1.0 - (lo - x) / (lo if lo else 1e-9))
    if x > hi:
        # linear falloff above hi
        return max(0.0, 1.0 - (x - hi) / (hi if hi else 1e-9))
    # inside the window
    mid = (lo + hi) / 2.0
    return 0.6 + 0.4 * (1.0 - abs(x - mid) / (hi - lo))

def _side_align(value_signed: float, side: str, scale: float = 1.0) -> float:
    """
    Map a signed feature (e.g., VWAPΔ%) to [-1..+1] in the direction of side.
    scale is a divisor to normalize the magnitude before clamping.
    """
    if scale == 0:
        scale = 1.0
    sgn = 1.0 if side == "long" else -1.0
    return _clamp(sgn * (value_signed / scale), -1.0, 1.0)


# ---------- data access ----------
def minute_snapshot(symbol: str) -> Dict[str, Any]:
    r = redis_client(os.getenv("REDIS_URL"), decode_responses=True)
    raw = r.get(f"snap:{symbol}")
    if not raw:
        raise RuntimeError(f"live snapshot not available for {symbol}")
    snap = json.loads(raw)
    snap["fresh_ms"] = int(time.time()*1000) - int(snap.get("ts_ms", int(time.time()*1000)))
    return snap


# ---------- main planner ----------
def plan(universe: List[str], top_n: int = 30) -> List[Dict[str, Any]]:
    """
    Multi-factor scoring using live indicators from Redis snapshots.
    Score ∈ [0..100]. Higher = better intraday readiness.

    Factors (weights):
      • Trend: EMA9–EMA21 separation % (+18)
      • Volume: minute_vol_multiple capped at 3× (+20)
      • RSI alignment with side (±10)
      • VWAP alignment with side (±8)  [normalized at 0.8%]
      • Volatility fitness: ATR% ideal window 0.25%..1.2% (+6)
      • BB width fitness (squeeze/expansion 0.35%..1.5%) (+6)
      • Donchian proximity (≤0.25% of price) (+8)
      • ORB interaction proximity (≤0.30% of price) (+6)

    Readiness:
      • 'enter' if score ≥ 62 AND VolX ≥ 1.2 AND
        (near VWAP (|VWAPΔ|≤0.25%) OR near Donchian (≤0.25%) OR touches ORB band)
      • else 'wait'
    """
    r = redis_client(os.getenv("REDIS_URL"), decode_responses=True)
    rows: List[Dict[str, Any]] = []

    for sym in universe[:2000]:
        raw = r.get(f"snap:{sym}")
        if not raw:
            continue
        s = json.loads(raw)

        # --- base indicators (safe-cast) ---
        ema9   = _safe(s.get("ema9"))
        ema21  = _safe(s.get("ema21"))
        rsi    = _safe(s.get("rsi14"), 50.0)
        volx   = _safe(s.get("minute_vol_multiple"))
        vwapd  = _safe(s.get("vwap_delta_pct"))           # %
        last   = _safe(s.get("last_close")) or _safe(s.get("bb_middle")) or _safe(s.get("ema21"), 1.0)
        bb_lo  = _safe(s.get("bb_lower"), last * 0.99)
        bb_up  = _safe(s.get("bb_upper"), last * 1.01)
        dc_lo  = _safe(s.get("donchian_lo"), bb_lo)
        dc_hi  = _safe(s.get("donchian_hi"), bb_up)
        atr    = _safe(s.get("atr14"))
        orb_hi = _safe(s.get("orb_high"))
        orb_lo = _safe(s.get("orb_low"))

        # --- derived ---
        side = "long" if ema9 >= ema21 else "short"
        mid  = last if last else (ema21 or 1.0)

        # separation in %
        try:
            ema_delta_pct = abs((ema9 - ema21) / mid * 100.0)
        except Exception:
            ema_delta_pct = 0.0

        # Percent widths/volatility
        try:
            bb_width_pct = abs((bb_up - bb_lo) / mid * 100.0)
        except Exception:
            bb_width_pct = 0.0
        try:
            atr_pct = abs(atr / mid * 100.0)
        except Exception:
            atr_pct = 0.0

        # Proximities for Donchian/ORB (in % of price)
        try:
            prox_hi = abs(dc_hi - last) / mid * 100.0
        except Exception:
            prox_hi = 999.0
        try:
            prox_lo = abs(last - dc_lo) / mid * 100.0
        except Exception:
            prox_lo = 999.0
        don_prox = min(prox_hi, prox_lo)

        orb_prox = 999.0
        if orb_hi and orb_lo:
            try:
                orb_prox = min(abs(orb_hi - last), abs(last - orb_lo)) / mid * 100.0
            except Exception:
                orb_prox = 999.0

        # --- component scores ---
        # Trend (0..2%) → 0..18
        trend_score = _clamp(ema_delta_pct, 0.0, 2.0) * 9.0  # 0..18

        # Volume (0..3×) → 0..20
        vol_score   = _clamp(volx, 0.0, 3.0) * (20.0 / 3.0)

        # RSI alignment with side (±10)
        rsi_dir    = (rsi - 50.0) / 50.0  # -1..+1
        rsi_score  = _side_align(rsi_dir, side) * 10.0

        # VWAP alignment with side (±8) normalized at 0.8% deviation
        vwap_align = _side_align(vwapd, side, scale=0.8)     # -1..+1 when |VWAPΔ|=0.8%
        vwap_score = vwap_align * 8.0

        # Volatility fitness (0.25%..1.2%) → up to +6
        vol_fit = _window_score(atr_pct, 0.25, 1.2) * 6.0

        # BB width fitness (0.35%..1.5%) → up to +6
        bb_fit = _window_score(bb_width_pct, 0.35, 1.5) * 6.0

        # Donchian proximity (≤0.25%) → up to +8
        don_score = _clamp(0.25 - don_prox, 0.0, 0.25) / 0.25 * 8.0

        # ORB interaction (≤0.30%) → up to +6
        orb_score = _clamp(0.30 - orb_prox, 0.0, 0.30) / 0.30 * 6.0

        # --- total score ---
        base  = 50.0
        score = base + trend_score + vol_score + rsi_score + vwap_score + vol_fit + bb_fit + don_score + orb_score
        score = _clamp(round(score, 1), 0.0, 100.0)

        # --- readiness ---
        near_vwap = abs(vwapd) <= 0.25
        near_dc   = don_prox <= 0.25
        orb_touch = (orb_score > 0.0)
        readiness = "enter" if (score >= 62.0 and volx >= 1.2 and (near_vwap or near_dc or orb_touch)) else "wait"

        checks = {
            "vwapRespect": (vwap_align >= 0.0),
            "VolX": (volx >= 1.1),
            "nearVWAP": near_vwap,
            "nearDonchian": near_dc,
            "orb": orb_touch,
        }

        rows.append({
            "strategy": "Ensemble",
            "symbol": sym,
            "side": side,
            "score": score,
            "readiness": readiness,
            "bands": {
                "upper": round(bb_up if bb_up else dc_hi, 2),
                "lower": round(bb_lo if bb_lo else dc_lo, 2),
            },
            "checks": checks,
            "note": "",
        })

    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows[:top_n]
