# 👑 M4DI~UciH4 Trading Intelligence System

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Desktop%20GUI%20(Windows%20%2F%20Linux%20%2F%20macOS)-0078D7?style=for-the-badge&logo=windows&logoColor=white" alt="Platform" />
  <img src="https://img.shields.io/badge/Python-3.11%2B%20%7C%203.14-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-00E5FF?style=for-the-badge" alt="GUI" />
  <img src="https://img.shields.io/badge/Database-SQLite%203.50%2B%20(WAL)-FFD700?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Tests-175%2F175%20Passing%20(100%25)-00E676?style=for-the-badge" alt="Build Status" />
  <img src="https://img.shields.io/badge/Edition-Enterprise%20Production%20Suite-00F5D4?style=for-the-badge" alt="Enterprise Edition" />
</p>

---

## 📌 Executive Overview

**M4DI~UciH4 Trading Intelligence System** is an institutional-grade, multi-asset desktop surveillance, quantitative intelligence, and algorithmic trading system built with Python.

Designed from the ground up for quantitative analysis and institutional trading (Gold/XAUUSD, Forex majors, US Indices, and Crypto), the system features an asynchronous, thread-safe architecture, local encrypted credential management, intelligent multi-key rotation, sliding-window rate limiting, a central multi-timeframe market data engine, 12 mathematical technical indicators, quantitative trend/volatility/volume analyzers, interactive high-performance candlestick charting, **macro news intelligence with local deterministic NLP sentiment analysis**, an **institutional multi-factor trading signal engine with automated risk-reward calculation and real-time event alerts**, a **strict risk management and position sizing engine**, a **real-time portfolio ledger and simulated paper trading desk (STRICTLY paper trading — no real-money execution)**, an **event-driven backtesting engine with mathematical performance metrics (Sharpe, Sortino, Max Drawdown, CAGR, Profit Factor) and anti-data leakage guarantees**, an **executive dashboard with live cross-subsystem telemetry**, **multi-watchlist management with alert triggers and notes**, **optional Telegram mobile alert notifications**, **system diagnostics and integrity auditing**, **universal CSV/JSON data exporter**, and **standalone Windows PyInstaller packaging**.

---

## 🚀 Subsystem Architecture & Implementation Status

| Subsystem | Core Component | Focus Areas | Status |
| :---: | :--- | :--- | :---: |
| **Core Architecture** | **Foundation & UI Shell** | 10-view desktop shell, SQLite WAL database, TaskManager, encrypted local storage, dark theme | ✅ Complete |
| **Data Director** | **API Integration & Multi-Key Manager** | Finnhub, Twelve Data, NewsAPI, multi-key rotation, rate limiter, provider health monitor, cache | ✅ Complete |
| **Market Data Engine** | **Technical Analysis & Surveillance** | Central Market Data Manager, 9 timeframes, Resampler, 12 indicators, MTF confluence, Candlestick Chart, Scanner GUI | ✅ Complete |
| **Intelligence Engine** | **News Sentiment & Signal Generation** | News categorization (11 categories), local NLP sentiment, impact scoring, deduplication, Signal Scoring & Confidence, SL/TP/RR math, real-time alerts | ✅ Complete |
| **Execution & Risk** | **Portfolio, Paper Trading & Backtesting** | Position sizing math, circuit breakers, portfolio manager, paper trading desk, backtest engine, 5 modular strategies, visual equity & drawdown curves | ✅ Complete |
| **Enterprise Suite** | **Optimization, Security & Telemetry** | Executive Dashboard, Multi-Watchlists with Alerts & Notes, Telegram Dispatcher, Failover Logs, Universal Exporter, System Diagnostics, Windows Packager | ✅ Complete |

---

## 🏆 Enterprise Suite Implementation Scope

