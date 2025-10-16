from __future__ import annotations
import os, sys, time, json, math, signal, threading
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import datetime as dt

from kiteconnect import KiteTicker, KiteConnect
from kiteconnect.exceptions import NetworkException, TokenException

from .rl import redis_client
from .kite import get_kite
from .hist import record_minute_bar

# ---------- Config ----------
IST = ZoneInfo("Asia/Kolkata")
EXCHANGES = [x.strip() for x in os.getenv("EXCHANGES", "NSE,BSE").split(",") if x.strip()]
UNIVERSE_DEFAULT = int(os.getenv("UNIVERSE_LIMIT", "200"))
ROTATE_INTERVAL_SEC = int(os.getenv("SUB_ROTATE_INTERVAL_SEC", "120"))
ROTATE_BATCH = int(os.getenv("SUB_ROTATE_BATCH", "25"))  # reserved for future batch swap
RANK_WINDOW_MIN = int(os.getenv("RANK_WINDOW_MIN", "10"))
BARS_CAP = int(os.getenv("BARS_CAP", "480"))  # ~ full day minutes
VWAP_ROLL_MIN = int(os.getenv("VWAP_ROLL_MIN", "60"))
VOL_BASELINE_MIN = int(os.getenv("VOL_BASELINE_MIN", "20"))
DONCHIAN_LEN = int(os.getenv("DONCHIAN_LEN", "20"))
BB_LEN = int(os.getenv("BB_LEN", "20"))
BB_STD = float(os.getenv("BB_STD", "2.0"))
ATR_LEN = int(os.getenv("ATR_LEN", "14"))
RSI_LEN = int(os.getenv("RSI_LEN", "14"))
EMA_FAST = int(os.getenv("EMA_FAST", "9"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "21"))
ORB_WINDOW_MIN = int(os.getenv("ORB_WINDOW_MIN", "30"))
HIST_BACKFILL_MIN = int(os.getenv("HIST_BACKFILL_MIN", "120"))
HIST_INTERVAL = os.getenv("HIST_INTERVAL", "minute")

MARKET_OPEN  = os.getenv("MARKET_OPEN",  "09:15")
MARKET_CLOSE = os.getenv("MARKET_CLOSE", "15:30")

# ---------- Data classes ----------
@dataclass
class Bar:
    t: int       # epoch seconds (minute start)
    o: float
    h: float
    l: float
    c: float
    v: float
    vwap_num: float  # sum(price*qty) in minute
    vwap_den: float  # sum(qty) in minute

# ---------- Utilities ----------
def now_s() -> int: return int(time.time())
def now_ms() -> int: return int(time.time() * 1000)
def ist_now() -> datetime: return datetime.now(tz=IST)

def parse_time_hhmm(s: str) -> Tuple[int, int]:
    hh, mm = s.strip().split(":")
    return int(hh), int(mm)

def is_market_open(ts: Optional[datetime] = None) -> bool:
    d = ts or ist_now()
    if d.weekday() >= 5:  # Sat/Sun
        return False
    oh, om = parse_time_hhmm(MARKET_OPEN)
    ch, cm = parse_time_hhmm(MARKET_CLOSE)
    start = d.replace(hour=oh, minute=om, second=0, microsecond=0)
    end = d.replace(hour=ch, minute=cm, second=0, microsecond=0)
    return start <= d <= end

