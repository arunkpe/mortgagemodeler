def summarize_metrics(df):
    """Summarize key loan metrics from a single amortization DataFrame."""
    paid_off = df[df['Ending Balance'] <= 0.01]['Month']
    payoff_month = int(paid_off.min()) if not paid_off.empty else int(df['Month'].max())
    return {
        'Total Interest': round(df['Interest'].sum(), 2),
        'Total PMI/MIP': round(df['PMI/MIP'].sum(), 2),
        'Total Payments': round(df['Total Payment'].sum(), 2),
        'Payoff Month': payoff_month,
        'Final Balance': round(df['Ending Balance'].iloc[-1], 2)
    }
