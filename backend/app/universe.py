"""
Universe of intraday tradable stocks for Indian markets (NSE/BSE)
Top 300 liquid stocks suitable for intraday trading
"""

# Top 300 NSE stocks by liquidity and intraday activity
# Categorized for easy maintenance
NSE_TOP_300 = [
    # Nifty 50 - Highest liquidity
    "NSE:RELIANCE", "NSE:TCS", "NSE:HDFCBANK", "NSE:INFY", "NSE:ICICIBANK",
    "NSE:HINDUNILVR", "NSE:ITC", "NSE:SBIN", "NSE:BHARTIARTL", "NSE:KOTAKBANK",
    "NSE:LT", "NSE:AXISBANK", "NSE:ASIANPAINT", "NSE:MARUTI", "NSE:SUNPHARMA",
    "NSE:TITAN", "NSE:ULTRACEMCO", "NSE:WIPRO", "NSE:NESTLEIND", "NSE:BAJFINANCE",
    "NSE:HCLTECH", "NSE:POWERGRID", "NSE:NTPC", "NSE:TATAMOTORS", "NSE:TATASTEEL",
    "NSE:ONGC", "NSE:M&M", "NSE:TECHM", "NSE:ADANIPORTS", "NSE:COALINDIA",
    "NSE:BAJAJFINSV", "NSE:BAJAJ-AUTO", "NSE:DIVISLAB", "NSE:DRREDDY", "NSE:EICHERMOT",
    "NSE:GRASIM", "NSE:HEROMOTOCO", "NSE:HINDALCO", "NSE:INDUSINDBK", "NSE:JSWSTEEL",
    "NSE:CIPLA", "NSE:BRITANNIA", "NSE:APOLLOHOSP", "NSE:BPCL", "NSE:TATACONSUM",
    "NSE:UPL", "NSE:SBILIFE", "NSE:SHRIRAMFIN", "NSE:ADANIENT", "NSE:LTIM",
    
    # Nifty Next 50 - High liquidity
    "NSE:ADANIGREEN", "NSE:ADANIPORTS", "NSE:AMBUJACEM", "NSE:BANDHANBNK", "NSE:BERGEPAINT",
    "NSE:BOSCHLTD", "NSE:CHOLAFIN", "NSE:COLPAL", "NSE:DABUR", "NSE:DLF",
    "NSE:GAIL", "NSE:GODREJCP", "NSE:HAVELLS", "NSE:HDFCAMC", "NSE:HDFCLIFE",
    "NSE:ICICIGI", "NSE:ICICIPRULI", "NSE:INDIGO", "NSE:JINDALSTEL", "NSE:MARICO",
    "NSE:MUTHOOTFIN", "NSE:NMDC", "NSE:NYKAA", "NSE:PAGEIND", "NSE:PIDILITIND",
    "NSE:PNB", "NSE:RECLTD", "NSE:SBICARD", "NSE:SIEMENS", "NSE:TATAPOWER",
    "NSE:TORNTPHARM", "NSE:TRENT", "NSE:UNITDSPR", "NSE:VEDL", "NSE:ZOMATO",
    "NSE:ABB", "NSE:ALKEM", "NSE:AMBUJACEM", "NSE:ASHOKLEY", "NSE:AUROPHARMA",
    "NSE:BALKRISIND", "NSE:BANKBARODA", "NSE:BEL", "NSE:BIOCON", "NSE:CANBK",
    
    # Banking & Finance - High intraday volatility
    "NSE:FEDERALBNK", "NSE:IDFCFIRSTB", "NSE:INDHOTEL", "NSE:IOC", "NSE:IRCTC",
    "NSE:LTF", "NSE:MOTHERSON", "NSE:MRF", "NSE:NAUKRI", "NSE:OBEROIRLTY",
    "NSE:OFSS", "NSE:OIL", "NSE:PERSISTENT", "NSE:PETRONET", "NSE:PFC",
    "NSE:PIIND", "NSE:PVR", "NSE:RBLBANK", "NSE:SAIL", "NSE:SOLARINDS",
    "NSE:THERMAX", "NSE:TIINDIA", "NSE:TORNTPOWER", "NSE:TVSMOTOR", "NSE:UNIONBANK",
    "NSE:VOLTAS", "NSE:YESBANK", "NSE:ZEEL", "NSE:APLAPOLLO", "NSE:ASTRAL",
    
    # IT & Technology
    "NSE:COFORGE", "NSE:LTTS", "NSE:MPHASIS", "NSE:TECHM", "NSE:MINDTREE",
    "NSE:PERSISTENT", "NSE:SONACOMS", "NSE:CYIENT", "NSE:KPITTECH", "NSE:ROUTE",
    "NSE:TATAELXSI", "NSE:ZENTEC", "NSE:POLYCAB", "NSE:CUMMINSIND", "NSE:SCHAEFFLER",
    
    # Pharma & Healthcare
    "NSE:LUPIN", "NSE:AUROPHARMA", "NSE:CADILAHC", "NSE:LALPATHLAB", "NSE:METROPOLIS",
    "NSE:LAURUSLABS", "NSE:ABBOTINDIA", "NSE:GLAXO", "NSE:IPCALAB", "NSE:NATCOPHARMA",
    "NSE:GRANULES", "NSE:STRIDES", "NSE:GLAND", "NSE:SYNGENE", "NSE:AJANTPHARM",
    
    # FMCG & Consumer
    "NSE:GODREJCP", "NSE:BATAINDIA", "NSE:MCDOWELL-N", "NSE:VGUARD", "NSE:CROMPTON",
    "NSE:HAVELLS", "NSE:WHIRLPOOL", "NSE:VOLTAS", "NSE:RAJESHEXPO", "NSE:JUBLFOOD",
    "NSE:VAIBHAVGBL", "NSE:VBL", "NSE:TASTYBITE", "NSE:CCL", "NSE:EMAMILTD",
    
    # Auto & Auto Ancillaries
    "NSE:ESCORTS", "NSE:EXIDEIND", "NSE:MRF", "NSE:APOLLOTYRE", "NSE:BALKRISIND",
    "NSE:MOTHERSON", "NSE:BOSCHLTD", "NSE:AMARAJABAT", "NSE:ENDURANCE", "NSE:SUPREMEIND",
    "NSE:TUBEINVEST", "NSE:BHARATFORG", "NSE:SKFINDIA", "NSE:MINDAIND", "NSE:ATUL",
    
    # Metals & Mining
    "NSE:HINDZINC", "NSE:NMDC", "NSE:NATIONALUM", "NSE:JINDALSTEL", "NSE:SAIL",
    "NSE:RATNAMANI", "NSE:WELCORP", "NSE:WELSPUNIND", "NSE:JSWENERGY", "NSE:MOIL",
    "NSE:VEDL", "NSE:HINDALCO", "NSE:TATASTEEL", "NSE:JSWSTEEL", "NSE:COALINDIA",
    
    # Energy & Power
    "NSE:NTPC", "NSE:POWERGRID", "NSE:ADANIPOWER", "NSE:TATAPOWER", "NSE:TORNTPOWER",
    "NSE:NHPC", "NSE:SJVN", "NSE:CESC", "NSE:RELINFRA", "NSE:ADANIGREEN",
    "NSE:IOC", "NSE:BPCL", "NSE:HINDPETRO", "NSE:ONGC", "NSE:OIL",
    "NSE:BHEL", "NSE:BEL", "NSE:HAL", "NSE:GAIL", "NSE:PFC",
    
    # Infrastructure & Realty
    "NSE:DLF", "NSE:GODREJPROP", "NSE:OBEROIRLTY", "NSE:PRESTIGE", "NSE:BRIGADE",
    "NSE:PHOENIXLTD", "NSE:IBREALEST", "NSE:SOBHA", "NSE:SUNTECK", "NSE:MAHLIFE",
    "NSE:LT", "NSE:ADANIPORTS", "NSE:GMR", "NSE:IRB", "NSE:JKCEMENT",
    
    # Telecom & Media
    "NSE:BHARTIARTL", "NSE:ZEEL", "NSE:PVR", "NSE:SAREGAMA", "NSE:TVTODAY",
    "NSE:HATHWAY", "NSE:NETWORK18", "NSE:TV18BRDCST", "NSE:INOXLEISUR", "NSE:TIPS",
    
    # Chemicals & Fertilizers
    "NSE:UPL", "NSE:PI", "NSE:DEEPAKNI", "NSE:AARTI", "NSE:NOCIL",
    "NSE:TATACHEMCAL", "NSE:GNFC", "NSE:CHAMBLFERT", "NSE:SUMICHEM", "NSE:NAVINFLUOR",
    "NSE:SRF", "NSE:ATUL", "NSE:CLEAN", "NSE:FINEORG", "NSE:ALKYLAMINE",
    
    # Cement & Construction
    "NSE:ULTRACEMCO", "NSE:AMBUJACEM", "NSE:ACC", "NSE:SHREECEM", "NSE:DALMIACEM",
    "NSE:JKCEMENT", "NSE:RAMCOCEM", "NSE:HEIDELBERG", "NSE:SUNDRMBRAK", "NSE:VINATIORGA",
    
    # Textiles & Apparel
    "NSE:RAYMOND", "NSE:ARVIND", "NSE:AHLUCONT", "NSE:WELSPUNIND", "NSE:VARDHACRLC",
    "NSE:TRIDENT", "NSE:GOENKA", "NSE:KPR", "NSE:PGHH", "NSE:PAGEIND",
    
    # Retail & E-commerce
    "NSE:TRENT", "NSE:ABFRL", "NSE:SHOPERSTOP", "NSE:TITAN", "NSE:VMART",
    "NSE:NYKAA", "NSE:ZOMATO", "NSE:PAYTM", "NSE:POLICYBZR", "NSE:INDIAMART",
    
    # Hotels & Tourism
    "NSE:INDHOTEL", "NSE:LEMONTREE", "NSE:CHALET", "NSE:MAHINDCIE", "NSE:EIH",
    "NSE:EIHOTEL", "NSE:TAJGVK", "NSE:ORIENTHOT", "NSE:ROYALORCHID", "NSE:COX&KINGS",
    
    # Logistics & Transport
    "NSE:CONCOR", "NSE:GICRE", "NSE:TCI", "NSE:VRL", "NSE:MAHLOG",
    "NSE:DELHIVERY", "NSE:BLUEDART", "NSE:AEGISCHEM", "NSE:GATEWAY", "NSE:ALLCARGO",
    
    # Additional High-Volume Stocks
    "NSE:LICHSGFIN", "NSE:CHOLAFIN", "NSE:POONAWALLA", "NSE:BAJAJHLDNG", "NSE:MANAPPURAM",
    "NSE:MOTILALOFS", "NSE:CDSL", "NSE:CAMS", "NSE:CREDITACC", "NSE:IIFL",
    "NSE:360ONE", "NSE:ANANDRATHI", "NSE:ANGELONE", "NSE:PAYTM", "NSE:POLICYBZR",
]

