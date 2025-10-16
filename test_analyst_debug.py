#!/usr/bin/env python3
"""
Analyst Tool Debug Tester - Python Version
Tests the analyst tool debug endpoints and verifies the fix.
"""

import sys
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API_URL = "http://localhost:8000"

# Color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

def print_color(text, color=Colors.NC):
    """Print colored text"""
    print(f"{color}{text}{Colors.NC}")

def print_header(text):
    """Print a section header"""
    print()
    print_color(f"{'='*70}", Colors.BLUE)
    print_color(f" {text}", Colors.BOLD)
    print_color(f"{'='*70}", Colors.BLUE)
    print()

def http_get(url):
    """Make HTTP GET request and return JSON"""
    try:
        with urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode('utf-8')}
    except URLError as e:
        return {"error": "Connection failed", "detail": str(e)}
    except Exception as e:
        return {"error": "Unknown error", "detail": str(e)}

def http_post(url):
    """Make HTTP POST request and return JSON"""
    try:
        req = Request(url, method='POST')
        with urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode('utf-8')}
    except URLError as e:
        return {"error": "Connection failed", "detail": str(e)}
    except Exception as e:
        return {"error": "Unknown error", "detail": str(e)}

def test_authentication():
    """Test if authenticated with Zerodha"""
    print_color("Step 1: Check Authentication", Colors.BLUE)
    print("---")
    
    response = http_get(f"{API_URL}/api/v2/session")
    
    if "error" in response:
        print_color(f"❌ Failed to connect: {response['error']}", Colors.RED)
        return False
    
    zerodha_ok = response.get("zerodha", False)
    
    if zerodha_ok:
        print_color("✅ Zerodha authenticated", Colors.GREEN)
        return True
    else:
        print_color("❌ Not authenticated with Zerodha", Colors.RED)
        print_color(f"Please login first: {API_URL}/kite/login_url", Colors.YELLOW)
        return False

def test_symbol_lookup(symbol, show_matches=True):
    """Test symbol lookup via debug endpoint"""
    print_color(f"Step 2: Test Symbol Lookup ({symbol})", Colors.BLUE)
    print("---")
    
    url = f"{API_URL}/api/v2/hist/debug/lookup?symbol={symbol}&show_matches={'true' if show_matches else 'false'}"
    response = http_get(url)
    
    if "error" in response:
        print_color(f"❌ Lookup failed: {response['error']}", Colors.RED)
        print(json.dumps(response, indent=2))
        return None
    
    print(json.dumps(response, indent=2))
    print()
    
    success = response.get("success", False)
    token = response.get("token")
    cache_empty = response.get("cache_status", {}).get("cache_is_empty", True)
    
    if success:
        print_color(f"✅ Symbol lookup successful!", Colors.GREEN)
        print(f"Token: {token}")
        print(f"Exchange: {response.get('found_exchange')}")
        return response
    else:
        print_color(f"❌ Symbol lookup failed", Colors.RED)
        
        if cache_empty:
            print_color("⚠️  Cache is empty! Attempting to refresh...", Colors.YELLOW)
            return None
        else:
            print_color("Symbol might not exist. Check similar_matches above.", Colors.YELLOW)
            return None

def refresh_cache():
    """Refresh the instruments cache"""
    print_color("Step 2.1: Refresh Cache", Colors.BLUE)
    print("---")
    
    response = http_post(f"{API_URL}/api/v2/hist/debug/cache/refresh")
    
    if "error" in response:
        print_color(f"❌ Cache refresh failed: {response['error']}", Colors.RED)
        return False
    
    print(json.dumps(response, indent=2))
    print()
    
    success = response.get("success", False)
    if success:
        print_color("✅ Cache refreshed successfully!", Colors.GREEN)
        return True
    else:
        print_color("❌ Cache refresh failed", Colors.RED)
        return False

def test_historical_bars(symbol, date):
    """Test fetching historical bars"""
    print_color(f"Step 3: Fetch Historical Bars ({symbol} on {date})", Colors.BLUE)
    print("---")
    
    url = f"{API_URL}/api/v2/hist/bars?symbol={symbol}&date={date}&auto_fetch=true"
    response = http_get(url)
    
    if "error" in response:
        print_color(f"❌ Failed to fetch bars: {response['error']}", Colors.RED)
        try:
            detail = json.loads(response['detail'])
            print(json.dumps(detail, indent=2))
        except:
            print(response['detail'])
        return False
    
    bars = response.get("bars", [])
    
    if bars:
        print_color(f"✅ Successfully fetched {len(bars)} bars", Colors.GREEN)
        if bars:
            print("\nSample of first bar:")
            print(json.dumps(bars[0], indent=2))
        return True
    else:
        print_color("❌ No bars returned", Colors.RED)
        return False

def main():
    """Main test function"""
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BSE:BHEL"
    date = sys.argv[2] if len(sys.argv) > 2 else "2025-10-14"
    
    print_header("🔍 Analyst Tool Debug Test")
    print(f"API URL: {API_URL}")
    print(f"Symbol: {symbol}")
    print(f"Date: {date}")
    
    # Test 1: Authentication
    print()
    if not test_authentication():
        print_color("\n❌ Test failed: Not authenticated", Colors.RED)
        sys.exit(1)
    
    # Test 2: Symbol Lookup
    print()
    lookup_result = test_symbol_lookup(symbol)
    
    # If lookup failed due to empty cache, try refreshing
    if not lookup_result:
        print()
        if refresh_cache():
            print()
            print_color("Step 2.2: Retry Symbol Lookup", Colors.BLUE)
            print("---")
            lookup_result = test_symbol_lookup(symbol, show_matches=False)
    
    lookup_success = lookup_result is not None and lookup_result.get("success", False)
    
    # Test 3: Historical Bars
    print()
    bars_success = test_historical_bars(symbol, date)
    
    # Summary
    print_header("🏁 Test Complete")
    
    print("📋 Summary:")
    print(f"  - Authentication: {'✅ OK' if test_authentication() else '❌ FAILED'}")
    print(f"  - Symbol Lookup: {'✅ OK' if lookup_success else '❌ FAILED'}")
    print(f"  - Data Fetch: {'✅ OK' if bars_success else '❌ FAILED'}")
    print()
    
    if not lookup_success or not bars_success:
        print_color("💡 Troubleshooting Tips:", Colors.YELLOW)
        print("  1. Check backend logs: docker-compose logs api | tail -50")
        print("  2. Verify symbol format: Should be 'NSE:SYMBOL' or 'BSE:SYMBOL'")
        print("  3. Check if date is a trading day (not weekend/holiday)")
        print("  4. If rate limited, wait 10 minutes and retry")
        print("  5. Try alternate exchange: NSE:BHEL instead of BSE:BHEL")
        print()
        sys.exit(1)
    
    print_color("🎉 All tests passed! Analyst tool is working.", Colors.GREEN)
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_color("\n\n⚠️  Test interrupted by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_color(f"\n\n❌ Unexpected error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)
