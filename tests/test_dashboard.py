from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
from model import Scenario, calculate  # noqa: E402


class HouseZeroChecks(unittest.TestCase):
    def test_default_reconciles_to_cached_workbook(self) -> None:
        hourly = pd.read_csv(ROOT / "dashboard" / "data" / "hourly.csv.gz")
        self.assertEqual(len(hourly), 8784)
        _, m, _ = calculate(hourly, Scenario())
        expected = {"demand": 13234.444531364, "pv_generation": 14664.503011982,
                    "grid_import": 5997.949180909911, "grid_export": 7187.481803249268,
                    "charge": 2478.8068999757297, "discharge": 2238.2810416970933,
                    "npv": -19963.36719882285}
        for name, value in expected.items():
            self.assertAlmostEqual(m[name], value, places=5, msg=name)
        self.assertEqual(m["annual_savings"], 0)
        _, zero_export, _ = calculate(hourly, Scenario(15, 10, 0))
        self.assertAlmostEqual(zero_export["npv"], -11700.776546247267, places=5)
        _, added_pv, _ = calculate(hourly, Scenario(18, 0, 1))
        self.assertAlmostEqual(added_pv["npv"], -12507.846705606935, places=5)

    def test_views_and_dark_mode_render(self) -> None:
        app = AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        for view in ("Energy patterns", "Scenario economics", "Sources & method"):
            app.radio[0].set_value(view).run()
            self.assertFalse(app.exception, view)
        app.toggle[0].set_value(True).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.toggle[0].value)


if __name__ == "__main__":
    unittest.main()
