import os
import json
from openai import OpenAI
from .rl import redis_client

# OpenAI client + model (expects OPENAI_API_KEY and OPENAI_MODEL=gpt-5 in env)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def _first_text_from_response(resp) -> str:
    """
    Robustly extract text from Responses API objects across SDK variants.
    """
    txt = (getattr(resp, "output_text", None) or "").strip()
    if txt:
        return txt
    # Fallbacks for older SDK shapes
    for attr in ("output", "content", "data"):
        part = getattr(resp, attr, None)
        if not part:
            continue
        try:
            if hasattr(part, "__iter__"):
                for p in part:
                    t = getattr(p, "text", None)
                    if t:
                        return (t or "").strip()
        except Exception:
            pass
    return ""


def _safe(x, d=0.0):
    try:
        f = float(x)
        return d if f != f else f  # NaN -> default
    except Exception:
        return d


def hint(metric: str, context: dict) -> str:
    """
    One short numeric sentence. Cached 5m (non-empty) / 30s (empty).
    Uses Responses API (max_output_tokens) — compatible with gpt-5.
    """
    r = redis_client()
    key = f"hint:v2:{metric}:{hash(json.dumps(context, sort_keys=True))}"
    cached = r.get(key)
    if cached is not None:
        return cached

    prompt = (
        f"In ONE short sentence, explain the metric '{metric}' using ONLY the numbers below. "
        f"Be precise and numeric.\nContext JSON: {json.dumps(context, sort_keys=True)}"
    )

    try:
        resp = client.responses.create(
            model=MODEL,
            input=prompt,
            max_output_tokens=60,
            temperature=0.1,
        )
        text = _first_text_from_response(resp)
    except Exception:
        text = ""

    # cache policy: non-empty for 5m; empty for 30s to recover quickly
    if text:
        r.setex(key, 300, text)
    else:
        r.setex(key, 30, "")
    return text