# ---------- Indicator helpers ----------
class MinuteIndicators:
    """Rolling, per-token minute indicators."""
    def __init__(self):
        self.min_bars: Dict[int, deque] = defaultdict(lambda: deque(maxlen=BARS_CAP))
        self.close_hist: Dict[int, deque] = defaultdict(lambda: deque(maxlen=max(BB_LEN, RSI_LEN, EMA_SLOW, ATR_LEN, DONCHIAN_LEN)))
        self.tr_hist: Dict[int, deque] = defaultdict(lambda: deque(maxlen=ATR_LEN))
        self.vwap_roll: Dict[int, deque] = defaultdict(lambda: deque(maxlen=VWAP_ROLL_MIN))  # (num, den)
        self.vol_hist: Dict[int, deque] = defaultdict(lambda: deque(maxlen=VOL_BASELINE_MIN))
        self.ema_fast: Dict[int, float] = {}
        self.ema_slow: Dict[int, float] = {}
        self.avg_gain: Dict[int, float] = {}
        self.avg_loss: Dict[int, float] = {}
        self.orb_hi: Dict[int, float] = {}
        self.orb_lo: Dict[int, float] = {}
        self.open_minute: Optional[int] = None

    def on_minute_close(self, token: int, bar: Bar):
        self.min_bars[token].append(bar)
        self.close_hist[token].append(bar.c)

        prev = self.min_bars[token][-2] if len(self.min_bars[token]) >= 2 else None
        pc  = prev.c if prev else bar.c
        tr  = max(bar.h - bar.l, abs(bar.h - pc), abs(bar.l - pc))
        self.tr_hist[token].append(tr)

        self.vwap_roll[token].append((bar.vwap_num, bar.vwap_den))
        self.vol_hist[token].append(bar.v)

        minute_index = int(bar.t // 60)
        if self.open_minute is None:
            self.open_minute = minute_index
        if (minute_index - self.open_minute) < ORB_WINDOW_MIN:
            self.orb_hi[token] = max(self.orb_hi.get(token, bar.h), bar.h)
            self.orb_lo[token] = min(self.orb_lo.get(token, bar.l), bar.l)

        for ln, store in ((EMA_FAST, self.ema_fast), (EMA_SLOW, self.ema_slow)):
            k = 2 / (ln + 1)
            prev_ema = store.get(token, bar.c)
            store[token] = prev_ema + k * (bar.c - prev_ema)

        if prev:
            delta = bar.c - prev.c
            gain = max(delta, 0.0)
            loss = max(-delta, 0.0)
            ag = self.avg_gain.get(token, gain)
            al = self.avg_loss.get(token, loss)
            ag = (ag * (RSI_LEN - 1) + gain) / RSI_LEN
            al = (al * (RSI_LEN - 1) + loss) / RSI_LEN
            self.avg_gain[token] = ag
            self.avg_loss[token] = al

    def snapshot(self, token: int) -> Dict[str, Any]:
        bars = self.min_bars[token]
        if not bars:
            return {}
        last = bars[-1]

        # VWAP(60)
        num = sum(n for n, d in self.vwap_roll[token])
        den = sum(d for n, d in self.vwap_roll[token])
        vwap60 = (num / den) if den > 0 else last.c
        vwap_delta_pct = ((last.c - vwap60) / vwap60 * 100.0) if vwap60 else 0.0

        # BB(20,2)
        closes = list(self.close_hist[token])[-BB_LEN:]
        bb_mid = sum(closes) / len(closes) if closes else last.c
        variance = sum((x - bb_mid) ** 2 for x in closes) / len(closes) if closes else 0.0
        bb_std = math.sqrt(variance)
        bb_up = bb_mid + BB_STD * bb_std
        bb_lo = bb_mid - BB_STD * bb_std

        # ATR(14)
        trs = list(self.tr_hist[token])
        atr = (sum(trs) / len(trs)) if trs else 0.0

        # Donchian(20)
        recent = list(bars)[-DONCHIAN_LEN:]
        d_hi = max(b.h for b in recent) if recent else last.h
        d_lo = min(b.l for b in recent) if recent else last.l

        # RSI
        ag = self.avg_gain.get(token, 0.0)
        al = self.avg_loss.get(token, 1e-9)
        rs = (ag / al) if al > 0 else 0.0
        rsi = 100.0 - (100.0 / (1.0 + rs))

        # EMA
        ema9 = self.ema_fast.get(token, last.c)
        ema21 = self.ema_slow.get(token, last.c)

        # ORB
        orb_hi = self.orb_hi.get(token)
        orb_lo = self.orb_lo.get(token)

        # VolX baseline
        vol_hist = self.vol_hist[token]
        baseline = (sum(vol_hist) / len(vol_hist)) if vol_hist else 0.0
        volx = (last.v / baseline) if baseline > 0 else 0.0

        return {
            "price": round(last.c, 2),
            "last_price": round(last.c, 2),
            "last_close": round(last.c, 2),
            "vwap": round(vwap60, 2),
            "vwap_delta_pct": round(vwap_delta_pct, 2),
            "minute_vol_multiple": round(volx, 2),
            "vol_mult": round(volx, 2),
            "ema9": round(ema9, 2),
            "ema21": round(ema21, 2),
            "rsi14": round(rsi, 1),
            "bb_middle": round(bb_mid, 2),
            "bb_upper": round(bb_up, 2),
            "bb_lower": round(bb_lo, 2),
            "atr": round(atr, 2),
            "atr14": round(atr, 2),
            "donchian_hi": round(d_hi, 2),
            "donchian_upper": round(d_hi, 2),
            "donchian_lo": round(d_lo, 2),
            "donchian_lower": round(d_lo, 2),
            "orb_high": None if orb_hi is None else round(orb_hi, 2),
            "orb_low":  None if orb_lo is None else round(orb_lo, 2),
            "last_volume": round(last.v, 2),
        }

# ---------- Universe & tokens ----------
def load_instruments(kite: KiteConnect) -> Tuple[Dict[int, str], Dict[str, int]]:
    """
    Build maps for NSE/BSE equities.
    Accept: exchange in EXCHANGES AND instrument_type == 'EQ' AND segment != 'INDICES'
    Token: instrument_token (or instrumenttoken)
    """
    token2sym: Dict[int, str] = {}
    sym2token: Dict[str, int] = {}

    def norm_exchange(inst: dict) -> Optional[str]:
        ex = inst.get("exchange")
        if not ex:
            seg = inst.get("segment") or ""
            ex = seg.split("-")[0] if "-" in seg else (seg or None)
        return ex

    def get_token(inst: dict) -> Optional[int]:
        tok = inst.get("instrument_token", inst.get("instrumenttoken"))
        try:
            return int(tok)
        except Exception:
            return None

    def get_type(inst: dict) -> Optional[str]:
        return inst.get("instrument_type") or inst.get("instrumenttype")

    def get_segment(inst: dict) -> str:
        return inst.get("segment") or ""

    def maybe_add(inst: dict, expected_exch: str):
        ex  = norm_exchange(inst)
        seg = get_segment(inst)
        it  = get_type(inst)
        if ex != expected_exch:
            return
        # Equities only; skip indices (segment == 'INDICES')
        if it != "EQ" or seg == "INDICES":
            return
        tsym = inst.get("tradingsymbol")
        tok  = get_token(inst)
        if not (tsym and tok is not None):
            return
        sym = f"{expected_exch}:{tsym}"
        token2sym[tok] = sym
        sym2token[sym]  = tok

    # 1) Exchange-specific (preferred)
    for exch in EXCHANGES:
        try:
            rows = kite.instruments(exch)
        except Exception:
            rows = []
        for inst in rows or []:
            maybe_add(inst, exch)

    # 2) Fallback to all-instruments if still empty
    if not token2sym:
        try:
            rows = kite.instruments()
        except Exception:
            rows = []
        for inst in rows or []:
            ex = norm_exchange(inst)
            if ex in EXCHANGES:
                maybe_add(inst, ex or "")

    # Log counts for diagnostics
    print(f"[ticker] instruments loaded: {len(token2sym)} across {EXCHANGES}", file=sys.stderr)
    if token2sym:
        any_tok = next(iter(token2sym))
        print(f"[ticker] sample: {any_tok} -> {token2sym[any_tok]}", file=sys.stderr)

    return token2sym, sym2token

def compute_active(sym2token: Dict[str, int], r, limit: int) -> List[int]:
    pinned = sorted(list(r.smembers("cfg:pinned") or []))
    limit = int(r.get("cfg:universe_limit") or limit)
    active: List[int] = []
    for s in pinned:
        t = sym2token.get(s)
        if t and t not in active:
            active.append(t)
    if len(active) < limit:
        for s, t in sym2token.items():
            if t not in active:
                active.append(t)
                if len(active) >= limit:
                    break
    return active[:limit]

# ---------- Ticker Daemon ----------
class TickerDaemon:
    def __init__(self):
        self.r = redis_client(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        self.ks = get_kite()
        if not self.ks.access_token:
            raise RuntimeError("Kite session not ready. Login first.")
        self.kite = self.ks.kite

        self.token2sym, self.sym2token = load_instruments(self.kite)
        if not self.token2sym:
            raise RuntimeError(
                "No instruments loaded (token2sym empty). "
                "Check EXCHANGES env (e.g., NSE,BSE) and Kite entitlements/schema."
            )

        self.active_tokens: List[int] = compute_active(self.sym2token, self.r, UNIVERSE_DEFAULT)
        self.subscribed: set[int] = set()
        self.kws = KiteTicker(self.ks.api_key, self.ks.access_token, reconnect=True)
        self.ind = MinuteIndicators()
        self.current_bar: Dict[int, Bar] = {}
        self.turnover: Dict[int, deque] = defaultdict(lambda: deque(maxlen=RANK_WINDOW_MIN))
        self._stop = threading.Event()
        self._last_min = int(now_s() // 60)

        # Persist maps (guard empty)
        if self.token2sym:
            self.r.hset("inst:token2sym", mapping={str(k): v for k, v in self.token2sym.items()})
        if self.sym2token:
            self.r.hset("inst:sym2token", mapping={k: str(v) for k, v in self.sym2token.items()})
        self.r.delete("symbols:active")
        if self.active_tokens:
            self.r.sadd("symbols:active", *[self.token2sym[t] for t in self.active_tokens])

    # ------------- Backfill (historical_data) -------------
    def backfill(self):
        end = ist_now()
        start = end - timedelta(minutes=HIST_BACKFILL_MIN + 2)
        for t in self.active_tokens:
            sym = self.token2sym.get(t)
            if not sym:
                continue
            try:
                candles = self.kite.historical_data(
                    instrument_token=t,
                    from_date=start,
                    to_date=end,
                    interval=HIST_INTERVAL,
                    continuous=False,
                    oi=False,
                )
            except Exception:
                continue
            bars: List[Bar] = []
            for c in candles:
                ts = int(c["date"].timestamp())
                v  = float(c["volume"])
                px = float(c["close"])
                bars.append(Bar(
                    t=ts, o=float(c["open"]), h=float(c["high"]),
                    l=float(c["low"]), c=px, v=v,
                    vwap_num=px * v, vwap_den=v,
                ))
            for b in bars[-BARS_CAP:]:
                self.ind.on_minute_close(t, b)
                # Persist finalized historical minute bar (snap to IST minute-open)
                try:
                    ist_dt = dt.datetime.fromtimestamp(b.t, IST).replace(second=0, microsecond=0)
                    bar_doc = {
                        "ts": ist_dt.isoformat(),
                        "o": float(b.o), "h": float(b.h), "l": float(b.l), "c": float(b.c),
                        "v": int(b.v),
                    }
                    record_minute_bar(sym, bar_doc)
                except Exception:
                    pass
                self.r.lpush(f"bars:{sym}", json.dumps(b.__dict__))
                self.r.ltrim(f"bars:{sym}", 0, BARS_CAP - 1)
            if bars:
                snap = self.ind.snapshot(t)
                snap["ts_ms"] = int(bars[-1].t * 1000)
                self.r.setex(f"snap:{sym}", 3600, json.dumps(snap))

    # ------------- Subscriptions / rotation -------------
    def _subscribe_active(self):
        to_add = [t for t in self.active_tokens if t not in self.subscribed]
        if not to_add:
            return
        self.kws.subscribe(to_add)
        self.kws.set_mode(self.kws.MODE_FULL, to_add)
        self.subscribed.update(to_add)
        self.r.sadd("subs:tokens", *[str(t) for t in to_add])

    def _rotate_active(self):
        ranked = sorted(self.active_tokens, key=lambda t: sum(self.turnover[t]) if self.turnover[t] else 0.0, reverse=True)
        new_active = ranked[:len(self.active_tokens)]
        if set(new_active) == set(self.active_tokens):
            return
        remove = [t for t in self.subscribed if t not in new_active]
        add = [t for t in new_active if t not in self.subscribed]
        if add:
            self.kws.subscribe(add)
            self.kws.set_mode(self.kws.MODE_FULL, add)
            self.subscribed.update(add)
        if remove:
            self.kws.unsubscribe(remove)
            for t in remove:
                self.subscribed.discard(t)
        self.active_tokens = new_active
        self.r.delete("symbols:active")
        if self.active_tokens:
            self.r.sadd("symbols:active", *[self.token2sym[t] for t in self.active_tokens])

    # ------------- Tick / minute handling -------------
    def _on_ticks(self, ws, ticks):
        now = now_s()
        cur_min = int(now // 60)

        if cur_min != self._last_min:
            for t, bar in list(self.current_bar.items()):
                self.ind.on_minute_close(t, bar)
                sym = self.token2sym.get(t)
                if sym:
                    # Persist finalized live minute bar (minute-open boundary)
                    try:
                        ist_dt = dt.datetime.fromtimestamp(bar.t, IST).replace(second=0, microsecond=0)
                        bar_doc = {
                            "ts": ist_dt.isoformat(),  # "YYYY-MM-DDTHH:MM:00+05:30"
                            "o": float(bar.o), "h": float(bar.h),
                            "l": float(bar.l), "c": float(bar.c),
                            "v": int(bar.v),
                        }
                        record_minute_bar(sym, bar_doc)
                    except Exception:
                        pass

                    self.r.lpush(f"bars:{sym}", json.dumps(bar.__dict__))
                    self.r.ltrim(f"bars:{sym}", 0, BARS_CAP - 1)
                    self.turnover[t].append(bar.c * bar.v)
                    snap = self.ind.snapshot(t)
                    if snap:
                        snap["ts_ms"] = now_ms()
                        self.r.setex(f"snap:{sym}", 120, json.dumps(snap))
            self.current_bar.clear()
            self._last_min = cur_min
            if (now % ROTATE_INTERVAL_SEC) < 2:
                try:
                    self._rotate_active()
                except Exception:
                    pass

        self.r.set("ticker:alive", now)
        self.r.set("ticker:heartbeat", now_ms())  # Also update heartbeat for session_status
        for tk in ticks:
            token = tk.get("instrument_token")
            lp    = tk.get("last_price")
            qty   = tk.get("last_quantity") or 0
            if not token or lp is None:
                continue
            price = float(lp); qty = float(qty)

            bar = self.current_bar.get(token)
            if bar is None:
                bar = Bar(t=cur_min * 60, o=price, h=price, l=price, c=price, v=0.0, vwap_num=0.0, vwap_den=0.0)
                self.current_bar[token] = bar
            else:
                bar.h = max(bar.h, price)
                bar.l = min(bar.l, price)
                bar.c = price
            if qty > 0:
                bar.v += qty
                bar.vwap_num += price * qty
                bar.vwap_den += qty

            sym = self.token2sym.get(token)
            if sym:
                snap = {"last_price": round(price, 2), "ts_ms": now_ms()}
                prev = self.r.get(f"snap:{sym}")
                if prev:
                    try:
                        snap_prev = json.loads(prev)
                        for k, v in snap_prev.items():
                            if k not in snap:
                                snap[k] = v
                    except Exception:
                        pass
                self.r.setex(f"snap:{sym}", 120, json.dumps(snap))

    def _on_connect(self, ws, resp):
        try:
            self._subscribe_active()
            print(f"[ticker] subscribed {len(self.subscribed)} tokens", file=sys.stderr)
        except Exception as e:
            print("subscribe failed:", e, file=sys.stderr)

    def _on_close(self, ws, code, reason):
        self.r.set("ticker:alive", 0)

    def _on_error(self, ws, code, reason):
        self.r.set("ticker:alive", 0)

    def run(self):
        try:
            self.backfill()
        except Exception as e:
            print("Backfill failed:", e, file=sys.stderr)

        self.kws.on_ticks = self._on_ticks
        self.kws.on_connect = self._on_connect
        self.kws.on_close  = self._on_close
        self.kws.on_error  = self._on_error

        def stop_handler(*_):
            self._stop.set()
            try:
                self.kws.stop()
            except Exception:
                pass

        signal.signal(signal.SIGINT,  stop_handler)
        signal.signal(signal.SIGTERM, stop_handler)

        while not self._stop.is_set():
            try:
                self.kws.connect(threaded=False)
            except (NetworkException, TokenException) as e:
                print("WebSocket error, retrying:", e, file=sys.stderr)
                time.sleep(2)
            except Exception as e:
                print("Unexpected socket error:", e, file=sys.stderr)
                time.sleep(2)


def run():
    TickerDaemon().run()


if __name__ == "__main__":
    run()
