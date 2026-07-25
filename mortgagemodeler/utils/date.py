from datetime import datetime, date
import calendar

def end_of_month(date_str: str) -> date:
    """
    Convert a YYYY-MM-DD string to the last day of that month.

    Parameters
    ----------
    date_str : str
        Date in 'YYYY-MM-DD' format

    Returns
    -------
    date
        Last day of the month for the given date
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return date(dt.year, dt.month, last_day)

# utils/date.py
def normalize_date(d):
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    elif isinstance(d, datetime):
        return d.date()
    elif isinstance(d, date):
        return d
    raise TypeError(f"Invalid date type: {type(d)}")
