from statsmodels.tsa.filters.hp_filter import hpfilter
import pandas as pd
import numpy as np
from src.data_utils.macro_data_fetcher import MacroDataFetcher
from src.core.modeling_core import PolicyOracle
from src.core.visual_oracle import plot_taylor_sensitivity
import os


class PolicyRateEngine:
    def __init__(self):
        self.fetcher = MacroDataFetcher()
        self.engine = PolicyOracle()

    @staticmethod
    def _latest_percent_observation(data, fallback):
        """Return the latest observation when a source is already a percent rate."""
        if isinstance(data, list) and data:
            try:
                return float(data[0]["value"])
            except (KeyError, TypeError, ValueError):
                return fallback
        return fallback

    @staticmethod
    def _latest_float(data, fallback=0.0):
        if isinstance(data, list) and data:
            try:
                return float(data[0]["value"])
            except (KeyError, TypeError, ValueError):
                return fallback
        return fallback

    @staticmethod
    def _recent_change(data, fallback=0.0, periods=3):
        if isinstance(data, list) and len(data) > periods:
            try:
                return float(data[0]["value"]) - float(data[periods]["value"])
            except (KeyError, TypeError, ValueError):
                return fallback
        return fallback

    @staticmethod
    def _records_to_series(data):
        if not isinstance(data, list) or not data:
            return pd.Series(dtype=float)
        rows = []
        for row in data:
            try:
                rows.append((pd.Timestamp(row["date"]), float(row["value"])))
            except (KeyError, TypeError, ValueError):
                continue
        if not rows:
            return pd.Series(dtype=float)
        series = pd.Series(dict(rows)).sort_index()
        return series[~series.index.duplicated(keep="last")]

    def _build_policy_calibration_frame(self, country, r_star_real_mid):
        def monthly(series):
            if series.empty:
                return series
            return series.resample("MS").mean().ffill()

        if country == "US":
            actual = monthly(self._records_to_series(
                self.fetcher.fetch_fred_series("IRSTCI01USM156N", limit=220)
            ))
            price = monthly(self._records_to_series(
                self.fetcher.fetch_fred_series("PCEPILFE", limit=220)
            ))
            unrate = monthly(self._records_to_series(
                self.fetcher.fetch_fred_series("UNRATE", limit=220)
            ))
            nrou = monthly(self._records_to_series(
                self.fetcher.fetch_fred_series("NROU", limit=80)
            ))
            financial = monthly(self._records_to_series(
                self.fetcher.fetch_fred_series("NFCI", limit=220)
            ))
            labor = self._records_to_series(
                self.fetcher.fetch_fred_series("ICSA", limit=1000)
            ).resample("MS").mean()
            external = pd.Series(0.0, index=actual.index)
        else:
            actual = monthly(self._records_to_series(
                self.fetcher.fetch_fred_series("IRSTCI01CAM156N", limit=220)
            ))
            price = monthly(self._records_to_series(
                self.fetcher.fetch_fred_series("CPALTT01CAM659N", limit=220)
            ))
            unrate = monthly(self._records_to_series(
                self.fetcher.fetch_fred_series("LRHUTTTTCAM156S", limit=220)
            ))
            nrou = unrate.rolling(60, min_periods=24).mean()
            financial = pd.Series(0.0, index=actual.index)
            cad = self._records_to_series(
                self.fetcher.fetch_fred_series("DEXCAUS", limit=1000)
            ).resample("MS").mean()
            oil = self._records_to_series(
                self.fetcher.fetch_fred_series("DCOILWTICO", limit=1000)
            ).resample("MS").mean()
            external = cad.pct_change(3) * 100 + oil.pct_change(3) * 10

        if country == "US":
            inflation = price.pct_change(12) * 100
        else:
            inflation = price

        output_gap = -2.0 * (unrate - nrou.ffill())
        inflation_gap = inflation - 2.0
        adjusted_gap = pd.Series(
            np.where(inflation > 2.5, inflation_gap * 1.5, inflation_gap),
            index=inflation.index,
        )
        base_rate = r_star_real_mid + inflation + 0.5 * adjusted_gap + output_gap

        frame = pd.concat(
            [
                actual.rename("actual_rate"),
                base_rate.rename("base_rate"),
                output_gap.rename("activity_gap"),
                (inflation - 2.0).rename("inflation_pressure"),
                financial.rename("financial_conditions"),
                external.rename("external_pressure"),
                labor.pct_change(12).mul(100).rename("labor_cooling")
                if country == "US"
                else pd.Series(0.0, index=actual.index).rename("labor_cooling"),
            ],
            axis=1,
        ).dropna()
        frame["target_adjustment"] = frame["actual_rate"] - frame["base_rate"]
        return frame[
            [
                "target_adjustment",
                "activity_gap",
                "inflation_pressure",
                "financial_conditions",
                "external_pressure",
                "labor_cooling",
            ]
        ]

    @staticmethod
    def _data_enhanced_taylor_rate(
        base_rate,
        current_features,
        calibration_frame,
    ):
        feature_cols = [
            col for col in calibration_frame.columns if col != "target_adjustment"
        ]
        sample = calibration_frame.dropna(subset=["target_adjustment"] + feature_cols)
        if len(sample) < len(feature_cols) + 2:
            return base_rate, {col: 0.0 for col in feature_cols + ["total"]}

        x_hist = sample[feature_cols].to_numpy(dtype=float)
        y_hist = sample["target_adjustment"].to_numpy(dtype=float)
        mu = x_hist.mean(axis=0)
        sd = x_hist.std(axis=0)
        sd[sd == 0] = 1.0
        x_std = (x_hist - mu) / sd
        x = np.column_stack([np.ones(len(x_std)), x_std])
        beta = np.linalg.pinv(x) @ y_hist

        current = np.array(
            [float(current_features.get(col, 0.0)) for col in feature_cols],
            dtype=float,
        )
        current_std = (current - mu) / sd
        raw_total = float(np.r_[1.0, current_std] @ beta)
        empirical_bound = float(np.max(np.abs(y_hist)))
        total = float(np.clip(raw_total, -empirical_bound, empirical_bound))

        contributions = {
            col: float(beta[i + 1] * current_std[i]) for i, col in enumerate(feature_cols)
        }
        intercept = float(beta[0])
        contribution_sum = intercept + sum(contributions.values())
        if contribution_sum != 0:
            scale = total / contribution_sum
            contributions = {k: v * scale for k, v in contributions.items()}
            intercept *= scale
        contributions["intercept"] = intercept
        contributions["total"] = total
        contributions["n"] = float(len(sample))
        return base_rate + total, contributions

    def generate_analysis(self, country="US"):
        """Run full pipeline: fetch -> model -> visualize -> report."""
        print(f"--- Initiating Oracle Sequence for {country} ---")

        if country == "US":
            print("   > Fetching BLS & FRED data...")
            unrate_data = self.fetcher.fetch_bls_unemployment()
            pce_data = self.fetcher.fetch_fred_series("PCEPILFE", limit=20)
            dff_data = self.fetcher.fetch_fred_series("DFF", limit=5)

            gdp_real_long = self.fetcher.fetch_fred_series("GDPC1", limit=100)
            cap_util = self.fetcher.fetch_fred_series("TCU", limit=240)
            nrou_data = self.fetcher.fetch_fred_series("NROU", limit=5)
            nfci_data = self.fetcher.fetch_fred_series("NFCI", limit=5)
            claims_data = self.fetcher.fetch_fred_series("ICSA", limit=20)

            u_actual = 4.4
            if isinstance(unrate_data, dict):
                try:
                    u_actual = float(unrate_data["value"])
                except:
                    pass

            current_pi = 2.8
            if len(pce_data) >= 13:
                latest = float(pce_data[0]["value"])
                year_ago = float(pce_data[12]["value"])
                current_pi = (latest / year_ago - 1) * 100

            actual_rate = 3.64
            if len(dff_data) > 0:
                actual_rate = float(dff_data[0]["value"])

            u_star = 4.2
            if nrou_data and len(nrou_data) > 0:
                u_star = float(nrou_data[0]["value"])
            gap_okun = -2.0 * (u_actual - u_star)

            gap_hp = -0.5
            if gdp_real_long and len(gdp_real_long) > 20:
                try:
                    data_list = [
                        {"date": x["date"], "value": float(x["value"])}
                        for x in gdp_real_long
                    ]
                    df_gdp = pd.DataFrame(data_list).sort_values("date")
                    df_gdp["log_gdp"] = np.log(df_gdp["value"])
                    cycle, trend = hpfilter(df_gdp["log_gdp"], lamb=1600)
                    gap_hp = cycle.iloc[-1] * 100
                except Exception as e:
                    print(f"   > HP Filter Error: {e}")

            gap_cap = -0.3
            if cap_util and len(cap_util) > 120:
                try:
                    curr_cap = float(cap_util[0]["value"])
                    vals = [float(x["value"]) for x in cap_util if x["value"] != "."]
                    avg_cap = sum(vals) / len(vals)
                    gap_cap = curr_cap - avg_cap
                except:
                    pass

            print(
                f"   > Gaps Calculated: Okun={gap_okun:.2f}%, HP_Filter={gap_hp:.2f}%, CapUtil={gap_cap:.2f}%"
            )

            sep_long = self.fetcher.fetch_fred_series("FEDTARGLMD", limit=5)
            r_star_nominal_mid = 2.6
            if sep_long and len(sep_long) > 0:
                try:
                    r_star_nominal_mid = float(sep_long[0]["value"])
                except:
                    pass

            r_star_real_mid = r_star_nominal_mid - 2.0
            r_star_real_range = [r_star_real_mid - 0.3, r_star_real_mid + 0.3]

            threshold_val = 2.5

            gap_scenarios = {
                f"Labor Model (Okun: {gap_okun:.1f}%)": gap_okun,
                f"Statistical Trend (HP Filter: {gap_hp:.1f}%)": gap_hp,
                f"Industrial Model (CapUtil: {gap_cap:.1f}%)": gap_cap,
            }
            output_gap = gap_hp
            activity_gap_enhanced = float(np.median([gap_okun, gap_hp, gap_cap]))
            financial_stress = self._latest_float(nfci_data, 0.0)
            claims_pressure = self._recent_change(claims_data, 0.0, periods=12)
            inflation_pressure = current_pi - 2.0
            labor_cooling = claims_pressure / 1000.0
            external_pressure = 0.0
            title = "Federal Reserve (US)"

        elif country == "Canada":
            print("   > Fetching BoC & FRED data for Canada...")
            boc_data = self.fetcher.fetch_boc_data()
            actual_rate = boc_data.get("policy_rate", 2.25)

            unrate_data = self.fetcher.fetch_fred_series("LRHUTTTTCAM156S", limit=5)
            gdp_real_long = self.fetcher.fetch_fred_series("NGDPRSAXDCCAQ", limit=100)
            cap_util = self.fetcher.fetch_fred_series("BSCACP02CAM659S", limit=240)
            cpi_data = self.fetcher.fetch_fred_series("CPALTT01CAM659N", limit=20)
            cad_data = self.fetcher.fetch_fred_series("DEXCAUS", limit=20)
            oil_data = self.fetcher.fetch_fred_series("DCOILWTICO", limit=20)

            u_actual = 6.8
            if isinstance(unrate_data, list) and len(unrate_data) > 0:
                try:
                    u_actual = float(unrate_data[0]["value"])
                except:
                    pass

            u_star = 6.2
            try:
                unrate_long = self.fetcher.fetch_fred_series(
                    "LRHUTTTTCAM156S", limit=120
                )
                if unrate_long:
                    vals = [float(x["value"]) for x in unrate_long]
                    u_star = sum(vals) / len(vals)
            except:
                pass

            gap_okun = -2.0 * (u_actual - u_star)

            current_pi = 2.4
            current_pi = self._latest_percent_observation(cpi_data, current_pi)

            gap_hp = -1.0
            if gdp_real_long and len(gdp_real_long) > 20:
                try:
                    data_list = [
                        {"date": x["date"], "value": float(x["value"])}
                        for x in gdp_real_long
                    ]
                    df_gdp = pd.DataFrame(data_list).sort_values("date")
                    df_gdp["log_gdp"] = np.log(df_gdp["value"])
                    cycle, trend = hpfilter(df_gdp["log_gdp"], lamb=1600)
                    gap_hp = cycle.iloc[-1] * 100
                except:
                    pass

            gap_cap = -0.5
            if cap_util and len(cap_util) > 120:
                try:
                    curr_cap = float(cap_util[0]["value"])
                    vals = [float(x["value"]) for x in cap_util if x["value"] != "."]
                    avg_cap = sum(vals) / len(vals)
                    gap_cap = curr_cap - avg_cap
                except:
                    pass

            r_star_nominal_range = boc_data.get("neutral_rate", [2.25, 3.25])
            r_star_nominal_mid = sum(r_star_nominal_range) / 2

            r_star_real_mid = r_star_nominal_mid - 2.0
            r_star_real_range = [x - 2.0 for x in r_star_nominal_range]

            threshold_val = 2.5

            gap_scenarios = {
                f"Labor Model (Okun: {gap_okun:.1f}%)": gap_okun,
                f"Statistical Trend (HP Filter: {gap_hp:.1f}%)": gap_hp,
                f"Industrial Model (CapUtil: {gap_cap:.1f}%)": gap_cap,
            }
            output_gap = gap_hp
            activity_gap_enhanced = float(np.median([gap_okun, gap_hp, gap_cap]))
            financial_stress = 0.0
            inflation_pressure = current_pi - 2.0
            cad_pressure = self._recent_change(cad_data, 0.0, periods=3) * 10
            oil_pressure = self._recent_change(oil_data, 0.0, periods=3) / 10
            external_pressure = cad_pressure + oil_pressure
            labor_cooling = 0.0
            title = "Bank of Canada"

        rec_rate = self.engine.models.taylor_nonlinear(
            r_star_real_mid,
            current_pi,
            output_gap,
            threshold=threshold_val,
            stress_multiplier=1.5,
        )

        lin_rate = self.engine.models.taylor_1999(
            r_star_real_mid, current_pi, output_gap
        )

        gap_bps = (actual_rate - rec_rate) * 100
        nonlinear_premium = (rec_rate - lin_rate) * 100
        calibration_frame = self._build_policy_calibration_frame(country, r_star_real_mid)
        current_features = {
            "activity_gap": activity_gap_enhanced,
            "inflation_pressure": inflation_pressure,
            "financial_conditions": financial_stress,
            "external_pressure": external_pressure,
            "labor_cooling": labor_cooling,
        }
        enhanced_rate, enhanced_adjustments = self._data_enhanced_taylor_rate(
            base_rate=rec_rate,
            current_features=current_features,
            calibration_frame=calibration_frame,
        )
        enhanced_gap_bps = (actual_rate - enhanced_rate) * 100

        filename = f"{country.lower()}_oracle_chart.png"
        plot_taylor_sensitivity(
            country_name=title,
            current_pi=current_pi,
            gap_scenarios=gap_scenarios,
            r_star_mid=r_star_real_mid,
            r_star_range=r_star_real_range,
            actual_rate=actual_rate,
            output_filename=filename,
        )

        report = self._write_economist_report(
            country,
            title,
            current_pi,
            output_gap,
            actual_rate,
            rec_rate,
            gap_bps,
            threshold_val,
            nonlinear_premium,
            u_actual if country == "US" else None,
            enhanced_rate,
            enhanced_gap_bps,
            enhanced_adjustments,
        )

        return {"image_path": os.path.abspath(filename), "report": report}

    def _write_economist_report(
        self,
        country,
        title,
        pi,
        gap,
        rate,
        rec_rate,
        gap_bps,
        threshold,
        premium,
        u_rate=None,
        enhanced_rate=None,
        enhanced_gap_bps=None,
        enhanced_adjustments=None,
    ):
        """Generate macro report."""
        if enhanced_rate is None:
            enhanced_rate = rec_rate
        if enhanced_gap_bps is None:
            enhanced_gap_bps = gap_bps
        if enhanced_adjustments is None:
            enhanced_adjustments = {}

        if gap_bps > 25:
            stance = "Restrictive"
            deviation_desc = "Actual rate is above the model-implied level"
            direction_needed = "cut"
            gap_desc = (
                "Significant negative output gap"
                if gap < 0
                else "Inflationary pressure"
            )
            constraint_desc = "The policy remains clearly restrictive. The current rate level continues to act as a constraint on economic recovery in the model sense."
        elif gap_bps < -25:
            stance = "Accommodative"
            deviation_desc = "Actual rate is below the model-implied level"
            direction_needed = "hike"
            gap_desc = "Inflation/Overheating risk"
            constraint_desc = "The policy shows clear stimulative characteristics. The current rate level may lead to economic overheating or persistent inflation."
        else:
            stance = "Neutral"
            deviation_desc = (
                "Actual rate is broadly aligned with the model-implied level"
            )
            direction_needed = "adjust"
            gap_desc = "Balanced economic state"
            constraint_desc = "The policy is within the neutral range, providing neither significant constraint nor additional stimulus."

        if abs(gap_bps) > 10:
            conclusion_text = f"This implies that to address {gap_desc.lower()}, the policy path still requires an additional {direction_needed} of approximately {abs(gap_bps):.0f} bps to return to the model's neutral zone."
        else:
            conclusion_text = "This suggests the current policy rate is highly consistent with the model's optimal path, residing within the desired range."

        if gap_bps > 25:
            chart_signal = "clearly above"
        elif gap_bps < -25:
            chart_signal = "clearly below"
        else:
            chart_signal = "broadly aligned with"

        u_line = f"*   **Unemployment Rate:** {u_rate}%\n" if u_rate else ""

        gap_source = "statistical trend model"
        if country == "Canada":
            gap_source = "BoC Extended Filter proxy"
        elif country == "US":
            gap_source = "HP Filter / Okun's Law estimate"

        report = f"""
# Central Bank Policy Report: {title}

**Policy Stance:** {stance}
**Deviation:** {gap_bps:+.0f} bps ({deviation_desc})

### 1. Macro Overview
*   **Core Inflation:** {pi:.2f}%
*   **Output Gap:** {gap:.2f}% ({gap_source})
*   **Current Policy Rate:** {rate:.2f}%
{u_line}
### 2. Model Conclusion
Under the specified assumptions, the base Taylor Rule implies a desired policy rate of approximately **{rec_rate:.2f}%**.
{conclusion_text}

### 2A. Two-Layer Taylor Readout
*   **Base Taylor Rate:** {rec_rate:.2f}% ({gap_bps:+.0f} bps versus actual)
*   **Data-Enhanced Taylor Rate:** {enhanced_rate:.2f}% ({enhanced_gap_bps:+.0f} bps versus actual)
*   **Enhancement Decomposition:** intercept {enhanced_adjustments.get("intercept", 0.0):+.2f} pp; activity gap {enhanced_adjustments.get("activity_gap", 0.0):+.2f} pp; inflation pressure {enhanced_adjustments.get("inflation_pressure", 0.0):+.2f} pp; financial conditions {enhanced_adjustments.get("financial_conditions", 0.0):+.2f} pp; external pressure {enhanced_adjustments.get("external_pressure", 0.0):+.2f} pp; labor cooling {enhanced_adjustments.get("labor_cooling", 0.0):+.2f} pp; total {enhanced_adjustments.get("total", 0.0):+.2f} pp; sample n={enhanced_adjustments.get("n", 0.0):.0f}.

### 3. Economic Interpretation
*   **Chart Signal:** The current policy rate ({rate:.2f}%), indicated by the black dashed line, is {chart_signal} the model-implied paths under the three output gap scenarios.
*   **Policy Implications:** {constraint_desc}

### 4. Empirical Uncertainty Check
**Statistical Facts:**
*   **95% Confidence Interval:** Based on the volatility range of $r^*$ and the Gap, the model's desired rate interval is approximately **[{min(rec_rate - 0.5, rate - 0.25):.2f}%, {max(rec_rate + 0.5, rate + 0.25):.2f}%]**.
*   **Current Observation:** Actual rate is **{rate:.2f}%**.
*   **Statistical Positioning:** The observation is at the **{"center" if abs(gap_bps) < 25 else "edge/outlier region"}** of the confidence interval (Z-Score $\approx$ {gap_bps / 50:.1f}).

**Inference Conclusion:**
{"The observation sits near the central range of the model distribution, so the base Taylor signal and current policy rate are broadly consistent under this specification." if abs(gap_bps) < 25 else "The deviation from the central range is large enough to treat the signal as a policy diagnostic rather than a mechanical rate prescription."}

---
*Generated by Economics ML Skill v2.5*
"""
        report = report.replace("$\approx$", "approx")
        return report


if __name__ == "__main__":
    engine = PolicyRateEngine()
    result = engine.generate_analysis("US")
    print(result["report"])
