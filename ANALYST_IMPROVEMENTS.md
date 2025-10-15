# Analyst Tab Improvements - Historical Analysis Update

## Summary of Changes

The Analyst tab and historical data fetching have been significantly improved to work **independently** and support analyzing **any of the top 300 intraday tradable stocks** on any historical date.

## What Was Wrong Before

### 1. **Limited to "Top Algos" Universe**
- ❌ Analyst tab could only analyze stocks already loaded in "Top Algos" tab
- ❌ Historical data was limited to whatever was cached in Redis
- ❌ Users couldn't analyze arbitrary stocks on historical dates

### 2. **Small Universe (20 stocks)**
- ❌ Historical plan only used 20 hardcoded stocks
- ❌ Not suitable for comprehensive market analysis
- ❌ Missing many intraday trading opportunities

### 3. **No Auto-Fetch**
- ❌ Had to manually backfill historical data
- ❌ Analyst tab would fail if data wasn't pre-cached
- ❌ Poor user experience

## What's Fixed Now

### ✅ 1. **Independent Analyst Tab**

The Analyst tab now works **completely independently** of the "Top Algos" tab:

- **Analyze ANY stock** from the top 300 intraday universe
- **Auto-fetches data** from Kite API if not cached
- **Works on ANY historical date** (not limited to cached data)
- **No pre-loading required** - just enter symbol and date

**Example Usage:**
```
1. Go to Analyst tab
2. Enter: NSE:RELIANCE
3. Select date: 2025-10-10
4. Click "Load Day"
5. ✨ Data is automatically fetched if not cached!
```

### ✅ 2. **300 Stock Universe**

Created a comprehensive universe of 300 intraday tradable NSE stocks:

**File:** `/workspace/backend/app/universe.py`

**Categories Included:**
- Nifty 50 (highest liquidity)
- Nifty Next 50
- Banking & Finance
- IT & Technology
- Pharma & Healthcare
- FMCG & Consumer
- Auto & Ancillaries
- Metals & Mining
- Energy & Power
- Infrastructure & Realty
- Telecom & Media
- Chemicals & Fertilizers
- Cement & Construction
- Textiles & Apparel
- Retail & E-commerce
- Hotels & Tourism
- Logistics & Transport
- And more...

**Functions Available:**
```python
from backend.app.universe import get_intraday_universe, is_intraday_tradable

# Get top 300 stocks
stocks = get_intraday_universe(limit=300, exchange="NSE")

# Check if a stock is intraday tradable
is_tradable = is_intraday_tradable("NSE:INFY")  # True

# Get stock category
category = get_symbol_category("NSE:INFY")  # "IT & Technology"
```

### ✅ 3. **Auto-Fetch Historical Data**

Both endpoints now auto-fetch data from Kite API:

#### **GET `/api/v2/hist/bars`**
```bash
# Now supports auto_fetch parameter
GET /api/v2/hist/bars?symbol=NSE:RELIANCE&date=2025-10-10&auto_fetch=true
```

**Behavior:**
1. Check Redis cache
2. If found → return cached data ⚡
3. If not found → fetch from Kite API 🔄
4. Cache in Redis for 14 days
5. Return data to user

#### **GET `/api/v2/hist/analyze`**
```bash
# Automatically fetches if needed
GET /api/v2/hist/analyze?symbol=NSE:TCS&date=2025-10-10&time=14:30
```

**Behavior:**
1. Check cache for bars
2. If not cached → auto-fetch from Kite
3. Analyze at specified time
4. Return analysis

### ✅ 4. **Enhanced Historical Plan**

#### **GET `/api/v2/hist/plan`**

Now scans up to **300 stocks** and returns top opportunities:

```bash
GET /api/v2/hist/plan?date=2025-10-10&top=10&time=15:10&universe_size=300
```

**Parameters:**
- `date`: Date in YYYY-MM-DD format
- `top`: Number of results to return (default: 10, max: 100)
- `time`: Analysis time in HH:MM format (default: 15:10)
- `universe_size`: Number of stocks to scan (default: 300, max: 300)

