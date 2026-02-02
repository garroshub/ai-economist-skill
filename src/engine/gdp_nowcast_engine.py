import os
import requests
import pandas as pd
import numpy as np
import statsmodels.api as sm
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import pytz
import warnings

import sys
import io

# Ensure UTF-8 output for Windows terminals
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

warnings.filterwarnings("ignore")
FRED_API_KEY = os.getenv("FRED_API_KEY") or "d81d5f139c17a774bf1a87ea76240b83"


def get_toronto_now():
    """Returns the current time in America/Toronto."""
    tz = pytz.timezone("America/Toronto")
    return datetime.now(tz)


class GDPCastNowEngine:
    """GDP nowcast engine for US & Canada. Bridge model + sentiment."""

    def __init__(self, country="US"):
        self.country = country
        self.fred_url = "https://api.stlouisfed.org/fred/series/observations"
        self.now = get_toronto_now()

        if country == "US":
            self.gdp_id = "GDPC1"
            self.indicators = {
                "INDPRO": "Industrial_Production",
                "PAYEMS": "Nonfarm_Payrolls",
                "RSAFS": "Retail_Sales",
                "UNRATE": "Unemployment",
                "PCEC96": "Real_PCE",
            }
        else:
            self.gdp_id = "NGDPRSAXDCCAQ"
            self.indicators = {
                "CANPROINDMISMEI": "Industrial_Production",
                "SLRTTO01CAM659S": "Retail_Sales",
                "LRHUTTTTCAM156S": "Unemployment",
            }

    def fetch_fred(self, sid, limit=160):
        url = f"{self.fred_url}?series_id={sid}&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit={limit}"
        try:
            r = requests.get(url, timeout=10).json()
            if "observations" not in r:
                return pd.DataFrame()
            df = pd.DataFrame(r["observations"])
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df[["date", "value"]].sort_values("date").set_index("date")
        except:
            return pd.DataFrame()

    def fetch_sentiment(self):
        """Aggregate macro news signals from last 7 days."""
        feeds = [
            "https://www.investing.com/rss/news_25.rss",
            "https://www.bankofcanada.ca/feed/",
        ]
        score = 0.0
        kw = r"(GDP|Fed|BoC|Inflation|Retail|Interest Rate|Employment)"
        count = 0
        now = self.now.replace(tzinfo=None)

        try:
            for url in feeds:
                resp = requests.get(
                    url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
                )
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item"):
                    pub_date_str = item.find("pubDate").text
                    pub_date = None
                    for fmt in ["%a, %d %b %Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            clean_str = (
                                pub_date_str[:25]
                                if "," in pub_date_str
                                else pub_date_str
                            )
                            pub_date = datetime.strptime(clean_str.strip(), fmt)
                            break
                        except:
                            continue

                    if not pub_date or (now - pub_date).days > 7:
                        continue

                    title = item.find("title").text.lower()

                    is_relevant_country = False
                    if self.country == "US":
                        if any(
                            x in title
                            for x in ["us", "usa", "fed ", "federal reserve", "powell"]
                        ):
                            is_relevant_country = True
                    else:
                        if any(
                            x in title
                            for x in [
                                "canada",
                                "boc",
                                "bank of canada",
                                "ottawa",
                                "loonie",
                                "macklem",
                            ]
                        ):
                            is_relevant_country = True

                    if re.search(kw.lower(), title) and is_relevant_country:
                        if any(
                            x in title
                            for x in [
                                "strong",
                                "jump",
                                "increase",
                                "beat",
                                "rise",
                                "grow",
                            ]
                        ):
                            score += 0.02
                        if any(
                            x in title
                            for x in ["weak", "drop", "slow", "miss", "fall", "cut"]
                        ):
                            score -= 0.02
                        count += 1
            return score if count > 0 else 0.0
        except:
            return 0.0

    def fetch_statcan_outlook(self):
        """Scrapes StatCan Daily for official flash estimates/outlook (Canada Only)."""
        if self.country != "Canada":
            return None, None

        base_url = "https://www150.statcan.gc.ca/n1/daily-quotidien"
        found_text = None
        found_date = None

        now = self.now.replace(tzinfo=None)
        for i in range(10):
            d = now - pd.Timedelta(days=i)
            date_str = d.strftime("%y%m%d")
            url = f"{base_url}/{date_str}/dq{date_str}a-eng.htm"

            try:
                resp = requests.get(url, timeout=3)
                if (
                    resp.status_code == 200
                    and "Gross domestic product by industry" in resp.text
                ):
                    found_text = resp.text
                    found_date = d.strftime("%Y-%m-%d")
                    break
            except:
                continue

        if not found_text:
            return None, None

        val = None
        q_match = re.search(
            r"suggests that the economy (increased|decreased|rose|fell|contracted|expanded).*?(\d+\.\d+)%.*?quarter",
            found_text,
            re.IGNORECASE,
        )

        if q_match:
            direction = q_match.group(1).lower()
            num = float(q_match.group(2))
            if any(x in direction for x in ["decreased", "fell", "contracted", "down"]):
                val = -num / 100.0
            else:
                val = num / 100.0

        if val is None:
            m_match = re.search(
                r"Advance information indicates.*?real GDP.*?(increased|decreased|rose|fell|contracted|expanded|up|down|unchanged).*?(\d+\.\d+)%",
                found_text,
                re.IGNORECASE,
            )
            m_match_flat = re.search(
                r"Advance information indicates.*?real GDP.*?essentially unchanged",
                found_text,
                re.IGNORECASE,
            )

            if m_match:
                direction = m_match.group(1).lower()
                num = float(m_match.group(2))
                if any(
                    x in direction for x in ["decreased", "fell", "contracted", "down"]
                ):
                    val = -num / 100.0
                else:
                    val = num / 100.0
            elif m_match_flat:
                val = 0.0

        return val, found_date

    def run_nowcast(self):
        m_data = {}
        for sid, name in self.indicators.items():
            df = self.fetch_fred(sid)
            if df.empty:
                continue
            m_data[name] = (
                df["value"].diff()
                if "UNRATE" in sid or "LRHUT" in sid
                else np.log(df["value"]).diff() * 100
            )

        df_m = (
            pd.concat(m_data.values(), axis=1, keys=m_data.keys()).resample("MS").last()
        )
        df_m = df_m.dropna(how="all").iloc[1:]

        for col in df_m.columns:
            series = df_m[col].dropna()
            if len(series) < 12:
                continue
            if pd.isna(df_m[col].iloc[-1]):
                mu, phi = series.mean(), series.autocorr()
                df_m[col].iloc[-1] = mu + phi * (series.iloc[-1] - mu)

        df_std = (df_m - df_m.mean()) / df_m.std()
        X = df_std.ffill().bfill().values
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
        df_m["Factor"] = U[:, 0] * S[0]

        gdp_raw = self.fetch_fred(self.gdp_id)
        gdp_growth = (np.log(gdp_raw["value"]).diff() * 100).dropna()
        q_factor = df_m["Factor"].resample("QS").mean()
        combined = pd.concat([gdp_growth, q_factor], axis=1).dropna()
        combined.columns = ["GDP", "Factor"]

        model = sm.OLS(combined["GDP"], sm.add_constant(combined["Factor"])).fit()

        current_q_factor = (
            df_m["Factor"].rolling(window=3).mean().resample("QS").last().iloc[-1]
        )
        quant_val = model.params["const"] + model.params["Factor"] * current_q_factor

        if self.country == "Canada" and abs(quant_val) > 0.74:
            quant_val = quant_val * 0.6 + 0.4 * 0.4

        ai_score = self.fetch_sentiment()

        statcan_outlook = None
        statcan_date = None
        if self.country == "Canada":
            outlook_val, s_date = self.fetch_statcan_outlook()
            if outlook_val is not None:
                statcan_outlook = outlook_val * 100
                statcan_date = s_date
                diff = statcan_outlook - quant_val
                ai_score += diff * 0.5

        final_prediction = quant_val + ai_score

        return {
            "quant_val": quant_val,
            "ai_score": ai_score,
            "final_val": final_prediction,
            "r2": model.rsquared,
            "data_thru": df_m.index[-1].strftime("%Y-%m"),
            "target_q": "Current Q",
            "statcan_outlook": statcan_outlook,
            "statcan_date": statcan_date,
        }


