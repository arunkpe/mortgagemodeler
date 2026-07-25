# utils/rates.py

import os
import warnings
import pandas as pd
from typing import Optional

class RateReader:
    """
    Utility class to read and serve forward interest rates from macroeconomic projections.
    Supports Prime, LIBOR, SOFR, MTA, CMT, and fallback to FRED codes.
    """

    SUPPORTED_INDICES = {
        'LIBOR1': 'LIBOR1MonRate',
        'LIBOR3': 'LIBOR3MonRate',
        'LIBOR6': 'LIBOR6MonRate',
        'LIBOR12': 'LIBOR12MonRate',
        'PRIME': 'PrimeRate',
        'MTA': 'TreasAvg',
        'CMT12': 'CMT1YearRate',
        'SOFR': 'SOFR30DAYAVG'
    }

    def __init__(self, filepath: Optional[str] = None):
        """
        Initialize the rate reader.

        Parameters
        ----------
        filepath : str, optional
            Path to the rate projection file. If not provided, defaults to the
            packaged 'mortgagemodeler/data/macroeconforward.txt'.
        """
        self.filepath = filepath or os.path.join(os.path.dirname(__file__), "..", "data", "macroeconforward.txt")
        self.rates_df = self._load_rates()

    def _load_rates(self) -> Optional[pd.DataFrame]:
        """
        Attempts to load macroeconomic rate projections. If file not found, returns None.

        Returns
        -------
        pd.DataFrame or None
            DataFrame of rates sorted by date if file exists, else None.
        """
        if not os.path.exists(self.filepath):
            warnings.warn(
                f"RateReader: file not found at {self.filepath}. "
                "Index lookups will return None and the last known rate will be held.",
                stacklevel=2,
            )
            return None

        if self.filepath.endswith(".csv"):
            df = pd.read_csv(self.filepath, sep=None, engine='python')
        else:
            df = pd.read_csv(self.filepath, sep=r'\s+', engine='python')

        # Normalize the first (date) column to string and sort ascending so
        # get_rate can do a most-recent-on-or-before lookup.
        df.iloc[:, 0] = df.iloc[:, 0].astype(str)
        return df.sort_values(df.columns[0]).reset_index(drop=True)

    def get_rate(self, index: str, date_str: str) -> Optional[float]:
        """
        Retrieve the forward rate for a given index as of a date, using the
        most recent observation on or before that date.

        Parameters
        ----------
        index : str
            The macroeconomic index (e.g., 'PRIME', 'LIBOR12', 'SOFR').
        date_str : str
            Date string in format 'YYYY-MM-DD'.

        Returns
        -------
        float or None
            Forward interest rate, or None when no data is available. Callers
            must treat None as "no index observation" (hold the last rate),
            never as a 0% index.
        """
        if self.rates_df is None:
            return None

        index_col = self.SUPPORTED_INDICES.get(index.upper()) if index else None
        if index_col is None:
            raise ValueError(f"Unsupported index: {index}. Supported: {list(self.SUPPORTED_INDICES.keys())}")
        if index_col not in self.rates_df.columns:
            # Fall back to a generic single-curve file with a 'Rate' column.
            if 'Rate' in self.rates_df.columns:
                index_col = 'Rate'
            else:
                return None

        eligible = self.rates_df[self.rates_df.iloc[:, 0] <= date_str]
        if eligible.empty:
            return None

        return float(eligible.iloc[-1][index_col])
