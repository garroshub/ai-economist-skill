import os
import unittest
import io
import zipfile
from unittest.mock import Mock, patch

from src.data_utils.macro_data_fetcher import MacroDataFetcher
from src.data_utils.statcan_fetcher import StatCanDataFetcher


class MacroDataFetcherTests(unittest.TestCase):
    def test_fetch_fred_series_respects_requested_limit(self):
        observations = [
            {"date": f"2026-01-{day:02d}", "value": str(day)}
            for day in range(1, 9)
        ]
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"observations": observations}

        with patch("src.data_utils.macro_data_fetcher.requests.get", return_value=response):
            fetcher = MacroDataFetcher(fred_api_key="test-key")
            result = fetcher.fetch_fred_series("TEST", limit=8)

        self.assertEqual(len(result), 8)

    def test_fetcher_prefers_environment_key(self):
        with patch.dict(os.environ, {"FRED_API_KEY": "env-key"}):
            fetcher = MacroDataFetcher()

        self.assertEqual(fetcher.fred_api_key, "env-key")

    def test_fetcher_has_no_builtin_private_key(self):
        with patch.dict(os.environ, {}, clear=True):
            fetcher = MacroDataFetcher()

        self.assertIsNone(fetcher.fred_api_key)

    def test_fetch_fred_series_without_key_returns_empty_list(self):
        with patch.dict(os.environ, {}, clear=True):
            fetcher = MacroDataFetcher()

        self.assertEqual(fetcher.fetch_fred_series("TEST"), [])

    def test_fetch_fred_series_error_returns_empty_list(self):
        with patch(
            "src.data_utils.macro_data_fetcher.requests.get",
            side_effect=RuntimeError("network down"),
        ):
            fetcher = MacroDataFetcher(fred_api_key="test-key")
            result = fetcher.fetch_fred_series("TEST")

        self.assertEqual(result, [])

    def test_statcan_retail_sales_parser_uses_canada_seasonally_adjusted_total(self):
        csv_text = "\n".join(
            [
                "REF_DATE,GEO,DGUID,North American Industry Classification System (NAICS),Sales,Adjustments,UOM,UOM_ID,SCALAR_FACTOR,SCALAR_ID,VECTOR,COORDINATE,VALUE,STATUS,SYMBOL,TERMINATED,DECIMALS",
                "2026-01,Canada,1,Retail trade [44-45],Total retail sales,Unadjusted,Dollars,81,thousands,3,v1,1,10,,,,0",
                "2026-01,Canada,1,Retail trade [44-45],Total retail sales,Seasonally adjusted,Dollars,81,thousands,3,v2,1,20,,,,0",
                "2026-01,Ontario,2,Retail trade [44-45],Total retail sales,Seasonally adjusted,Dollars,81,thousands,3,v3,1,30,,,,0",
            ]
        )
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, mode="w") as archive:
            archive.writestr("20100056.csv", csv_text)

        df = StatCanDataFetcher._parse_retail_sales_zip(payload.getvalue())

        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["value"], 20)


if __name__ == "__main__":
    unittest.main()
