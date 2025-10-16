# Quick Ticker Fix Guide ⚡

## TL;DR - Run This First

```bash
cd /workspace

# 1. Run diagnostic script
./check_ticker_status.sh

# 2. If Docker not running:
docker compose up -d

# 3. If not logged in:
# Open http://localhost:3000 → Click "Login with Zerodha"

# 4. If no symbols:
# Go to Config tab → Set Universe Limit to 300 → Save

# 5. Restart ticker
docker compose restart ticker

# 6. Check logs
docker compose logs -f ticker
```

---

## The #1 Root Cause

**🔴 THE TICKER DAEMON IS NOT RUNNING**

The ticker is a **separate Docker container** that must be running. Without it, you'll NEVER get ticks.

**How to check:**
```bash
docker compose ps ticker
# Should show: "Up" status

ps aux | grep ticker
# Should show: python -m app.ticker_daemon
```

**If not running:**
```bash
docker compose up -d ticker
```

---

## Common Issues & Quick Fixes

### Issue 1: "Ticker Stopped" in Frontend
**Cause:** Ticker daemon not running OR not connected to WebSocket

**Fix:**
```bash
# Check if running
docker compose ps ticker

# If not, start it
docker compose up -d ticker

# Check logs
docker compose logs ticker --tail 50

# Should see:
# "[ticker] connected and subscribed X tokens"
```

### Issue 2: Ticker Crashes on Startup
**Cause:** Not logged in to Zerodha

**Error in logs:** `RuntimeError: Kite session not ready. Login first.`

**Fix:**
1. Open: http://localhost:3000
2. Click: "Login with Zerodha"
3. Complete OAuth flow
4. Run: `docker compose restart ticker`

### Issue 3: No Ticks Coming Through
**Cause:** Either market is closed OR no symbols configured

**Fix:**
```bash
# Check market hours
TZ=Asia/Kolkata date
# Market: 09:15-15:30 IST, Mon-Fri only

# Check symbols
docker compose exec redis redis-cli SCARD symbols:active
# Should show: >0

# If 0, configure via frontend:
# Config tab → Universe Limit: 300 → Save
```

### Issue 4: "No Instruments Loaded"
**Cause:** Invalid Kite credentials or API issues

**Fix:**
1. Check `backend/.env`:
   ```bash
   cat backend/.env | grep KITE
   ```
2. Verify:
   - `KITE_API_KEY` is set (not "your_kite_api_key_here")
   - `KITE_API_SECRET` is set
   - `KITE_REDIRECT_URI=http://127.0.0.1:8000/callback`
3. Restart: `docker compose restart ticker`

### Issue 5: WebSocket Keeps Reconnecting
**Cause:** Network issues or invalid token

**Fix:**
```bash
# Test connectivity
docker compose exec ticker ping -c 3 kite.zerodha.com

# Re-login
# Frontend → Logout → Login again

# Restart ticker
docker compose restart ticker
```

---

## Diagnostic Commands

### Check Everything at Once
```bash
./check_ticker_status.sh
```

### Manual Checks
```bash
# 1. Ticker status
docker compose ps ticker

# 2. Recent logs
docker compose logs ticker --tail 50

# 3. Heartbeat (should be recent timestamp)
docker compose exec redis redis-cli GET ticker:alive

# 4. Active symbols count
docker compose exec redis redis-cli SCARD symbols:active

# 5. Session file exists
docker compose exec ticker ls -la /app/app/data/session/

# 6. Environment
docker compose exec ticker env | grep KITE
```

---

## What The Fixes Do

### ✅ My Code Changes

1. **Set heartbeat on connection** (not just on ticks)
   - Before: Ticker only updated status when ticks arrived
   - After: Status updates immediately when WebSocket connects
   - Impact: "Ticker live" shows as soon as connected

2. **Enhanced logging**
   - Added detailed logs at every step
   - Easier to debug connection issues
   - Clear error messages

3. **Frontend error handling**
   - Fixed "Cannot read properties of undefined"
   - App won't crash when analyzing symbols

4. **Better error messages**
   - Warning when no symbols configured
   - Clear logs for each failure point

---

## Expected Behavior

### When Working Correctly:

**Logs show:**
```
[ticker] Starting ticker daemon with 300 active tokens
[ticker] Running backfill...
[ticker] Backfill completed
[ticker] Connecting to KiteTicker WebSocket...
[ticker] connected and subscribed 300 tokens
```

**Redis shows:**
```bash
$ docker compose exec redis redis-cli GET ticker:alive
"1729065234"  # Recent timestamp

$ docker compose exec redis redis-cli SCARD symbols:active  
300  # Number of symbols
```

**Frontend shows:**
- ✅ "Zerodha connected" (green)
- ✅ "Ticker live" (green)
- ✅ "Market open" (green, during market hours)

### Outside Market Hours (Normal):

- Ticker connects successfully ✅
- No ticks arrive ✅ (expected!)
- Frontend might show "WAITING" mode ✅
- Historical analysis still works ✅

---

## Step-by-Step Setup (First Time)

1. **Start all containers:**
   ```bash
   cd /workspace
   docker compose up -d
   ```

2. **Check they're running:**
   ```bash
   docker compose ps
   # All should show "Up"
   ```

3. **Configure credentials** (if not done):
   ```bash
   cp backend/.env.example backend/.env
   nano backend/.env
   # Set: KITE_API_KEY, KITE_API_SECRET
   ```

4. **Login to Zerodha:**
   - Open: http://localhost:3000
   - Click: "Login with Zerodha"
   - Authorize the app
   - Should redirect back

5. **Configure universe:**
   - Go to: "Config" tab
   - Set "Universe Limit": 300
   - Click "Save Configuration"

6. **Restart ticker:**
   ```bash
   docker compose restart ticker
   ```

7. **Verify:**
   ```bash
   docker compose logs ticker --tail 30
   # Should see successful connection
   ```

8. **Use the app:**
   - During market hours: Live ticks flow
   - Outside market hours: Use historical mode

---

## Still Not Working?

Run the full diagnostic:
```bash
./check_ticker_status.sh
```

Check the detailed guide:
```bash
cat TICKER_DEEP_DIVE_ANALYSIS.md
```

Watch logs in real-time:
```bash
docker compose logs -f ticker
```

Monitor Redis heartbeat:
```bash
watch -n 2 'docker compose exec redis redis-cli GET ticker:alive'
```

---

## Key Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/app/ticker_daemon.py` | Set heartbeat on connect | Show "live" immediately |
| `backend/app/ticker_daemon.py` | Enhanced logging | Easier debugging |
| `web/components/AnalystClient.tsx` | Null checks for entry_range | Prevent crashes |

---

## Market Hours Reminder

**Indian Stock Market (NSE/BSE):**
- **Open:** 09:15 AM IST
- **Close:** 03:30 PM IST  
- **Days:** Monday - Friday
- **Holidays:** Check Zerodha calendar

**Outside these hours:** Ticker connects but NO ticks arrive (this is normal!)

---

Need help? Check:
1. `./check_ticker_status.sh` - Run diagnostics
2. `TICKER_DEEP_DIVE_ANALYSIS.md` - Detailed analysis
3. `docker compose logs ticker -f` - Live logs
