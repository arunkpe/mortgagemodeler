# utils/rates.py

import os
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
            Path to the rate projection file. If not provided, defaults to 'data/macroeconforward.txt'.
        """
        self.filepath = filepath or os.path.join(os.path.dirname(__file__), "../data", "macroeconforward.txt")
        self.rates_df = self._load_rates()

    def _load_rates(self) -> pd.DataFrame:
        if self.filepath.endswith(".csv"):
            return pd.read_csv(self.filepath, sep=None, engine='python')
        else:
            return pd.read_csv(self.filepath, sep='\t')

    def get_rate(self, index: str, date_str: str) -> float:
        """
        Retrieve the forward rate for a specific index and date.

        Parameters
        ----------
        index : str
            The macroeconomic index (e.g., 'PRIME', 'LIBOR12').
        date_str : str
            Date string in format 'YYYY-MM-DD'.

        Returns
        -------
        float
            Forward interest rate.
        """
        index_col = self.SUPPORTED_INDICES.get(index.upper())
        if index_col is None:
            raise ValueError(f"Unsupported index: {index}. Supported: {list(self.SUPPORTED_INDICES.keys())}")

        row = self.rates_df[self.rates_df.iloc[:, 0] == date_str]
        if row.empty:
            raise KeyError(f"Date {date_str} not found in rate file.")

        return float(row[index_col].values[0])
