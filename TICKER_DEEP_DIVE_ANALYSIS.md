# Ticker Deep Dive Analysis - Why It's Not Working

## Architecture Overview

The ticker system has 4 components that must all work together:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Zerodha   │────▶│    Ticker    │────▶│     Redis       │────▶│   Frontend  │
│  Kite API   │     │    Daemon    │     │   (State DB)    │     │   (React)   │
└─────────────┘     └──────────────┘     └─────────────────┘     └─────────────┘
                           ▲                                              │
                           │                                              │
                           └──────────────────────────────────────────────┘
                                    (Shows ticker status)
```

## Critical Discovery: The Root Cause

After deep investigation, I found **THE PRIMARY ISSUE**:

### 🔴 The Ticker Daemon Is Not Running

**Evidence:**
1. `ps aux | grep ticker` shows NO ticker process
2. This is a development environment, NOT the Docker production environment
3. The ticker requires Docker to be running: `docker compose up ticker`

**What this means:**
- The ticker daemon (`/workspace/backend/app/ticker_daemon.py`) is designed to run as a separate Docker container
- Without Docker running, there is NO ticker daemon process
- Without the ticker daemon, there will NEVER be ticks, regardless of market hours or authentication

## Ticker Startup Flow (What Should Happen)

### 1. **Docker Container Starts** ✅
```yaml
# docker-compose.yml
ticker:
  build: ./backend
  command: ["python", "-m", "app.ticker_daemon"]
  depends_on:
    - redis
  volumes:
    - kite_session:/app/app/data/session
```

### 2. **Ticker Daemon Initializes** ⚠️
```python
# ticker_daemon.py line 290-320
class TickerDaemon:
    def __init__(self):
        # 1. Connect to Redis
        self.r = redis_client(...)
        
        # 2. Get Kite session (REQUIRES LOGIN!)
        self.ks = get_kite()
        if not self.ks.access_token:
            raise RuntimeError("Kite session not ready. Login first.")
        
        # 3. Load instruments from Kite API
        self.token2sym, self.sym2token = load_instruments(self.kite)
        if not self.token2sym:
            raise RuntimeError("No instruments loaded")
        
        # 4. Compute active tokens to subscribe
        self.active_tokens = compute_active(self.sym2token, self.r, UNIVERSE_DEFAULT)
        
        # 5. Initialize KiteTicker WebSocket
        self.kws = KiteTicker(self.ks.api_key, self.ks.access_token, reconnect=True)
```

### 3. **WebSocket Connection** ⚠️
```python
# ticker_daemon.py line 489-520
def run(self):
    # Backfill historical data
    self.backfill()
    
    # Set up callbacks
    self.kws.on_connect = self._on_connect
    self.kws.on_ticks = self._on_ticks
    
    # Connect to Zerodha WebSocket
    while not self._stop.is_set():
        try:
            self.kws.connect(threaded=False)  # BLOCKS HERE
        except NetworkException:
            time.sleep(2)
```

### 4. **On Connection** ✅ (Fixed)
```python
# ticker_daemon.py line 476-488 (AFTER MY FIX)
def _on_connect(self, ws, resp):
    # ✅ NOW sets heartbeat immediately
    now = now_s()
    self.r.set("ticker:alive", now)
    self.r.set("ticker:heartbeat", now_ms())
    
    # Subscribe to instruments
    self._subscribe_active()
```

### 5. **Receiving Ticks** ✅
```python
# ticker_daemon.py line 402-474
def _on_ticks(self, ws, ticks):
    # Updates ticker:alive on every tick batch
    self.r.set("ticker:alive", now)
    
    # Process each tick
    for tk in ticks:
        # Build minute bars
        # Update snapshots
        # Store in Redis
```

## Complete Failure Point Analysis

### ❌ Failure Point 1: Docker Not Running
**Symptom:** No ticker process exists
**Check:** `docker compose ps` or `ps aux | grep ticker`
**Fix:** `docker compose up -d ticker`
**Priority:** 🔴 CRITICAL - Nothing else matters if this fails

### ❌ Failure Point 2: Not Logged In
**Symptom:** Ticker container crashes immediately
**Error Log:** `RuntimeError: Kite session not ready. Login first.`
**Check:** 
```bash
docker compose logs ticker | grep -i "kite session"
ls -la backend/app/data/session/.kite_session.json
```
**Fix:** 
1. Go to frontend: `http://localhost:3000`
2. Click "Login with Zerodha"
3. Complete OAuth flow
4. Restart ticker: `docker compose restart ticker`
**Priority:** 🔴 CRITICAL

### ❌ Failure Point 3: Invalid Kite Credentials
**Symptom:** Authentication fails
**Error Log:** `TokenException` or 401 errors
**Check:** `docker compose logs ticker | grep -i "token\|auth\|401"`
**Fix:** 
1. Verify `.env` file:
   - `KITE_API_KEY=your_actual_key`
   - `KITE_API_SECRET=your_actual_secret`
   - `KITE_REDIRECT_URI=http://127.0.0.1:8000/callback`