| Requirement | Implementation Details | Status |
| :--- | :--- | :---: |
| **Executive Intelligence Dashboard** | Real-time cross-subsystem command center (`gui/views/dashboard_view.py`) consolidating live Portfolio Equity, Risk status, News sentiment score, Active signal count, Provider status, Market benchmarks, Active Watchlist switcher, and one-click diagnostics | ✅ Complete |
| **Multi-Watchlist Management** | Full lifecycle manager (`watchlist/watchlist_manager.py` & `gui/dialogs/watchlist_dialog.py`): Create, Rename, Delete watchlists, Add/Remove symbols, Asset classes, Institutional thesis notes, and automated price alert conditions (`> 2650.00` / `< 2580.00`) | ✅ Complete |
| **Market Scanner Integration** | Direct loading and batch quantitative scanning of any custom watchlist pool, with one-click chart deep-linking and result export | ✅ Complete |
| **Optional Telegram Notifications** | Thread-safe notification dispatcher (`notifications/telegram_notifier.py`): Dispatches instant formatted mobile alerts for Trading Signals (Strong Buy/Sell), High-Impact Breaking News, Risk Circuit Breakers, and Paper Orders. Fully optional with instant test ping | ✅ Complete |
| **Advanced API Telemetry & Failover** | Ring-buffer and database persistence (`api_request_logs`): request latency tracking, per-key call counters, cooldown countdowns, and automated failover event logging modal (`gui/views/api_management_view.py`) | ✅ Complete |
| **Universal CSV & JSON Exporter** | Institutional data export engine (`utils/exporter.py`): Native CSV and JSON export for Market Scanner, Trading Signals, News Wire, Portfolio Holdings, Paper Trade Ledger, and Backtesting Tear Sheets | ✅ Complete |
| **System Diagnostics Suite** | End-to-end automated system audit (`diagnostics/system_diagnostics.py`): Checks API connectivity, SQLite integrity (`PRAGMA integrity_check`), table row counts, in-memory cache hit ratio, host environment threads, task queues, and audit log errors | ✅ Complete |
| **Security & Hardening** | AES-256 / PBKDF2 local credential encryption, universal secret masking in logs/tables/exports, parameterized SQL statements everywhere (SQL injection immune), and strict numerical input validation | ✅ Complete |
| **Comprehensive Application Settings** | Dynamic configuration center (`gui/views/settings_view.py`): 4 Dark Themes, Market/Timeframe defaults, Risk circuit breakers, Commission/Slippage models, Chart display preferences, and Telegram credentials | ✅ Complete |
| **Windows Desktop Packaging** | Standalone PyInstaller build specification (`m4di_ucih4.spec`) and automated compilation script (`build_windows.py`) to create a single-folder / single-exe Windows distribution | ✅ Complete |
| **Documentation Manuals** | Comprehensive guides in `docs/`: `INSTALLATION.md`, `CONFIGURATION.md`, `API_SETUP.md`, `TROUBLESHOOTING.md` | ✅ Complete |
| **Automated Test Suite** | **175 unit and integration tests** verifying all system components with 100% pass rate | ✅ 100% Passing |

---

## 🛡️ Risk Management, Portfolio & Backtesting Implementation Scope

| Requirement | Implementation Details | Status |
| :--- | :--- | :---: |
| **Risk Management Engine** | Transparent mathematical position sizer, dynamic SL/TP calculation, R:R calculation ($1:\text{R}$), max portfolio exposure check, max drawdown circuit breaker, daily loss limit protector, and maximum open positions ceiling | ✅ Complete |
| **Mathematical Position Sizer** | Calculates exact position size from account balance, risk percentage (e.g. 1.0%), entry price, and stop-loss distance with full audit step transparency ($Units = \frac{\text{Capital} \times \text{Risk\%}}{\text{SL Distance}}$) | ✅ Complete |
| **Portfolio Manager** | SQLite-backed positions ledger (`portfolio_positions`) and trades ledger (`portfolio_trades`), real-time mark-to-market valuations, unrealized/realized P&L, exposure %, and asset allocation weights | ✅ Complete |
| **Portfolio GUI** | Interactive view (`gui/views/portfolio_view.py`) with 4 StatCards, active holdings table, historical trades ledger, interactive "New Paper Order" modal with live position sizing calculator, and manual position closure | ✅ Complete |
| **Simulated Paper Trading Desk** | Strict simulated paper execution (`portfolio/paper_trader.py`) with customizable fee/slippage modeling, circuit breaker validation, and automated intra-bar High/Low Stop-Loss and Take-Profit triggers (**NO real-money trading**) | ✅ Complete |
| **Event-Driven Backtest Engine** | Bar-by-bar historical backtesting (`backtesting/backtest_engine.py`) with next-bar execution, realistic intra-bar stop-loss/take-profit evaluation, configurable commission, and slippage modeling | ✅ Complete |
| **Anti-Data Leakage Architecture** | Strict prevention of lookahead bias; signals evaluate exclusively historical data up to bar $i$; orders fill on bar $i+1$ Open; zero future data leakage | ✅ Complete |
| **5 Modular Trading Strategies** | 1. EMA Crossover (9/21 cross + 50 EMA filter)<br>2. RSI Mean Reversion (oversold/overbought pullbacks)<br>3. MACD Trend Following (zero-line cross + histogram)<br>4. Bollinger Breakout (volatility squeeze & band expansion)<br>5. Institutional Confluence (EMA stack + RSI + RVOL) | ✅ Complete |
| **Quantitative Backtest Metrics** | Exact mathematical calculation (`backtesting/metrics.py`) of Total Return %, CAGR %, Win Rate %, Profit Factor, Sharpe Ratio (annualized), Sortino Ratio (downside deviation), Maximum Drawdown %, Average Trade P&L, Average Win/Loss, and Expectancy | ✅ Complete |
| **Backtesting GUI Workspace** | Comprehensive workbench (`gui/views/backtesting_view.py`) with strategy selection, parameter configuration, 6 KPI StatCards, pure Tkinter Canvas interactive Equity Curve and Drawdown Chart, sortable trade execution log, and printable Tear Sheet summary | ✅ Complete |
| **Automated Test Suite** | **145 unit and integration tests** verifying all core components with 100% pass rate | ✅ 100% Passing |

