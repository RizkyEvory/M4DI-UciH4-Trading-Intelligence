"""
M4DI~UciH4 Trading Intelligence System
Portfolio Manager Engine (Phase 5)
Handles persistent position lifecycle (Open, Scale, SL/TP Adjust, Close),
mark-to-market valuations, realized/unrealized P&L calculations, and portfolio allocation metrics.
"""
import uuid
import threading
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from config.constants import (
    SIDE_BUY,
    SIDE_SELL,
    POSITION_OPEN,
    POSITION_CLOSED,
    TRADE_ENTRY,
    TRADE_EXIT,
    DEFAULT_INITIAL_CAPITAL
)
from database.db_manager import DatabaseManager
from portfolio.models import Position, TradeRecord, PortfolioSummary
from core.logger import get_app_logger

logger = get_app_logger("PortfolioManager")


class PortfolioManager:
    """Institutional Portfolio & Multi-Asset Book Manager"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._lock = threading.RLock()
        self._ensure_default_account()

    def _ensure_default_account(self, account_id: str = "default_paper", initial_balance: float = DEFAULT_INITIAL_CAPITAL):
        """Ensure the primary simulation paper account exists in the database"""
        with self._lock:
            row = self.db.fetchone("SELECT id FROM portfolio_accounts WHERE id = ?", (account_id,))
            if not row:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.execute(
                    """
                    INSERT INTO portfolio_accounts (id, name, initial_balance, current_cash, currency, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (account_id, "Primary Simulation Account", initial_balance, initial_balance, "USD", now_str, now_str)
                )
                logger.info(f"Initialized simulation account [{account_id}] with ${initial_balance:,.2f}")

    def get_account_balance(self, account_id: str = "default_paper") -> float:
        """Fetch current available cash balance"""
        with self._lock:
            row = self.db.fetchone("SELECT current_cash FROM portfolio_accounts WHERE id = ?", (account_id,))
            if not row:
                return DEFAULT_INITIAL_CAPITAL
            return float(row[0] if isinstance(row, (tuple, list)) else row["current_cash"])

    def get_open_positions(self, account_id: str = "default_paper") -> List[Position]:
        """Fetch all currently open positions for an account"""
        with self._lock:
            rows = self.db.fetchall(
                """
                SELECT id, account_id, symbol, side, units, entry_price, current_price,
                       stop_loss, take_profit, status, realized_pnl, opened_at, closed_at, notes
                FROM portfolio_positions
                WHERE account_id = ? AND status = ?
                ORDER BY opened_at DESC
                """,
                (account_id, POSITION_OPEN)
            )
            return [self._row_to_position(r) for r in rows]

    def get_closed_positions(self, account_id: str = "default_paper", limit: int = 50) -> List[Position]:
        """Fetch historical closed positions"""
        with self._lock:
            rows = self.db.fetchall(
                """
                SELECT id, account_id, symbol, side, units, entry_price, current_price,
                       stop_loss, take_profit, status, realized_pnl, opened_at, closed_at, notes
                FROM portfolio_positions
                WHERE account_id = ? AND status = ?
                ORDER BY closed_at DESC LIMIT ?
                """,
                (account_id, POSITION_CLOSED, limit)
            )
            return [self._row_to_position(r) for r in rows]

    def get_trade_history(self, account_id: str = "default_paper", limit: int = 100) -> List[TradeRecord]:
        """Fetch executed trade ledger records (latest first)"""
        with self._lock:
            rows = self.db.fetchall(
                """
                SELECT id, account_id, position_id, symbol, side, units, price, fee,
                       slippage, pnl, trade_type, timestamp, notes
                FROM portfolio_trades
                WHERE account_id = ?
                ORDER BY timestamp DESC, rowid DESC LIMIT ?
                """,
                (account_id, limit)
            )
            return [self._row_to_trade(r) for r in rows]

    def open_position(
        self,
        symbol: str,
        side: str,
        units: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        fee: float = 0.0,
        slippage: float = 0.0,
        account_id: str = "default_paper",
        notes: str = ""
    ) -> Position:
        """
        Executes a paper order entry: creates a position, deducts cash, logs trade.
        """
        with self._lock:
            pos_id = str(uuid.uuid4())[:8]
            trade_id = str(uuid.uuid4())[:8]
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            exec_price = entry_price + slippage if side == SIDE_BUY else entry_price - slippage
            total_cost = (units * exec_price) + fee

            # 1. Deduct cash from account
            curr_cash = self.get_account_balance(account_id)
            new_cash = round(curr_cash - total_cost, 2)
            self.db.execute(
                "UPDATE portfolio_accounts SET current_cash = ?, updated_at = ? WHERE id = ?",
                (new_cash, now_str, account_id)
            )

            # 2. Insert Position
            self.db.execute(
                """
                INSERT INTO portfolio_positions (
                    id, account_id, symbol, side, units, entry_price, current_price,
                    stop_loss, take_profit, status, realized_pnl, opened_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?)
                """,
                (pos_id, account_id, symbol.upper(), side, units, exec_price, exec_price,
                 stop_loss, take_profit, POSITION_OPEN, now_str, notes)
            )

            # 3. Insert Execution Trade Record
            self.db.execute(
                """
                INSERT INTO portfolio_trades (
                    id, account_id, position_id, symbol, side, units, price, fee,
                    slippage, pnl, trade_type, timestamp, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?, ?)
                """,
                (trade_id, account_id, pos_id, symbol.upper(), side, units, exec_price, fee,
                 slippage, TRADE_ENTRY, now_str, notes)
            )

            logger.info(f"Opened paper position [{pos_id}] {side} {units} {symbol} @ {exec_price:.4f} (Cost: ${total_cost:,.2f})")

            return Position(
                id=pos_id,
                account_id=account_id,
                symbol=symbol.upper(),
                side=side,
                units=units,
                entry_price=exec_price,
                current_price=exec_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                status=POSITION_OPEN,
                realized_pnl=0.0,
                opened_at=now_str,
                notes=notes
            )

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        fee: float = 0.0,
        slippage: float = 0.0,
        trade_type: str = TRADE_EXIT,
        account_id: str = "default_paper",
        notes: str = ""
    ) -> Tuple[Position, float]:
        """
        Closes an open position: computes realized P&L, credits cash, logs exit trade.
        """
        with self._lock:
            row = self.db.fetchone(
                """
                SELECT id, account_id, symbol, side, units, entry_price, current_price,
                       stop_loss, take_profit, status, realized_pnl, opened_at, closed_at, notes
                FROM portfolio_positions
                WHERE id = ? AND status = ?
                """,
                (position_id, POSITION_OPEN)
            )
            if not row:
                raise ValueError(f"Open position [{position_id}] not found.")

            pos = self._row_to_position(row)
            exec_exit = exit_price - slippage if pos.side == SIDE_BUY else exit_price + slippage

            # Realized PnL calculation
            if pos.side == SIDE_BUY:
                raw_pnl = (exec_exit - pos.entry_price) * pos.units
            else:
                raw_pnl = (pos.entry_price - exec_exit) * pos.units

            net_pnl = round(raw_pnl - fee, 2)
            capital_returned = round((pos.units * pos.entry_price) + net_pnl, 2)

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Update account cash
            curr_cash = self.get_account_balance(account_id)
            new_cash = round(curr_cash + capital_returned, 2)
            self.db.execute(
                "UPDATE portfolio_accounts SET current_cash = ?, updated_at = ? WHERE id = ?",
                (new_cash, now_str, account_id)
            )

            # 2. Update position status to CLOSED
            self.db.execute(
                """
                UPDATE portfolio_positions
                SET status = ?, current_price = ?, realized_pnl = ?, closed_at = ?, notes = ?
                WHERE id = ?
                """,
                (POSITION_CLOSED, exec_exit, net_pnl, now_str, notes, position_id)
            )

            # 3. Log Exit Trade
            trade_id = str(uuid.uuid4())[:8]
            exit_side = SIDE_SELL if pos.side == SIDE_BUY else SIDE_BUY
            self.db.execute(
                """
                INSERT INTO portfolio_trades (
                    id, account_id, position_id, symbol, side, units, price, fee,
                    slippage, pnl, trade_type, timestamp, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (trade_id, account_id, position_id, pos.symbol, exit_side, pos.units, exec_exit,
                 fee, slippage, net_pnl, trade_type, now_str, notes)
            )

            pos.status = POSITION_CLOSED
            pos.current_price = exec_exit
            pos.realized_pnl = net_pnl
            pos.closed_at = now_str

            logger.info(f"Closed position [{position_id}] {pos.symbol} @ {exec_exit:.4f} (Net PnL: ${net_pnl:+,.2f})")
            return pos, net_pnl

    def update_position_sl_tp(
        self,
        position_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """Modify risk boundaries (SL/TP) of an active open position"""
        with self._lock:
            self.db.execute(
                "UPDATE portfolio_positions SET stop_loss = ?, take_profit = ? WHERE id = ?",
                (stop_loss, take_profit, position_id)
            )
            return True

    def update_market_price(self, symbol: str, price: float, account_id: str = "default_paper"):
        """Convenience method to update mark-to-market price for a single symbol"""
        self.update_market_prices({symbol: price}, account_id=account_id)

    def update_market_prices(self, price_map: Dict[str, float], account_id: str = "default_paper"):
        """Batch update current market price of open positions for mark-to-market valuations"""
        with self._lock:
            for sym, price in price_map.items():
                if price > 0:
                    self.db.execute(
                        "UPDATE portfolio_positions SET current_price = ? WHERE symbol = ? AND status = ?",
                        (price, sym.upper(), POSITION_OPEN)
                    )

    def get_portfolio_summary(self, account_id: str = "default_paper") -> PortfolioSummary:
        """
        Consolidates complete portfolio telemetry:
        Equity = Cash + Invested + Unrealized P&L
        """
        with self._lock:
            acc_row = self.db.fetchone("SELECT current_cash, initial_balance, name FROM portfolio_accounts WHERE id = ?", (account_id,))
            if acc_row:
                if isinstance(acc_row, (tuple, list)):
                    cash = float(acc_row[0])
                    initial_balance = float(acc_row[1])
                    acc_name = str(acc_row[2])
                else:
                    cash = float(acc_row["current_cash"])
                    initial_balance = float(acc_row["initial_balance"])
                    acc_name = str(acc_row["name"])
            else:
                cash = DEFAULT_INITIAL_CAPITAL
                initial_balance = DEFAULT_INITIAL_CAPITAL
                acc_name = "Simulation Account"

            open_positions = self.get_open_positions(account_id)

            invested = sum(p.cost_basis for p in open_positions)
            unrealized_pnl = sum(p.unrealized_pnl for p in open_positions)
            total_equity = round(cash + invested + unrealized_pnl, 2)

            # Cumulative realized PnL
            realized_row = self.db.fetchone(
                "SELECT COALESCE(SUM(realized_pnl), 0.0) as total_realized FROM portfolio_positions WHERE account_id = ?",
                (account_id,)
            )
            if realized_row:
                realized_pnl = round(float(realized_row[0] if isinstance(realized_row, (tuple, list)) else realized_row["total_realized"]), 2)
            else:
                realized_pnl = 0.0

            total_return_pct = round(((total_equity - initial_balance) / initial_balance) * 100.0, 2) if initial_balance > 0 else 0.0
            exposure_pct = round((invested / total_equity) * 100.0, 2) if total_equity > 0 else 0.0

            # Symbol Allocations (% of Total Equity)
            allocations = {}
            for p in open_positions:
                val = p.market_value
                pct = round((val / total_equity) * 100.0, 1) if total_equity > 0 else 0.0
                allocations[p.symbol] = allocations.get(p.symbol, 0.0) + pct

            return PortfolioSummary(
                account_id=account_id,
                name=acc_name,
                cash=round(cash, 2),
                invested_capital=round(invested, 2),
                total_equity=total_equity,
                initial_balance=initial_balance,
                unrealized_pnl=round(unrealized_pnl, 2),
                realized_pnl=realized_pnl,
                total_return_pct=total_return_pct,
                exposure_pct=exposure_pct,
                open_positions_count=len(open_positions),
                allocations=allocations
            )

    @staticmethod
    def _row_to_position(r: Any) -> Position:
        if isinstance(r, (tuple, list)):
            return Position(
                id=str(r[0]),
                account_id=str(r[1]),
                symbol=str(r[2]),
                side=str(r[3]),
                units=float(r[4]),
                entry_price=float(r[5]),
                current_price=float(r[6]),
                stop_loss=float(r[7]) if r[7] is not None else None,
                take_profit=float(r[8]) if r[8] is not None else None,
                status=str(r[9]),
                realized_pnl=float(r[10]),
                opened_at=str(r[11]),
                closed_at=str(r[12]) if r[12] else None,
                notes=str(r[13] or "")
            )
        return Position(
            id=str(r["id"]),
            account_id=str(r["account_id"]),
            symbol=str(r["symbol"]),
            side=str(r["side"]),
            units=float(r["units"]),
            entry_price=float(r["entry_price"]),
            current_price=float(r["current_price"]),
            stop_loss=float(r["stop_loss"]) if r["stop_loss"] is not None else None,
            take_profit=float(r["take_profit"]) if r["take_profit"] is not None else None,
            status=str(r["status"]),
            realized_pnl=float(r["realized_pnl"]),
            opened_at=str(r["opened_at"]),
            closed_at=str(r["closed_at"]) if r["closed_at"] else None,
            notes=str(r["notes"] or "")
        )

    @staticmethod
    def _row_to_trade(r: Any) -> TradeRecord:
        if isinstance(r, (tuple, list)):
            return TradeRecord(
                id=str(r[0]),
                account_id=str(r[1]),
                position_id=str(r[2]),
                symbol=str(r[3]),
                side=str(r[4]),
                units=float(r[5]),
                price=float(r[6]),
                fee=float(r[7]),
                slippage=float(r[8]),
                pnl=float(r[9]),
                trade_type=str(r[10]),
                timestamp=str(r[11]),
                notes=str(r[12] or "")
            )
        return TradeRecord(
            id=str(r["id"]),
            account_id=str(r["account_id"]),
            position_id=str(r["position_id"]),
            symbol=str(r["symbol"]),
            side=str(r["side"]),
            units=float(r["units"]),
            price=float(r["price"]),
            fee=float(r["fee"]),
            slippage=float(r["slippage"]),
            pnl=float(r["pnl"]),
            trade_type=str(r["trade_type"]),
            timestamp=str(r["timestamp"]),
            notes=str(r["notes"] or "")
        )
