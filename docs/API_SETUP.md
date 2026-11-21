# 🔑 M4DI~UciH4 Trading Intelligence System — API Setup Guide

This guide explains how to obtain free API keys from official financial providers and configure them in the application.

---

## 1. Finnhub Stock & Forex API

**Primary Use**: Real-time stock quotes, institutional company profiles, market news, and candle histories.

1. Navigate to: [https://finnhub.io](https://finnhub.io)
2. Click **Get Free API Key** and create an account.
3. Copy your API token from your Finnhub dashboard.
4. In **M4DI~UciH4 Trading Intelligence**:
   - Go to **API Management** in the sidebar.
   - Click **➕ Add Key**.
   - Select **Finnhub** as the provider, assign a friendly name (e.g. `Finnhub Primary`), paste the key, and set Priority (e.g. `1`).
   - Click **Save Key**.
   - Click **🧪 Test Key** to verify connectivity.

---

## 2. Twelve Data Financial API

**Primary Use**: Multi-asset time series, Gold/Commodities (`XAU/USD`), Indices (`US30`, `SPX`), Forex majors, and Crypto.

1. Navigate to: [https://twelvedata.com](https://twelvedata.com)
2. Register for a free plan (allows 8 requests/minute, 800 requests/day).
3. Copy your API key from your Twelve Data dashboard.
4. In the application:
   - Go to **API Management**.
   - Click **➕ Add Key**.
   - Select **Twelve Data**, enter a name (e.g. `12Data Main`), and paste the key.
   - Click **Save Key** and test the connection.

---

## 3. NewsAPI.org Macro Intelligence

**Primary Use**: Global economic releases, central bank news, inflation, and market sentiment newsfeeds.

1. Navigate to: [https://newsapi.org](https://newsapi.org)
2. Register for a free developer account.
3. Copy your API key.
4. Add the key under **NewsAPI.org** in the **API Management** view.

---

## 4. Multi-Key Rotation Strategy

If you register multiple free keys for Finnhub or Twelve Data:
- The system supports unlimited keys per provider.
- In **API Management**, select the **Active Strategy**:
  - **Priority-Based**: Always uses the highest priority healthy key.
  - **Round-Robin**: Cycles through active keys sequentially.
  - **Least-Used**: Routes requests to the key with the lowest total call count.
  - **Failover**: Uses Primary until rate-limited (HTTP 429), then seamlessly switches to Backup keys.

---

## 5. Setting up Telegram Bot Notifications (Optional)

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow instructions to name your bot.
3. Copy the HTTP API token provided by BotFather.
4. Message `@userinfobot` on Telegram to get your numeric **Chat ID**.
5. In **M4DI~UciH4**:
   - Go to **Settings**.
   - Scroll to **Telegram Notifications**.
   - Check **Enable Telegram Notification Transmissions**.
   - Paste your **Bot Token** and **Chat ID**.
   - Click **📡 Send Test Telegram Ping** to verify delivery.
   - Click **Save All Settings**.
