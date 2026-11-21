# ⚙️ M4DI~UciH4 Trading Intelligence System — Configuration Guide

This guide details how to customize and configure the application settings, risk guardrails, and preferences.

---

## 🎨 Visual Themes & UI Customization

The system features 4 built-in dark color palettes:
1. **Dark Charcoal (Default)**: Deep Obsidian with Cyan `#00E5FF` accents (designed for high-contrast multi-hour screen time).
2. **Obsidian Gold**: Imperial Gold `#FFD700` accents for premium commodities surveillance.
3. **Emerald Obsidian**: High-visibility Green `#10B981` accents.
4. **Cyberpunk Cyan**: Vibrant Turquoise & Magenta accents.

To switch themes:
- Open **Settings** from the sidebar.
- Select your preferred palette in the **Active Color Palette** dropdown.
- Click **Save All Settings**.

---

## 🛡️ Risk Management Parameters

All risk parameters are enforced automatically across the **Paper Trading Desk** and **Backtesting Engine**:

| Setting | Default | Description |
| :--- | :--- | :--- |
| `risk_per_trade_pct` | `1.0%` | Maximum percentage of account balance risked per trade setup |
| `max_drawdown_limit_pct` | `15.0%` | Peak-to-trough account drawdown limit that halts paper trading |
| `daily_loss_limit_pct` | `3.0%` | Daily session loss threshold that pauses trading |
| `max_open_positions` | `5` | Maximum concurrent active positions permitted |

---

## 💼 Simulation & Paper Trading Parameters

The application is **strictly for paper trading and simulation**:

| Setting | Default | Description |
| :--- | :--- | :--- |
| `default_commission_pct` | `0.05%` | Simulated broker transaction commission per round-turn |
| `default_slippage_pct` | `0.02%` | Simulated execution price spread and market slippage |
| `initial_balance` | `$100,000.00` | Default virtual paper trading equity balance |

---

## 📱 Telegram Notifications (Optional)

Configure instant mobile alerts for trading events:
- `telegram_enabled`: `true` or `false`
- `telegram_bot_token`: Bot token generated via `@BotFather`
- `telegram_chat_id`: Your personal or group chat ID
- Alert categories: Signals, High-Impact News, Risk Circuit Breakers, Paper Orders.
