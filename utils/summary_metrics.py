def summarize_metrics(df):
    """Summarize key loan metrics from a single amortization DataFrame."""
    return {
        'Total Interest': round(df['Interest'].sum(), 2),
        'Total PMI/MIP': round(df['PMI/MIP'].sum(), 2),
        'Total Payments': round(df['Total Payment'].sum(), 2),
        'Payoff Month': df[df['Ending Balance'] <= 0.01]['Month'].min() or df['Month'].max(),
        'Final Balance': round(df['Ending Balance'].iloc[-1], 2)
    }