2. Re-login through frontend
**Priority:** 🔴 CRITICAL

### ❌ Failure Point 4: No Instruments Loaded
**Symptom:** Ticker starts but no subscriptions
**Error Log:** `No instruments loaded (token2sym empty)`
**Check:** `docker compose logs ticker | grep "instruments loaded"`
**Root Causes:**
- Invalid `EXCHANGES` env var (default: "NSE,BSE")
- Kite API rate limit exceeded
- Network issues reaching Kite servers
**Fix:**
```bash
# Check env var
docker compose exec ticker env | grep EXCHANGES

# Restart to retry
docker compose restart ticker
```
**Priority:** 🟠 HIGH

### ❌ Failure Point 5: No Active Tokens Computed
**Symptom:** WebSocket connects but no ticks
**Error Log:** `WARNING: No active tokens computed`
**Check:** 
```bash
docker compose logs ticker | grep "active tokens"
docker compose exec redis redis-cli SMEMBERS "symbols:active"
docker compose exec redis redis-cli GET "cfg:universe_limit"
```
**Root Causes:**
- `cfg:universe_limit` is 0 or not set
- `cfg:pinned` is empty
- All instruments filtered out
**Fix:**
1. Set universe limit via Config tab: Set to 200-300
2. Or via Redis:
   ```bash
   docker compose exec redis redis-cli SET cfg:universe_limit 300
   docker compose restart ticker
   ```
**Priority:** 🟠 HIGH

### ❌ Failure Point 6: WebSocket Connection Fails
**Symptom:** Ticker keeps retrying connection
**Error Log:** `NetworkException` or `WebSocket error`
**Check:** `docker compose logs ticker | grep -i "websocket\|network"`
**Root Causes:**
- Internet connectivity issues
- Zerodha WebSocket server down
- Firewall blocking WebSocket connections
- Invalid access token (expired)
**Fix:**
1. Check internet: `docker compose exec ticker ping -c 3 kite.zerodha.com`
2. Verify token: Re-login through frontend
3. Check Zerodha status: https://status.zerodha.com
**Priority:** 🟡 MEDIUM

### ❌ Failure Point 7: Market Closed
**Symptom:** WebSocket connects but no ticks arrive
**Expected:** This is NORMAL outside 09:15-15:30 IST (Mon-Fri)
**Check:** 
```python
# Check market hours
from datetime import datetime
from zoneinfo import ZoneInfo
now = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
print(f"IST Time: {now.strftime('%H:%M')}")
# Market open: 09:15-15:30 IST, Mon-Fri only
```
**Fix:** Wait for market hours or use historical mode
**Priority:** ℹ️ INFO - Not a bug

### ❌ Failure Point 8: Redis Down
**Symptom:** Ticker crashes or can't store data
**Error Log:** `Failed to connect to Redis`
**Check:** 
```bash
docker compose ps redis
docker compose exec redis redis-cli PING
```
**Fix:** `docker compose up -d redis`
**Priority:** 🔴 CRITICAL

## My Fixes Applied

### ✅ Fix 1: Set Heartbeat on Connection (Not Just Ticks)

**Problem:** Ticker appeared "stopped" even when connected
```python
# BEFORE: Only set heartbeat when ticks arrive
def _on_ticks(self, ws, ticks):
    self.r.set("ticker:alive", now)  # ❌ Only here!
```

**Fixed:**
```python
# AFTER: Set heartbeat immediately on connection
def _on_connect(self, ws, resp):
    now = now_s()
    self.r.set("ticker:alive", now)      # ✅ Set immediately
    self.r.set("ticker:heartbeat", now_ms())
    self._subscribe_active()
```

**Impact:** Ticker shows "live" as soon as WebSocket connects

### ✅ Fix 2: Enhanced Logging Throughout

Added debug logs at every critical point:
- ✅ Instrument loading
- ✅ Active token computation
- ✅ Subscription attempts
- ✅ Connection events
- ✅ Error details

**Impact:** Easier to diagnose issues via `docker compose logs ticker`

### ✅ Fix 3: Warning for Empty Token Lists

```python
if not self.active_tokens:
    print("[ticker] WARNING: No active tokens computed. Check cfg:universe_limit and cfg:pinned in Redis.", file=sys.stderr)
```

**Impact:** Clear error message when configuration is wrong

### ✅ Fix 4: Frontend Error Handling

Fixed `Cannot read properties of undefined (reading '0')`:
```typescript
// Added null checks for entry_range
if(!az || !az.action || !az.action.entry_range) { 
    setWhatif(null); 
    return; 
}
```

**Impact:** No more crashes when analyzing symbols

## Diagnostic Checklist (Run These Commands)

### 1. Check if Docker is Running
```bash
docker compose ps
# Should show: ticker, api, redis, web all "Up"
```