---

## 🔬 News Intelligence & Trading Signals Implementation Scope

| Requirement | Implementation Details | Status |
| :--- | :--- | :---: |
| **News Intelligence Ingestion** | Unified aggregation of market headlines, company news, and symbol-specific feeds from **Finnhub** & **NewsAPI.org** | ✅ Complete |
| **11 News Categories** | Automated classifier covering: `Earnings`, `Economic data`, `Interest rates`, `Inflation`, `Company announcements`, `Mergers and acquisitions`, `Regulation`, `Geopolitical events`, `Analyst upgrades/downgrades`, `Product launches`, `Market sentiment` | ✅ Complete |
| **Deterministic NLP Sentiment** | Local high-precision financial lexicon with negation inversion (`not beat`, `failed to`), intensifier boosters (`significantly surged`), and continuous scoring (-1.0 to +1.0) without fabricated cloud AI claims | ✅ Complete |
| **News Impact Scorer** | Quantitative impact rating (0-100) and 4-tier classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) incorporating category base weights, sentiment extremity, volatility triggers, market mover bonuses, and recency time decay | ✅ Complete |
| **News Deduplication** | Dual-layer deduplication engine stripping tracking query parameters, canonical URL matching, and fuzzy headline Jaccard token similarity | ✅ Complete |
| **News Intelligence GUI** | Dedicated dashboard (`gui/views/news_view.py`) with search, symbol/category/sentiment/impact dropdown filters, sortable tables, NLP reason breakdown, and browser deep-linking | ✅ Complete |
| **Multi-Factor Signal Engine** | Algorithmic synthesis combining Technical Indicators, Trend & Market Structure, Volume RVOL, Volatility regimes, News Sentiment, and MTF Confluence into 5 signal states: `Strong Buy`, `Buy`, `Neutral`, `Sell`, `Strong Sell` | ✅ Complete |
| **Configurable Signal Scoring** | Weighted transparent score across Technical (50%), Fundamental/News (25%), and Risk/Volatility (25%) with fully transparent human-readable audit reasons | ✅ Complete |
| **Model Confidence Metric** | Quantitative 0-100% confidence calculated from Indicator Agreement (concordance), MTF Alignment, News Confirmation synergy, and Data Quality sample depth | ✅ Complete |
| **SL / TP1 / TP2 & R:R Engine** | Mathematical calculation of dynamic Stop Loss (ATR & swing boundaries), Take Profit 1 (1.5R), Take Profit 2 (2.5R), and Risk/Reward ratio | ✅ Complete |
| **Real-Time Signal Alerts** | Event-driven alert monitor (`signals/alerts_engine.py`) dispatching real-time notifications for Strong Buy/Sell, Trend Breakouts, RSI Extremes (<25 / >75), MACD Crossovers, Volume Breakouts (RVOL > 2.0), and High-Impact News releases | ✅ Complete |
| **Trading Signals GUI** | Advanced command center (`gui/views/signals_view.py`) featuring metrics telemetry, multi-filter watchlist scanning, setup thesis inspector, execution risk framework, active alert logs, and chart deep-linking | ✅ Complete |
| **Automated Test Suite** | **123 unit and integration tests** verifying all intelligence components with 100% pass rate | ✅ 100% Passing |

---

## 🏗️ Modular Architecture & Folder Structure

