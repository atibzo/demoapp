# Intraday Trading Filter - Top Algos vs Analyst

## Overview

The system now properly distinguishes between:
1. **Top Algos Tab** - Shows ONLY intraday-tradeable stocks (strict filtering)
2. **Analyst Tab** - Works with ANY stock (universal, no filtering)

## Why This Distinction?

### Top Algos = Real Trading Opportunities
The Top Algos tab is for **actual trading recommendations**. It should ONLY show stocks that are:
- ✅ Highly liquid (tight spreads, good volume)
- ✅ In regular equity segment (EQ series)
- ✅ Suitable for intraday trading (can be bought and sold same day)

### Analyst = Universal Analysis Tool
The Analyst tab is for **learning and analysis**. It works with ANY stock because:
- 📊 You might want to analyze a stock to understand WHY it's not suitable for intraday
- 📈 You might want to study historical patterns of any stock
- 🔍 You might want to backtest on stocks that later became liquid
- 📚 Educational purposes - analyze any stock's behavior

## What Makes a Stock "Intraday-Tradeable"?

### ✅ GOOD for Intraday (Shown in Top Algos)

#### 1. **Regular Equity Segment (EQ series)**
- Example: `NSE:INFY-EQ`, `NSE:RELIANCE-EQ`
- High liquidity, tight spreads
- Can be bought and sold freely
- **Status**: ✅ Allowed in Top Algos

#### 2. **Stocks in Curated Universe**
- 600+ carefully selected liquid stocks
- Proven track record of good volume
- Institutional participation
- **Status**: ✅ Allowed in Top Algos

### ❌ BAD for Intraday (Filtered from Top Algos)