### 2. Check Ticker Logs
```bash
docker compose logs ticker --tail 100
# Look for:
# ✅ "[ticker] Starting ticker daemon with X active tokens"
# ✅ "[ticker] connected and subscribed X tokens"
# ❌ "RuntimeError: Kite session not ready"
# ❌ "No instruments loaded"
# ❌ "WebSocket error"
```

### 3. Check Redis State
```bash
# Ticker heartbeat (should be recent timestamp)
docker compose exec redis redis-cli GET ticker:alive

# Active symbols
docker compose exec redis redis-cli SMEMBERS symbols:active

# Universe limit
docker compose exec redis redis-cli GET cfg:universe_limit

# Pinned symbols
docker compose exec redis redis-cli SMEMBERS cfg:pinned
```

### 4. Check Authentication
```bash
# Session file should exist
docker compose exec ticker ls -la /app/app/data/session/
# Should show: .kite_session.json

# Verify env vars
docker compose exec ticker env | grep KITE
```

### 5. Check Network Connectivity
```bash
# Can reach Kite servers?
docker compose exec ticker ping -c 3 kite.zerodha.com
docker compose exec ticker ping -c 3 api.kite.trade
```

### 6. Check Frontend Status
```bash
# Open browser: http://localhost:3000
# Header should show:
# ✅ "Zerodha connected" (green)
# ✅ "Ticker live" (green) 
# ✅ "Market open" (green, during market hours)
```

## Quick Fix Steps (In Order)

### Step 1: Ensure Docker is Running
```bash
cd /workspace
docker compose up -d
```

### Step 2: Login to Zerodha
1. Open: http://localhost:3000
2. Click: "Login with Zerodha"
3. Complete OAuth
4. Should redirect back to app

### Step 3: Configure Universe
1. Go to "Config" tab
2. Set "Universe Limit": 300
3. Add pinned symbols (optional): NSE:INFY, NSE:RELIANCE
4. Click "Save"

### Step 4: Restart Ticker
```bash
docker compose restart ticker
```

### Step 5: Verify
```bash
# Check logs
docker compose logs ticker --tail 50

# Should see:
# [ticker] Starting ticker daemon with 300 active tokens
# [ticker] Connecting to KiteTicker WebSocket...
# [ticker] connected and subscribed 300 tokens

# Check heartbeat
docker compose exec redis redis-cli GET ticker:alive
# Should show recent timestamp (within 15 seconds)
```

### Step 6: Check Frontend
Refresh browser - header should show "Ticker live" in green

## Market Hours Reminder

**Indian Stock Market Hours (IST):**
- Open: 09:15 AM
- Close: 03:30 PM
- Days: Monday - Friday (excluding holidays)

**Outside these hours:**
- Ticker connects but receives NO ticks ✅ (This is normal!)
- Frontend shows "Ticker stopped" or "WAITING" mode
- Historical analysis still works

## Environment Variables Checklist

Ensure these are set in `backend/.env`:

```bash
# Required for ticker
REDIS_URL=redis://redis:6379/0          # ✅
KITE_API_KEY=your_actual_key            # ✅ Get from Kite Developer Console
KITE_API_SECRET=your_actual_secret      # ✅ Get from Kite Developer Console
KITE_REDIRECT_URI=http://127.0.0.1:8000/callback  # ✅

# Optional but recommended
UNIVERSE_LIMIT=300                       # Default: 200
EXCHANGES=NSE,BSE                        # Default: NSE,BSE
TICKER_HEARTBEAT_MAX_AGE=15             # Default: 15 seconds
```

## Final Root Cause Summary

**Primary Issue: Ticker Daemon Not Running**
- The ticker daemon MUST run as a Docker container
- Command: `docker compose up -d ticker`
- Without this, nothing else matters

**Secondary Issues (If Docker is running):**
1. ❌ Not logged in to Zerodha → Login via frontend
2. ❌ Invalid Kite credentials → Check .env file
3. ❌ No universe configured → Set via Config tab
4. ❌ Redis not accessible → Check Docker network
5. ❌ WebSocket connection fails → Check Kite API status
6. ❌ Market closed → Wait for market hours (09:15-15:30 IST)

**My Fixes Help With:**
- ✅ Better status reporting (heartbeat on connect)
- ✅ Clearer error messages (enhanced logging)
- ✅ Frontend stability (null checks for entry_range)
- ✅ Easier debugging (detailed logs)

## Next Steps for User

1. **Start Docker containers:**
   ```bash
   cd /workspace
   docker compose up -d
   ```

2. **Check ticker is running:**
   ```bash
   docker compose ps ticker
   docker compose logs ticker --tail 50
   ```

3. **If not logged in, login:**
   - Go to: http://localhost:3000
   - Click "Login with Zerodha"

4. **Configure universe:**
   - Config tab → Set limit to 300

5. **Monitor:**
   ```bash
   # Watch logs in real-time
   docker compose logs -f ticker
   
   # Check Redis heartbeat every few seconds
   watch -n 2 'docker compose exec redis redis-cli GET ticker:alive'
   ```

The ticker should now work! 🎉