def analyze(symbol: str, snapshot: dict) -> dict:
    """
    Deterministic, JSON-shaped analysis. Cached 60s.
    Uses Responses API with JSON output; if parsing fails, synthesize
    a non-generic verdict + data-driven confidence from indicators.
    """
    r = redis_client()
    key = f"analyze:v4:{symbol}:{hash(json.dumps(snapshot, sort_keys=True))}"
    cached = r.get(key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    prompt = (
        "Decide long/short/skip for the symbol below, based ONLY on the numeric snapshot. "
        "Return strict JSON with fields exactly: "
        '{"decision":"long|short|skip","bands":[lower,upper],"confidence":0..1,"checks":{}}. '
        f"Symbol: {symbol}\nSnapshot: {json.dumps(snapshot, sort_keys=True)}"
    )

    data = None
    try:
        resp = client.responses.create(
            model=MODEL,
            input=prompt,
            response_format={"type": "json_object"},
            max_output_tokens=300,
            temperature=0.0,
        )
        txt = _first_text_from_response(resp)
        if txt:
            maybe = json.loads(txt)
            if isinstance(maybe, dict):
                # If model provided confidence, clamp and return directly
                if "confidence" in maybe:
                    try:
                        c = float(maybe["confidence"])
                        c = max(0.45, min(0.85, round(c, 2)))
                        maybe["confidence"] = c
                        r.setex(key, 60, json.dumps(maybe))
                        return maybe
                    except Exception:
                        pass
                data = maybe
    except Exception:
        data = None

    # ---------- Deterministic fallback (data-driven confidence) ----------
    if not data:
        bb_lo = _safe(snapshot.get("bb_lower"))
        bb_up = _safe(snapshot.get("bb_upper"))
        dc_lo = _safe(snapshot.get("donchian_lo"))
        dc_hi = _safe(snapshot.get("donchian_hi"))
        ema9  = _safe(snapshot.get("ema9"))
        ema21 = _safe(snapshot.get("ema21"))
        rsi   = _safe(snapshot.get("rsi14"), 50.0)
        volx  = _safe(snapshot.get("minute_vol_multiple"), 0.0)
        last  = _safe(snapshot.get("last_close"))
        atr   = _safe(snapshot.get("atr14"), 0.0)
        mid   = _safe(snapshot.get("bb_middle")) or last or ema21 or 1.0

        # Bands from BB -> Donchian -> last ± ATR guard
        lo = bb_lo if bb_lo else (dc_lo if dc_lo else (last - max(atr, 0.01) if last else 1.0))
        hi = bb_up if bb_up else (dc_hi if dc_hi else (last + max(atr, 0.01) if last else 1.0))
        if hi == lo and last:
            hi = last + max(atr, 0.01)
            lo = last - max(atr, 0.01)

        # Direction from EMAs (no hard vol gate)
        decision = "skip"
        if ema9 and ema21:
            if ema9 > ema21:
                decision = "long"
            elif ema9 < ema21:
                decision = "short"

        # --- Confidence: calibrated 0.45..0.85 from multiple signals (no hacks) ---
        # EMA separation strength (0..1) with 1% cap
        try:
            ema_sep_pct = abs((ema9 - ema21) / mid * 100.0) if (ema9 and ema21) else 0.0
        except Exception:
            ema_sep_pct = 0.0
        ema_strength = min(ema_sep_pct / 1.0, 1.0)

        # RSI tilt strength (0..1) : 25 pts from 50 maps to 1.0
        rsi_strength = min(abs(rsi - 50.0) / 25.0, 1.0) if rsi else 0.0

        # BB width strength (peak at ~0.9%, window 0.35..1.5%)
        bbw_strength = 0.0
        try:
            if bb_up and bb_lo and bb_up > bb_lo:
                bbw_pct = abs(bb_up - bb_lo) / mid * 100.0
                if 0.35 < bbw_pct < 1.5:
                    peak = 0.9
                    rng_half = (1.5 - 0.35) / 2.0
                    bbw_strength = max(0.0, 1.0 - abs(bbw_pct - peak) / rng_half)
        except Exception:
            bbw_strength = 0.0

        # ATR% strength (window 0.25..1.2%)
        atr_strength = 0.0
        try:
            atr_pct = (atr / mid * 100.0) if (atr and mid) else 0.0
            if 0.25 < atr_pct < 1.2:
                center = (0.25 + 1.2) / 2.0
                rng_half = (1.2 - 0.25) / 2.0
                atr_strength = max(0.0, 1.0 - abs(atr_pct - center) / rng_half)
        except Exception:
            atr_strength = 0.0

        # VWAP alignment strength in direction of decision (±0.8% cap)
        vwap_align_strength = 0.0
        try:
            vwapd = snapshot.get("vwap_delta_pct")
            want = 1 if decision == "long" else (-1 if decision == "short" else 0)
            if want != 0 and isinstance(vwapd, (int, float)):
                v = max(-0.8, min(0.8, vwapd))
                vwap_align_strength = max(0.0, (want * v) / 0.8)
        except Exception:
            vwap_align_strength = 0.0

        # Volume strength (0..1 for 0..3x)
        vol_strength = min(max(volx, 0.0), 3.0) / 3.0

        # Weights sum to 1.0 (tune if needed)
        w_ema, w_rsi, w_bbw, w_atr, w_vwap, w_vol = 0.35, 0.20, 0.15, 0.10, 0.10, 0.10
        signal = (
            w_ema  * ema_strength +
            w_rsi  * rsi_strength +
            w_bbw  * bbw_strength +
            w_atr  * atr_strength +
            w_vwap * vwap_align_strength +
            w_vol  * vol_strength
        )  # 0..1

        base = 0.56 if decision != "skip" else 0.50  # mild directional premium
        conf = base + 0.28 * signal                  # 0.50..0.84 typical
        conf = max(0.45, min(0.85, round(conf, 2)))

        data = {
            "decision": decision,
            "bands": [round(lo, 2), round(hi, 2)],
            "confidence": conf,
            "checks": {
                "ema_cross": (ema9 > ema21) if (ema9 and ema21) else None,
                "volx": volx,
            },
        }

    r.setex(key, 60, json.dumps(data))
    return data
