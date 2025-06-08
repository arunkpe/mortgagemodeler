from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

from utils.interest import calculate_interest
from utils.rates import RateReader


class LoanAmortizer:
    """
    LoanAmortizer builds an amortization schedule for various loan types including:
    - Fixed Rate Loans
    - Adjustable Rate Mortgages (ARMs)
    - FHA Loans with MIP
    - VA and USDA Loans with Guarantee Fees
    - HELOCs with draw and repayment phases

    It supports:
    - Custom forward rate schedules
    - Insurance premiums (PMI, MIP, USDA annual fee)
    - Decimal-based precision for all financial calculations

    Parameters
    ----------
    loan : Loan
        An instance of the Loan class with fully defined parameters.
    custom_rate_schedule : dict, optional
        A dictionary mapping date strings ("YYYY-MM-DD") to interest rate overrides.
    """
    def __init__(self, loan, custom_rate_schedule=None):
        self.loan = loan
        self.schedule = []
        self.custom_rate_schedule = custom_rate_schedule or {}
        self.rates = RateReader()
        self._build_amortization()

    def _get_effective_rate(self, date_str) -> Decimal:
        """
        Returns the effective interest rate for a given date.
        - Uses fixed rate if applicable
        - Uses indexed rate + margin for ARM/HELOC
        - Honors custom rate schedule overrides

        Parameters
        ----------
        date_str : str
            Date in YYYY-MM-DD format.

        Returns
        -------
        Decimal
            Effective interest rate as a Decimal.
        """
        if self.loan.loan_type == 'fixed':
            return self.loan.rate
        elif self.loan.loan_type in ['arm', 'heloc'] and self.loan.index:
            raw_rate = self.rates.get_rate(self.loan.index, date_str)
            return (Decimal(str(raw_rate)) + self.loan.margin).quantize(Decimal("0.0001"))
        else:
            return self.loan.rate

    def _calculate_insurance(self, balance: Decimal, month: int) -> Decimal:
        """
        Calculate monthly insurance (MIP, PMI, or USDA annual fee) based on loan type.

        Parameters
        ----------
        balance : Decimal
            Current outstanding balance.
        month : int
            Current month number in the loan term.

        Returns
        -------
        Decimal
            Monthly insurance premium amount.
        """
        if self.loan.is_fha:
            return (balance * self.loan.fha_monthly).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif self.loan.is_usda:
            return (balance * self.loan.usda_annual_fee / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif self.loan.is_pmi:
            ltv = balance / self.loan.original_balance
            if ltv <= Decimal("0.78") or month > 132:
                return Decimal("0.00")
            return (balance * self.loan.pmi_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal("0.00")

    def _build_amortization(self):
        """
        Constructs the full amortization schedule from origination through maturity.
        Handles:
        - Draw period and interest-only payments (HELOC)
        - Full amortization including principal + interest
        - Monthly insurance additions
        - Accurate payment calculations using present value formula
        """
        balance = self.loan.principal
        rate = self.loan.rate
        current_date = self.loan.origination_date
        total_term = self.loan.term
        draw_period = self.loan.draw_period_months
        repay_term = self.loan.repayment_term_months or (total_term - draw_period)

        for month in range(1, total_term + 1):
            current_date += timedelta(days=30)
            date_str = current_date.strftime('%Y-%m-%d')

            rate = Decimal(str(self.custom_rate_schedule.get(date_str, self._get_effective_rate(date_str))))
            interest = Decimal(calculate_interest(balance, rate, 30, self.loan.compounding)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if self.loan.is_heloc and month <= draw_period:
                payment = interest
                principal = Decimal("0.00")
            else:
                monthly_rate = rate / Decimal("12") / Decimal("100")
                if self.loan.is_heloc:
                    remaining_term = total_term - draw_period - (month - draw_period - 1)
                else:
                    remaining_term = total_term - month + 1
                payment = (balance * monthly_rate / (1 - (1 + monthly_rate) ** -remaining_term)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                principal = (payment - interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            insurance = self._calculate_insurance(balance, month)
            total_payment = (payment + insurance).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ending_balance = (balance - principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            self.schedule.append({
                "Month": month,
                "Date": date_str,
                "Beginning Balance": float(balance),
                "Payment": float(payment),
                "Principal": float(principal),
                "Interest": float(interest),
                "PMI/MIP": float(insurance),
                "Total Payment": float(total_payment),
                "Ending Balance": float(ending_balance)
            })

            balance = ending_balance

    def to_dataframe(self):
        """
        Returns the amortization schedule as a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Tabular amortization schedule.
        """
        return pd.DataFrame(self.schedule)

    def to_csv(self, filepath):
        """
        Writes the amortization schedule to a CSV file.

        Parameters
        ----------
        filepath : str
            Destination file path.
        """
        self.to_dataframe().to_csv(filepath, index=False)
