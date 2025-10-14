# Intraday Co-Pilot

A sophisticated AI-powered intraday trading assistant for the Indian stock market (NSE/BSE) that provides real-time algorithmic trading recommendations and analysis.

## Features

- **Live Market Integration**: Real-time data from Zerodha Kite API
- **AI-Powered Analysis**: OpenAI GPT integration for market insights
- **Algorithmic Scoring**: Multi-factor analysis (VWAP, volume, technical indicators)
- **Web Dashboard**: Modern React/Next.js interface with real-time updates
- **Historical Backtesting**: Analyze past market data
- **Risk Management**: ATR-based position sizing and stop-loss calculations

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Zerodha trading account with API access
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd intraday-copilot
   ```

2. **Configure environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

3. **Required Environment Variables**
   ```env
   # Zerodha Kite API (Get from https://kite.trade/connect/login)
   KITE_API_KEY=your_kite_api_key
   KITE_API_SECRET=your_kite_api_secret
   KITE_REDIRECT_URI=http://127.0.0.1:8000/callback
   
   # OpenAI API (Get from https://platform.openai.com/api-keys)
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - Web Interface: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

### First Time Setup

1. **Login with Zerodha**: Click "Login with Zerodha" in the web interface
2. **Configure Universe**: Go to Config tab to set up your trading symbols
3. **Adjust Policy**: Use Policy tab to fine-tune trading parameters

## Architecture

### Backend (Python/FastAPI)
- **API Server**: FastAPI with automatic OpenAPI documentation
- **Real-time Engine**: Live market data processing and analysis
- **AI Integration**: OpenAI GPT for market analysis and insights
- **Data Storage**: Redis for fast real-time data access
- **Trading Integration**: Zerodha Kite API for market data and orders

### Frontend (Next.js/React)
- **Dashboard**: Real-time trading interface
- **Charts**: Historical and live market data visualization  
- **Configuration**: Policy and parameter management
- **Analysis**: Individual stock analysis and recommendations

### Services
- **API**: Main FastAPI application (port 8000)
- **Web**: Next.js frontend (port 3000)  
- **Redis**: Data caching and real-time storage (port 6379)
- **Ticker**: Background service for live market data collection

## Usage

### Trading Modes

- **LIVE**: Market hours with real-time data
- **WAITING**: Market open but no live data yet
- **HISTORICAL**: Market closed, historical analysis only

### Main Features

1. **Top Algos**: AI-ranked list of best trading opportunities
2. **Watch**: Custom watchlist with real-time metrics
3. **Analyst**: Detailed individual stock analysis
4. **Journal**: Trading history and performance tracking
5. **Policy**: Configure trading parameters and risk management
6. **Config**: Manage universe and system settings

## API Endpoints

### Core Endpoints
- `GET /api/session` - System status and connectivity
- `GET /api/plan` - Top trading recommendations  
- `GET /api/analyze?symbol=NSE:INFY` - Individual stock analysis
- `GET /api/bars?symbol=NSE:INFY` - Historical price data

### V2 Endpoints (Enhanced)
- `GET /api/v2/session` - Enhanced session status
- `GET /api/v2/plan` - Improved recommendations
- `GET /api/v2/policy` - Policy management
- `GET /api/v2/hist/*` - Historical analysis tools

## Configuration

### Trading Policy
Configure via Policy tab or API:
- **Universe**: Stock selection criteria
- **Entry Windows**: Trading time restrictions  
- **Scoring Weights**: Factor importance (trend, volume, etc.)
- **Risk Management**: ATR-based stops and targets

### System Settings
- **Universe Limit**: Maximum active symbols
- **Pinned Symbols**: Always-included stocks
- **Staleness Threshold**: Data freshness requirements

## Development

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend  
cd web
npm install
npm run dev
```

### Docker Development
```bash
# Rebuild after code changes
docker-compose up --build

# View logs
docker-compose logs -f api
docker-compose logs -f web
```

## Troubleshooting

### Common Issues

1. **Analyst Tab Not Working**
   - Ensure API v2 routes are registered
   - Check backend logs for errors
   - Verify OpenAI API key is set

2. **No Live Data**
   - Check Zerodha login status
   - Verify ticker service is running
   - Ensure market is open (9:15-15:30 IST)

3. **Redis Connection Errors**
   - Check Redis service status: `docker-compose ps redis`
   - Verify REDIS_URL environment variable

4. **API Errors**
   - Check API logs: `docker-compose logs api`
   - Verify all environment variables are set
   - Test API endpoints: http://localhost:8000/docs

### Health Checks
- **System Status**: http://localhost:8000/healthz
- **Redis**: Check connection in /healthz response
- **Zerodha**: Login status in session endpoint
- **OpenAI**: LLM status in session endpoint

## Security Notes

- Never commit API keys to version control
- Use environment variables for all secrets
- Regularly rotate API keys
- Monitor API usage and costs
- Restrict CORS origins in production

## License

This project is for educational and personal use only. Trading involves financial risk.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at /docs
3. Check Docker logs for error details
4. Ensure all environment variables are properly set