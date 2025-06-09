def cost_until_exit(amortizer, exit_month: int, include_extra: bool = True) -> dict:
    """
    Calculate total cost (principal + interest) up to a given month.

    Parameters
    ----------
    amortizer : LoanAmortizer
        The amortizer instance with a full amortization table.
    exit_month : int
        Month number at which the borrower exits the loan.
    include_extra : bool
        Whether to include extra payments in total paid.

    Returns
    -------
    dict
        Dictionary with total paid, interest paid, principal paid, and balance.
    """
    df = amortizer.to_dataframe()
    df_exit = df[df['Month'] <= exit_month]

    total_paid = df_exit['Payment'].sum()
    total_interest = df_exit['Interest'].sum()
    total_principal = df_exit['Principal'].sum()
    match = df[df['Month'] == exit_month]
    final_balance = float(match['Balance'].values[0]) if not match.empty else 0.0
    
    if not include_extra:
        total_paid -= df_exit['ExtraPayment'].sum()

    return {
        'exit_month': exit_month,
        'total_paid': float(total_paid),
        'total_interest': float(total_interest),
        'total_principal': float(total_principal),
        'ending_balance': float(final_balance)
    }
