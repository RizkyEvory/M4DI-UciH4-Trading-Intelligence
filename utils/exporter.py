"""
M4DI~UciH4 Trading Intelligence System
Universal Data Exporter (Phase 6)
Supports institutional-grade CSV and JSON exports for:
- Market Scanner results
- Trading Signals
- Enriched News Intelligence
- Portfolio Holdings & Metrics
- Trade History Execution Ledger
- Quantitative Backtesting Tear Sheets & Equity Curves
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Union, Tuple, Optional
from datetime import datetime

from core.logger import get_logger
from config.constants import EXPORT_FORMAT_CSV, EXPORT_FORMAT_JSON

logger = get_logger("Exporter")


class UniversalExporter:
    """Universal export utility for tabular and hierarchical trading datasets"""

    @staticmethod
    def _ensure_dir(filepath: Union[str, Path]) -> Path:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def export_csv(cls, data: List[Dict[str, Any]], filepath: Union[str, Path]) -> Tuple[bool, str]:
        """Export a list of dictionaries to a clean standard CSV file"""
        if not data:
            return False, "No data available to export."

        try:
            path = cls._ensure_dir(filepath)
            # Collect union of all keys across items to ensure complete headers
            fieldnames = []
            for row in data:
                for k in row.keys():
                    if k not in fieldnames:
                        fieldnames.append(k)

            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for row in data:
                    # Sanitize any nested structures to strings
                    clean_row = {}
                    for k, v in row.items():
                        if isinstance(v, (dict, list)):
                            clean_row[k] = json.dumps(v)
                        else:
                            clean_row[k] = v
                    writer.writerow(clean_row)

            logger.info(f"Successfully exported {len(data)} records to CSV: {path}")
            return True, f"Exported {len(data)} rows to {path.name}"
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False, f"CSV Export Error: {str(e)}"

    @classmethod
    def export_json(cls, data: Union[List[Dict[str, Any]], Dict[str, Any]], filepath: Union[str, Path], indent: int = 2) -> Tuple[bool, str]:
        """Export dataset to formatted JSON file"""
        if data is None:
            return False, "Data is None, cannot export."

        try:
            path = cls._ensure_dir(filepath)
            with open(path, mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, default=str, ensure_ascii=False)

            count = len(data) if isinstance(data, list) else 1
            logger.info(f"Successfully exported JSON payload to: {path}")
            return True, f"Exported JSON ({count} records) to {path.name}"
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return False, f"JSON Export Error: {str(e)}"

    @classmethod
    def export_scanner_results(cls, results: List[Any], filepath: Union[str, Path], fmt: str = EXPORT_FORMAT_CSV) -> Tuple[bool, str]:
        """Export Market Scanner table data"""
        dict_data = []
        for r in results:
            if hasattr(r, "to_dict"):
                dict_data.append(r.to_dict())
            elif isinstance(r, dict):
                dict_data.append(r)
            else:
                dict_data.append(vars(r))

        if fmt.lower() == EXPORT_FORMAT_JSON:
            return cls.export_json(dict_data, filepath)
        return cls.export_csv(dict_data, filepath)

    @classmethod
    def export_trading_signals(cls, signals: List[Any], filepath: Union[str, Path], fmt: str = EXPORT_FORMAT_CSV) -> Tuple[bool, str]:
        """Export Trading Signals list"""
        dict_data = []
        for s in signals:
            if hasattr(s, "to_dict"):
                dict_data.append(s.to_dict())
            elif isinstance(s, dict):
                dict_data.append(s)
            else:
                dict_data.append(vars(s))

        if fmt.lower() == EXPORT_FORMAT_JSON:
            return cls.export_json(dict_data, filepath)
        return cls.export_csv(dict_data, filepath)

    @classmethod
    def export_news(cls, articles: List[Any], filepath: Union[str, Path], fmt: str = EXPORT_FORMAT_CSV) -> Tuple[bool, str]:
        """Export Macro & Company News articles"""
        dict_data = []
        for a in articles:
            if hasattr(a, "to_dict"):
                dict_data.append(a.to_dict())
            elif isinstance(a, dict):
                dict_data.append(a)
            else:
                dict_data.append(vars(a))

        if fmt.lower() == EXPORT_FORMAT_JSON:
            return cls.export_json(dict_data, filepath)
        return cls.export_csv(dict_data, filepath)

    @classmethod
    def export_portfolio(
        cls,
        summary: Any,
        positions: List[Any],
        filepath: Union[str, Path],
        fmt: str = EXPORT_FORMAT_CSV
    ) -> Tuple[bool, str]:
        """Export Portfolio Holdings and summary"""
        if fmt.lower() == EXPORT_FORMAT_JSON:
            summary_dict = summary.to_dict() if hasattr(summary, "to_dict") else vars(summary)
            pos_dicts = [p.to_dict() if hasattr(p, "to_dict") else vars(p) for p in positions]
            payload = {
                "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "portfolio_summary": summary_dict,
                "holdings": pos_dicts
            }
            return cls.export_json(payload, filepath)
        else:
            # Flatten holdings for CSV
            dict_data = [p.to_dict() if hasattr(p, "to_dict") else vars(p) for p in positions]
            return cls.export_csv(dict_data, filepath)

    @classmethod
    def export_trade_history(cls, trades: List[Any], filepath: Union[str, Path], fmt: str = EXPORT_FORMAT_CSV) -> Tuple[bool, str]:
        """Export executed paper trading transactions ledger"""
        dict_data = [t.to_dict() if hasattr(t, "to_dict") else vars(t) for t in trades]
        if fmt.lower() == EXPORT_FORMAT_JSON:
            return cls.export_json(dict_data, filepath)
        return cls.export_csv(dict_data, filepath)

    @classmethod
    def export_backtest_results(cls, result: Any, filepath: Union[str, Path], fmt: str = EXPORT_FORMAT_JSON) -> Tuple[bool, str]:
        """Export backtesting metrics, trade log, and equity curves"""
        if hasattr(result, "to_dict"):
            payload = result.to_dict()
        else:
            payload = vars(result)

        if fmt.lower() == EXPORT_FORMAT_JSON:
            return cls.export_json(payload, filepath)
        else:
            # For CSV, export the trade execution list
            trades = payload.get("trades", [])
            return cls.export_csv(trades, filepath)
