"""
M4DI~UciH4 Trading Intelligence System
Entry Point & Application Bootstrapper — Enterprise Edition
"""
import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.constants import APP_NAME, APP_VERSION
from core.app_context import AppContext
from core.logger import setup_logging, get_app_logger
from gui.main_window import MainWindow


def main():
    """Application Initialization & Main Execution Loop"""
    # 1. Initialize Dependency Container
    ctx = AppContext()

    # 2. Configure Logging System with SQLite & File Handlers
    log_level = ctx.settings.get("log_level", "INFO")
    logger = setup_logging(db_manager=ctx.db, log_level=log_level)

    logger.info("=" * 70)
    logger.info(f"Starting {APP_NAME} ({APP_VERSION})")
    logger.info("M4DI~UciH4 Core Services, Multi-threaded Engine & GUI initialized.")
    logger.info("=" * 70)

    # 3. Launch Desktop GUI Shell
    try:
        app = MainWindow(ctx)
        app.mainloop()
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt received. Terminating application.")
        ctx.shutdown()
    except Exception as e:
        logger.critical(f"Unhandled fatal exception in GUI event loop: {e}", exc_info=True)
        ctx.shutdown()
        sys.exit(1)

    logger.info(f"{APP_NAME} shut down cleanly. Goodbye.")


if __name__ == "__main__":
    main()
