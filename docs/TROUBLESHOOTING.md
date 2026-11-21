# 🛠️ M4DI~UciH4 Trading Intelligence System — Troubleshooting Guide

Common questions, operational anomalies, and their solutions.

---

## 1. API Rate Limits & Cooldowns (HTTP 429)

### Symptom:
A provider badge displays `⏳ Cooldown` or logs show `API Key placed in cooldown for 60s`.

### Cause:
Free tier quotas have been exceeded (e.g. Twelve Data free tier allows 8 requests/minute).

### Resolution:
1. The system **automatically protects your keys**: it places the rate-limited key into a temporary cooldown without crashing.
2. In **API Management**, add additional backup keys for that provider and select **Round-Robin** or **Failover** strategy.
3. In **Settings**, increase the **Data Refresh Interval** from 15s to 30s or 60s to reduce outbound polling frequency.

---

## 2. Invalid API Key / Unauthorized (HTTP 401 or 403)

### Symptom:
A key shows status `INVALID_KEY` or `🔴 Auth Error`.

### Resolution:
1. Ensure the key was copied without leading or trailing spaces.
2. Verify in your provider dashboard that your account email is confirmed.
3. In **API Management**, select the key, click **✏️ Edit**, re-paste the token, and test connection.

---

## 3. Database Locked or Inaccessible

### Symptom:
Log displays `sqlite3.OperationalError: database is locked`.

### Cause:
Multiple external SQLite browsers or antivirus scanners locking the `data/m4di_ucih4_trading.db` file.

### Resolution:
1. The application operates in **WAL mode (Write-Ahead Logging)**, which allows concurrent readers and writers.
2. Close any external database viewers (such as DB Browser for SQLite) that might hold an exclusive file lock.
3. Run the automated diagnostic check: click **🩺 Diagnostics** on the Dashboard to execute `PRAGMA integrity_check`.

---

## 4. Telegram Notification Not Arriving

### Symptom:
Test ping fails with `Telegram API error: Bad Request: chat not found`.

### Resolution:
1. Open your Telegram app, search for your bot's username, and press **Start** (`/start`). A bot cannot send messages to a user who has not initiated contact first.
2. Double-check your numeric Chat ID by sending a message to `@userinfobot`.
3. Verify internet connectivity and ensure port 443 (HTTPS) is not blocked by a firewall.

---

## 5. System Diagnostics Audit

To inspect application health at any time:
1. Open the **Executive Dashboard**.
2. Click **🩺 Diagnostics** in the upper right.
3. View the full diagnostic report including API connectivity, SQLite integrity, in-memory cache hit ratio, active threads, and error logs.
