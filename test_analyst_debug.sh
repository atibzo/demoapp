#!/bin/bash
# Test script for analyst tool debugging
# Run this to diagnose issues with the analyst tool

set -e

API_URL="${API_URL:-http://localhost:8000}"
SYMBOL="${1:-BSE:BHEL}"
DATE="${2:-2025-10-14}"

echo "================================================"
echo "🔍 Analyst Tool Debug Test"
echo "================================================"
echo "API URL: $API_URL"
echo "Symbol: $SYMBOL"
echo "Date: $DATE"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Check Authentication${NC}"
echo "---"
AUTH_RESPONSE=$(curl -s "$API_URL/api/v2/session")
ZERODHA_OK=$(echo "$AUTH_RESPONSE" | grep -o '"zerodha":[^,}]*' | cut -d':' -f2)

if [ "$ZERODHA_OK" = "true" ]; then
    echo -e "${GREEN}✅ Zerodha authenticated${NC}"
else
    echo -e "${RED}❌ Not authenticated with Zerodha${NC}"
    echo "Please login first: $API_URL/kite/login_url"
    exit 1
fi
echo ""

echo -e "${BLUE}Step 2: Test Symbol Lookup${NC}"
echo "---"
LOOKUP_RESPONSE=$(curl -s "$API_URL/api/v2/hist/debug/lookup?symbol=$SYMBOL&show_matches=true")
echo "$LOOKUP_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOOKUP_RESPONSE"

SUCCESS=$(echo "$LOOKUP_RESPONSE" | grep -o '"success":[^,}]*' | cut -d':' -f2)
TOKEN=$(echo "$LOOKUP_RESPONSE" | grep -o '"token":[^,}]*' | cut -d':' -f2)
CACHE_EMPTY=$(echo "$LOOKUP_RESPONSE" | grep -o '"cache_is_empty":[^,}]*' | cut -d':' -f2)

echo ""
if [ "$SUCCESS" = "true" ]; then
    echo -e "${GREEN}✅ Symbol lookup successful!${NC}"
    echo "Token: $TOKEN"
else
    echo -e "${RED}❌ Symbol lookup failed${NC}"
    
    if [ "$CACHE_EMPTY" = "true" ]; then
        echo -e "${YELLOW}⚠️  Cache is empty! Attempting to refresh...${NC}"
        echo ""
        
        echo -e "${BLUE}Step 2.1: Refresh Cache${NC}"
        echo "---"
        REFRESH_RESPONSE=$(curl -s -X POST "$API_URL/api/v2/hist/debug/cache/refresh")
        echo "$REFRESH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$REFRESH_RESPONSE"
        echo ""
        
        echo -e "${BLUE}Step 2.2: Retry Symbol Lookup${NC}"
        echo "---"
        LOOKUP_RESPONSE=$(curl -s "$API_URL/api/v2/hist/debug/lookup?symbol=$SYMBOL&show_matches=true")
        echo "$LOOKUP_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOOKUP_RESPONSE"
        
        SUCCESS=$(echo "$LOOKUP_RESPONSE" | grep -o '"success":[^,}]*' | cut -d':' -f2)
        if [ "$SUCCESS" = "true" ]; then
            echo -e "${GREEN}✅ Symbol lookup successful after cache refresh!${NC}"
        else
            echo -e "${RED}❌ Symbol still not found. Check similar_matches in the response.${NC}"
        fi
    fi
fi
echo ""

echo -e "${BLUE}Step 3: Fetch Historical Bars${NC}"
echo "---"
BARS_RESPONSE=$(curl -s "$API_URL/api/v2/hist/bars?symbol=$SYMBOL&date=$DATE&auto_fetch=true")

if echo "$BARS_RESPONSE" | grep -q '"bars"'; then
    BAR_COUNT=$(echo "$BARS_RESPONSE" | grep -o '"bars":\[[^]]*' | grep -o '{' | wc -l)
    echo -e "${GREEN}✅ Successfully fetched $BAR_COUNT bars${NC}"
    echo "Sample of first bar:"
    echo "$BARS_RESPONSE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(json.dumps(data['bars'][0], indent=2) if data.get('bars') else 'No bars')" 2>/dev/null
else
    echo -e "${RED}❌ Failed to fetch bars${NC}"
    echo "$BARS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$BARS_RESPONSE"
fi
echo ""

echo "================================================"
echo "🏁 Test Complete"
echo "================================================"
echo ""
echo "📋 Summary:"
echo "  - Authentication: $([ "$ZERODHA_OK" = "true" ] && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAILED${NC}")"
echo "  - Symbol Lookup: $([ "$SUCCESS" = "true" ] && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAILED${NC}")"
echo "  - Data Fetch: $(echo "$BARS_RESPONSE" | grep -q '"bars"' && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAILED${NC}")"
echo ""

if [ "$SUCCESS" != "true" ] || ! echo "$BARS_RESPONSE" | grep -q '"bars"'; then
    echo -e "${YELLOW}💡 Troubleshooting Tips:${NC}"
    echo "  1. Check backend logs: docker-compose logs api | tail -50"
    echo "  2. Verify symbol format: Should be 'NSE:SYMBOL' or 'BSE:SYMBOL'"
    echo "  3. Check if date is a trading day (not weekend/holiday)"
    echo "  4. If rate limited, wait 10 minutes and retry"
    echo "  5. Try alternate exchange: NSE:BHEL instead of BSE:BHEL"
    echo ""
    exit 1
fi

echo -e "${GREEN}🎉 All tests passed! Analyst tool is working.${NC}"
exit 0