#### 1. **Trade-to-Trade Segment (BE series)**
- Example: `NSE:SOMETHING-BE`
- Must be delivered (can't be squared off intraday)
- Lower liquidity, wider spreads
- **Status**: ❌ Blocked in Top Algos
- **Reason**: `trade_to_trade`

#### 2. **Special Series (BZ)**
- Example: `NSE:RISKY-BZ`
- High volatility, surveillance stocks
- Additional risk factors
- **Status**: ❌ Blocked in Top Algos
- **Reason**: `special_series`

#### 3. **Blacklisted (BL)**
- Example: `NSE:PROBLEM-BL`
- Under regulatory scrutiny
- **Status**: ❌ Blocked in Top Algos
- **Reason**: `blacklisted`

#### 4. **Low Liquidity (Not in Universe)**
- Example: Obscure small-cap with low volume
- Not in curated 600+ universe
- Potentially illiquid
- **Status**: ❌ Blocked in Top Algos
- **Reason**: `low_liquidity`

## Implementation Details

### Top Algos Filtering

```python
# backend/app/engine_v2.py

def _universe_soft_reason(sym: str, pol: Dict) -> Optional[str]:
    """
    Strict filtering for Top Algos.
    Only shows intraday-suitable stocks.
    """
    from .universe import get_non_intraday_reason
    
    # Check if stock is suitable for intraday
    reason = get_non_intraday_reason(sym)
    if reason:
        return reason  # Block if not suitable
    
    return None  # Allow if suitable
```

**Result**: Top Algos shows stocks like:
- ✅ `NSE:INFY-EQ`
- ✅ `NSE:RELIANCE-EQ`
- ✅ `NSE:TCS-EQ`
- ❌ `NSE:SOMETHING-BE` (blocked: trade_to_trade)
- ❌ Obscure low-volume stocks (blocked: low_liquidity)

### Analyst - NO Filtering

```python
# backend/app/api_v2_hist.py

@router.get("/analyze")
def hist_analyze(...):
    """
    UNIVERSAL ANALYZER: Works with ANY NSE/BSE stock,
    regardless of intraday-suitability.
    """
    # NO filtering here!
    # Fetch and analyze ANY stock
```

**Result**: Analyst works with:
- ✅ `NSE:INFY-EQ` (good for intraday)
- ✅ `NSE:SOMETHING-BE` (NOT good for intraday, but can analyze)
- ✅ `NSE:OBSCURE` (low liquidity, but can analyze)
- ✅ ANY valid NSE/BSE stock

## User Experience

### Scenario 1: Trading with Top Algos

```
User opens Top Algos tab:
- Sees: NSE:INFY, NSE:RELIANCE, NSE:TCS, etc. (all EQ series, high liquidity)
- Does NOT see: BE series stocks, low liquidity stocks
- Clicks "Open" on NSE:INFY
- Analyst shows detailed analysis for trading
```

**Why**: Top Algos is for actual trading - only show actionable opportunities!

### Scenario 2: Analyzing with Analyst

```
User opens Analyst tab:
- Enters: NSE:SOMETHING-BE (trade-to-trade stock)
- Clicks "Load Day"
- System: ✅ Loads data successfully!
- Shows: Full analysis with charts, indicators, etc.
- User can study: "Why is this stock in BE series? What's the pattern?"
```

**Why**: Analyst is for learning - analyze anything to understand market behavior!

### Scenario 3: Filtering in Action

```
Top Algos Tab:
Stock: NSE:RISKY-BE
Status: Blocked
Reason: "trade_to_trade"
Display: ❌ Not shown in Top Algos list

Analyst Tab:
Stock: NSE:RISKY-BE
Status: ✅ Can be analyzed
Display: Full analysis available
Message: "Note: This stock is in BE series (trade-to-trade) - not suitable for intraday trading"
```

## Benefits of This Approach

### For Traders (Top Algos)
✅ **Safety**: Only see stocks suitable for intraday  
✅ **Efficiency**: No time wasted on illiquid stocks  
✅ **Confidence**: All recommendations are actionable  
✅ **Risk Management**: Automatic filtering of risky series  

### For Learners (Analyst)
✅ **Freedom**: Analyze any stock for educational purposes  
✅ **Understanding**: Learn why certain stocks aren't tradeable  
✅ **Flexibility**: Study historical patterns of any stock  
✅ **Comprehensive**: No artificial limitations  

## Configuration

### Policy Settings

You can control the filtering behavior via policy:

```json
{
  "universe": {
    "mode": "strict",  // Options: strict, soft, off
    "exclude_patterns": ["-BE", "-BZ", "-BL"]
  }
}
```

**Modes**:
- **strict**: Block non-intraday stocks completely (default for Top Algos)
- **soft**: Show but mark as "Blocked" with reason
- **off**: No filtering (not recommended for Top Algos)

**Note**: Analyst ALWAYS operates with no filtering, regardless of policy settings.

## Technical Implementation

### Filtering Functions

```python
# backend/app/universe.py

def is_intraday_tradable(symbol: str, strict: bool = True) -> bool:
    """
    Check if suitable for intraday trading.
    
    strict=True: Must be in curated universe (for Top Algos)
    strict=False: Just check series suffix (for Analyst)
    """
    # 1. Exclude BE, BZ, BL series
    if symbol.endswith("-BE"): return False
    if symbol.endswith("-BZ"): return False
    if symbol.endswith("-BL"): return False
    
    # 2. Check universe (if strict)
    if strict:
        return symbol in NSE_UNIVERSE
    
    # 3. Allow EQ series (for Analyst)
    return symbol.endswith("-EQ") or True

def get_non_intraday_reason(symbol: str) -> str | None:
    """
    Get reason why stock is not suitable for intraday.
    
    Returns:
        - "trade_to_trade" for BE series
        - "special_series" for BZ series
        - "blacklisted" for BL series
        - "low_liquidity" if not in universe
        - None if suitable
    """
    if symbol.endswith("-BE"): return "trade_to_trade"
    if symbol.endswith("-BZ"): return "special_series"
    if symbol.endswith("-BL"): return "blacklisted"
    if symbol not in NSE_UNIVERSE: return "low_liquidity"
    return None
```

### Usage in Code

```python
# Top Algos - Apply strict filtering
def plan(top_n: int = 10):
    for sym in list_active_symbols():
        # Check if suitable for intraday
        reason = _universe_soft_reason(sym, pol)
        if reason:
            readiness = "Blocked"
            block_reason = reason
        # ... rest of logic

# Analyst - NO filtering
def hist_analyze(symbol: str, date: str, time: str):
    # Fetch and analyze ANY stock
    bars = _fetch_and_cache_historical_bars(symbol, date)
    # No filtering check!
    return analyze_snapshot(...)
```

## Examples

### Top Algos List (Filtered)

```
✅ NSE:INFY-EQ         | Score: 85 | Readiness: Ready
✅ NSE:RELIANCE-EQ     | Score: 82 | Readiness: Ready
✅ NSE:TCS-EQ          | Score: 78 | Readiness: Near
❌ NSE:LOWVOL-EQ       | Score: -- | Blocked: low_liquidity
❌ NSE:RISKY-BE        | Score: -- | Blocked: trade_to_trade
```

### Analyst (Universal)

```
Query: NSE:INFY-EQ
Result: ✅ Full analysis available
Note: "High liquidity stock, suitable for intraday trading"

Query: NSE:RISKY-BE
Result: ✅ Full analysis available
Note: "⚠️ This stock is in BE series (trade-to-trade). Not suitable for intraday trading, but you can analyze historical behavior."

Query: NSE:OBSCURE
Result: ✅ Full analysis available (if data exists)
Note: "This stock is not in our curated universe. Check liquidity before trading."
```

## Summary

| Aspect | Top Algos | Analyst |
|--------|-----------|---------|
| **Purpose** | Real trading opportunities | Universal analysis tool |
| **Filtering** | ✅ Strict (intraday-only) | ❌ None (universal) |
| **Shows** | EQ series, high liquidity | ANY valid stock |
| **Blocks** | BE, BZ, BL, low liquidity | Nothing |
| **Use Case** | Execute trades | Learn & analyze |
| **Universe** | 600+ curated stocks | ALL NSE/BSE stocks |

## Conclusion

The distinction is clear:
- **Top Algos** = Strict filtering for safe, actionable trading opportunities
- **Analyst** = Universal tool for learning and comprehensive analysis

This gives you the best of both worlds:
1. **Safety and efficiency** in your trading recommendations
2. **Freedom and flexibility** in your analysis capabilities

You can trust Top Algos to only show you stocks you should actually trade, while using Analyst to learn from any stock in the market! 🎯

---

**Files Changed**:
1. `backend/app/universe.py` - Added comprehensive filtering functions
2. `backend/app/engine_v2.py` - Applied filtering to Top Algos
3. `backend/app/api_v2_hist.py` - Documented Analyst as universal

**Status**: ✅ Complete - Top Algos shows only intraday-tradeable stocks, Analyst remains universal!
