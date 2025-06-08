import pandas as pd
from typing import Optional

def summarize_amortization(df: pd.DataFrame, original_loan_amount: Optional[float] = None) -> dict:
    """
    Summarize key metrics from the amortization schedule.

    Parameters
    ----------
    df : pd.DataFrame
        The amortization schedule dataframe.
    original_loan_amount : float, optional
        Original loan amount for computing PMI drop-off threshold.

    Returns
    -------
    dict
        Dictionary of computed statistics.
    """
    total_interest = df["Interest"].sum()
    total_principal = df["Principal"].sum()
    total_payment = df["Total Payment"].sum() if "Total Payment" in df.columns else df["Payment"].sum()
    pmi_total = df["PMI/MIP"].sum() if "PMI/MIP" in df.columns else 0.0

    ending_balance = df.iloc[-1]["Ending Balance"]
    months = df.shape[0]

    pmi_end_month = None
    if original_loan_amount and "PMI/MIP" in df.columns:
        for i, row in df.iterrows():
            ltv = row["Ending Balance"] / original_loan_amount
            if ltv < 0.78:
                pmi_end_month = row["Month"]
                break

    return {
        "Total Interest Paid": round(total_interest, 2),
        "Total Principal Paid": round(total_principal, 2),
        "Total Payment": round(total_payment, 2),
        "Total PMI/MIP Paid": round(pmi_total, 2),
        "Loan Duration (months)": months,
        "Final Balance": round(ending_balance, 2),
        "PMI Ends Month": pmi_end_month
    }