# BSE high-volume stocks (additional to NSE)
BSE_HIGH_VOLUME = [
    "BSE:RELIANCE", "BSE:TCS", "BSE:HDFCBANK", "BSE:INFY", "BSE:ICICIBANK",
    "BSE:SBIN", "BSE:BHARTIARTL", "BSE:ITC", "BSE:LT", "BSE:KOTAKBANK",
]


def get_intraday_universe(limit: int = 300, exchange: str = "NSE") -> list[str]:
    """
    Get list of intraday tradable stocks.
    
    Args:
        limit: Maximum number of stocks to return (default 300)
        exchange: Exchange to filter (NSE/BSE/ALL, default NSE)
    
    Returns:
        List of stock symbols in EXCHANGE:SYMBOL format
    """
    if exchange.upper() == "ALL":
        universe = NSE_TOP_300 + BSE_HIGH_VOLUME
    elif exchange.upper() == "BSE":
        universe = BSE_HIGH_VOLUME
    else:  # NSE or default
        universe = NSE_TOP_300
    
    return universe[:limit]


def is_intraday_tradable(symbol: str) -> bool:
    """
    Check if a symbol is suitable for intraday trading.
    
    Args:
        symbol: Symbol in EXCHANGE:SYMBOL format
    
    Returns:
        True if symbol is in the intraday universe
    """
    symbol = symbol.upper().replace(" ", "")
    all_symbols = NSE_TOP_300 + BSE_HIGH_VOLUME
    return symbol in all_symbols