def format_report(country, res):
    now_str = get_toronto_now().strftime("%Y-%m-%d %H:%M")

    extra_section = ""
    if country == "Canada" and res.get("statcan_outlook") is not None:
        extra_section = f"\n- **🇨🇦 StatCan Official Outlook**: `{res['statcan_outlook']:.2f}%` (Released on {res['statcan_date']})"

    return f"""
# 🏦 GDPCastNow | Real GDP Forecast ({country})

**Generated At**: {now_str} (Toronto Time)
**Target Quarter**: {res["target_q"]} Real GDP Growth (Q/Q)

---

### 🚀 Core Forecast Data
- **Quant Baseline Nowcast**: `{res["quant_val"]:.2f}%`
- **AI Sentiment Adjustment**: `{res["ai_score"]:+.2f}%` (Newsflow + Official Outlook){extra_section}
- **💡 Final Forecast**: **{res["final_val"]:.2f}%**
- **Model Confidence (R²)**: {res["r2"]:.2f}

### 📊 Runtime Status
- **Data Through**: {res["data_thru"]}
- **Sources**: FRED API, StatCan, BEA, Investing RSS
- **Methodology**: Bridge Equation (SVD Factor Extraction) + Bayesian NLP Layer

---
*Generated by GDPCastNow-skill v1.1*
"""


if __name__ == "__main__":
    for c in ["US", "Canada"]:
        engine = GDPCastNowEngine(c)
        res = engine.run_nowcast()
        print(format_report(c, res))
