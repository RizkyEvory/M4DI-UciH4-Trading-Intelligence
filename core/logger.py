"""
M4DI~UciH4 Trading Intelligence System
Multi-Target Logging System (Console, File, SQLite DB)
"""
import logging
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from config.constants import LOG_FILE_PATH

# Safe sanitization regex to mask potential secrets in logs
_KEY_PATTERN = re.compile(r'(api[-_]?key|secret|token|password)[\s:=]+([a-zA-Z0-9_\-\.]{8,})', re.IGNORECASE)


def sanitize_message(msg: str) -> str:
    """Mask any API keys or tokens accidentally included in log messages"""
    def _replacer(match):
        prefix = match.group(1)
        val = match.group(2)
        masked = f"{val[:2]}••••••••{val[-2:]}" if len(val) > 4 else "••••••••"
        return f"{prefix}={masked}"
    return _KEY_PATTERN.sub(_replacer, msg)


class SQLiteLogHandler(logging.Handler):
    """Custom logging handler that records events into SQLite logs table"""

    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self._lock = threading.Lock()

    def set_db_manager(self, db_manager):
        with self._lock:
            self.db_manager = db_manager

    def emit(self, record: logging.LogRecord):
        if not self.db_manager:
            return
            
        try:
            msg = self.format(record)
            sanitized = sanitize_message(msg)
            # Use module name or split logger name
            module = record.name.replace("m4di.", "")
            level = record.levelname
            timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

            with self._lock:
                self.db_manager.execute(
                    "INSERT INTO logs (timestamp, level, module, message) VALUES (?, ?, ?, ?)",
                    (timestamp, level, module, sanitized)
                )
        except Exception:
            # Avoid infinite recursion if DB write fails
            pass


_APP_LOGGER: Optional[logging.Logger] = None
_SQLITE_HANDLER: Optional[SQLiteLogHandler] = None


def setup_logging(db_manager=None, log_level: str = "INFO") -> logging.Logger:
    """Initialize root application logger with File, Stream, and SQLite Handlers"""
    global _APP_LOGGER, _SQLITE_HANDLER

    logger = logging.getLogger("m4di")
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers on re-init
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 1. Console Stream Handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(numeric_level)
        logger.addHandler(stream_handler)

        # 2. File Handler
        try:
            LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(LOG_FILE_PATH), encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_level)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Failed to initialize file logger: {e}")

        # 3. SQLite Database Handler
        _SQLITE_HANDLER = SQLiteLogHandler(db_manager)
        db_formatter = logging.Formatter("%(message)s")
        _SQLITE_HANDLER.setFormatter(db_formatter)
        _SQLITE_HANDLER.setLevel(numeric_level)
        logger.addHandler(_SQLITE_HANDLER)
    else:
        if db_manager and _SQLITE_HANDLER:
            _SQLITE_HANDLER.set_db_manager(db_manager)

    _APP_LOGGER = logger
    return logger


def get_app_logger(submodule: str = "") -> logging.Logger:
    """Get a scoped sub-logger for a specific module"""
    name = f"m4di.{submodule}" if submodule else "m4di"
    return logging.getLogger(name)

# Semantic alias
get_logger = get_app_logger
