"""
Universe of intraday tradable stocks for Indian markets (NSE/BSE)
Expanded to 600+ liquid stocks suitable for intraday trading

NOTE: The Analyst feature works with ANY NSE/BSE stock, not just those in this list.
This universe is used for quick scanning in "Top Algos", but the analyst has 
a universal instrument lookup that can find and analyze ANY valid stock symbol.
"""

# Top 600+ NSE stocks by liquidity and intraday activity
# Categorized for easy maintenance
NSE_UNIVERSE = [
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
    
    # Mid-cap Banking & Finance (100+ stocks)
    "NSE:AUBANK", "NSE:IDFC", "NSE:EQUITAS", "NSE:UJJIVAN", "NSE:CREDITACC",
    "NSE:HOMEFIRST", "NSE:AAVAS", "NSE:CANFINHOME", "NSE:GRUH", "NSE:SHRIRAMCIT",
    "NSE:SRTRANSFIN", "NSE:MAHINDRA", "NSE:MMFIN", "NSE:SUNDARMFIN", "NSE:BAJAJCON",
    "NSE:JBCHEPHARM", "NSE:CAPLIPOINT", "NSE:ABSLAMC", "NSE:NAM-INDIA", "NSE:UTIAMC",
    
    # Mid-cap IT & Technology
    "NSE:INTELLECT", "NSE:HAPPSTMNDS", "NSE:RATEGAIN", "NSE:LATENTVIEW", "NSE:MASTEK",
    "NSE:DATAPATTNS", "NSE:NEWGEN", "NSE:KPITTECH", "NSE:CYIENT", "NSE:BIRLASOFT",
    "NSE:MAITHANALL", "NSE:NAUKRI", "NSE:ZOMATO", "NSE:IRCTC", "NSE:PAYTM",
    
    # Mid-cap Pharma
    "NSE:ALKEM", "NSE:TORNTPHARM", "NSE:IPCALAB", "NSE:LALPATHLAB", "NSE:METROPOLIS",
    "NSE:THYROCARE", "NSE:KRSNAA", "NSE:VIJAYA", "NSE:SANOFI", "NSE:PFIZER",
    "NSE:GLENMARK", "NSE:TORNTPHARM", "NSE:SUNPHARMA", "NSE:ALEMBIC", "NSE:JBCHEPHARM",
    
    # Consumer Goods
    "NSE:GILLETTE", "NSE:HONAUT", "NSE:RADICO", "NSE:VSTIND", "NSE:GODFRYPHLP",
    "NSE:JYOTHYLAB", "NSE:JUBLPHARMA", "NSE:MARICO", "NSE:GODREJCP", "NSE:EMAMILTD",
    "NSE:ZYDUSWELL", "NSE:ABBOTINDIA", "NSE:COLGATE", "NSE:HINDUNILVR", "NSE:ITC",
    
    # Auto Components & Manufacturing
    "NSE:ASALCBR", "NSE:SUNDRMFAST", "NSE:SUPRAJIT", "NSE:MINDA", "NSE:FIEM",
    "NSE:SANDHAR", "NSE:JBMUTO", "NSE:MOTHERSUMI", "NSE:SWARAJENG", "NSE:SCHAEFFLER",
    "NSE:WABCO", "NSE:WABAG", "NSE:BLUEDART", "NSE:CREDITACC", "NSE:TIINDIA",
    
    # Capital Goods & Engineering
    "NSE:AIAENG", "NSE:CUMMINSIND", "NSE:THERMAX", "NSE:CROMPTON", "NSE:HAVELLS",
    "NSE:POLYCAB", "NSE:KEI", "NSE:FINOLEX", "NSE:VGUARD", "NSE:DIXON",
    "NSE:AMBER", "NSE:KALPATPOWR", "NSE:CARBORUNIV", "NSE:GRINDWELL", "NSE:COCHINSHIP",
    
    # Metals & Commodity
    "NSE:APLAPOLLO", "NSE:JINDAL", "NSE:JINDALSTEL", "NSE:JSWSTEEL", "NSE:SAIL",
    "NSE:TATASTEEL", "NSE:HINDALCO", "NSE:VEDL", "NSE:NATIONALUM", "NSE:HINDZINC",
    "NSE:GMRINFRA", "NSE:ADANIPOWER", "NSE:ADANIGREEN", "NSE:NTPC", "NSE:POWERGRID",
    
    # Chemicals & Specialty
    "NSE:BALRAMCHIN", "NSE:GUJALKALI", "NSE:DCMSHRIRAM", "NSE:COROMANDEL", "NSE:GSFC",
    "NSE:GNFC", "NSE:RCF", "NSE:CHAMBLFERT", "NSE:NAVINFLUOR", "NSE:DEEPAKNTR",
    "NSE:AARTI", "NSE:ATUL", "NSE:CLEAN", "NSE:SRF", "NSE:PIDILITIND",
    
    # Real Estate & Construction  
    "NSE:SIGNATURE", "NSE:MAHLIFE", "NSE:BRIGADE", "NSE:SOBHA", "NSE:SUNTECK",
    "NSE:IBREALEST", "NSE:PHOENIXLTD", "NSE:GODREJPROP", "NSE:DLF", "NSE:OBEROIRLTY",
    "NSE:PRESTIGE", "NSE:LODHA", "NSE:MACROTECH", "NSE:RPOWER", "NSE:IRCON",
    
    # Textiles & Apparel
    "NSE:PAGEIND", "NSE:AHLUCONT", "NSE:RAYMONDSL", "NSE:SIYARAM", "NSE:GOKEX",
    "NSE:VARDHACRLC", "NSE:TRIDENT", "NSE:WELINV", "NSE:WELENT", "NSE:KPR",
    "NSE:SPANDANA", "NSE:SUTLEJTEX", "NSE:DOLLAR", "NSE:GOKALDAS", "NSE:SRFLTD",
    
    # Food & Beverages
    "NSE:TATACONSUM", "NSE:BRITANNIA", "NSE:NESTLEIND", "NSE:JUBLFOOD", "NSE:WESTLIFE",
    "NSE:DEVYANI", "NSE:SAPPHIRE", "NSE:RELAXO", "NSE:BATA", "NSE:VBL",
    "NSE:CCL", "NSE:VAIBHAVGBL", "NSE:HERITAGE", "NSE:HATSUN", "NSE:PGHH",
    
    # Media & Entertainment
    "NSE:PVRINOX", "NSE:SAREGAMA", "NSE:TIPS", "NSE:EROS", "NSE:BALAJITELE",
    "NSE:NAZARA", "NSE:NETWORK18", "NSE:TV18BRDCST", "NSE:HATHWAY", "NSE:DEN",
    
    # Healthcare Services
    "NSE:APOLLOHOSP", "NSE:MAXHEALTH", "NSE:FORTIS", "NSE:NARAYANA", "NSE:RAINBOWHSP",
    "NSE:ASTER", "NSE:STARHEALTH", "NSE:CARERATING", "NSE:ICRA", "NSE:CRISIL",
    
    # Insurance & AMC
    "NSE:SBILIFE", "NSE:HDFCLIFE", "NSE:ICICIGI", "NSE:ICICIPRULI", "NSE:STARHEALTH",
    "NSE:GODIGIT", "NSE:HDFCAMC", "NSE:ABSLAMC", "NSE:UTIAMC", "NSE:NAM-INDIA",
    
    # Specialty Retail
    "NSE:TRENT", "NSE:SHOPERSTOP", "NSE:VMART", "NSE:VEDANT", "NSE:ADITYA",
    "NSE:BARBEQUE", "NSE:SAFARI", "NSE:KDDL", "NSE:HIMATSEIDE", "NSE:GOCOLORS",
    
    # Logistics & Supply Chain
    "NSE:CONCOR", "NSE:TCI", "NSE:VRL", "NSE:MAHLOG", "NSE:DELHIVERY",
    "NSE:BLUEDART", "NSE:ALLCARGO", "NSE:GATEWAY", "NSE:GATI", "NSE:MAHLOG",
    
    # Agro & Commodities
    "NSE:MAHABANK", "NSE:IEX", "NSE:MCDHOLDING", "NSE:JUBLPHARMA", "NSE:AVANTIFEED",
    "NSE:AEGISCHEM", "NSE:SUDARSCHEM", "NSE:DHANUKA", "NSE:RALLIS", "NSE:PNBHOUSING",
    
    # Industrials & Manufacturing
    "NSE:ABB", "NSE:SIEMENS", "NSE:HONAUT", "NSE:3MINDIA", "NSE:CUMMINSIND",
    "NSE:THERMAX", "NSE:VOLTAS", "NSE:BLUESTAR", "NSE:LLOYDSME", "NSE:KAJARIACER",
    
    # Paper & Packaging
    "NSE:TNPL", "NSE:WEST", "NSE:BALAXI", "NSE:SESAGOA", "NSE:ORIENTPPR",
    "NSE:TDPOWERSYS", "NSE:JKPAPER", "NSE:BALKRISHNA", "NSE:APCL", "NSE:SHREDIGCEM",
    
    # Sugar & Ethanol
    "NSE:BAJAJHIND", "NSE:DHAMPUR", "NSE:BALRAMCHIN", "NSE:TRIVENI", "NSE:SHREERENUKA",
    "NSE:DDPL", "NSE:RENUKA", "NSE:EID", "NSE:BALSUGIND", "NSE:RAJESHEXPO",
    
    # PSU & Government
    "NSE:BHEL", "NSE:BEL", "NSE:HAL", "NSE:GAIL", "NSE:PFC", "NSE:REC",
    "NSE:IRFC", "NSE:IRCON", "NSE:RAILVIKAS", "NSE:RITES", "NSE:CONCOR",
    "NSE:HUDCO", "NSE:NBCC", "NSE:NMDC", "NSE:COALINDIA", "NSE:OIL",
    
    # Smallcap High-Volume  
    "NSE:TANLA", "NSE:HAPPSTMNDS", "NSE:ROUTE", "NSE:NAZARA", "NSE:NYKAA",
    "NSE:ZOMATO", "NSE:PAYTM", "NSE:POLICYBZR", "NSE:CARTRADE", "NSE:EASEMYTRIP",
    "NSE:METROPOLIS", "NSE:THYROCARE", "NSE:KRSNAA", "NSE:RAINBOW", "NSE:ASTER",
]

