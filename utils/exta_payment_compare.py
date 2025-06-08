import pandas as pd

def compare_scenarios(df1, df2):
    """Compare two amortization schedules by summarizing key outcome metrics."""
    def summarize(df):
        return {
            'Total Interest': round(df['Interest'].sum(), 2),
            'Total PMI/MIP': round(df['PMI/MIP'].sum(), 2),
            'Total Payments': round(df['Total Payment'].sum(), 2),
            'Payoff Month': df[df['Ending Balance'] <= 0.01]['Month'].min() or df['Month'].max(),
            'Final Balance': round(df['Ending Balance'].iloc[-1], 2)
        }

    summary1 = summarize(df1)
    summary2 = summarize(df2)
    comparison = pd.DataFrame([summary1, summary2], index=["Scenario 1", "Scenario 2"])
    return comparison
