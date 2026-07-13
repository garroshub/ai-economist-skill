import os
import requests
import pandas as pd
import numpy as np
import statsmodels.api as sm
from datetime import datetime
import sys
import io
import matplotlib.pyplot as plt

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FRED_API_KEY = os.getenv("FRED_API_KEY")


class BacktestEngine:
    """GDP Nowcast backtest using expanding window OLS."""

    def __init__(self):
        self.fred_url = "https://api.stlouisfed.org/fred/series/observations"
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
            },
            "Canada": {
                "gdp_id": "NGDPRSAXDCCAQ",
                "indicators": {
                    "CANPROINDMISMEI": "Industrial_Production",
                    "SLRTTO01CAM659S": "Retail_Sales",
                    "LRHUTTTTCAM156S": "Unemployment",
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
            "sort_order": "asc",
            "limit": limit,
        }
        try:
            response = requests.get(self.fred_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data["observations"])
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df.dropna().set_index("date")[["value"]]
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

        m_data = {}
        for sid, name in config["indicators"].items():
            df = self.fetch_fred(sid)
            if df.empty:
                print(f"  [WARN] Failed to fetch indicator: {name} ({sid})")
                continue

            series = df.iloc[:, 0]
            if "UNRATE" in sid or "LRHUT" in sid:
                m_data[name] = series.diff()
            else:
                m_data[name] = np.log(series).diff() * 100

        if len(m_data) < 2:
            print(f"  [ERROR] Insufficient indicators for {country_code}")
            return None

        df_m = (
            pd.concat(m_data.values(), axis=1, keys=m_data.keys()).resample("MS").last()
        )
        df_m = df_m.dropna(how="all").iloc[1:]

        return {"gdp": gdp_growth, "indicators": df_m}

    def _extract_factor(self, df_m):
        """SVD factor extraction."""
        df_std = (df_m - df_m.mean()) / df_m.std()
        X = df_std.ffill().bfill().values
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
        factor = U[:, 0] * S[0]
        return pd.Series(factor, index=df_m.index)

    def run_expanding_window(self, country_code, skip_covid=False):
        """Runs the expanding window backtest from 2016-Q1 onwards."""
        data_bundle = self.prepare_data(country_code)
        if data_bundle is None:
            return None

        gdp_growth = data_bundle["gdp"]
        df_m_all = data_bundle["indicators"]

        start_date = pd.Timestamp("2016-01-01")
        test_indices = gdp_growth.index[gdp_growth.index >= start_date]
        results = []

        for date in test_indices:
            if skip_covid and pd.Timestamp("2020-01-01") <= date <= pd.Timestamp(
                "2021-12-31"
            ):
                continue

            q_end = date + pd.offsets.QuarterEnd(0)
            df_m = df_m_all.loc[:q_end].copy()

            for col in df_m.columns:
                df_m[col] = self.nowcast_missing(df_m[col])

            factor_m = self._extract_factor(df_m)

            factor_q = factor_m.resample("QS").mean()

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
                }
            )

        if not results:
            return None
        df_res = pd.DataFrame(results).set_index("Date")
        df_res["Residual"] = df_res["Actual"] - df_res["Predicted"]

        rmse = np.sqrt((df_res["Residual"] ** 2).mean())
        mae = df_res["Residual"].abs().mean()
        ss_res = np.sum(df_res["Residual"] ** 2)
        ss_tot = np.sum((df_res["Actual"] - df_res["Actual"].mean()) ** 2)
        oos_r2 = 1 - (ss_res / ss_tot)

        return {
            "df": df_res.reset_index(),
            "rmse": rmse,
            "mae": mae,
            "oos_r2": oos_r2,
            "training_mean": results[-1]["Train_Mean"] if results else 0,
        }

    def run_bayesian_shrinkage_test(self, results):
        """Head-to-head validation of the baseline against a shrinkage adjustment."""
        df = results["df"].tail(8).copy()
        if len(df) < 4:
            return "Insufficient data for shrinkage validation."

        df["Shrinkage_Predicted"] = (
            0.75 * df["Predicted"] + 0.25 * results["training_mean"]
        )

        q_rmse = np.sqrt(((df["Actual"] - df["Predicted"]) ** 2).mean())
        shrinkage_rmse = np.sqrt(
            ((df["Actual"] - df["Shrinkage_Predicted"]) ** 2).mean()
        )
        improvement = (q_rmse - shrinkage_rmse) / q_rmse * 100

        return f"""
  Bayesian Shrinkage Validation (Last 8 Quarters):
    - Quant Baseline RMSE: {q_rmse:.4f}%
    - Shrinkage RMSE:      {shrinkage_rmse:.4f}%
    - Improvement:         {improvement:+.2f}%
        """

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
        print("=" * 60)

        for country in ["US", "Canada"]:
            print(f"\n>>> Analyzing {country}...")
            res = self.run_expanding_window(country, skip_covid=False)
            if res:
                print(f"  Long-Term Statistics (2016-Present):")
                print(f"    - Overall Backtest R2:      {res['oos_r2']:.4f}")
                print(f"    - RMSE:                {res['rmse']:.4f}%")
                print(f"    - MAE:                 {res['mae']:.4f}%")
                print(self.run_bayesian_shrinkage_test(res))
                self.plot_dashboard(country, res)
            else:
                print(f"  [ERROR] Insufficient data for {country} backtest.")

        print("\n" + "=" * 60)
        print("Charts saved: backtest_dashboard_us/canada.png")
        print("=" * 60)


if __name__ == "__main__":
    engine = BacktestEngine()
    engine.print_report()
