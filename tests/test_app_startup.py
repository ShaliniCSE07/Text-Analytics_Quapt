import os
import sqlite3
import unittest

from app import main as app_module


class AppStartupDatabaseTest(unittest.TestCase):
    def test_startup_creates_required_tables(self):
        db_path = os.path.join("data", "reviews.db")
        app_module.init_db()

        self.assertTrue(os.path.exists(db_path))
        with sqlite3.connect(db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()

        self.assertIn(("Customer_Reviews",), tables)
        self.assertIn(("Customer_Reviews_Analysis",), tables)


if __name__ == "__main__":
    unittest.main()
