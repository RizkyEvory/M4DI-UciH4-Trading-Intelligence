"""
Integration Test for Desktop GUI Startup, Navigation, and Clean Teardown
"""
import unittest
import tempfile
from pathlib import Path

from config.constants import NAV_ITEMS
from core.app_context import AppContext
from database.db_manager import DatabaseManager
from gui.main_window import MainWindow


class TestGuiStartup(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_gui.db"
        
        # Reset singletons
        DatabaseManager._instance = None
        AppContext._instance = None
        
        self.ctx = AppContext()
        self.ctx._db_manager = DatabaseManager(self.db_path)

    def tearDown(self):
        self.ctx.shutdown()
        if hasattr(self.ctx, "_db_manager") and self.ctx._db_manager:
            self.ctx._db_manager.close()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass
        DatabaseManager._instance = None
        AppContext._instance = None

    def test_main_window_startup_and_navigation(self):
        """Instantiate MainWindow and verify every single view opens without crashing"""
        app = MainWindow(self.ctx)
        # Withdraw window so it doesn't pop up during test
        app.withdraw()

        try:
            # Test navigation to each of the 10 navigation views
            for page_name, _ in NAV_ITEMS:
                app.navigate_to(page_name)
                app.update_idletasks()
                self.assertEqual(app._current_view_name, page_name)
                self.assertIn(page_name, app._view_instances)
                self.assertIsNotNone(app._view_instances[page_name])

            # Verify active sidebar button matches
            self.assertEqual(app.sidebar.current_page, NAV_ITEMS[-1][0])
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