```
PROJECT APLIKASI/
├── main.py                          # Application entry point & bootstrapper
├── requirements.txt                 # Dependencies specification
├── README.md                        # Master documentation
├── config/
│   ├── __init__.py
│   ├── constants.py                 # System constants, timeframes, news categories, signal/alert types
│   ├── settings.py                  # Thread-safe SettingsManager with SQLite persistence
│   └── theme.py                     # Modern dark styling, color tokens, semantic aliases & TTK theme
├── core/
│   ├── __init__.py
│   ├── app_context.py               # Central Dependency Container (Singleton with lazy providers)
│   ├── event_bus.py                 # Decoupled Pub/Sub messaging system
│   ├── logger.py                    # Multi-channel logger with secret sanitization
│   └── task_manager.py              # Thread-safe async TaskManager with queue polling
├── database/
│   ├── __init__.py
│   ├── db_manager.py                # Thread-safe SQLite manager with automatic migration
│   └── schema.py                    # DDL definitions, provider settings & default watchlists
├── api/
│   ├── __init__.py
│   ├── base_client.py               # Base HTTP client with backoff, key rotation, and rate limiter
│   ├── finnhub_client.py            # Finnhub client with normalized models
│   ├── twelve_data_client.py        # Twelve Data client with multi-asset and indicator support
│   ├── newsapi_client.py            # NewsAPI macro intelligence client
│   ├── models.py                    # Normalized Quote, Candle, News, Company, Symbol models
│   ├── cache.py                     # In-memory thread-safe response cache with TTL
│   ├── rate_limiter.py              # Provider rate limit & sliding-window throttle manager
│   ├── key_rotation.py              # Multi-key rotation (Priority, RR, Least-Used, Failover)
│   ├── health_monitor.py            # Real-time provider health tracker & telemetry
│   ├── key_manager.py               # Key lifecycle management, masking, and test hooks
│   └── exceptions.py                # Structured API exception hierarchy
├── engine/
│   ├── __init__.py
│   ├── market_data_engine.py        # Central Market Data Manager (quotes, candles, caching)
│   ├── resampler.py                 # Mathematical OHLCV timeframe aggregation
│   ├── data_validator.py            # Bar integrity, future timestamp rejection, dedup, gap detection
│   └── scanner_engine.py            # Batch market scanner with quantitative filters
├── analytics/
│   ├── __init__.py
│   ├── indicators.py                # 12 pure-math indicators (SMA, EMA, RSI, MACD, BB, ATR, ADX, Stoch, VWAP, OBV)
│   ├── trend.py                     # Multi-MA trend & swing structure analyzer (HH/HL/LH/LL)
│   ├── volatility.py                # ATR%, Historical Vol, BB Width, 4-tier regime classification
│   ├── volume.py                    # RVOL, volume breakout & confirmation, OBV trend
│   ├── mtf.py                       # Multi-Timeframe Confluence (5m -> 1w) scoring
│   └── technical_score.py           # Composite 0-100 technical rating calculator
├── news/
│   ├── __init__.py
│   ├── categories.py                # 11 institutional news category classifiers with weighted pattern matching
│   ├── sentiment_analyzer.py        # Local deterministic financial NLP sentiment analyzer with negations
│   ├── impact_scorer.py             # Market impact scoring (0-100) and tier mapping (Low to Critical)
│   ├── deduplicator.py              # Canonical URL & fuzzy Jaccard headline deduplication
│   ├── models.py                    # EnrichedNewsArticle model with full metadata
│   └── news_engine.py               # Central orchestrator integrating Finnhub & NewsAPI
├── signals/
│   ├── __init__.py
│   ├── models.py                    # TradingSignal, SignalConfidence, SignalScoreBreakdown, SignalAlert
│   ├── scoring_engine.py            # Multi-factor scoring (Tech 50%, Fund 25%, Risk 25%) with transparent reasons
│   ├── confidence_engine.py         # Model confidence calculator (agreement, MTF, news synergy, data quality)
│   ├── signal_generator.py          # End-to-end signal synthesizer with dynamic SL, TP1, TP2, and R:R
│   └── alerts_engine.py             # Event-driven real-time alert dispatcher with configurable rules
├── risk/
│   ├── __init__.py
│   ├── models.py                    # PositionSizeResult, RiskCheckResult, AccountRiskProfile
│   ├── position_sizer.py            # Mathematical Position Sizer (Risk % of balance / SL distance)
│   └── risk_manager.py              # Max drawdown, daily loss limit, exposure, open positions manager
├── portfolio/
│   ├── __init__.py
│   ├── models.py                    # Position, TradeRecord, PortfolioSummary data structures
│   ├── portfolio_manager.py         # SQLite position & trade ledger manager with mark-to-market
│   └── paper_trader.py              # Simulated paper trading desk with fee/slippage & SL/TP triggers
├── backtesting/
│   ├── __init__.py
│   ├── models.py                    # BacktestConfig, BacktestTrade, BacktestResult
│   ├── metrics.py                   # Sharpe, Sortino, Max Drawdown, CAGR, Profit Factor, Expectancy
│   ├── backtest_engine.py           # Bar-by-bar event-driven engine with next-bar execution & anti-leakage
│   └── strategies/
│       ├── __init__.py              # Strategy catalog (AVAILABLE_STRATEGIES)
│       ├── base_strategy.py         # Abstract strategy interface ensuring strict anti-lookahead
│       ├── ema_crossover.py         # EMA 9/21 cross + 50 EMA trend filter
│       ├── rsi_mean_reversion.py    # RSI 30/70 extreme reversion
│       ├── macd_trend.py            # MACD zero cross + histogram expansion
│       ├── bollinger_breakout.py    # Bollinger Band squeeze breakout
│       └── institutional_confluence.py # Multi-factor institutional setup (EMA + RSI + RVOL)
├── watchlist/
│   ├── __init__.py
│   └── watchlist_manager.py         # Multi-watchlist lifecycle, symbol notes, and price alert rules
├── notifications/
│   ├── __init__.py
│   └── telegram_notifier.py         # Optional Telegram alert dispatcher for signals, news, risk
├── diagnostics/
│   ├── __init__.py
│   └── system_diagnostics.py        # End-to-end automated health & integrity auditing suite
├── security/
│   ├── __init__.py
│   └── encryption.py                # Local secret encryption & key masking helpers
├── utils/
│   ├── __init__.py
│   ├── formatters.py                # Datetime & numerical formatters
│   ├── helpers.py                   # Window centering & GUI utility helpers
│   └── exporter.py                  # Universal CSV & JSON dataset exporter
├── docs/
│   ├── INSTALLATION.md              # Installation manual across platforms
│   ├── CONFIGURATION.md             # Parameter customization & theme manual
│   ├── API_SETUP.md                 # Finnhub, Twelve Data, NewsAPI & Telegram setup guide
│   └── TROUBLESHOOTING.md           # Operational solutions & rate limit diagnostics
├── gui/
│   ├── __init__.py
│   ├── main_window.py               # Main window coordinating Header, Sidebar & Views
│   ├── components/
│   │   ├── __init__.py
│   │   ├── cards.py                 # CardFrame & StatCard telemetry widgets
│   │   ├── header.py                # Real-time clock, status pills & system telemetry
│   │   ├── sidebar.py               # 10 Navigation buttons with active indicators
│   │   ├── tables.py                # Sortable Treeview with alternating dark rows
│   │   └── candlestick_chart.py     # Pure Tkinter Canvas high-performance interactive chart
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── api_key_dialog.py        # Add / Edit API key modal with priority & secret toggle
│   │   ├── confirm_dialog.py        # Confirmation modal
│   │   └── watchlist_dialog.py      # Multi-watchlist and symbol alert manager modal
│   └── views/
│       ├── __init__.py
│       ├── dashboard_view.py        # Executive Command Dashboard with live subsystem telemetry
│       ├── api_management_view.py   # Multi-key manager, testing, and failover logs
│       ├── market_scanner_view.py   # Quantitative Market Scanner with filters & export
│       ├── charts_view.py           # Interactive Multi-Timeframe Charting Workspace
│       ├── news_view.py             # News Intelligence & Sentiment Analysis Hub with export
│       ├── signals_view.py          # Institutional Trading Signal Engine & Alerts Center with export
│       ├── portfolio_view.py        # Live Portfolio Manager & Paper Trading Desk with export
│       ├── backtesting_view.py      # Backtest Workspace with Equity & Drawdown Curves and export
│       ├── settings_view.py         # Application settings, themes, risk guardrails, Telegram
│       └── logs_view.py             # Filterable & searchable audit log viewer
├── build_windows.py                 # Automated Windows PyInstaller packager
├── m4di_ucih4.spec                  # Standalone Windows packaging specification
└── tests/
    ├── __init__.py
    ├── test_database.py             # Database schema & parameterized query tests
    ├── test_security.py             # Encryption & masking tests
    ├── test_api_keys.py             # Key CRUD tests
    ├── test_key_rotation.py         # 4 Rotation policies & failover tests
    ├── test_rate_limiter.py         # Sliding window, pacing, & backoff tests
    ├── test_cache.py                # In-memory TTL expiry & cache stats tests
    ├── test_data_normalization.py   # Normalized data models tests
    ├── test_api_clients.py          # Finnhub, 12Data, NewsAPI mock tests & fault handling
    ├── test_provider_health.py      # Provider health telemetry tests
    ├── test_settings.py             # Settings manager tests
    ├── test_task_manager.py         # Async task execution tests
    ├── test_logging.py              # Secret sanitization & log tests
    ├── test_gui_startup.py          # GUI startup & 10-page navigation integration test
    ├── test_indicators.py           # 12 Technical Indicators mathematical verification tests
    ├── test_trend_volatility_volume.py # Trend, Volatility, Volume, and Tech Score tests
    ├── test_resampler.py            # Mathematical OHLCV aggregation & validation tests
    ├── test_data_validator.py       # Data integrity, future bar rejection & gap detection tests
    ├── test_mtf_confluence.py       # Multi-Timeframe confluence scoring tests
    ├── test_market_data_engine.py   # Central Market Data Manager & Scanner Engine tests
    ├── test_news_intelligence.py    # 11 categories, local sentiment NLP, impact, deduplication tests
    ├── test_signal_engine.py        # Signal scoring, confidence, SL/TP/RR, and real-time alert tests
    ├── test_risk_management.py      # Position sizing math, circuit breakers & risk rules tests
    ├── test_portfolio_manager.py    # Position lifecycle, trade ledger & P/L calculation tests
    ├── test_paper_trading.py        # Paper orders, fee/slippage & automated SL/TP trigger tests
    ├── test_backtest_engine.py      # Metrics math, 5 strategies & anti-data-leakage tests
    ├── test_watchlist_manager.py    # Watchlist lifecycle, notes & price alert triggers tests
    ├── test_telegram_notifier.py    # Telegram optional alerts & payload tests
    ├── test_exporter.py             # CSV & JSON exporter pipeline tests
    ├── test_diagnostics.py          # Automated system health & integrity check tests
    └── test_advanced_api.py         # Request logging & failover history tests
```