**Response:**
```json
{
  "date": "2025-10-10",
  "top": 10,
  "time": "15:10",
  "universe_scanned": 300,
  "count": 10,
  "items": [
    {
      "symbol": "NSE:RELIANCE",
      "side": "long",
      "score": 8.5,
      "confidence": 0.78,
      "age_s": 0.0,
      "delta_trigger_bps": 15.2,
      "regime": "Normal",
      "readiness": "Ready",
      "checks": {"VWAPΔ": true, "VolX": true}
    },
    // ... 9 more top opportunities
  ]
}
```

**Features:**
- ✅ Scans 300 stocks (configurable)
- ✅ Auto-fetches missing data from Kite
- ✅ Caches results for 14 days
- ✅ Progress logging
- ✅ Returns top N ranked by score

## API Changes Summary

### New/Updated Endpoints

| Endpoint | Change | Description |
|----------|--------|-------------|
| `GET /api/v2/hist/bars` | **Enhanced** | Added `auto_fetch` parameter (default: true) |
| `GET /api/v2/hist/analyze` | **Enhanced** | Auto-fetches data if not cached |
| `GET /api/v2/hist/plan` | **Enhanced** | Now scans 300 stocks, added `universe_size` param |

### New Module

**`/workspace/backend/app/universe.py`**
- Defines top 300 intraday tradable stocks
- Utility functions for universe management
- Stock categorization

## Frontend Changes

### AnalystClient.tsx Updates

1. **Better Symbol Input**
   - Wider input field
   - Helpful placeholder text
   - Tooltip explaining it works independently

2. **Auto-Fetch Enabled**
   - `auto_fetch=true` parameter added to API calls
   - Better error messages
   - Clearer user guidance

3. **Improved Help Text**
   - Instructions on how to use
   - Explanation that it works independently
   - Lists the capabilities

## Usage Examples

### Example 1: Analyze Any Stock Independently

```typescript
// No need to load in "Top Algos" first!
const symbol = "NSE:HDFC";
const date = "2025-10-10";

// Auto-fetches data if needed
const response = await fetch(
  `${API}/api/v2/hist/analyze?symbol=${symbol}&date=${date}&time=14:30`
);

const analysis = await response.json();
// Returns full analysis with decision, confidence, brackets, etc.
```

### Example 2: Get Top 10 from 300 Stocks

```bash
curl "http://localhost:8000/api/v2/hist/plan?date=2025-10-10&top=10&universe_size=300"
```

Returns top 10 trading opportunities after scanning 300 stocks.

### Example 3: Fetch Historical Bars

```bash
# Automatically fetches from Kite if not cached
curl "http://localhost:8000/api/v2/hist/bars?symbol=NSE:RELIANCE&date=2025-10-10"
```

## Performance Considerations

### Caching Strategy

- **Bars cached for 14 days** in Redis
- **First load**: Fetches from Kite API (1-3 seconds per stock)
- **Subsequent loads**: Instant from cache (<100ms)

### Historical Plan Performance

Scanning 300 stocks:
- **All cached**: ~5-10 seconds
- **All need fetching**: ~5-10 minutes (one-time cost)
- **Mixed**: Varies based on cache hit rate

**Optimization Tips:**
1. Pre-populate cache during off-hours
2. Start with smaller `universe_size` (50-100)
3. Use cached data when available
4. Run full scan once, then use cache

### Recommended Usage

**For Daily Analysis:**
```bash
# First time (morning): Fetch for top 100 stocks
GET /api/v2/hist/plan?date=2025-10-10&top=10&universe_size=100

# Throughout day: Use cached data
GET /api/v2/hist/analyze?symbol=NSE:INFY&date=2025-10-10&time=14:30
```

**For Comprehensive Analysis:**
```bash
# Full universe scan (do once per date)
GET /api/v2/hist/plan?date=2025-10-10&top=50&universe_size=300
```

## Error Handling

### Authentication Errors

If Zerodha session expired:
```json
{
  "status_code": 401,
  "detail": "Zerodha session expired or not authenticated. Please login to fetch historical data."
}
```

**Solution**: Login to Zerodha via the app

### Symbol Not Found

