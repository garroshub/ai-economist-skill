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
                "target_q": "2026 Q2",
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
        self.assertNotIn("Current Q", report)

    def test_nowcast_requires_enough_indicator_data(self):
        import pandas as pd

        from src.engine.gdp_nowcast_engine import GDPCastNowEngine

        engine = GDPCastNowEngine("US")
        engine.fetch_fred = lambda _sid: pd.DataFrame()

        with self.assertRaisesRegex(RuntimeError, "Insufficient FRED indicator data"):
            engine.run_nowcast()

    def test_policy_report_has_clean_uncertainty_section_label(self):
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

        self.assertIn("Empirical Uncertainty Check", report)
        self.assertIn("Z-Score approx", report)
        self.assertNotIn(chr(65) + chr(73), report)
        self.assertNotIn("Bayesian", report)
        self.assertNotIn("\a", report)

    def test_policy_report_shows_base_and_data_enhanced_taylor_layers(self):
        from src.engine.policy_rate_engine import PolicyRateEngine

        report = PolicyRateEngine()._write_economist_report(
            country="US",
            title="Federal Reserve",
            pi=3.0,
            gap=-0.5,
            rate=3.5,
            rec_rate=4.0,
            gap_bps=-50,
            threshold=2.5,
            premium=0,
            enhanced_rate=3.8,
            enhanced_gap_bps=-30,
            enhanced_adjustments={
                "activity_gap": -0.10,
                "financial_conditions": -0.05,
            },
        )

        self.assertIn("Base Taylor Rate", report)
        self.assertIn("Data-Enhanced Taylor Rate", report)
        self.assertIn("Enhancement Decomposition", report)
        self.assertNotIn("SEP", report)

    def test_policy_data_enhancement_is_learned_from_history(self):
        import pandas as pd

        from src.engine.policy_rate_engine import PolicyRateEngine

        calibration_frame = pd.DataFrame(
            {
                "target_adjustment": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
                "activity_gap": [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
                "inflation_pressure": [0.0, 0.1, 0.0, 0.1, 0.0, 0.1, 0.0],
                "financial_conditions": [0.0, 0.0, 0.1, 0.0, 0.1, 0.0, 0.1],
                "external_pressure": [0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.1],
            }
        )

        enhanced_rate, adjustments = PolicyRateEngine._data_enhanced_taylor_rate(
            base_rate=5.0,
            current_features={
                "activity_gap": 5.0,
                "inflation_pressure": 0.0,
                "financial_conditions": 0.0,
                "external_pressure": 0.0,
            },
            calibration_frame=calibration_frame,
        )

        total_adjustment = enhanced_rate - 5.0

        self.assertGreater(total_adjustment, 0.0)
        self.assertLessEqual(
            abs(total_adjustment),
            calibration_frame["target_adjustment"].abs().max() + 1e-9,
        )
        self.assertIn("activity_gap", adjustments)
        self.assertIn("financial_conditions", adjustments)
        self.assertIn("external_pressure", adjustments)

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

    def test_quarter_label_uses_concrete_calendar_quarter(self):
        import pandas as pd

        from src.engine.gdp_nowcast_engine import GDPCastNowEngine

        self.assertEqual(GDPCastNowEngine._quarter_label(pd.Timestamp("2026-06-01")), "2026 Q2")
        self.assertEqual(GDPCastNowEngine._quarter_label(pd.Timestamp("2026-07-01")), "2026 Q3")

    def test_backtest_quarterly_feature_frame_preserves_monthly_information(self):
        import pandas as pd

        from backtest_engine import BacktestEngine

        df_m = pd.DataFrame(
            {
                "Production": [1.0, 2.0, 4.0, 3.0],
                "Jobs": [0.5, 0.7, 1.0, 1.2],
            },
            index=pd.to_datetime(["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01"]),
        )

        features = BacktestEngine._quarterly_feature_frame(df_m)

        self.assertIn("Production_last", features.columns)
        self.assertIn("Production_mean3", features.columns)
        self.assertIn("Production_change3", features.columns)
        self.assertAlmostEqual(features.loc[pd.Timestamp("2026-01-01"), "Production_last"], 4.0)
        self.assertAlmostEqual(features.loc[pd.Timestamp("2026-01-01"), "Production_mean3"], 7.0 / 3.0)
        self.assertAlmostEqual(features.loc[pd.Timestamp("2026-01-01"), "Production_change3"], 3.0)

    def test_backtest_mixed_frequency_calibration_uses_prior_errors_only(self):
        import numpy as np
        import pandas as pd

        from backtest_engine import BacktestEngine

        dates = pd.date_range("2020-01-01", periods=10, freq="QS")
        df = pd.DataFrame(
            {
                "Actual": np.arange(10, dtype=float),
                "Predicted": np.arange(10, dtype=float) - 1.0,
                "Feature_last": np.arange(10, dtype=float),
                "Feature_mean3": np.arange(10, dtype=float),
            },
            index=dates,
        )

        calibrated = BacktestEngine._apply_mixed_frequency_calibration(
            df, min_history=5, alpha=1.0, max_abs_adjustment=0.5
        )

        self.assertTrue(calibrated["ML_Calibrated"].iloc[:5].isna().all())
        self.assertLessEqual(abs(calibrated["ML_Adjustment"].iloc[5]), 0.5)
        self.assertAlmostEqual(calibrated["ML_Calibrated"].iloc[5], calibrated["Predicted"].iloc[5] + calibrated["ML_Adjustment"].iloc[5])

    def test_backtest_fred_fetch_requests_latest_observations(self):
        import os
        from unittest.mock import Mock, patch

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "observations": [{"date": "2026-01-01", "value": "1"}]
        }

        with patch.dict(os.environ, {"FRED_API_KEY": "test-key"}):
            with patch("backtest_engine.requests.get", return_value=response) as get:
                from backtest_engine import BacktestEngine

                BacktestEngine().fetch_fred("TEST")

        params = get.call_args.kwargs["params"]
        self.assertEqual(params["sort_order"], "desc")

    def test_release_lag_filter_excludes_unreleased_monthly_observations(self):
        import pandas as pd

        from backtest_engine import BacktestEngine

        df_m = pd.DataFrame(
            {"Slow": [1.0, 2.0], "Fast": [10.0, 20.0]},
            index=pd.to_datetime(["2026-01-01", "2026-02-01"]),
        )

        filtered = BacktestEngine._filter_by_release_lag(
            df_m,
            as_of=pd.Timestamp("2026-02-15"),
            release_lags={"Slow": 20, "Fast": 5},
        )

        self.assertEqual(list(filtered["Slow"].dropna()), [])
        self.assertEqual(list(filtered["Fast"].dropna()), [10.0])

    def test_us_has_country_specific_auxiliary_high_frequency_indicators(self):
        from backtest_engine import BacktestEngine

        config = BacktestEngine().countries["US"]

        self.assertIn("ICSA", config["aux_indicators"])
        self.assertIn("HOUST", config["aux_indicators"])
        self.assertIn("DGORDER", config["aux_indicators"])

    def test_canada_has_open_economy_auxiliary_indicators(self):
        from backtest_engine import BacktestEngine

        config = BacktestEngine().countries["Canada"]

        self.assertIn("CPALTT01CAM659N", config["aux_indicators"])
        self.assertIn("DEXCAUS", config["aux_indicators"])
        self.assertIn("DCOILWTICO", config["aux_indicators"])
        self.assertIn("INDPRO", config["aux_indicators"])


if __name__ == "__main__":
    unittest.main()