---

## 🛡️ Risk Management & Position Sizing Engine

1. **Exact Mathematical Position Sizing**:
   $$\text{Cash at Risk} = \text{Account Balance} \times \left(\frac{\text{Risk \%}}{100}\right)$$
   $$\text{SL Distance} = |\text{Entry Price} - \text{Stop Loss}|$$
   $$\text{Units} = \frac{\text{Cash at Risk}}{\text{SL Distance}}$$
   - Completely transparent calculation audit trail logged with each evaluation.
   - Automatically capped at maximum capital allocation when specified.

2. **Institutional Circuit Breakers & Risk Constraints**:
   - **Daily Loss Limit**: Halts order placement if current session losses exceed user threshold (e.g. 3.0%).
   - **Maximum Drawdown Circuit Breaker**: Blocks trading when peak-to-trough account drawdown reaches maximum limit (e.g. 15.0%).
   - **Maximum Portfolio Exposure**: Restricts total invested capital as a percentage of total equity (e.g. max 80.0%).
   - **Max Open Positions Ceiling**: Prevents excessive simultaneous active risk (e.g. max 5 concurrent positions).
   - **Minimum Risk / Reward Check**: Enforces positive trade expectancy (e.g. minimum $1:1.5\text{R}$).

---

## 💼 Portfolio Ledger & Paper Trading Desk