If symbol doesn't exist:
```json
{
  "status_code": 404,
  "detail": "No historical data available for NSE:INVALID on 2025-10-10. Make sure you're logged in to Zerodha and the symbol exists."
}
```

### No Data Available

If data fetch fails:
```json
{
  "status_code": 404,
  "detail": "No bars recorded for NSE:XYZ on 2025-10-10. Try logging in to Zerodha to fetch historical data."
}
```

## Testing

### Test Auto-Fetch

```bash
# 1. Clear cache (optional)
redis-cli FLUSHDB

# 2. Try fetching a stock
curl "http://localhost:8000/api/v2/hist/bars?symbol=NSE:INFY&date=2025-10-10"

# 3. Should auto-fetch from Kite and return data
```

### Test Independent Analyst

```bash
# 1. Go to Analyst tab: http://localhost:3000/analyst
# 2. Enter symbol: NSE:TCS
# 3. Select date: any past date
# 4. Click "Load Day"
# 5. Should work even if TCS is not in "Top Algos"
```

### Test 300 Stock Universe

```bash
# Get historical plan with full universe
curl "http://localhost:8000/api/v2/hist/plan?date=2025-10-10&top=20&universe_size=300" \
  | jq '.universe_scanned, .count, .items[0]'

# Should show:
# 300 (universe_scanned)
# 20 (count)
# { symbol, score, confidence, ... }
```

## Benefits

### For Users
✅ **Flexibility** - Analyze any stock anytime  
✅ **No pre-loading** - Just enter symbol and go  
✅ **Comprehensive** - Access to 300 stocks  
✅ **Fast** - Cached data loads instantly  
✅ **Independent** - No dependency on "Top Algos"

### For Analysis
✅ **Broader coverage** - 300 stocks vs 20  
✅ **Better opportunities** - Find hidden gems  
✅ **Complete history** - Any date, any stock  
✅ **Reliable** - Auto-fetch ensures data availability

## Limitations & Notes

1. **Kite API Rate Limits**
   - Zerodha limits historical data requests
   - Cache mitigates this (14 day retention)
   - Pre-populate cache to avoid limits

2. **Universe Size**
   - Max 300 stocks (configurable)
   - Can reduce for faster scans
   - Focused on NSE liquid stocks

3. **Data Availability**
   - Requires valid Zerodha session
   - Only works for market trading hours (9:15-15:30)
   - Limited to stocks available via Kite API

4. **First Load Time**
   - Fetching 300 stocks can take 5-10 minutes first time
   - Subsequent loads are instant (cached)
   - Consider pre-populating cache

## Migration Notes

### Breaking Changes
None - all changes are backward compatible

### Deprecations
None

### New Features
- 300 stock universe module
- Auto-fetch capability
- Independent analyst analysis
- Enhanced error messages

## Future Enhancements

Potential improvements:
- [ ] Add BSE stocks support
- [ ] Multi-exchange scanning
- [ ] Background cache pre-population
- [ ] Stock filtering by category
- [ ] Custom universe management
- [ ] Real-time universe updates
- [ ] Stock recommendation engine
- [ ] Backtest across universe

## Support

### Troubleshooting

**Issue**: Analyst tab shows "No bars recorded"
- **Fix**: Make sure you're logged in to Zerodha
- **Fix**: Check if the date is a trading day

**Issue**: Historical plan takes too long
- **Fix**: Reduce `universe_size` parameter (try 50 or 100)
- **Fix**: Use cached data (run once, then access cache)

**Issue**: Some stocks fail to fetch
- **Fix**: Check Zerodha API rate limits
- **Fix**: Verify stock symbols are correct
- **Fix**: Ensure market was open on that date

### Logs

Check backend logs for detailed info:
```bash
docker-compose logs -f api | grep "Historical plan"
```

Look for:
- Progress updates
- Cache hits/misses
- Fetch successes/failures
- Performance metrics

---

## Summary

The Analyst tab is now **truly independent** and can analyze **any of the top 300 intraday tradable stocks** on **any historical date**, with **automatic data fetching** from Kite API when needed. This is a major improvement in flexibility and usability! 🎉
