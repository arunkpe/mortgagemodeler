import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")


def plot_amortization(df: pd.DataFrame, title="Amortization Schedule", save_path=None):
    """
    Plot the amortization schedule: balances and payment components.

    Parameters
    ----------
    df : pd.DataFrame
        Output from LoanAmortizer.to_dataframe()
    title : str
        Title for the plot.
    save_path : str or None
        If provided, saves the plot to file.
    """
    plt.figure(figsize=(12, 6))
    
    if 'Total Payment' in df.columns:
        payment_col = 'Total Payment'
    else:
        payment_col = 'Payment'

    sns.lineplot(data=df, x="Month", y="Beginning Balance", label="Beginning Balance")
    sns.lineplot(data=df, x="Month", y="Principal", label="Principal")
    sns.lineplot(data=df, x="Month", y="Interest", label="Interest")
    sns.lineplot(data=df, x="Month", y=payment_col, label="Total Payment")

    if "PMI/MIP" in df.columns:
        sns.lineplot(data=df, x="Month", y="PMI/MIP", label="PMI/MIP")

    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel("Amount ($)")
    plt.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