1. **Simulation-Only Architecture**:
   - **STRICTLY paper trading**: All order routing is simulated locally in SQLite. **NO real-money trading or brokerage execution accounts are accessed**.
2. **Mark-to-Market Valuation**:
   - Continuous real-time revaluation of open positions using live market quotes.
   - Separate accounting for available Cash, Invested Capital, Total Equity, Unrealized P&L, Realized P&L, and Total Return %.
3. **Automated Stop-Loss & Take-Profit Triggers**:
   - Intra-bar high/low scanner automatically triggers limit exits when candle prices touch or pierce Stop-Loss or Take-Profit thresholds.
   - Modeled realistic execution with customizable commission fees (e.g. 0.05%) and execution slippage (e.g. 0.02%).

---

## 📈 Quantitative Backtesting & Strategy Framework

1. **Anti-Data Leakage Guarantees**:
   - **Zero Lookahead Bias**: Bar-by-bar evaluation ensuring strategy signals at bar $i$ are computed strictly using data from bars $0 \dots i$.
   - **Realistic Next-Bar Execution**: Signal generated at close of bar $i$ is executed at the Open of bar $i+1$.
   - **Intra-Bar SL/TP Evaluation**: Bar High and Low are analyzed to simulate intra-bar stop-outs and profit targets conservatively (SL checked first if both penetrated).
2. **5 Built-In Modular Strategies**:
   - `EMA Crossover`: 9/21 Exponential Moving Average cross with 50 EMA trend direction filter and ATR stops.
   - `RSI Mean Reversion`: Institutional oversold pullback ($\text{RSI} < 30$) and overbought exhaustion ($\text{RSI} > 70$).
   - `MACD Trend Following`: MACD line cross over Signal line confirmed by histogram momentum expansion.
   - `Bollinger Breakout`: Volatility squeeze contraction followed by band breakout with expanding bandwidth.
   - `Institutional Confluence`: Multi-factor setup combining moving average alignment, RSI momentum, and RVOL volume expansion.
3. **Mathematical Performance Metrics**:
   - **Total Return % & CAGR %**: Compounded annual growth rate accounting for historical duration.
   - **Win Rate % & Profit Factor**: Ratio of gross profits to gross losses.
   - **Sharpe Ratio**: Annualized risk-adjusted excess return ($\text{Risk-Free Rate} = 2.0\%$).
   - **Sortino Ratio**: Downside volatility adjusted return penalizing only negative variations.
   - **Maximum Drawdown %**: Peak-to-trough worst portfolio drawdown during the test window.
   - **Mathematical Expectancy**: Expected dollar return per trade based on historical edge.

---

## 📱 Telegram Alerts & Multi-Watchlist Architecture

1. **Optional Telegram Notifications**:
   - Easily set up via `@BotFather` and configured in the **Settings** view.
   - Formats and dispatches instant mobile alerts for Strong Buy/Sell signals, High-Impact Macro News catalysts, Risk circuit breaker triggers, and paper order fills.
   - Includes a live test ping tool to verify bot connectivity directly from the desktop GUI.
2. **Multi-Watchlist & Symbol Surveillance**:
   - Group symbols into separate pools (e.g. *Gold & Metals*, *Forex Majors*, *US Tech*, *Crypto*).
   - Attach institutional thesis notes and set active price trigger conditions (`> 2650.00` or `< 2580.00`).
   - Seamlessly launch the Market Scanner directly on any watchlist pool.

---

## 📥 Universal Data Exporter (CSV & JSON)

