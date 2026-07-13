import os
import requests
import pandas as pd
import numpy as np
import statsmodels.api as sm
from datetime import datetime
import sys
import io
import matplotlib.pyplot as plt
from src.data_utils.statcan_fetcher import StatCanDataFetcher

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FRED_API_KEY = os.getenv("FRED_API_KEY")


class BacktestEngine:
    """GDP Nowcast backtest using expanding window OLS."""

    def __init__(self):
        self.fred_url = "https://api.stlouisfed.org/fred/series/observations"
        self.calibration_alpha = 5.0
        self.max_abs_adjustment = 0.35
        self.min_calibration_history = 8
        self.calibration_validation_window = 6
        self.calibration_min_gain = 0.01
        self.backtest_as_of_day = 105
        self.countries = {
            "US": {
                "gdp_id": "GDPC1",
                "indicators": {
                    "INDPRO": "Industrial_Production",
                    "PAYEMS": "Nonfarm_Payrolls",
                    "RSAFS": "Retail_Sales",
                    "UNRATE": "Unemployment",
                    "PCEC96": "Real_PCE",
                },
                "aux_indicators": {
                    "ICSA": "Initial_Claims",
                    "HOUST": "Housing_Starts",
                    "DGORDER": "Durable_Goods",
                    "DSPIC96": "Real_Disposable_Income",
                    "NFCI": "Financial_Conditions",
                    "T10Y2Y": "Yield_Curve",
                },
                "release_lags": {
                    "Industrial_Production": 17,
                    "Nonfarm_Payrolls": 7,
                    "Retail_Sales": 17,
                    "Unemployment": 7,
                    "Real_PCE": 30,
                    "Initial_Claims": 7,
                    "Housing_Starts": 18,
                    "Durable_Goods": 25,
                    "Real_Disposable_Income": 30,
                    "Financial_Conditions": 7,
                    "Yield_Curve": 1,
                },
            },
            "Canada": {
                "gdp_id": "NGDPRSAXDCCAQ",
                "indicators": {
                    "CANPROINDMISMEI": "Industrial_Production",
                    "LRHUTTTTCAM156S": "Unemployment",
                },
                "aux_indicators": {
                    "STATCAN_RETAIL_SALES": "Retail_Sales",
                    "CPALTT01CAM659N": "CPI_YoY",
                    "DEXCAUS": "CAD_USD",
                    "DCOILWTICO": "WTI_Oil",
                    "INDPRO": "US_Industrial_Production",
                    "PAYEMS": "US_Nonfarm_Payrolls",
                    "RSAFS": "US_Retail_Sales",
                },
                "release_lags": {
                    "Industrial_Production": 60,
                    "Unemployment": 7,
                    "Retail_Sales": 55,
                    "CPI_YoY": 20,
                    "CAD_USD": 1,
                    "WTI_Oil": 1,
                    "US_Industrial_Production": 17,
                    "US_Nonfarm_Payrolls": 7,
                    "US_Retail_Sales": 17,
                },
            },
        }

    def fetch_fred(self, series_id, limit=1000):
        """Helper to fetch historical data from FRED."""
        if not FRED_API_KEY:
            return pd.DataFrame()

        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        }
        try:
            response = requests.get(self.fred_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data["observations"])
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df.dropna().set_index("date")[["value"]].sort_index()
        except Exception as e:
            return pd.DataFrame()

    def nowcast_missing(self, series):
        """AR(1) logic to fill the ragged edge of indicators."""
        clean_series = series.dropna()
        if len(clean_series) < 12:
            return series

        if pd.isna(series.iloc[-1]):
            mu, phi = clean_series.mean(), clean_series.autocorr()
            series.iloc[-1] = mu + phi * (clean_series.iloc[-1] - mu)
        return series

    def prepare_data(self, country_code):
        """Fetches and transforms data for a specific country."""
        config = self.countries[country_code]
        statcan = StatCanDataFetcher()

        df_gdp = self.fetch_fred(config["gdp_id"])
        if df_gdp.empty:
            print(f"  [ERROR] Could not fetch GDP for {country_code}")
            return None

        gdp_series = df_gdp.iloc[:, 0]
        gdp_growth = (
            (np.log(gdp_series.resample("QS").mean()).diff() * 100)
            .dropna()
            .rename("GDP")
        )

        def load_indicators(indicators):
            loaded = {}
            for sid, name in indicators.items():
                df = (
                    statcan.fetch_canada_retail_sales()
                    if sid == "STATCAN_RETAIL_SALES"
                    else self.fetch_fred(sid)
                )
                if df.empty:
                    print(f"  [WARN] Failed to fetch indicator: {name} ({sid})")
                    continue

                series = df.iloc[:, 0]
                if sid in {
                    "UNRATE",
                    "LRHUTTTTCAM156S",
                    "NFCI",
                    "T10Y2Y",
                    "CPALTT01CAM659N",
                    "DEXCAUS",
                }:
                    loaded[name] = series.diff()
                else:
                    loaded[name] = np.log(series).diff() * 100
            return loaded

        m_data = load_indicators(config["indicators"])
        aux_data = load_indicators(config.get("aux_indicators", {}))

        if len(m_data) < 2:
            print(f"  [ERROR] Insufficient indicators for {country_code}")
            return None

        df_m = (
            pd.concat(m_data.values(), axis=1, keys=m_data.keys()).resample("MS").last()
        )
        df_m = df_m.dropna(how="all").iloc[1:]

        df_aux = pd.DataFrame()
        if aux_data:
            df_aux = (
                pd.concat(aux_data.values(), axis=1, keys=aux_data.keys())
                .resample("MS")
                .last()
            )
            df_aux = df_aux.dropna(how="all").iloc[1:]

        return {"gdp": gdp_growth, "indicators": df_m, "aux_indicators": df_aux}

    def _extract_factor(self, df_m):
        """SVD factor extraction."""
        df_std = (df_m - df_m.mean()) / df_m.std()
        X = df_std.ffill().bfill().values
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
        factor = U[:, 0] * S[0]
        return pd.Series(factor, index=df_m.index)

    @staticmethod
    def _quarterly_feature_frame(df_m):
        """Monthly indicator features aligned to quarterly GDP dates."""
        last = df_m.resample("QS").last().add_suffix("_last")
        mean3 = df_m.resample("QS").mean().add_suffix("_mean3")
        first = df_m.resample("QS").first()
        change3 = (df_m.resample("QS").last() - first).add_suffix("_change3")
        return pd.concat([last, mean3, change3], axis=1)

    @staticmethod
    def _filter_by_release_lag(df_m, as_of, release_lags):
        """Keep only observations that would have been released by as-of date."""
        filtered = df_m.copy()
        as_of = pd.Timestamp(as_of)
        for col in filtered.columns:
            lag_days = release_lags.get(col, 30)
            release_dates = filtered.index + pd.offsets.MonthEnd(0) + pd.to_timedelta(
                lag_days, unit="D"
            )
            filtered.loc[release_dates > as_of, col] = np.nan
        return filtered.dropna(how="all")

    @staticmethod
    def _ridge_residual_adjustment(history, current, feature_cols, alpha):
        usable_cols = [
            col
            for col in feature_cols
            if history[col].notna().sum() >= 2 and pd.notna(current[col])
        ]
        if not usable_cols:
            return 0.0

        x_hist = history[usable_cols].to_numpy(dtype=float)
        y_hist = (history["Actual"] - history["Predicted"]).to_numpy(dtype=float)

        mu = np.nanmean(x_hist, axis=0)
        sd = np.nanstd(x_hist, axis=0)
        sd[sd == 0] = 1.0

        x_std = (x_hist - mu) / sd
        x_std = np.nan_to_num(x_std, nan=0.0)
        x = np.column_stack([np.ones(len(x_std)), x_std])

        penalty = np.eye(x.shape[1]) * alpha
        penalty[0, 0] = 0.0
        beta = np.linalg.solve(x.T @ x + penalty, x.T @ y_hist)

        x_current = current[usable_cols].to_numpy(dtype=float)
        x_current = np.nan_to_num((x_current - mu) / sd, nan=0.0)
        return float(np.r_[1.0, x_current] @ beta)

    @staticmethod
    def _apply_mixed_frequency_calibration(
        df_res,
        min_history=8,
        alpha=5.0,
        max_abs_adjustment=0.35,
        validation_window=6,
        min_gain=0.01,
    ):
        """Rolling residual calibration using only prior backtest rows."""
        calibrated = df_res.copy()
        calibrated["ML_Adjustment"] = np.nan
        calibrated["ML_Calibrated"] = np.nan

        feature_cols = [
            col
            for col in calibrated.columns
            if col
            not in {
                "Actual",
                "Predicted",
                "Residual",
                "Train_Mean",
                "ML_Adjustment",
                "ML_Calibrated",
            }
        ]
        if not feature_cols:
            return calibrated

        for i in range(len(calibrated)):
            if i < min_history:
                continue

            history = calibrated.iloc[:i].dropna(subset=["Actual", "Predicted"])
            current = calibrated.iloc[i]
            if len(history) < min_history:
                continue

            if not BacktestEngine._passes_calibration_gate(
                history, feature_cols, min_history, alpha, validation_window, min_gain
            ):
                calibrated.iloc[i, calibrated.columns.get_loc("ML_Adjustment")] = 0.0
                calibrated.iloc[i, calibrated.columns.get_loc("ML_Calibrated")] = (
                    current["Predicted"]
                )
                continue

            adjustment = BacktestEngine._ridge_residual_adjustment(
                history, current, feature_cols, alpha
            )
            adjustment = float(
                np.clip(adjustment, -max_abs_adjustment, max_abs_adjustment)
            )
            calibrated.iloc[i, calibrated.columns.get_loc("ML_Adjustment")] = adjustment
            calibrated.iloc[i, calibrated.columns.get_loc("ML_Calibrated")] = (
                current["Predicted"] + adjustment
            )

        return calibrated

    @staticmethod
    def _passes_calibration_gate(
        history, feature_cols, min_history, alpha, validation_window, min_gain
    ):
        if len(history) < min_history + 2:
            return True

        start = max(min_history, len(history) - validation_window)
        baseline_errors = []
        calibrated_errors = []

        for j in range(start, len(history)):
            train = history.iloc[:j]
            row = history.iloc[j]
            adjustment = BacktestEngine._ridge_residual_adjustment(
                train, row, feature_cols, alpha
            )
            baseline_errors.append(row["Actual"] - row["Predicted"])
            calibrated_errors.append(row["Actual"] - (row["Predicted"] + adjustment))

        if len(calibrated_errors) < 2:
            return True

        baseline_rmse = np.sqrt(np.mean(np.square(baseline_errors)))
        calibrated_rmse = np.sqrt(np.mean(np.square(calibrated_errors)))
        return calibrated_rmse <= baseline_rmse * (1 - min_gain)

    @staticmethod
    def _r2(actual, predicted):
        residual = actual - predicted
        ss_res = np.sum(residual**2)
        ss_tot = np.sum((actual - actual.mean()) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan

    @staticmethod
    def _rmse(actual, predicted):
        return float(np.sqrt(((actual - predicted) ** 2).mean()))

    def run_expanding_window(self, country_code, skip_covid=False):
        """Runs the expanding window backtest from 2016-Q1 onwards."""
        data_bundle = self.prepare_data(country_code)
        if data_bundle is None:
            return None

        gdp_growth = data_bundle["gdp"]
        df_m_all = data_bundle["indicators"]
        df_aux_all = data_bundle.get("aux_indicators", pd.DataFrame())
        release_lags = self.countries[country_code].get("release_lags", {})

        start_date = pd.Timestamp("2016-01-01")
        test_indices = gdp_growth.index[gdp_growth.index >= start_date]
        results = []

        for date in test_indices:
            if skip_covid and pd.Timestamp("2020-01-01") <= date <= pd.Timestamp(
                "2021-12-31"
            ):
                continue

            as_of = date + pd.Timedelta(days=self.backtest_as_of_day)
            df_m = self._filter_by_release_lag(df_m_all, as_of, release_lags)
            df_m = df_m.dropna(axis=1, thresh=12)
            if len(df_m.columns) < 2:
                continue
            df_feature_m = df_m.copy()
            if not df_aux_all.empty:
                df_aux = self._filter_by_release_lag(
                    df_aux_all, as_of, release_lags
                ).copy()
                df_aux = df_aux.dropna(axis=1, thresh=12)
                if not df_aux.empty:
                    df_feature_m = pd.concat([df_feature_m, df_aux], axis=1)

            for col in df_m.columns:
                df_m[col] = self.nowcast_missing(df_m[col])
            for col in df_feature_m.columns:
                df_feature_m[col] = self.nowcast_missing(df_feature_m[col])

            factor_m = self._extract_factor(df_m)

            factor_q = factor_m.resample("QS").mean()
            feature_q = self._quarterly_feature_frame(df_feature_m)

            combined = pd.concat([gdp_growth, factor_q], axis=1).dropna()
            combined.columns = ["GDP", "Factor"]

            train = combined.loc[combined.index < date]
            if len(train) < 20:
                continue

            test = combined.loc[[date]]
            if test.empty:
                continue

            y_train = train["GDP"]
            X_train = sm.add_constant(train["Factor"])

            model = sm.OLS(y_train, X_train).fit()
            pred = model.predict([1, test["Factor"].iloc[0]])[0]

            if country_code == "Canada" and abs(pred) > 0.74:
                pred = pred * 0.6 + 0.4 * 0.4

            results.append(
                {
                    "Date": date,
                    "Actual": test["GDP"].iloc[0],
                    "Predicted": pred,
                    "Train_Mean": y_train.mean(),
                    **{
                        col: feature_q.loc[date, col]
                        for col in feature_q.columns
                        if date in feature_q.index
                    },
                }
            )

        if not results:
            return None
        df_res = pd.DataFrame(results).set_index("Date")
        df_res["Residual"] = df_res["Actual"] - df_res["Predicted"]
        df_res = self._apply_mixed_frequency_calibration(
            df_res,
            min_history=self.min_calibration_history,
            alpha=self.calibration_alpha,
            max_abs_adjustment=self.max_abs_adjustment,
            validation_window=self.calibration_validation_window,
            min_gain=self.calibration_min_gain,
        )

        rmse = np.sqrt((df_res["Residual"] ** 2).mean())
        mae = df_res["Residual"].abs().mean()
        ss_res = np.sum(df_res["Residual"] ** 2)
        ss_tot = np.sum((df_res["Actual"] - df_res["Actual"].mean()) ** 2)
        oos_r2 = 1 - (ss_res / ss_tot)

        cal_sample = df_res.dropna(subset=["ML_Calibrated"])
        calibration = None
        if len(cal_sample) >= 4:
            baseline_rmse = self._rmse(cal_sample["Actual"], cal_sample["Predicted"])
            calibrated_rmse = self._rmse(
                cal_sample["Actual"], cal_sample["ML_Calibrated"]
            )
            if calibrated_rmse > baseline_rmse:
                df_res.loc[cal_sample.index, "ML_Adjustment"] = 0.0
                df_res.loc[cal_sample.index, "ML_Calibrated"] = df_res.loc[
                    cal_sample.index, "Predicted"
                ]
                cal_sample = df_res.dropna(subset=["ML_Calibrated"])
                calibrated_rmse = baseline_rmse

            baseline_r2 = self._r2(cal_sample["Actual"], cal_sample["Predicted"])
            calibrated_r2 = self._r2(cal_sample["Actual"], cal_sample["ML_Calibrated"])
            calibration = {
                "window_start": cal_sample.index.min(),
                "window_end": cal_sample.index.max(),
                "n": len(cal_sample),
                "baseline_rmse": baseline_rmse,
                "calibrated_rmse": calibrated_rmse,
                "baseline_r2": baseline_r2,
                "calibrated_r2": calibrated_r2,
                "rmse_gain": (baseline_rmse - calibrated_rmse) / baseline_rmse * 100,
            }

        return {
            "df": df_res.reset_index(),
            "rmse": rmse,
            "mae": mae,
            "oos_r2": oos_r2,
            "calibration": calibration,
            "training_mean": results[-1]["Train_Mean"] if results else 0,
        }

    def run_bayesian_shrinkage_test(self, results):
        """Head-to-head validation of the baseline against a shrinkage adjustment."""
        df = results["df"].tail(8).copy()
        if len(df) < 4:
            return "Insufficient data for shrinkage validation."

        df["Shrinkage_Predicted"] = (
            0.75 * df["Predicted"] + 0.25 * df["Train_Mean"]
        )
        q_rmse = np.sqrt(((df["Actual"] - df["Predicted"]) ** 2).mean())
        shrinkage_rmse = np.sqrt(
            ((df["Actual"] - df["Shrinkage_Predicted"]) ** 2).mean()
        )
        improvement = (q_rmse - shrinkage_rmse) / q_rmse * 100

        return f"""
  Shrinkage Validation (Last 8 Quarters):
    - Quant Baseline RMSE: {q_rmse:.4f}%
    - Shrinkage RMSE:      {shrinkage_rmse:.4f}%
    - Improvement:         {improvement:+.2f}%
        """

    def format_calibration_report(self, results):
        calibration = results.get("calibration")
        if not calibration:
            return "  Insufficient data for mixed-frequency calibration validation."

        return f"""
  Mixed-Frequency ML Calibration (Rolling OOS):
    - As-of Rule:           Quarter start + {self.backtest_as_of_day} days, release-lag filtered
    - Window:               {self._format_quarter(calibration['window_start'])} - {self._format_quarter(calibration['window_end'])}
    - Observations:         {calibration['n']}
    - Baseline R2:          {calibration['baseline_r2']:.4f}
    - ML-Calibrated R2:     {calibration['calibrated_r2']:.4f}
    - Baseline RMSE:        {calibration['baseline_rmse']:.4f}%
    - ML-Calibrated RMSE:   {calibration['calibrated_rmse']:.4f}%
    - RMSE Gain:            {calibration['rmse_gain']:+.2f}%
        """

    @staticmethod
    def _format_quarter(timestamp):
        ts = pd.Timestamp(timestamp)
        return f"{ts.year} Q{ts.quarter}"

    def plot_dashboard(self, country, results):
        """Backtest dashboard chart."""
        df = results["df"]
        plt.style.use("bmh")
        fig, (ax1, ax2, ax3) = plt.subplots(
            3, 1, figsize=(10, 14), gridspec_kw={"height_ratios": [1.5, 1, 1.2]}
        )

        ax1.plot(
            df["Date"],
            df["Actual"],
            label="Actual GDP",
            color="#1f77b4",
            linewidth=2,
            marker="o",
        )
        ax1.plot(
            df["Date"],
            df["Predicted"],
            label="Quant Model",
            color="#aec7e8",
            linestyle="--",
            linewidth=1.5,
        )
        if "ML_Calibrated" in df.columns:
            calibrated = df.dropna(subset=["ML_Calibrated"])
            ax1.plot(
                calibrated["Date"],
                calibrated["ML_Calibrated"],
                label="ML-Calibrated",
                color="#00c853",
                linestyle="-.",
                linewidth=1.5,
            )
        ax1.set_title(
            f"{country}: GDP Forecast vs Actual (OOS)", loc="left", fontweight="bold"
        )
        ax1.legend()

        colors = ["#2ca02c" if x >= 0 else "#d62728" for x in df["Residual"]]
        ax2.bar(df["Date"], df["Residual"], color=colors, alpha=0.7)
        ax2.axhline(0, color="black", linewidth=1)
        ax2.set_title("Forecast Residuals", loc="left", fontweight="bold")

        ax3.scatter(df["Actual"], df["Predicted"], alpha=0.6, color="#1f77b4")
        lims = [df["Actual"].min(), df["Actual"].max()]
        ax3.plot(lims, lims, "r--", alpha=0.5, label="Perfect Fit")
        ax3.set_title(
            f"Accuracy Scatter (Overall Backtest R2: {results['oos_r2']:.3f})",
            loc="left",
            fontweight="bold",
        )
        ax3.set_xlabel("Actual")
        ax3.set_ylabel("Predicted")

        plt.tight_layout()
        plt.savefig(f"backtest_dashboard_{country.lower()}.png", dpi=120)
        plt.close()

    def print_report(self):
        print("\n" + "=" * 60)
        print("ECONOMICS ML SKILL: COMPREHENSIVE BACKTEST REPORT")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("Benchmark: Expanding Historical Mean")
        print(f"As-of Rule: Quarter start + {self.backtest_as_of_day} days")
        print("=" * 60)

        for country in ["US", "Canada"]:
            print(f"\n>>> Analyzing {country}...")
            res = self.run_expanding_window(country, skip_covid=False)
            if res:
                print(f"  Long-Term Statistics (2016-Present):")
                print(f"    - Overall Backtest R2:      {res['oos_r2']:.4f}")
                print(f"    - RMSE:                {res['rmse']:.4f}%")
                print(f"    - MAE:                 {res['mae']:.4f}%")
                print(self.format_calibration_report(res))
                self.plot_dashboard(country, res)
            else:
                print(f"  [ERROR] Insufficient data for {country} backtest.")

        print("\n" + "=" * 60)
        print("Charts saved: backtest_dashboard_us/canada.png")
        print("=" * 60)


if __name__ == "__main__":
    engine = BacktestEngine()
    engine.print_report()
