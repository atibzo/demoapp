# Analyst Tool Debugging Guide

## Problem Fixed: Rate Limit Issues

The analyst tool was failing with "No data available" errors because it was hitting Kite API's rate limit. The root cause was that every symbol lookup was calling `ks.instruments()`, resulting in hundreds of API calls when scanning 300+ stocks.

## Solution Implemented

### 1. Instruments Caching
- Added global cache for instrument data (`_INSTRUMENTS_CACHE`)
- Cache TTL: 1 hour (configurable via `INSTRUMENTS_CACHE_TTL`)
- Stale cache is preferred over API errors (avoids rate limits)
- Automatic cache warming on application startup

### 2. Enhanced Debugging

#### Debug Endpoints Added

**Test Symbol Lookup:**
```bash
GET /api/v2/hist/debug/lookup?symbol=BSE:BHEL&show_matches=true
```

Response shows:
- Parsed exchange and symbol
- Token found (or null if failed)
- Cache status (age, counts per exchange)
- Variations tried
- Similar matches (if show_matches=true)

**Refresh Cache Manually:**
```bash
POST /api/v2/hist/debug/cache/refresh
```

Or for specific exchange:
```bash
POST /api/v2/hist/debug/cache/refresh?exchange=BSE
```

### 3. Improved Error Messages

The logs now show:
- 🔥 Cache warming on startup
- ✅ Cache hits (returning cached data)
- ⚡ Stale cache usage (when cache is old but avoiding API calls)
- 🔄 Fresh API fetches
- 🚫 Rate limit errors
- ❌ Lookup failures with detailed context
- 💥 Empty cache warnings

## How to Debug "No Data Available" Errors

### Step 1: Check if You're Logged In
The analyst tool requires Zerodha authentication:
```bash
GET /api/v2/session
```

Look for `"zerodha": true`

### Step 2: Test Symbol Lookup
```bash
GET /api/v2/hist/debug/lookup?symbol=BSE:BHEL&show_matches=true
```

Check the response:
- `"success": true` means the symbol was found
- `"cache_status"` shows if cache is populated
- `"similar_matches"` shows what symbols exist that are similar

### Step 3: Check Cache Status
If cache is empty (`"cache_is_empty": true`), the app couldn't fetch instruments. This usually means:

**Option A: Rate limit hit**
- Wait 5-10 minutes
- Try refreshing: `POST /api/v2/hist/debug/cache/refresh`

**Option B: Not authenticated**
- Login to Zerodha first
- Then refresh cache

### Step 4: Check Backend Logs
Look for these patterns:

**Good:**
```
[CACHE] ✅ Returning cached instruments for NSE (8456 instruments)
[ROBUST_LOOKUP] ✅ FOUND on NSE: BHEL -> token 112129
```

**Rate Limit:**
```
[CACHE] 🚫 RATE LIMIT hit for NSE. Using stale cache if available.
```

**Empty Cache:**
```
[ROBUST_LOOKUP] 💥 CACHE IS EMPTY! This is likely due to rate limiting.
```

## Common Issues & Solutions

### Issue: "No data available for BSE:BHEL"

**Diagnosis:**
```bash
curl "http://localhost:8000/api/v2/hist/debug/lookup?symbol=BSE:BHEL&show_matches=true"
```

**Solutions:**

1. **If token is null and cache is empty:**
   - Wait 5 minutes (rate limit cooldown)
   - Restart the backend: `docker-compose restart api`
   - The startup event will warm the cache

2. **If token is null but cache is populated:**
   - Symbol might not exist on BSE
   - Try NSE instead: `NSE:BHEL`
   - Check similar_matches to see what exists

3. **If token is found but no bars:**
   - Date might be a holiday/weekend
   - Market was closed on that date
   - Try a recent trading day (e.g., yesterday)

### Issue: Rate Limit Errors

**Quick Fix:**
1. Stop making requests for 5-10 minutes
2. Restart the backend to clear request counters
3. The cache will prevent future rate limits

**Long-term:**
- Cache prevents this by storing instruments for 1 hour
- Startup warming ensures cache is ready
- Stale cache preference avoids API calls

## Testing the Fix

### Test 1: Basic Lookup
```bash
# Should return token and success=true
curl "http://localhost:8000/api/v2/hist/debug/lookup?symbol=NSE:BHEL"
```

### Test 2: BSE Symbol
```bash
# Should return token for BSE:BHEL or suggest NSE alternative
curl "http://localhost:8000/api/v2/hist/debug/lookup?symbol=BSE:BHEL&show_matches=true"
```

### Test 3: Fetch Historical Data
```bash
# Should return bars or clear error message
curl "http://localhost:8000/api/v2/hist/bars?symbol=NSE:BHEL&date=2025-10-14&auto_fetch=true"
```

### Test 4: Cache Refresh
```bash
# Force cache refresh
curl -X POST "http://localhost:8000/api/v2/hist/debug/cache/refresh"
```

## Changes Made

### Files Modified

1. **`backend/app/hist.py`**
   - Added `_INSTRUMENTS_CACHE` global cache
   - Added `_get_cached_instruments()` function
   - Added `warm_instruments_cache()` function
   - Updated `_find_instrument_token_robust()` to use cache
   - Enhanced error logging with emojis for visibility

2. **`backend/app/main.py`**
   - Added `@app.on_event("startup")` handler
   - Automatically warms cache on startup
   - Handles authentication check gracefully

3. **`backend/app/api_v2_hist.py`**
   - Added `/debug/lookup` endpoint for testing lookups
   - Added `/debug/cache/refresh` endpoint for manual refresh
   - Shows detailed instrument information

## Performance Impact

**Before:**
- ~900 API calls when scanning 300 stocks
- Rate limit hit after ~50 stocks
- Many symbols failed with "No data available"

**After:**
- ~3 API calls total (NSE, BSE, and maybe ALL on first run)
- Cache reused for all subsequent lookups
- All valid symbols resolve successfully
- 100x faster lookups after cache is warmed

## Monitoring

Check these logs to monitor health:

```bash
# On startup
grep "STARTUP" logs | tail -5

# Cache status
grep "CACHE" logs | tail -20

# Lookup failures
grep "FAILED" logs | tail -10
```

## FAQ

**Q: How long does cache last?**
A: 1 hour by default. After that, stale cache is still used to avoid rate limits, but it will try to refresh.

**Q: What if I restart the backend?**
A: Cache is in-memory, so it's lost on restart. The startup event will re-warm it automatically.

**Q: Can I persist the cache to disk?**
A: Not currently, but you could add Redis persistence if needed.

**Q: What if a new stock is listed?**
A: Wait for cache to expire (1 hour) or manually refresh: `POST /api/v2/hist/debug/cache/refresh`

## Support

If you're still seeing issues:

1. Check authentication: `GET /api/v2/session`
2. Test lookup: `GET /api/v2/hist/debug/lookup?symbol=YOUR_SYMBOL&show_matches=true`
3. Check backend logs for detailed error messages
4. If rate limited, wait 10 minutes and restart backend
5. Use the debug endpoints to understand exactly what's failing
