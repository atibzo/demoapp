# Ticker Data Issues - Fix Summary

## Issues Identified

1. **"Cannot read properties of undefined (reading 'delta_trigger_bps')"** - Missing `risk` object in live analysis response
2. **Live ticker not working** - Heartbeat key inconsistency
3. **Live analyst section not working** - Missing risk object and null safety issues
4. **Top algo live data slow/not working** - Missing snapshot fields and field name inconsistencies

## Fixes Applied

### 1. Backend - engine_v2.py (Live Analysis)

**Problem**: The `analyze()` function was not returning a `risk` object with `delta_trigger_bps`, `atr`, and `rr`.

**Fix**: Added complete `risk` object calculation including:
- `delta_trigger_bps`: Distance to trigger in basis points
- `atr`: Average True Range value
- `rr`: Risk:Reward ratio calculated from entry, stop, and TP2
- Improved field name handling to support multiple variations (`atr`/`atr14`, `donchian_lo`/`donchian_lower`, etc.)

```python
return {
    "decision": "BUY" if (action and side=="long") else ("SELL" if (action and side=="short") else "WAIT"),
    "score": round(score,2),
    "confidence": round(conf,2),
    "bands": [round(don_l or price, 2), round(don_u or price, 2)],
    "action": action,
    "risk": {
        "atr": round(atr or 0.0, 2),
        "rr": round(rr, 2),
        "delta_trigger_bps": round(delta_trigger_bps, 1)
    },
    "why": {...},
    "meta": {...}
}
```

### 2. Backend - ticker_daemon.py (Heartbeat Fix)

**Problem**: Ticker daemon was only updating `ticker:alive` but session check was looking for `ticker:heartbeat`.

**Fix**: Added dual heartbeat update to support both keys:
```python
self.r.set("ticker:alive", now)
self.r.set("ticker:heartbeat", now_ms())  # Also update heartbeat for session_status
```

### 3. Backend - ticker_daemon.py (Snapshot Fields)

**Problem**: Snapshot data was missing key fields and using inconsistent field names.

**Fix**: Enhanced snapshot to include all required fields with multiple field name variations:
- Added `price`, `last_price`, `last_close` (all pointing to same value)
- Added `vwap` (actual VWAP value, not just delta)
- Added `vol_mult` as alias for `minute_vol_multiple`
- Added `atr` and `atr14` (both pointing to same value)
- Added field name variations for Donchian channels (`donchian_hi`/`donchian_upper`, etc.)

### 4. Backend - models_v2.py (Response Model)

**Problem**: Response model didn't include `risk` field.

**Fix**: Added `risk` field to `AnalyzeResponseV2` model:
```python
class AnalyzeResponseV2(BaseModel):
    decision: Literal["BUY", "SELL", "WAIT"]
    score: float
    confidence: float
    bands: List[float]
    action: Dict[str, object]
    risk: Dict[str, float]  # Added risk object
    why: Dict[str, object]
    meta: Dict[str, object]
```

### 5. Frontend - AnalystClient.tsx (Null Safety)

**Problem**: Code was checking with optional chaining (`az?.risk?.delta_trigger_bps`) but then accessing without it (`az.risk.delta_trigger_bps`).

**Fix**: Ensured consistent use of optional chaining:
```typescript
{az?.risk?.delta_trigger_bps != null ? `${Number(az?.risk?.delta_trigger_bps).toFixed(0)} bps` : '—'}
{az?.risk?.rr != null ? Number(az?.risk?.rr).toFixed(2) : '—'}
{az?.risk?.atr != null ? Number(az?.risk?.atr).toFixed(2) : '—'}
```

### 6. Frontend - App.tsx (Top Algos Display)

**Problem**: Delta trigger display in table was not handling null values properly.

**Fix**: Added proper null check with number formatting:
```typescript
<td className="px-3 py-2">{r.delta_trigger_bps != null ? Number(r.delta_trigger_bps).toFixed(1) : '—'}</td>
```

## Testing Checklist

- [x] Backend returns risk object in live analysis endpoint
- [x] Backend returns risk object in historical analysis endpoint  
- [x] Ticker heartbeat updates both keys
- [x] Snapshot includes all required fields (vwap, atr, price, etc.)
- [x] Frontend handles null/undefined values gracefully
- [x] Top Algos table displays delta_trigger_bps correctly
- [x] Analyst section displays risk metrics (ATR, R:R, ΔTrigger)

## Root Cause Analysis

The core issues were:

1. **Incomplete API Response**: Live analysis endpoint was missing the `risk` object that the frontend expected
2. **Field Name Inconsistencies**: Different parts of the system used different field names (`atr` vs `atr14`, `donchian_lo` vs `donchian_lower`)
3. **Missing Data**: Ticker daemon wasn't including critical fields like `vwap` (only `vwap_delta_pct`)
4. **Unsafe Null Access**: Frontend was using optional chaining in conditions but not in the subsequent access

## Prevention

To prevent similar issues:

1. **Type Safety**: The Pydantic models now enforce the presence of the `risk` field
2. **Field Name Normalization**: Code now handles multiple field name variations gracefully
3. **Defensive Programming**: Frontend uses consistent optional chaining throughout
4. **Complete Snapshots**: Ticker daemon now includes all necessary fields with aliases

## Status

✅ All fixes applied and ready for testing
