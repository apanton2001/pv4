# Prometheus Trading Bot

A powerful, scalable algorithmic trading framework inspired by LiuAlgoTrader, built for effective trading strategy development, backtesting, and deployment.

## Features

- **Modular Design**: Clean separation between strategy logic, data handling, and trading execution
- **Asynchronous Architecture**: Fast, responsive trading using Python's asyncio
- **Enhanced Error Handling**: Robust error recovery with automatic retries and fallbacks
- **Extensible Strategy Framework**: Create custom strategies by implementing the Strategy interface
- **Advanced Data Management**: Efficient data fetching with caching and multiple data source fallbacks
- **Risk Management**: Built-in position sizing and risk controls

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/prometheus-bot.git
cd prometheus-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Alpaca API credentials:
```
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
```

## Usage

### Running the Trading Bot

```bash
python -m src.bot.trader \
    --api-key your_api_key \
    --api-secret your_api_secret \
    --symbols AAPL MSFT GOOGL \
    --paper \
    --max-positions 5 \
    --risk-per-trade 0.02 \
    --timeframe 1Min
```

### Creating Custom Strategies

Create your own trading strategies by extending the `Strategy` class:

```python
from src.bot.strategy import Strategy

class MyCustomStrategy(Strategy):
    def __init__(self, param1, param2, name="MyStrategy"):
        super().__init__(name)
        self.param1 = param1
        self.param2 = param2
        
    def get_required_data(self):
        return {
            "timeframe": "1H",
            "lookback_bars": 100
        }
        
    async def analyze(self, symbol, data):
        # Your strategy logic here
        # Return a signal dictionary:
        # e.g., {"action": "buy", "price": price, "stop_loss": stop_loss}
        # or {"action": "sell"}
        # or {"action": None} for no signal
```

## Project Structure