Institutional data can be exported in standardized formats:
- **Market Scanner**: Export scanned rows with prices, RVOL, RSI, MACD, Trend, and Technical Score.
- **Trading Signals**: Export active setups with confidence %, score breakdown, entry, SL, and TP targets.
- **News Wire**: Export deduplicated articles with NLP sentiment scores, impact ratings, and categories.
- **Portfolio & Ledger**: Export current holdings and complete historical transaction journals.
- **Backtest Results**: Export complete Tear Sheets and trade execution logs.

---

## 🩺 System Diagnostics & Health Suite

One-click automated system audit checks:
- **API Connectivity**: Validates key configurations and connection states for Finnhub, Twelve Data, and NewsAPI.
- **SQLite Database**: Runs `PRAGMA integrity_check;`, verifies WAL mode, and tallies table row counts.
- **Cache Telemetry**: Reports in-memory cache hit ratio, active entries, and capacity utilization.
- **Host Runtime**: Monitors active thread count, process ID, OS platform, and Python runtime version.
- **Background Tasks**: Verifies worker thread pool health and pending execution queues.
- **Error Audit**: Summarizes recent application error and warning frequencies.

---

## 🔑 Panduan Lengkap Cara Membuat & Konfigurasi API Key (API Setup Guide)

Aplikasi **M4DI~UciH4 Trading Intelligence System** menggunakan API resmi dari penyedia data finansial institusional untuk menyajikan kuotasi real-time, grafik candlestick interaktif, scanner kuantitatif, dan berita makro ekonomi. 

Seluruh API key yang Anda masukkan disimpan secara aman di database lokal terenkripsi (**AES-256 / PBKDF2**) dan tidak pernah di-hardcode atau dikirimkan ke pihak luar.

Berikut adalah panduan langkah-demi-langkah untuk mendapatkan API Key secara **GRATIS** dari masing-masing penyedia:

---

