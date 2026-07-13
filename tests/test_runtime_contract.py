import importlib
import unittest


class RuntimeContractTests(unittest.TestCase):
    def test_policy_engine_imports_from_package_context(self):
        module = importlib.import_module("src.engine.policy_rate_engine")

        self.assertTrue(hasattr(module, "PolicyRateEngine"))

    def test_gdp_report_uses_measurement_language(self):
        from src.engine.gdp_nowcast_engine import format_report

        report = format_report(
            "US",
            {
                "quant_val": 0.5,
                "measurement_adjustment": 0.1,
                "ml_calibration_adjustment": 0.05,
                "final_val": 0.6,
                "calibrated_val": 0.65,
                "r2": 0.7,
                "data_thru": "2026-06",
                "target_q": "Current Q",
                "statcan_outlook": None,
                "statcan_date": None,
            },
        )

        self.assertIn("Measurement Adjustment", report)
        self.assertIn("ML Auxiliary Calibration", report)
        self.assertIn("Final Calibrated Nowcast", report)
        self.assertIn("auxiliary calibration", report)
        self.assertNotIn(chr(65) + chr(73), report)
        self.assertNotIn("Sentiment Adjustment", report)
        self.assertNotIn("ML forecast", report)

    def test_nowcast_requires_enough_indicator_data(self):
        import pandas as pd

        from src.engine.gdp_nowcast_engine import GDPCastNowEngine

        engine = GDPCastNowEngine("US")
        engine.fetch_fred = lambda _sid: pd.DataFrame()

        with self.assertRaisesRegex(RuntimeError, "Insufficient FRED indicator data"):
            engine.run_nowcast()

    def test_policy_report_has_clean_bayesian_section_label(self):
        from src.engine.policy_rate_engine import PolicyRateEngine

        report = PolicyRateEngine()._write_economist_report(
            country="US",
            title="Federal Reserve",
            pi=2.5,
            gap=-0.5,
            rate=3.0,
            rec_rate=3.1,
            gap_bps=-10,
            threshold=2.5,
            premium=0,
        )

        self.assertIn("Bayesian Policy Uncertainty", report)
        self.assertIn("Z-Score approx", report)
        self.assertNotIn(chr(65) + chr(73), report)
        self.assertNotIn("\a", report)

    def test_latest_percent_observation_uses_canada_yoy_series_directly(self):
        from src.engine.policy_rate_engine import PolicyRateEngine

        cpi_yoy_data = [
            {"date": "2025-03-01", "value": "2.315394"},
            {"date": "2025-02-01", "value": "2.644836"},
        ]

        current_pi = PolicyRateEngine._latest_percent_observation(
            cpi_yoy_data, fallback=2.4
        )

        self.assertAlmostEqual(current_pi, 2.315394)

    def test_ridge_calibration_is_bounded_auxiliary_adjustment(self):
        import numpy as np
        import pandas as pd
        import statsmodels.api as sm

        from src.engine.gdp_nowcast_engine import GDPCastNowEngine

        combined = pd.DataFrame(
            {
                "GDP": np.linspace(0.0, 3.0, 32),
                "Factor": np.linspace(-1.0, 1.0, 32),
            }
        )
        model = sm.OLS(combined["GDP"], sm.add_constant(combined["Factor"])).fit()

        adjustment = GDPCastNowEngine._ridge_calibration_adjustment(
            combined, model, current_baseline=2.0, max_abs_adjustment=0.25
        )

        self.assertLessEqual(abs(adjustment), 0.25)


if __name__ == "__main__":
    unittest.main()
