# Historical Data Fetch Fix - Summary

## Problem
The historical data fetch was not working when users selected a historical date. Clicking "Run Scan" did nothing, and no data was displayed.

## Root Causes

### 1. **Stale Closure in Frontend (App.tsx)**
- The `refresh` function was recreated on every render without using `useCallback`
- Event handlers and `useEffect` hooks held references to old versions of the function with outdated `dataMode` and `historicalDate` values
- When clicking "Run Scan", it would use stale values

### 2. **Missing On-Demand Data Fetching in Backend (hist.py)**
- The `historical_plan` function only read from Redis cache
- It returned empty results if no data had been pre-backfilled for that date
- There was no automatic fetching from Kite Connect API when data wasn't cached
- The `/api/v2/hist/backfill` endpoint existed but required manual calls

## Solutions Implemented

### Frontend Changes (web/components/App.tsx)

1. **Wrapped `refresh` function in `React.useCallback`**
   - Ensures the function always has latest values of `dataMode` and `historicalDate`
   - Prevents stale closures
   ```typescript
   const refresh = React.useCallback(async () => {
     // ... fetch logic
   }, [dataMode, historicalDate]);
   ```

2. **Updated all `useEffect` dependencies**
   - Added `refresh` to dependency arrays so React re-runs effects correctly
   - Ensures proper cleanup and re-subscription

3. **Added automatic fetching on date change**
   - New `useEffect` that triggers refresh when historical date changes
   - Users don't need to manually click "Run Scan" after selecting a date

4. **Improved error handling and logging**
   - Better error messages with HTTP status codes
   - Console logs with emoji prefixes (🔄, 📊, ✅, ❌) for easier debugging

5. **Cleaned up "Run Scan" button**
   - Removed debug alert
   - Directly calls `refresh()` function

### Backend Changes

#### backend/app/hist.py

1. **Added `_fetch_and_cache_historical_bars` function**
   - Checks if data is already cached in Redis
   - If not cached, fetches from Kite Connect API using `historical_data()` method
   - Converts Kite API format to internal format:
     ```python
     # Kite format: {date, open, high, low, close, volume}
     # Internal format: {ts, o, h, l, c, v}
     ```
   - Caches fetched data in Redis for future use (14 day TTL)
   - Returns empty list on failure with error logging

2. **Enhanced `historical_plan` function**
   - Now automatically fetches data from Kite API if not in cache
   - Uses a default watchlist of liquid NSE stocks when no cached symbols exist:
     - Top 20 stocks: RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, etc.
   - Each symbol's data is fetched on-demand as needed
   - Results are cached for subsequent requests

#### backend/app/api_v2_hist.py

1. **Improved error handling in `/plan` endpoint**
   - Catches authentication errors (expired/missing Kite session)
   - Returns HTTP 401 with helpful message: "Please login to fetch historical data"
   - Returns HTTP 500 with detailed error message for other failures
   - Added `count` field to response for better debugging

## How It Works Now

### User Flow
1. User switches to "Historical Data" mode
2. User selects a date from date picker
3. Frontend automatically triggers data fetch (or user clicks "Run Scan")
4. Backend checks if data is cached in Redis:
   - **If cached**: Returns data immediately
   - **If not cached**: 
     - Fetches minute-level OHLCV data from Kite Connect API
     - Caches in Redis
     - Analyzes opportunities
     - Returns top results
5. Frontend displays the trading opportunities

### API Integration (Kite Connect)
- Uses Kite Connect's `historical_data()` method:
  ```python
  kite.historical_data(
      instrument_token=token,
      from_date=start_ist,  # YYYY-MM-DD 09:15:00 IST
      to_date=end_ist,      # YYYY-MM-DD 15:30:00 IST
      interval="minute",
      continuous=False,
      oi=False
  )
  ```
- Automatically handles instrument token lookup
- Gracefully degrades if Kite session is not authenticated

## Technical Details

### Kite Connect API Format
- Endpoint: `/instruments/historical/:instrument_token/:interval`
- Response: Array of candles `[timestamp, open, high, low, close, volume]`
- Time format: ISO 8601 with timezone (e.g., `2017-12-15T09:15:00+0530`)

### Caching Strategy
- Key format: `bars:<SYMBOL>:<DATE>` (e.g., `bars:NSE:INFY:2025-10-13`)
- TTL: 14 days
- Storage: Redis LIST with JSON-encoded bars
- Benefits: Reduces API calls, faster subsequent loads

### Error Handling
- **401 Unauthorized**: Zerodha session expired → User should re-login
- **404 Not Found**: No data available for symbol/date
- **500 Internal Error**: Kite API failure or other server errors
- All errors logged to console with descriptive messages

## Files Modified

1. `web/components/App.tsx` - Frontend fixes for stale closures and auto-fetch
2. `backend/app/hist.py` - On-demand data fetching from Kite API
3. `backend/app/api_v2_hist.py` - Better error handling and responses

## Testing Recommendations

1. **Test with cached data**: Select a previously backfilled date
2. **Test with uncached data**: Select a new historical date
3. **Test without auth**: Logout from Zerodha and try historical fetch
4. **Test error handling**: Try invalid dates, weekends, holidays
5. **Test performance**: Monitor API call count and response times

## Future Improvements

1. **Bulk fetching**: Fetch multiple symbols in parallel to speed up initial load
2. **Progress indicator**: Show "Fetching data for X/Y symbols..." during bulk fetch
3. **Symbol selection**: Allow users to choose which symbols to analyze
4. **Date validation**: Warn if selected date is a holiday/weekend
5. **Caching optimization**: Pre-fetch data for adjacent dates
6. **Rate limiting**: Respect Kite API rate limits (3 req/sec)

## Notes

- Requires valid Zerodha/Kite Connect session for fresh data fetches
- Cached data works without authentication
- Default watchlist used when no symbols are cached (20 liquid NSE stocks)
- Historical analysis runs at 15:10 IST by default (near market close)