### 1. Finnhub Stock & Forex API (Kuotasi Real-Time & Berita Emiten)
* **Kegunaan Utama**: Real-time market quotes (Saham & Forex), profil emiten, berita pasar institusional, dan riwayat candlestick.
* **Langkah Mendapatkan API Key Gratis**:
  1. Buka browser dan kunjungi: [https://finnhub.io](https://finnhub.io)
  2. Klik tombol hijau **Get free API key** di pojok kanan atas.
  3. Daftarkan akun baru dengan Email Anda, atau login cepat menggunakan akun Google / GitHub.
  4. Setelah masuk ke Dashboard Finnhub, temukan bagian **API Key / API Token** (string acak, contoh: `c1234567890abcdef...`).
  5. Salin (**Copy**) API key tersebut.
* **Cara Memasukkan ke Aplikasi**:
  1. Buka aplikasi **M4DI~UciH4**, di sidebar kiri klik menu **API Management**.
  2. Klik tombol **➕ Add Key**.
  3. Pada jendela yang muncul:
     - **Provider**: Pilih `Finnhub`
     - **Key Name**: Beri nama label (contoh: `Finnhub Primary`)
     - **API Key**: Tempelkan (**Paste**) API key yang disalin tadi
     - **Priority**: Masukkan angka prioritas (default: `1`)
  4. Klik **Save Key**.
  5. Klik tombol **🧪 Test Key** pada tabel untuk memastikan koneksi berhasil (**Active / Valid**).
* **Kuota Gratis**: 60 requests / menit.

---

### 2. Twelve Data Financial API (Gold/XAUUSD, Forex, Indeks & Crypto)
* **Kegunaan Utama**: Data time series multi-aset, komoditas Emas (`XAU/USD`), Indeks Global (`US30`, `SPX`, `QQQ`), pasangan mata uang Forex, dan Kripto.
* **Langkah Mendapatkan API Key Gratis**:
  1. Kunjungi situs resmi Twelve Data: [https://twelvedata.com](https://twelvedata.com)
  2. Klik tombol **Register** atau **Get Started for Free**.
  3. Isi formulir pendaftaran (Nama, Email, Password) atau login menggunakan akun Google.
  4. Buka email Anda dan lakukan konfirmasi verifikasi jika diminta.
  5. Masuk ke Dashboard Twelve Data, lalu navigasikan ke menu **API Keys**.
  6. Salin (**Copy**) API key Anda.
* **Cara Memasukkan ke Aplikasi**:
  1. Di aplikasi **M4DI~UciH4**, buka menu **API Management**.
  2. Klik tombol **➕ Add Key**.
  3. Pada form:
     - **Provider**: Pilih `Twelve Data`
     - **Key Name**: Beri nama (contoh: `TwelveData Main`)
     - **API Key**: Tempelkan API key Twelve Data Anda
     - **Priority**: `1`
  4. Klik **Save Key**, lalu klik **🧪 Test Key** untuk verifikasi konektivitas.
* **Kuota Gratis**: 8 requests / menit, 800 requests / hari.

---

### 3. NewsAPI.org Macro Intelligence (Berita Pasar Global & Makro Ekonomi)
* **Kegunaan Utama**: Agregasi berita global makro, pengumuman suku bunga bank sentral (The Fed, ECB, BOJ), rilis data inflasi (CPI/PPI), dan analisis sentimen pasar untuk News Intelligence Engine.
* **Langkah Mendapatkan API Key Gratis**:
  1. Kunjungi: [https://newsapi.org](https://newsapi.org)
  2. Klik tombol **Get API Key** di menu navigasi.
  3. Lengkapi formulir pendaftaran (Nama, Email, Password), pilih jenis penggunaan individu/pengembangan.
  4. Setelah submit, API key Anda akan langsung muncul di halaman (string alfanumerik 32 karakter).
  5. Salin (**Copy**) API key tersebut.
* **Cara Memasukkan ke Aplikasi**:
  1. Di aplikasi **M4DI~UciH4**, buka menu **API Management**.
  2. Klik tombol **➕ Add Key**.
  3. Pada form:
     - **Provider**: Pilih `NewsAPI.org`
     - **Key Name**: Beri nama (contoh: `NewsAPI Developer`)
     - **API Key**: Tempelkan kunci NewsAPI Anda
  4. Klik **Save Key** dan uji dengan klik **🧪 Test Key**.
* **Kuota Gratis**: 100 requests / hari.

---

### 4. Fitur Cerdas: Multi-Key Rotation & Failover Otomatis
Jika Anda memiliki beberapa akun gratis Finnhub atau Twelve Data:
* Aplikasi mendukung **unlimited keys** per provider.
* Anda dapat memilih strategi rotasi di tab **API Management**:
  * **Priority-Based**: Selalu menggunakan key dengan nomor prioritas tertinggi.
  * **Round-Robin**: Menggilir panggilan request secara seimbang di seluruh key aktif.
  * **Least-Used**: Otomatis memilih key yang pemakaian kuotanya paling sedikit.
  * **Failover**: Otomatis berpindah ke key cadangan jika key utama terkena limit (HTTP 429) dengan periode *cooldown* cerdas.

---

### 5. Notifikasi Telegram Bot (Opsional)
Aplikasi dapat mengirimkan notifikasi sinyal trading instan (*Strong Buy / Sell*), *high-impact news*, dan *risk alerts* langsung ke ponsel Telegram Anda.

* **Cara Membuat Bot Telegram**:
  1. Buka aplikasi Telegram di HP/Komputer Anda.
  2. Cari user resmi `@BotFather` (bertanda centang biru).
  3. Kirim pesan `/newbot` dan ikuti petunjuk nama bot Anda.
  4. BotFather akan memberikan **HTTP API Bot Token** (contoh: `123456789:ABCdefGhIJKlmNoPQRstuVWXyz...`). Salin token ini.
  5. Untuk mengetahui ID chat Anda, cari user `@userinfobot` di Telegram, lalu klik **Start**. Bot tersebut akan menampilkan angka **Id** Anda (contoh: `987654321`). Salin ID tersebut.
* **Cara Memasukkan ke Aplikasi**:
  1. Buka menu **Settings** di aplikasi **M4DI~UciH4**.
  2. Scroll ke bagian **Telegram Notifications Settings**.
  3. Centang opsi **Enable Telegram Notification Transmissions**.
  4. Masukkan **Telegram Bot Token** dan **Telegram Chat ID**.
  5. Klik tombol **📡 Send Test Telegram Ping** untuk memastikan notifikasi masuk ke HP Anda.
  6. Klik **Save All Settings**.

---

## ⚠️ Known Limitations & Boundaries

1. **Paper Trading Only**: The software is strictly built for quantitative research, surveillance, backtesting, and paper execution. It does **not** connect to live brokerage execution accounts or execute real-money orders.
2. **Provider Rate Limits**: Free API keys from Finnhub (60 req/min), Twelve Data (8 req/min), and NewsAPI (100 req/day) are subject to provider quotas. Multi-key rotation and caching help mitigate these limits, but heavy scanning should respect provider rate policies.
3. **Historical Data Depth**: Historical candle depth depends on the connected provider's plan. When higher timeframe data is unavailable, mathematical resampling is applied where 1m/5m base data exists.

---

## 🧪 Testing Suite Execution

Run all 175 unit and integration tests:

```bash
cd "c:\Users\qwert\PROJECT APLIKASI"
python -m unittest discover tests
```

Expected Output:
```text
Ran 175 tests in ~8.1s
OK (175/175 Passing — 100%)
```

---

## 💻 Running the Application

Launch the desktop system from source:

```bash
cd "c:\Users\qwert\PROJECT APLIKASI"
python main.py
```

---

## 🪟 Standalone Windows Executable Build

Compile a standalone Windows desktop app:

```bash
cd "c:\Users\qwert\PROJECT APLIKASI"
python build_windows.py
```
Output executable will be placed in `dist\M4DI_UciH4_Trading_Intelligence\`.
