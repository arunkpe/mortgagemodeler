import os
import pandas as pd
from typing import Optional
from fredapi import Fred


class FredFetcher:
    """
    A utility class to interface with the FRED (Federal Reserve Economic Data) API.
    Allows fetching macroeconomic indicators and handling common aliases for ease of use.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the FredFetcher with an API key.

        Parameters
        ----------
        api_key : str, optional
            Your FRED API key. If not provided, will attempt to read from the environment variable 'FRED_API_KEY'.
        """
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        self.fred = Fred(api_key=self.api_key)
        self.base_dir = os.path.dirname(__file__)

    def available_codes(self) -> pd.DataFrame:
        """
        Load available FRED codes from a CSV reference file.

        Returns
        -------
        pd.DataFrame
            A DataFrame listing available macroeconomic codes and descriptions.
        """
        csv_path = os.path.join(self.base_dir, "data", "FREDCode.csv")
        return pd.read_csv(csv_path)

    def sanitize(self, code: str) -> Optional[str]:
        """
        Standardize or alias macroeconomic variable names into valid FRED series codes.

        Parameters
        ----------
        code : str
            Raw input string (e.g., 'CPI', 'UR', 'SOFR').

        Returns
        -------
        str or None
            Valid FRED code or None if the input cannot be resolved.
        """
        lookup = self.available_codes()
        code = code.upper()
        alias_map = {
            'UE': 'UNRATE', 'UR': 'UNRATE',
            'CPI': 'CPILFESL',
            'HPI': 'USSTHPI', 'HPA': 'USSTHPI',
            'SOFR': 'SOFR', 'SOFRAVG': 'SOFR30DAYAVG',
            'LIBOR12': 'SOFR30DAYAVG', 'LIBOR': 'SOFR30DAYAVG'
        }
        if code in lookup['Code'].values or code in alias_map:
            return alias_map.get(code, code)
        return None

    def fetch_data(self, code_input: str) -> pd.DataFrame:
        """
        Fetch the latest release of a macroeconomic time series from FRED.

        Parameters
        ----------
        code_input : str
            A macroeconomic indicator code or alias (e.g., 'CPI', 'SOFR', 'UR').

        Returns
        -------
        pd.DataFrame
            A DataFrame with columns ['Date', <code>] containing the time series data.

        Raises
        ------
        ValueError
            If the input code cannot be resolved to a valid FRED series.
        """
        code = self.sanitize(code_input)
        if code is None:
            raise ValueError("Invalid code. Use available_codes() to inspect valid inputs.")
        df = self.fred.get_series_latest_release(code).reset_index()
        df.columns = ['Date', code_input.upper()]
        return df
