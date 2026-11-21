"""
M4DI~UciH4 Trading Intelligence System
Watchlist Manager (Phase 6)
Provides multi-watchlist lifecycle management: create, rename, delete watchlists,
add/remove symbols, symbol-specific quantitative notes, price/indicator alert rules,
and seamless scanner integration.
"""
import re
import threading
from typing import Dict, Any, List, Optional, Tuple, Union
from core.logger import get_logger
from database.db_manager import DatabaseManager

logger = get_logger("WatchlistManager")


class WatchlistManager:
    """Thread-safe multi-watchlist controller backed by SQLite"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._lock = threading.Lock()

    def get_watchlists(self) -> List[Dict[str, Any]]:
        """Retrieve all active watchlists with their respective symbol count"""
        with self._lock:
            sql = """
            SELECT w.id, w.name, w.description, w.created_at, COUNT(ws.id) as symbol_count
            FROM watchlists w
            LEFT JOIN watchlist_symbols ws ON w.id = ws.watchlist_id
            GROUP BY w.id, w.name, w.description, w.created_at
            ORDER BY w.id ASC
            """
            rows = self.db.fetchall(sql)
            results = []
            for r in rows:
                if isinstance(r, (tuple, list)):
                    results.append({
                        "id": int(r[0]),
                        "name": str(r[1]),
                        "description": str(r[2] or ""),
                        "created_at": str(r[3]),
                        "symbol_count": int(r[4])
                    })
                else:
                    results.append({
                        "id": int(r["id"]),
                        "name": str(r["name"]),
                        "description": str(r["description"] or ""),
                        "created_at": str(r["created_at"]),
                        "symbol_count": int(r["symbol_count"])
                    })
            return results

    def create_watchlist(self, name: str, description: str = "") -> Tuple[bool, str, Optional[int]]:
        """Create a new watchlist container"""
        name = name.strip()
        if not name:
            return False, "Watchlist name cannot be empty.", None

        with self._lock:
            # Check duplicate name
            existing = self.db.fetchone("SELECT id FROM watchlists WHERE LOWER(name) = LOWER(?)", (name,))
            if existing:
                return False, f"Watchlist '{name}' already exists.", None

            row_id = self.db.execute(
                "INSERT INTO watchlists (name, description) VALUES (?, ?)",
                (name, description.strip())
            )
            logger.info(f"Created new watchlist '{name}' [ID: {row_id}]")
            return True, f"Watchlist '{name}' created successfully.", row_id

    def rename_watchlist(self, watchlist_id: int, new_name: str) -> Tuple[bool, str]:
        """Rename an existing watchlist"""
        new_name = new_name.strip()
        if not new_name:
            return False, "New watchlist name cannot be empty."

        with self._lock:
            existing = self.db.fetchone("SELECT id FROM watchlists WHERE id = ?", (watchlist_id,))
            if not existing:
                return False, f"Watchlist [ID: {watchlist_id}] not found."

            duplicate = self.db.fetchone(
                "SELECT id FROM watchlists WHERE LOWER(name) = LOWER(?) AND id != ?",
                (new_name, watchlist_id)
            )
            if duplicate:
                return False, f"A watchlist named '{new_name}' already exists."

            self.db.execute(
                "UPDATE watchlists SET name = ? WHERE id = ?",
                (new_name, watchlist_id)
            )
            logger.info(f"Renamed watchlist [ID: {watchlist_id}] to '{new_name}'")
            return True, f"Watchlist successfully renamed to '{new_name}'."

    def delete_watchlist(self, watchlist_id: int) -> Tuple[bool, str]:
        """Delete an entire watchlist and its contained symbols (cascaded)"""
        with self._lock:
            existing = self.db.fetchone("SELECT name FROM watchlists WHERE id = ?", (watchlist_id,))
            if not existing:
                return False, f"Watchlist [ID: {watchlist_id}] not found."

            wl_name = existing[0] if isinstance(existing, (tuple, list)) else existing["name"]

            # Also ensure at least one watchlist remains
            count_row = self.db.fetchone("SELECT COUNT(*) FROM watchlists")
            total = count_row[0] if isinstance(count_row, (tuple, list)) else count_row["COUNT(*)"]
            if total <= 1:
                return False, "Cannot delete the sole remaining watchlist. Create another first."

            self.db.execute("DELETE FROM watchlist_symbols WHERE watchlist_id = ?", (watchlist_id,))
            self.db.execute("DELETE FROM watchlists WHERE id = ?", (watchlist_id,))
            logger.info(f"Deleted watchlist '{wl_name}' [ID: {watchlist_id}]")
            return True, f"Watchlist '{wl_name}' deleted."

    def get_symbols(self, watchlist_id_or_name: Union[int, str]) -> List[Dict[str, Any]]:
        """Retrieve all symbols in a given watchlist with notes and alerts"""
        with self._lock:
            if isinstance(watchlist_id_or_name, int) or str(watchlist_id_or_name).isdigit():
                sql = """
                SELECT ws.id, ws.watchlist_id, ws.symbol, ws.market, ws.notes, ws.alert_condition, ws.added_at, w.name
                FROM watchlist_symbols ws
                JOIN watchlists w ON ws.watchlist_id = w.id
                WHERE ws.watchlist_id = ?
                ORDER BY ws.id ASC
                """
                params = (int(watchlist_id_or_name),)
            else:
                sql = """
                SELECT ws.id, ws.watchlist_id, ws.symbol, ws.market, ws.notes, ws.alert_condition, ws.added_at, w.name
                FROM watchlist_symbols ws
                JOIN watchlists w ON ws.watchlist_id = w.id
                WHERE LOWER(w.name) = LOWER(?)
                ORDER BY ws.id ASC
                """
                params = (str(watchlist_id_or_name).strip(),)

            rows = self.db.fetchall(sql, params)
            results = []
            for r in rows:
                if isinstance(r, (tuple, list)):
                    results.append({
                        "id": int(r[0]),
                        "watchlist_id": int(r[1]),
                        "symbol": str(r[2]),
                        "market": str(r[3] or ""),
                        "notes": str(r[4] or ""),
                        "alert_condition": str(r[5] or ""),
                        "added_at": str(r[6]),
                        "watchlist_name": str(r[7])
                    })
                else:
                    results.append({
                        "id": int(r["id"]),
                        "watchlist_id": int(r["watchlist_id"]),
                        "symbol": str(r["symbol"]),
                        "market": str(r["market"] or ""),
                        "notes": str(r["notes"] or ""),
                        "alert_condition": str(r["alert_condition"] or ""),
                        "added_at": str(r["added_at"]),
                        "watchlist_name": str(r["name"])
                    })
            return results

    def add_symbol(
        self,
        watchlist_id: int,
        symbol: str,
        market: str = "Equities / Crypto",
        notes: str = "",
        alert_condition: str = ""
    ) -> Tuple[bool, str]:
        """Add a ticker symbol to a watchlist"""
        symbol = symbol.strip().upper()
        if not symbol:
            return False, "Symbol cannot be empty."

        with self._lock:
            # Check watchlist existence
            wl = self.db.fetchone("SELECT id, name FROM watchlists WHERE id = ?", (watchlist_id,))
            if not wl:
                return False, f"Target watchlist [ID: {watchlist_id}] does not exist."

            # Check duplicate in this watchlist
            dup = self.db.fetchone(
                "SELECT id FROM watchlist_symbols WHERE watchlist_id = ? AND UPPER(symbol) = ?",
                (watchlist_id, symbol)
            )
            if dup:
                return False, f"Symbol '{symbol}' is already present in this watchlist."

            self.db.execute(
                """
                INSERT INTO watchlist_symbols (watchlist_id, symbol, market, notes, alert_condition)
                VALUES (?, ?, ?, ?, ?)
                """,
                (watchlist_id, symbol, market.strip(), notes.strip(), alert_condition.strip())
            )
            logger.info(f"Added symbol '{symbol}' to watchlist ID {watchlist_id}")
            return True, f"Symbol '{symbol}' added successfully."

    def remove_symbol(self, watchlist_id: int, symbol: str) -> Tuple[bool, str]:
        """Remove a ticker symbol from a watchlist"""
        symbol = symbol.strip().upper()
        with self._lock:
            res = self.db.execute(
                "DELETE FROM watchlist_symbols WHERE watchlist_id = ? AND UPPER(symbol) = ?",
                (watchlist_id, symbol)
            )
            if res > 0:
                logger.info(f"Removed symbol '{symbol}' from watchlist ID {watchlist_id}")
                return True, f"Symbol '{symbol}' removed from watchlist."
            return False, f"Symbol '{symbol}' not found in watchlist."

    def update_symbol_notes(self, watchlist_id: int, symbol: str, notes: str) -> Tuple[bool, str]:
        """Update institutional thesis notes for a tracked symbol"""
        symbol = symbol.strip().upper()
        with self._lock:
            res = self.db.execute(
                "UPDATE watchlist_symbols SET notes = ? WHERE watchlist_id = ? AND UPPER(symbol) = ?",
                (notes.strip(), watchlist_id, symbol)
            )
            if res > 0:
                return True, f"Notes updated for {symbol}."
            return False, f"Symbol '{symbol}' not found."

    def set_symbol_alert(self, watchlist_id: int, symbol: str, alert_condition: str) -> Tuple[bool, str]:
        """
        Set or clear a price/condition alert for a symbol.
        Format: '> 2650.00', '< 2580.00', '>= 100.5'
        """
        symbol = symbol.strip().upper()
        alert_condition = alert_condition.strip()

        if alert_condition:
            match = re.match(r"^([><]=?)\s*([0-9]+(?:\.[0-9]+)?)$", alert_condition)
            if not match:
                return False, "Invalid alert format. Use operators like '> 2650.00' or '< 2580.00'."

        with self._lock:
            res = self.db.execute(
                "UPDATE watchlist_symbols SET alert_condition = ? WHERE watchlist_id = ? AND UPPER(symbol) = ?",
                (alert_condition, watchlist_id, symbol)
            )
            if res > 0:
                msg = f"Alert '{alert_condition}' set for {symbol}." if alert_condition else f"Alert cleared for {symbol}."
                return True, msg
            return False, f"Symbol '{symbol}' not found."

    def evaluate_symbol_alerts(self, symbol: str, current_price: float) -> List[str]:
        """
        Evaluates active watchlist alerts for a given symbol against current price.
        Returns list of alert notification messages if triggered.
        """
        symbol = symbol.strip().upper()
        if current_price <= 0:
            return []

        triggered = []
        with self._lock:
            rows = self.db.fetchall(
                """
                SELECT ws.id, w.name, ws.alert_condition, ws.notes
                FROM watchlist_symbols ws
                JOIN watchlists w ON ws.watchlist_id = w.id
                WHERE UPPER(ws.symbol) = ? AND ws.alert_condition IS NOT NULL AND ws.alert_condition != ''
                """,
                (symbol,)
            )

            for r in rows:
                cond = str(r[2] if isinstance(r, (tuple, list)) else r["alert_condition"]).strip()
                wl_name = str(r[1] if isinstance(r, (tuple, list)) else r["name"])
                match = re.match(r"^([><]=?)\s*([0-9]+(?:\.[0-9]+)?)$", cond)
                if not match:
                    continue

                op, threshold_str = match.groups()
                threshold = float(threshold_str)

                is_triggered = False
                if op == ">" and current_price > threshold:
                    is_triggered = True
                elif op == ">=" and current_price >= threshold:
                    is_triggered = True
                elif op == "<" and current_price < threshold:
                    is_triggered = True
                elif op == "<=" and current_price <= threshold:
                    is_triggered = True

                if is_triggered:
                    triggered.append(
                        f"🚨 WATCHLIST ALERT [{wl_name}]: {symbol} hit {cond} (Current: ${current_price:,.4f})"
                    )

        return triggered