- `src/`: Main source code directory
  - `api/`: API client implementations (Alpaca, etc.)
  - `bot/`: Bot core and strategy implementations
  - `data/`: Data providers and processing utilities
  - `utils/`: Utilities for logging, configuration, etc.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Inspired by [LiuAlgoTrader](https://github.com/amor71/LiuAlgoTrader)
- Powered by [Alpaca Markets API](https://alpaca.markets)

# Prometheus Trading Bot (MVP Stage)

**Dashboard:** View the interactive implementation status dashboard (if running locally) at: [http://localhost:3000](http://localhost:3000)

## Project Goal

To develop and operate a personal, automated algorithmic trading bot initially focused on US stocks (AAPL, TSLA) using the Alpaca brokerage API (Paper Trading environment). The ultimate goal is to incorporate machine learning models to identify potentially profitable trading opportunities based on various market indicators, starting with basic execution logic. *(Long-term goal includes potential expansion to options trading based on validated strategies).*

*(Self-Correction Note: While the long-term goal involves sophisticated ML and potentially options, the immediate, validated state is much simpler).*

## Current Status (MVP v0.1 - Local Execution Verified)

*   **Phase:** Phase 1/2 - Incremental Enhancement. Basic MA Crossover logic with risk checks running locally.
*   **Functionality:** The current active script (`simple_alpaca_bot.py`) successfully:
    *   Connects to the Alpaca Paper Trading API using environment variables.
    *   Fetches a window of recent hourly bars for a hardcoded stock (AAPL) using a date range and the IEX feed.
    *   Calculates Simple Moving Averages (10-hour, 30-hour).
    *   Makes trading decisions (BUY/SELL/HOLD) based on MA Crossover logic.
    *   Checks for existing positions before placing BUY/SELL orders.
    *   Includes basic risk checks (buying power) before BUY orders.
    *   Calculates basic position sizing.
    *   Submits market orders to the Alpaca paper trading account if conditions are met.
    *   Runs in a loop with a configurable sleep timer.
    *   Logs actions to console and `trading_log.txt`.
    *   Includes basic API retry logic.
*   **Focus:** This existing MVP validates end-to-end mechanics with simple logic and basic risk management. **It does NOT implement sophisticated strategy or ML yet.** Previous ML validation attempts were **blocked by historical data access issues.**

## Implementation Timeline & Phases (Planned & In Progress)

```mermaid
gantt
    title Prometheus Trading Bot Implementation Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1: MVP Trading Bot
    Basic API Connection & Price Fetching   :done,    des1, 2025-01-01, 2025-01-07
    Simple Trading Logic                    :done,    des2, 2025-01-01, 2025-01-07
    Paper Trading Order Submission          :done,    des3, 2025-01-01, 2025-01-07
    Basic Execution Loop                    :done,    des4, 2025-01-01, 2025-01-07
    Historical data integration             :active,  des5, 2025-01-08, 2025-01-14 # Status based on last attempt
    Performance logging                     :active,  des6, 2025-01-08, 2025-01-14 # Status based on last attempt

    section Phase 2: Backtesting Framework
    Develop a backtest engine               :planned, des7, 2025-01-15, 2025-01-21
    Calculate performance metrics           :planned, des8, 2025-01-15, 2025-01-21

    section Phase 3: UI Development
    Create a simple, informative dashboard  :planned, des9, 2025-01-22, 2025-02-04

    section Phase 4: Infrastructure
    Setup deployment                        :planned, des10, 2025-02-05, 2025-02-18
    Setup database                          :planned, des11, 2025-02-05, 2025-02-18
    Setup automation                        :planned, des12, 2025-02-05, 2025-02-18
    Setup API                               :planned, des13, 2025-02-05, 2025-02-18
    Setup subscriptions                     :planned, des14, 2025-02-05, 2025-02-18

    section Phase 5: Testing & Launch
    Beta testing                            :planned, des15, 2025-02-19, 2025-03-03
    Performance monitoring                  :planned, des16, 2025-02-19, 2025-03-03
    Refinement                              :planned, des17, 2025-02-19, 2025-03-03
```

### PHASE 3: ML Implementation (FUTURE - Blocked by Historical Data Access)

### PHASE 4: Advanced Testing (FUTURE)

### PHASE 5: Options Trading & Production Readiness (FUTURE)
*   [⬜] **Options Data Integration:** Integrate fetch for options chains, IV, greeks (Requires appropriate API access/library, e.g., Alpaca Options API, CBOE DataShop).
*   [⬜] **Options Strategy Formulation:** Develop and backtest options-specific strategies (e.g., straddles, spreads based on volatility/direction). Requires Options Data.
*   [⬜] **Options Order Execution:** Implement logic to place options orders via Alpaca API (using specific contract symbols, order types).
*   [⬜] **Options Risk Management:** Implement handling for assignment/exercise, specific options risk metrics.
*   [⬜] Real-Time Processing Optimizations
*   [⬜] Advanced Risk Management (Stop-loss, Daily Limits, Volatility Sizing - for chosen asset class)
*   [⬜] Portfolio Integration (Handling multiple symbols/asset classes)
*   [⬜] Monitoring Dashboard (UI - e.g., Supabase/Vercel)
*   [⬜] Production Deployment (Cloud service, e.g., EC2/PythonAnywhere)

## Modified Setup Instructions

1.  **Environment Setup**
    ```bash
    # Clone repository (Replace with your actual repo URL)
    git clone https://github.com/apanton2001/prometheus-bot.git # Or your current repo
    cd prometheus-bot

    # Create virtual environment
    python -m venv venv
    # Activate (Examples)
    # source venv/Scripts/activate  # Git Bash on Windows
    # .\venv\Scripts\Activate.ps1   # PowerShell on Windows
    # source venv/bin/activate      # Linux/macOS

    # Install dependencies (Update requirements.txt first)
    # Example: pip install -r requirements.txt
    # For current MVP:
    pip install alpaca-trade-api python-dotenv
    ```

2.  **Configuration**
    ```bash
    # Create .env file in the project root
    # Add your Alpaca Paper Trading Keys:
    ALPACA_KEY=your_key_here
    ALPACA_SECRET=your_secret_here
    ```

3.  **Running the Bot (Current MVP)**
    ```bash
    # Start the bot (ensure venv is active)
    python simple_alpaca_bot.py

    # To stop the bot: Press CTRL+C in the terminal
    ```
    *(Note: Logging currently goes only to console. `tail` command requires a log file, which isn't implemented yet).*

## Current Development Focus

1.  **Immediate Tasks (Based on completed MVP):**
    *   **Validate Basic Functionality:** Let `simple_alpaca_bot.py` run for a period (e.g., 1 hour) and confirm paper trades appear correctly in the Alpaca dashboard when thresholds are met.
    *   **Implement Historical Fetch:** Modify `simple_alpaca_bot.py` (or create `src/bot/historical_data.py`) to fetch a window of historical data (e.g., 200 bars) needed for future feature calculation, addressing Alpaca/IEX data limitations as best possible.
    *   **Implement Basic Logging:** Modify `simple_alpaca_bot.py` (or create `src/bot/performance_logger.py`) to log trades and decisions to a simple CSV or SQLite database instead of just the console.
    *   **(Defer)** Do *not* start the backtesting framework (Phase 2) until basic historical data fetching and logging are working reliably in the core bot script.
2.  **Success Metrics (for this immediate focus):**
    *   Confirmed paper trades executed via Alpaca dashboard match bot logs.
    *   Script reliably fetches the last N bars of data for AAPL/TSLA without crashing.
    *   Decisions and simulated/paper trades are logged persistently (e.g., to a file or simple DB).
    *   Bot runs stably for at least an hour locally.

## Project Structure (Target - Based on Plan)

```
prometheus-bot/
├── api/
│   └── Tarriff Data.csv     # Asset from previous analysis (Archived/Separate?)
├── src/                     # Main source code
│   ├── bot/                 # Core bot logic
│   │   ├── __init__.py
│   │   ├── simple_alpaca_bot.py # Current MVP / Evolving bot script
│   │   ├── historical_data.py   # FUTURE: Module for data fetching
│   │   └── performance_logger.py  # FUTURE: Module for logging trades/performance
│   ├── backtesting/         # FUTURE: Backtesting components
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── metrics.py
│   └── utils/               # FUTURE: Utility functions (e.g., config loading)
│       ├── __init__.py
│       └── config.py
├── tests/                   # FUTURE: Automated tests
├── user_data/               # Potential location for logs, models, db?
│   └── models/              # From previous ML attempts
│   └── data/                # From previous ML attempts
├── venv/                    # Virtual environment
├── .env                     # Environment variables (API Keys)
├── .env.example             # Example environment file
├── .gitignore
├── requirements.txt         # Project dependencies
├── tariff_analysis.py       # Script from previous validation MVP (Archive?)
└── README.md                # This file
```

## Known Issues / Challenges

*   **Historical Data Access:** Primary blocker for ML/backtesting (Alpaca/IEX limited, yfinance network issues).
*   **Simple Logic:** Current bot logic is basic MA crossover.
*   **No Backtesting:** No robust backtesting implemented.
*   **Options Complexity:** Options trading (data, strategy, execution) is significantly more complex than the current equity MVP and is deferred.

## Alpaca Options API Capabilities (Future Reference)
*   **Endpoints:** Dedicated endpoints exist (`/v2/options/contracts`) to fetch option contract details.
*   **Trading:** Uses the standard Orders API (`/v2/orders`) but requires using the options contract symbol (e.g., `AAPL240119C00100000`) and options-specific validations (whole number qty, type market/limit, TIF=day).
*   **Data:** Alpaca provides real-time and historical options data feeds (likely requires appropriate subscriptions beyond basic plan).
*   **Activities:** Specific non-trade activities (NTAs) exist for exercise, assignment, expiry.
*   **Exercise:** API endpoint available (`POST /v2/positions/{symbol_or_contract_id}/exercise`) to exercise contracts.
*   *(Full details: <https://docs.alpaca.markets/docs/options-trading>)*

## Configuration

The application is configured through environment variables. See `.env.example` for all available options.

Key configuration areas:
- API settings
- Database connection
- Redis configuration
- Trading parameters
- Content generation
- Monitoring setup

## Testing

Run the test suite:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=.
```

## Deployment

See `deployment_checklist.md` for detailed deployment instructions.

Key deployment steps:
1. Configure environment
2. Set up infrastructure
3. Deploy services
4. Initialize database
5. Configure monitoring
6. Verify functionality

## Monitoring

The application includes comprehensive monitoring:

- **Prometheus**: Collects metrics
- **Grafana**: Visualizes metrics
- **Logging**: Structured JSON logs
- **Alerts**: Email & Slack notifications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository.

# Current Implementation State

## Core Components
- [x] Basic MA Crossover Logic
- [x] Alpaca API Integration
- [x] Position Management
- [x] Risk Checks
- [ ] Advanced Logging (In Progress)
- [ ] Data Persistence (Planned)

## Known Issues
1. Historical Data Access:
   - IEX limitations on historical bars
   - SIP feed integration pending
   - Alternative data sources being evaluated

2. Performance Monitoring:
   - Basic console logging implemented
   - Structured logging in progress
   - Dashboard template created

## Next Steps
1. Implement structured logging
2. Add data persistence layer
3. Create basic monitoring dashboard
4. Enhance error handling 