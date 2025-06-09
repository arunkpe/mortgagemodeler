import pandas as pd

def breakeven_analysis(refi_df, base_df, refi_costs=0.0):
    """Compute breakeven month when refinancing pays off via cumulative monthly savings.

    Parameters
    ----------
    refi_df : pd.DataFrame
        Amortization table for refinanced loan.
    base_df : pd.DataFrame
        Amortization table for original loan.
    refi_costs : float
        Closing/refinance costs incurred upfront.

    Returns
    -------
    dict
        Contains breakeven month and cumulative savings profile.
    """
    merged = pd.merge(
        base_df[['Month', 'Total Payment']],
        refi_df[['Month', 'Total Payment']],
        on='Month',
        suffixes=('_base', '_refi')
    )

    merged['Monthly Savings'] = merged['Total Payment_base'] - merged['Total Payment_refi']
    merged['Cumulative Savings'] = merged['Monthly Savings'].cumsum()
    merged['Net Savings'] = merged['Cumulative Savings'] - refi_costs

    breakeven_months = merged[merged['Net Savings'] > 0]['Month']
    breakeven_month = int(breakeven_months.iloc[0]) if not breakeven_months.empty else None

    return {
        'breakeven_month': breakeven_month,
        'net_savings': round(merged['Net Savings'].iloc[-1], 2),
        'monthly_savings': merged[['Month', 'Monthly Savings', 'Net Savings']]
    }
