def effective_apr(principal, rate, term_months, points=0.0, fees=0.0):
    """Estimate Effective APR using cost-adjusted loan proceeds and IRR method.

    Parameters
    ----------
    principal : float
        Loan amount.
    rate : float
        Nominal APR.
    term_months : int
        Loan term in months.
    points : float
        Discount points as percent of loan (e.g., 1.0 for 1 point).
    fees : float
        Closing costs not rolled into the loan.

    Returns
    -------
    float
        Effective APR expressed as annual percent.
    """
    from numpy_financial import irr
    from decimal import Decimal

    loan_amount = Decimal(str(principal))
    upfront_cost = loan_amount * Decimal(str(points)) / Decimal("100") + Decimal(str(fees))
    net_proceeds = loan_amount - upfront_cost

    monthly_payment = (loan_amount * Decimal(str(rate)) / Decimal("1200")) / \
                      (1 - (1 + Decimal(str(rate)) / Decimal("1200")) ** -term_months)
    cash_flows = [-float(net_proceeds)] + [float(monthly_payment)] * term_months

    internal_rate = irr(cash_flows)
    if internal_rate is None:
        return None

    return round((1 + internal_rate) ** 12 - 1, 5) * 100  # Convert monthly IRR to annual %