def get_symbol_category(symbol: str) -> str:
    """
    Get category of a symbol (for filtering/grouping).
    
    Returns:
        Category name like "Nifty50", "Banking", "IT", etc.
    """
    symbol = symbol.upper().replace(" ", "")
    
    nifty_50 = NSE_TOP_300[:50]
    if symbol in nifty_50:
        return "Nifty50"
    
    # Simple categorization by common patterns
    if any(x in symbol for x in ["BANK", "FINSV", "FINSERV", "CHOLA", "BAJAJ"]):
        return "Banking & Finance"
    elif any(x in symbol for x in ["TCS", "INFY", "WIPRO", "TECH", "HCLTECH", "LTTS", "LTIM"]):
        return "IT & Technology"
    elif any(x in symbol for x in ["PHARMA", "CIPLA", "DRREDDY", "LUPIN", "BIO", "LABS"]):
        return "Pharma & Healthcare"
    elif any(x in symbol for x in ["TATA", "MARUTI", "BAJAJ-AUTO", "HERO", "EICHER"]):
        return "Auto & Ancillaries"
    elif any(x in symbol for x in ["STEEL", "HINDALCO", "VEDL", "JINDAL", "COAL"]):
        return "Metals & Mining"
    elif any(x in symbol for x in ["NTPC", "POWER", "ONGC", "IOC", "BPCL"]):
        return "Energy & Power"
    elif any(x in symbol for x in ["CEMENT", "DLF", "GODREJ", "OBEROI"]):
        return "Infrastructure & Realty"
    
    return "Others"
