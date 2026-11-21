"""
M4DI~UciH4 Trading Intelligence System
Date, Currency, and String Formatting Helpers
"""
from datetime import datetime


def format_timestamp(dt_str: str) -> str:
    """Format an ISO or SQLite timestamp into a friendly readable format"""
    if not dt_str:
        return "-"
    try:
        # If timestamp contains date and time
        dt = datetime.strptime(dt_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return dt_str


def format_number(val: float, decimals: int = 2) -> str:
    """Format floating point numbers cleanly with comma separators"""
    try:
        return f"{val:,.{decimals}f}"
    except (ValueError, TypeError):
        return "0.00"
