#!/bin/bash
# Ticker Diagnostic Script
# Run this to diagnose why the ticker is not working

set -e

echo "🔍 TICKER DIAGNOSTIC TOOL"
echo "=========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_docker() {
    echo "1️⃣  Checking Docker..."
    if command -v docker &> /dev/null && command -v docker compose &> /dev/null; then
        echo -e "   ${GREEN}✅ Docker installed${NC}"
        
        if docker compose ps | grep -q "Up"; then
            echo -e "   ${GREEN}✅ Docker containers running${NC}"
            docker compose ps
        else
            echo -e "   ${RED}❌ Docker containers NOT running${NC}"
            echo "   Fix: Run 'docker compose up -d'"
            return 1
        fi
    else
        echo -e "   ${RED}❌ Docker not found${NC}"
        echo "   Fix: Install Docker and Docker Compose"
        return 1
    fi
    echo ""
}

check_ticker_process() {
    echo "2️⃣  Checking Ticker Process..."
    if docker compose ps ticker | grep -q "Up"; then
        echo -e "   ${GREEN}✅ Ticker container is running${NC}"
        
        # Check if it's actually healthy (not crash-looping)
        RESTARTS=$(docker compose ps ticker | grep ticker | awk '{print $4}')
        if [[ "$RESTARTS" == *"Restarting"* ]]; then
            echo -e "   ${YELLOW}⚠️  Ticker is restarting (crash loop)${NC}"
            echo "   Check logs: docker compose logs ticker"
        fi
    else
        echo -e "   ${RED}❌ Ticker container NOT running${NC}"
        echo "   Fix: docker compose up -d ticker"
        return 1
    fi
    echo ""
}

check_ticker_logs() {
    echo "3️⃣  Checking Ticker Logs (last 20 lines)..."
    echo "   ----------------------------------------"
    docker compose logs ticker --tail 20 2>&1 | sed 's/^/   /'
    echo "   ----------------------------------------"
    
    # Check for specific errors
    if docker compose logs ticker --tail 100 | grep -q "Kite session not ready"; then
        echo -e "   ${RED}❌ ERROR: Not logged in to Zerodha${NC}"
        echo "   Fix: Go to http://localhost:3000 and click 'Login with Zerodha'"
        return 1
    fi
    
    if docker compose logs ticker --tail 100 | grep -q "No instruments loaded"; then
        echo -e "   ${RED}❌ ERROR: No instruments loaded${NC}"
        echo "   Fix: Check EXCHANGES env var and Kite API credentials"
        return 1
    fi
    
    if docker compose logs ticker --tail 100 | grep -q "connected and subscribed"; then
        echo -e "   ${GREEN}✅ Ticker successfully connected and subscribed${NC}"
    else
        echo -e "   ${YELLOW}⚠️  No successful connection message found${NC}"
    fi
    echo ""
}

check_redis() {
    echo "4️⃣  Checking Redis State..."
    
    if ! docker compose ps redis | grep -q "Up"; then
        echo -e "   ${RED}❌ Redis container NOT running${NC}"
        echo "   Fix: docker compose up -d redis"
        return 1
    fi
    
    # Check ticker heartbeat
    HEARTBEAT=$(docker compose exec -T redis redis-cli GET ticker:alive 2>/dev/null || echo "0")
    CURRENT_TIME=$(date +%s)
    AGE=$((CURRENT_TIME - HEARTBEAT))
    
    if [ "$HEARTBEAT" == "0" ] || [ "$HEARTBEAT" == "" ]; then
        echo -e "   ${RED}❌ Ticker heartbeat: NEVER (ticker never connected)${NC}"
    elif [ $AGE -lt 15 ]; then
        echo -e "   ${GREEN}✅ Ticker heartbeat: ${AGE}s ago (ALIVE)${NC}"
    elif [ $AGE -lt 60 ]; then
        echo -e "   ${YELLOW}⚠️  Ticker heartbeat: ${AGE}s ago (STALE)${NC}"
    else
        echo -e "   ${RED}❌ Ticker heartbeat: ${AGE}s ago (DEAD)${NC}"
    fi
    
    # Check active symbols
    SYMBOL_COUNT=$(docker compose exec -T redis redis-cli SCARD symbols:active 2>/dev/null || echo "0")
    if [ "$SYMBOL_COUNT" -gt 0 ]; then
        echo -e "   ${GREEN}✅ Active symbols: ${SYMBOL_COUNT}${NC}"
    else
        echo -e "   ${RED}❌ Active symbols: 0 (no symbols subscribed)${NC}"
        echo "   Fix: Configure universe limit in Config tab"
    fi
    
    # Check universe limit
    UNIVERSE_LIMIT=$(docker compose exec -T redis redis-cli GET cfg:universe_limit 2>/dev/null || echo "not set")
    if [ "$UNIVERSE_LIMIT" != "not set" ] && [ "$UNIVERSE_LIMIT" != "" ]; then
        echo -e "   ${GREEN}✅ Universe limit: ${UNIVERSE_LIMIT}${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Universe limit: not set (using default)${NC}"
    fi
    
    echo ""
}

