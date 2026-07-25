import pandas as pd

from .summary_metrics import summarize_metrics


def compare_scenarios(*dfs, labels=None):
    """Compare any number of amortization schedules by summarizing key outcome metrics.

    Parameters
    ----------
    *dfs : pd.DataFrame
        Amortization schedules from LoanAmortizer.to_dataframe().
    labels : list of str, optional
        Row labels; defaults to 'Scenario 1', 'Scenario 2', ...

    Returns
    -------
    pd.DataFrame
        One summary row per scenario.
    """
    if not dfs:
        raise ValueError("compare_scenarios requires at least one amortization DataFrame.")
    if labels is None:
        labels = [f"Scenario {i + 1}" for i in range(len(dfs))]
    if len(labels) != len(dfs):
        raise ValueError("labels must match the number of scenarios.")

    return pd.DataFrame([summarize_metrics(df) for df in dfs], index=labels)
