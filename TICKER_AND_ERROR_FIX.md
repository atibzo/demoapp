# Ticker and JavaScript Error Fix

## Issues Identified

### 1. JavaScript Error: "Cannot read properties of undefined (reading '0')"

**Root Cause:**
The backend's `engine_v2.analyze()` function returns an `action` object that can be empty (`{}`) when certain conditions aren't met:
- When `trig` (trigger price) is `None`
- When `atr` (Average True Range) is falsy
- When `price` is falsy

In these cases, `action.entry_range` is undefined, but the frontend tries to access `action.entry_range[0]` and `action.entry_range[1]`, causing the error.

**Location in Code:**
- Backend: `/workspace/backend/app/engine_v2.py` lines 208-215
- Frontend: `/workspace/web/components/AnalystClient.tsx` lines 175, 505

**Fix Applied:**
Added defensive null checks in `AnalystClient.tsx`:
```typescript
// Line 171: Check if action and entry_range exist before using
if(!az || !az.action || !az.action.entry_range) { setWhatif(null); return; }

// Line 505: Use optional chaining
<div>Entry: <span className="font-mono">{az?.action?.entry_range? `${fmt(az.action.entry_range[0])} – ${fmt(az.action.entry_range[1])}`:'—'}</span></div>
```

---

### 2. Ticker Not Working Despite Market Being Open

**Root Cause:**
The ticker daemon only updates `ticker:alive` and `ticker:heartbeat` Redis keys when it **receives ticks** (inside the `_on_ticks` callback). This means:

1. If the WebSocket connects but no ticks arrive → ticker appears dead
2. If the daemon starts but can't connect → ticker appears dead
3. If there's a connection delay → ticker appears dead

The frontend checks if the ticker is alive by comparing the timestamp in `ticker:alive` with the current time. If it's older than 15 seconds, the ticker is marked as "stopped".

**Location in Code:**
- `/workspace/backend/app/ticker_daemon.py` lines 439-440 (only place where heartbeat was set)
- `/workspace/backend/app/main.py` lines 238-244 (where it checks if ticker is alive)

**Fixes Applied:**

1. **Set heartbeat on connection** (lines 476-488):
   ```python
   def _on_connect(self, ws, resp):
       # Mark ticker as alive immediately on connection
       now = now_s()
       self.r.set("ticker:alive", now)
       self.r.set("ticker:heartbeat", now_ms())
       
       self._subscribe_active()
       print(f"[ticker] connected and subscribed {len(self.subscribed)} tokens", file=sys.stderr)
   ```

2. **Enhanced logging throughout** to help debug connection issues:
   - Added logs when computing active tokens
   - Added logs when subscribing
   - Added logs on connection, close, and error
   - Added logs during startup and shutdown

3. **Better error handling**:
   - Set `ticker:alive = 0` when errors occur
   - Set `ticker:alive = 0` on stop signal
   - Added warning when no active tokens are computed

4. **Improved debugging** (lines 304-307):
   ```python
   if not self.active_tokens:
       print("[ticker] WARNING: No active tokens computed. Check cfg:universe_limit and cfg:pinned in Redis.", file=sys.stderr)
   else:
       print(f"[ticker] Computed {len(self.active_tokens)} active tokens to subscribe", file=sys.stderr)
   ```

---

## Testing Recommendations

1. **Restart the ticker daemon** to apply the fixes:
   ```bash
   docker compose restart ticker
   ```

2. **Monitor the logs** to see connection status:
   ```bash
   docker compose logs -f ticker
   ```

   You should now see:
   - `[ticker] Starting ticker daemon with X active tokens`
   - `[ticker] Connecting to KiteTicker WebSocket...`
   - `[ticker] connected and subscribed X tokens`

3. **Check the frontend** - the "Ticker stopped" badge should change to "Ticker live" once connected

4. **Verify the JavaScript error is gone** - check the browser console for any errors

---

## Key Changes Summary

| File | Changes |
|------|---------|
| `web/components/AnalystClient.tsx` | Added null checks for `entry_range` to prevent undefined access |
| `backend/app/ticker_daemon.py` | - Set heartbeat on connection (not just on ticks)<br>- Enhanced logging throughout<br>- Better error handling<br>- Added warnings for empty token lists |

---

## Additional Notes

### Why the ticker might still show "stopped":

1. **Not logged in to Zerodha** - The ticker requires a valid Zerodha session
2. **No symbols configured** - Check Redis keys `cfg:universe_limit` and `cfg:pinned`
3. **WebSocket connection issues** - Check ticker logs for connection errors
4. **Market is closed** - The ticker connects but won't receive ticks outside trading hours

### How to verify the ticker is working:

1. Check Redis: `redis-cli GET ticker:alive` should show a recent timestamp
2. Check Redis: `redis-cli SMEMBERS symbols:active` should show subscribed symbols
3. Check logs: Look for `[ticker] connected and subscribed X tokens` message
4. Frontend: The header should show "Ticker live" badge in green

---

## Impact

✅ **JavaScript error fixed** - The analyst tab will no longer crash when analyzing symbols
✅ **Ticker status improved** - The ticker status will update as soon as it connects, not waiting for ticks
✅ **Better debugging** - Enhanced logging makes it easier to diagnose ticker issues
✅ **More robust** - Better error handling prevents silent failures
