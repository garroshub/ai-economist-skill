import io
import zipfile

import pandas as pd
import requests


class StatCanDataFetcher:
    RETAIL_SALES_URL = "https://www150.statcan.gc.ca/n1/tbl/csv/20100056-eng.zip"

    @staticmethod
    def _parse_retail_sales_zip(content):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            with archive.open("20100056.csv") as raw:
                df = pd.read_csv(raw)

        mask = (
            (df["GEO"] == "Canada")
            & (
                df["North American Industry Classification System (NAICS)"]
                == "Retail trade [44-45]"
            )
            & (df["Sales"] == "Total retail sales")
            & (df["Adjustments"] == "Seasonally adjusted")
        )
        series = df.loc[mask, ["REF_DATE", "VALUE"]].copy()
        series["date"] = pd.to_datetime(series["REF_DATE"])
        series["value"] = pd.to_numeric(series["VALUE"], errors="coerce")
        return series.dropna().set_index("date")[["value"]].sort_index()

    def fetch_canada_retail_sales(self):
        try:
            response = requests.get(self.RETAIL_SALES_URL, timeout=20)
            response.raise_for_status()
            return self._parse_retail_sales_zip(response.content)
        except Exception:
            return pd.DataFrame()
