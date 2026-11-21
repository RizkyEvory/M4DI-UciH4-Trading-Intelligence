"""
M4DI~UciH4 Trading Intelligence System
Database DDL Schema Definition
"""

SCHEMA_SQL = """
-- 1. User and Application Settings Table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. API Keys Management Table (Multi-key per provider supported)
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    name TEXT NOT NULL,
    key_encrypted TEXT NOT NULL,
    key_masked TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    priority INTEGER NOT NULL DEFAULT 1,
    last_used_at TIMESTAMP,
    last_success_at TIMESTAMP,
    error_count INTEGER NOT NULL DEFAULT 0,
    rate_limit_count INTEGER NOT NULL DEFAULT 0,
    cooldown_until TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'UNTESTED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Provider Settings & Rotation Strategy Configuration Table
CREATE TABLE IF NOT EXISTS provider_settings (
    provider TEXT PRIMARY KEY,
    rotation_strategy TEXT NOT NULL DEFAULT 'priority',
    rpm_limit INTEGER DEFAULT 60,
    min_interval_sec REAL DEFAULT 1.0,
    daily_limit INTEGER,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Application System & Audit Logs Table
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,
    module TEXT NOT NULL,
    message TEXT NOT NULL
);

-- 5. Watchlists Table
CREATE TABLE IF NOT EXISTS watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Watchlist Symbols Table
CREATE TABLE IF NOT EXISTS watchlist_symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    notes TEXT,
    alert_condition TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
    UNIQUE(watchlist_id, symbol)
);

-- 7. Portfolio Accounts Table (Paper Trading / Simulation)
CREATE TABLE IF NOT EXISTS portfolio_accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    initial_balance REAL NOT NULL DEFAULT 100000.0,
    current_cash REAL NOT NULL DEFAULT 100000.0,
    currency TEXT NOT NULL DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Portfolio Positions Table
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL, -- BUY or SELL
    units REAL NOT NULL,
    entry_price REAL NOT NULL,
    current_price REAL NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    status TEXT NOT NULL DEFAULT 'OPEN', -- OPEN or CLOSED
    realized_pnl REAL DEFAULT 0.0,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (account_id) REFERENCES portfolio_accounts(id)
);

-- 9. Portfolio Trades Execution Ledger
CREATE TABLE IF NOT EXISTS portfolio_trades (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    position_id TEXT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    units REAL NOT NULL,
    price REAL NOT NULL,
    fee REAL DEFAULT 0.0,
    slippage REAL DEFAULT 0.0,
    pnl REAL DEFAULT 0.0,
    trade_type TEXT NOT NULL, -- ENTRY, EXIT, PARTIAL_EXIT, SL_HIT, TP_HIT
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (account_id) REFERENCES portfolio_accounts(id)
);

-- 10. API Request & Audit Logs Table (Phase 6 Advanced Telemetry)
CREATE TABLE IF NOT EXISTS api_request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    key_id INTEGER,
    endpoint TEXT NOT NULL,
    status_code INTEGER,
    is_success INTEGER NOT NULL,
    response_time_ms REAL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Query & Search Performance
CREATE INDEX IF NOT EXISTS idx_api_keys_provider ON api_keys(provider);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_module ON logs(module);
CREATE INDEX IF NOT EXISTS idx_watchlist_symbols_wid ON watchlist_symbols(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_positions_account ON portfolio_positions(account_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON portfolio_positions(status);
CREATE INDEX IF NOT EXISTS idx_trades_account ON portfolio_trades(account_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON portfolio_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_api_req_logs_provider ON api_request_logs(provider);
CREATE INDEX IF NOT EXISTS idx_api_req_logs_timestamp ON api_request_logs(timestamp);
"""

# Seed Data for Initial Watchlists
DEFAULT_WATCHLISTS_DATA = [
    ("Gold & Metals", "Institutional precious metals (XAUUSD, XAGUSD, Platinum)", [
        ("XAUUSD", "Commodities (Gold/Silver)"),
        ("XAGUSD", "Commodities (Gold/Silver)"),
        ("XPTUSD", "Commodities (Gold/Silver)")
    ]),
    ("Forex Majors", "High-volume institutional FX pairs", [
        ("EURUSD", "Forex (Major & Crosses)"),
        ("GBPUSD", "Forex (Major & Crosses)"),
        ("USDJPY", "Forex (Major & Crosses)"),
        ("AUDUSD", "Forex (Major & Crosses)")
    ]),
    ("US Tech & Indices", "Macro liquid stock index futures & equities", [
        ("US30", "Indices (US30 / NAS100 / SPX500)"),
        ("NAS100", "Indices (US30 / NAS100 / SPX500)"),
        ("SPX500", "Indices (US30 / NAS100 / SPX500)")
    ]),
    ("Crypto Top 10", "Digital asset benchmarks", [
        ("BTCUSDT", "Crypto (BTC / ETH / SOL)"),
        ("ETHUSDT", "Crypto (BTC / ETH / SOL)"),
        ("SOLUSDT", "Crypto (BTC / ETH / SOL)")
    ])
]