# Legacy alias for backward compatibility
NSE_TOP_300 = NSE_UNIVERSE[:300]

# BSE high-volume stocks (additional to NSE)
BSE_HIGH_VOLUME = [
    "BSE:RELIANCE", "BSE:TCS", "BSE:HDFCBANK", "BSE:INFY", "BSE:ICICIBANK",
    "BSE:SBIN", "BSE:BHARTIARTL", "BSE:ITC", "BSE:LT", "BSE:KOTAKBANK",
]


def get_intraday_universe(limit: int = 300, exchange: str = "NSE") -> list[str]:
    """
    Get list of intraday tradable stocks.
    
    Args:
        limit: Maximum number of stocks to return (default 300, max 600)
        exchange: Exchange to filter (NSE/BSE/ALL, default NSE)
    
    Returns:
        List of stock symbols in EXCHANGE:SYMBOL format
    """
    if exchange.upper() == "ALL":
        universe = NSE_UNIVERSE + BSE_HIGH_VOLUME
    elif exchange.upper() == "BSE":
        universe = BSE_HIGH_VOLUME
    else:  # NSE or default
        universe = NSE_UNIVERSE
    
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
    all_symbols = NSE_UNIVERSE + BSE_HIGH_VOLUME
    return symbol in all_symbols


def get_symbol_category(symbol: str) -> str:
    """
    Get category of a symbol (for filtering/grouping).
    
    Returns:
        Category name like "Nifty50", "Banking", "IT", etc.
    """
    symbol = symbol.upper().replace(" ", "")
    
    nifty_50 = NSE_UNIVERSE[:50]
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
