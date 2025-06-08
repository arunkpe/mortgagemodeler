import matplotlib.pyplot as plt

def plot_amortization_curve(df):
    """
    Plot cumulative loan metrics: balance, principal, interest, and PMI over time.

    Parameters
    ----------
    df : pd.DataFrame
        Amortization schedule with at least ['Month', 'Principal', 'Interest', 'Ending Balance']
    """
    df['Cumulative Principal'] = df['Principal'].cumsum()
    df['Cumulative Interest'] = df['Interest'].cumsum()
    if 'PMI/MIP' in df.columns:
        df['Cumulative PMI/MIP'] = df['PMI/MIP'].cumsum()
    else:
        df['Cumulative PMI/MIP'] = 0

    plt.figure(figsize=(12, 6))
    plt.plot(df['Month'], df['Ending Balance'], label='Remaining Balance', linewidth=2)
    plt.plot(df['Month'], df['Cumulative Principal'], label='Cumulative Principal', linestyle='--')
    plt.plot(df['Month'], df['Cumulative Interest'], label='Cumulative Interest', linestyle='--')
    if df['Cumulative PMI/MIP'].max() > 0:
        plt.plot(df['Month'], df['Cumulative PMI/MIP'], label='Cumulative PMI/MIP', linestyle=':')

    plt.xlabel("Month")
    plt.ylabel("Amount ($)")
    plt.title("Loan Amortization Curve (Cumulative View)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.show()
