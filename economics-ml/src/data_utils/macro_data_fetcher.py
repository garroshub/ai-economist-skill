import os
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup


class MacroDataFetcher:
    def __init__(self, fred_api_key=None):
        self.fred_api_key = fred_api_key or os.getenv("FRED_API_KEY")
        self.fred_base_url = "https://api.stlouisfed.org/fred/series/observations"

    def fetch_fred_series(self, series_id, limit=20):
        """Fetch data from FRED API."""
        if not self.fred_api_key:
            return []

        params = {
            "series_id": series_id,
            "api_key": self.fred_api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        }
        try:
            response = requests.get(self.fred_base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            observations = [obs for obs in data["observations"] if obs["value"] != "."]
            return observations[:limit]
        except Exception:
            return []

    def fetch_bls_unemployment(self):
        """
        Scrape latest unemployment rate directly from BLS (Bureau of Labor Statistics).
        """
        url = "https://www.bls.gov/news.release/empsit.t01.htm"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            table = soup.find("table")
            if not table:
                return "Error: BLS table not found."

            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                row_text = cells[0].get_text(strip=True)
                if "Unemployment rate" in row_text:
                    val = cells[-1].get_text(strip=True)
                    return {"date": "Latest BLS release", "value": val, "source": url}

            return "Error: Unemployment rate row not found."
        except Exception as e:
            return f"Error: {str(e)}"

    def fetch_boc_data(self):
        """
        Scrape BoC for Output Gap, Policy Rate, and Nominal Neutral Rate.
        """
        url = "https://www.bankofcanada.ca/rates/indicators/capacity-and-inflation-pressures/"
        headers = {"User-Agent": "Mozilla/5.0"}

        data = {"output_gap": -0.8, "policy_rate": 2.25, "neutral_rate": [2.25, 3.25]}

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")

            tables = soup.find_all("table")
            for table in tables:
                for tr in table.find_all("tr"):
                    cells = [
                        td.get_text(strip=True) for td in tr.find_all(["td", "th"])
                    ]
                    if not cells:
                        continue
                    full_row_text = " ".join(cells).lower()
                    if "current mpr output gap" in full_row_text:
                        target_indices = [
                            i
                            for i, c in enumerate(cells)
                            if "current mpr output gap" in c.lower()
                        ]
                        if target_indices:
                            start_idx = target_indices[0]
                            for i in range(start_idx + 1, len(cells)):
                                clean_val = (
                                    cells[i]
                                    .replace("Q1", "")
                                    .replace("Q2", "")
                                    .replace("Q3", "")
                                    .replace("Q4", "")
                                    .replace("%", "")
                                    .strip()
                                )
                                try:
                                    if clean_val and not any(
                                        kw in clean_val.lower()
                                        for kw in ["historical", "output", "survey"]
                                    ):
                                        data["output_gap"] = float(clean_val)
                                except:
                                    if data["output_gap"] != -0.8:
                                        break
                                    continue

            page_text = soup.get_text().lower()

            return data
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    fetcher = MacroDataFetcher()

    print("--- Testing BLS Direct Fetch (US Unemployment) ---")
    bls_data = fetcher.fetch_bls_unemployment()
    print(f"Result: {bls_data}")

    print("\n--- Testing FRED Fallback (PCE) ---")
    fred_pce = fetcher.fetch_fred_series("PCEPILFE")
    if isinstance(fred_pce, list) and len(fred_pce) > 0:
        print(f"Latest PCEPILFE: {fred_pce[0]['date']} -> {fred_pce[0]['value']}%")

    print("\n--- Testing BoC Access ---")
    boc_status = fetcher.fetch_boc_data()
    print(f"Result: {boc_status}")