check_authentication() {
    echo "5️⃣  Checking Zerodha Authentication..."
    
    if docker compose exec -T ticker test -f /app/app/data/session/.kite_session.json 2>/dev/null; then
        echo -e "   ${GREEN}✅ Kite session file exists${NC}"
        
        # Try to read session validity (if jq is available)
        if command -v jq &> /dev/null; then
            SESSION_DATA=$(docker compose exec -T ticker cat /app/app/data/session/.kite_session.json 2>/dev/null)
            USER_NAME=$(echo "$SESSION_DATA" | jq -r '.user_name' 2>/dev/null || echo "unknown")
            echo -e "   ${GREEN}✅ Logged in as: ${USER_NAME}${NC}"
        fi
    else
        echo -e "   ${RED}❌ No Kite session file found${NC}"
        echo "   Fix: Login via http://localhost:3000"
        return 1
    fi
    
    echo ""
}

check_env_vars() {
    echo "6️⃣  Checking Environment Variables..."
    
    KITE_KEY=$(docker compose exec -T ticker env 2>/dev/null | grep KITE_API_KEY | cut -d= -f2)
    if [ -n "$KITE_KEY" ] && [ "$KITE_KEY" != "your_kite_api_key_here" ]; then
        echo -e "   ${GREEN}✅ KITE_API_KEY is set${NC}"
    else
        echo -e "   ${RED}❌ KITE_API_KEY not configured${NC}"
        echo "   Fix: Set in backend/.env"
        return 1
    fi
    
    REDIS_URL=$(docker compose exec -T ticker env 2>/dev/null | grep REDIS_URL | cut -d= -f2)
    if [ -n "$REDIS_URL" ]; then
        echo -e "   ${GREEN}✅ REDIS_URL: ${REDIS_URL}${NC}"
    else
        echo -e "   ${YELLOW}⚠️  REDIS_URL not set (using default)${NC}"
    fi
    
    echo ""
}

check_market_hours() {
    echo "7️⃣  Checking Market Hours..."
    
    # This is a simplified check - doesn't account for holidays
    CURRENT_HOUR=$(TZ=Asia/Kolkata date +%H)
    CURRENT_MIN=$(TZ=Asia/Kolkata date +%M)
    CURRENT_DAY=$(TZ=Asia/Kolkata date +%u)
    CURRENT_TIME=$(TZ=Asia/Kolkata date +"%Y-%m-%d %H:%M:%S %Z")
    
    echo "   📅 IST Time: ${CURRENT_TIME}"
    
    if [ "$CURRENT_DAY" -ge 6 ]; then
        echo -e "   ${YELLOW}⚠️  Market is CLOSED (Weekend)${NC}"
        echo "   Ticker won't receive ticks outside Mon-Fri"
    elif [ "$CURRENT_HOUR" -lt 9 ] || [ "$CURRENT_HOUR" -gt 15 ]; then
        echo -e "   ${YELLOW}⚠️  Market is CLOSED (Outside 09:15-15:30)${NC}"
        echo "   Ticker won't receive ticks outside market hours"
    elif [ "$CURRENT_HOUR" -eq 9 ] && [ "$CURRENT_MIN" -lt 15 ]; then
        echo -e "   ${YELLOW}⚠️  Market is CLOSED (Before 09:15)${NC}"
    elif [ "$CURRENT_HOUR" -eq 15 ] && [ "$CURRENT_MIN" -gt 30 ]; then
        echo -e "   ${YELLOW}⚠️  Market is CLOSED (After 15:30)${NC}"
    else
        echo -e "   ${GREEN}✅ Market is OPEN (ticks should be flowing)${NC}"
    fi
    
    echo ""
}

check_network() {
    echo "8️⃣  Checking Network Connectivity..."
    
    if docker compose exec -T ticker ping -c 2 -W 2 kite.zerodha.com &>/dev/null; then
        echo -e "   ${GREEN}✅ Can reach kite.zerodha.com${NC}"
    else
        echo -e "   ${RED}❌ Cannot reach kite.zerodha.com${NC}"
        echo "   Fix: Check internet connection or firewall"
        return 1
    fi
    
    if docker compose exec -T ticker ping -c 2 -W 2 api.kite.trade &>/dev/null; then
        echo -e "   ${GREEN}✅ Can reach api.kite.trade${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Cannot reach api.kite.trade${NC}"
    fi
    
    echo ""
}

# Run all checks
echo "Running diagnostics..."
echo ""

ERRORS=0

check_docker || ((ERRORS++))
check_ticker_process || ((ERRORS++))
check_ticker_logs || ((ERRORS++))
check_redis || ((ERRORS++))
check_authentication || ((ERRORS++))
check_env_vars || ((ERRORS++))
check_market_hours || true  # Don't count as error
check_network || ((ERRORS++))

# Summary
echo "=========================================="
echo "📊 DIAGNOSTIC SUMMARY"
echo "=========================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    echo ""
    echo "If ticker still shows 'stopped' in frontend:"
    echo "  1. Refresh browser (Ctrl/Cmd + R)"
    echo "  2. Check if market is open (09:15-15:30 IST, Mon-Fri)"
    echo "  3. Wait 15-30 seconds for initial connection"
    echo "  4. Check browser console for errors"
else
    echo -e "${RED}❌ Found ${ERRORS} critical issue(s)${NC}"
    echo ""
    echo "Quick fixes to try:"
    echo "  1. docker compose up -d                    # Start all containers"
    echo "  2. docker compose restart ticker           # Restart ticker"
    echo "  3. Login: http://localhost:3000            # Re-authenticate"
    echo "  4. docker compose logs ticker -f           # Watch logs"
fi

echo ""
echo "📚 For detailed analysis, see: TICKER_DEEP_DIVE_ANALYSIS.md"
