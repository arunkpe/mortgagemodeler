from decimal import Decimal, ROUND_HALF_UP
from datetime import date


def calculate_interest(principal: Decimal, rate: Decimal, days: int, method: str = "30E/360") -> Decimal:
    """
    Calculate interest for a given principal, rate, number of days, and compounding method.

    Parameters
    ----------
    principal : Decimal
        The principal balance.
    rate : Decimal
        Annual interest rate (in percent).
    days : int
        Number of days to apply interest.
    method : str
        Interest calculation convention.
        One of: '30A/360', '30U/360', '30E/360', '30E/360 ISDA', 'A/360', 'A/365F', 'A/A ISDA', 'A/A AFB'

    Returns
    -------
    Decimal
        Interest amount, rounded to 2 decimal places.
    """
    method = method.upper()

    if method in ("30A/360", "30U/360", "30E/360", "30E/360 ISDA"):
        year_basis = Decimal("360")
    elif method == "A/360":
        year_basis = Decimal("360")
    elif method == "A/365F":
        year_basis = Decimal("365")
    elif method in ("A/A ISDA", "A/A AFB"):
        year_basis = Decimal("365.25")
    else:
        raise ValueError(f"Unknown compounding method: {method}")

    interest = (principal * rate * Decimal(days) / (Decimal("100.0") * year_basis))
    return interest.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Optional: day count utility (stub for now)
def day_count(start: date, end: date, method: str = "30E/360") -> int:
    """
    Approximate the number of days between two dates under a given convention.
    For advanced methods, stubbed for future extension.
    """
    delta = (end - start).days
    return delta
