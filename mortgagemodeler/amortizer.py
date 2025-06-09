from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

from mortgagemodeler.utils.interest import calculate_interest
from mortgagemodeler.utils.rates import RateReader

from typing import Optional

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
    - Extra principal payments
    - Balloon payments
    - Monthly or biweekly payment frequencies
    - Mid-life loan entry (starting at a custom month and balance)
    - Decimal-based precision for all financial calculations
    - ARM resets and optional manual recasts
    """

    def __init__(
        self, loan, custom_rate_schedule=None, start_month=1,
        starting_balance=None, starting_date=None, balloon_month=None
    ):
        """
        Initialize the amortizer.

        Parameters
        ----------
        loan : Loan
            A Loan object with complete terms.
        custom_rate_schedule : dict, optional
            Dictionary of date strings to annual rate overrides.
        start_month : int
            Month index (1-based) to start amortization from.
        starting_balance : Decimal, optional
            Custom initial balance to override loan.principal.
        starting_date : datetime.date, optional
            Starting date override.
        balloon_month : int, optional
            Month where balloon payment ends amortization.
        """
        self.loan = loan
        self.schedule = []
        self.initial_rate = loan.rate
        self.last_rate = loan.rate
        self.custom_rate_schedule = custom_rate_schedule or {}
        self.rates = RateReader() if loan.loan_type in ['arm', 'heloc'] else None

        self.start_month = start_month
        self.starting_balance = Decimal(starting_balance) if starting_balance else loan.principal
        self.starting_date = starting_date or loan.origination_date
        self.balloon_month = balloon_month

        self.original_term = loan.term
        self.recast_schedule = {}  # Dict of {month: new_term}

        # Scheduled fixed payment for amortizing loans (non-HELOC)
        if not loan.is_heloc:
            monthly_rate = self.initial_rate / Decimal("12") / Decimal("100")
            self.scheduled_payment = (self.starting_balance * monthly_rate / (1 - (1 + monthly_rate) ** -loan.term)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            self.scheduled_payment = None

        self._build_amortization()

    def apply_recast(self, month: int, new_term: Optional[int] = None):
        """
        Schedule a manual recast at a given amortization month.

        Parameters
        ----------
        month : int
            Month index to trigger recast.
        new_term : int, optional
            Optional new term in months. If not provided, uses remaining months.
        """
        self.recast_schedule[month] = new_term

    def _get_effective_rate(self, date_str: str, month: int):
        """
        Determine the effective rate for a given date, handling:
        - User overrides
        - Forward curves (with nearest backfilled logic)
        - ARM rate resets with caps/floors

        Returns
        -------
        (Decimal, bool)
            Tuple of (effective annual interest rate, reset_triggered)
        """
        if date_str in self.custom_rate_schedule:
            return Decimal(str(self.custom_rate_schedule[date_str])), False

        if self.loan.loan_type == 'fixed':
            return self.loan.rate, False

        if self.loan.loan_type == 'arm' and self.loan.index and (self.rates is not None or self.loan.forward_curve):
            base_rate = None

            if self.loan.forward_curve:
                sorted_dates = sorted(self.loan.forward_curve.keys())
                for fwd_date in reversed(sorted_dates):
                    if date_str >= fwd_date:
                        base_rate = Decimal(str(self.loan.forward_curve[fwd_date]))
                        break
            elif self.rates is not None:
                try:
                    base_rate = Decimal(str(self.rates.get_rate(self.loan.index, date_str)))
                except Exception:
                    pass

            if base_rate is None:
                base_rate = self.last_rate - self.loan.margin

            proposed = (base_rate + self.loan.margin).quantize(Decimal("0.0001"))

            fixed_months = self.loan.arm_structure[0] * 12
            reset_freq = self.loan.arm_structure[1]

            is_reset_month = (
                month > fixed_months and
                (month - fixed_months - 1) % reset_freq == 0
            )

            if is_reset_month:
                cap = Decimal(self.loan.rate_bounds['periodic_cap'])
                upper = self.last_rate + cap
                lower = self.last_rate - cap
                capped = min(max(proposed, lower), upper)

                max_life = Decimal(self.loan.rate_bounds['lifetime_cap'])
                min_life = Decimal(self.loan.rate_bounds.get('lifetime_floor', 0))
                life_upper = self.initial_rate + max_life
                life_lower = self.initial_rate - min_life
                capped = min(max(capped, life_lower), life_upper)

                self.last_rate = capped
                return capped, True

            return self.last_rate, False

        return self.loan.rate, False

    def _calculate_insurance(self, balance: Decimal, month: int) -> Decimal:
        """
        Calculate monthly mortgage insurance amount if applicable.

        Returns
        -------
        Decimal
            Monthly insurance premium.
        """
        if self.loan.is_fha:
            return (balance * self.loan.fha_monthly).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif self.loan.is_usda:
            return (balance * self.loan.usda_annual_fee / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif self.loan.is_pmi:
            ltv = balance / self.loan.original_balance
            if ltv <= Decimal("0.78") or month > 132:
                return Decimal("0.00")
            pmi_rate = getattr(self.loan, "pmi_rate", Decimal("0.0075"))
            return (balance * pmi_rate / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return Decimal("0.00")

    def _build_amortization(self):
        """
        Constructs full amortization schedule month-by-month.
        Handles:
        - HELOC draw phase and repayment
        - Insurance and extra payments
        - ARM rate resets and balloon cutoffs
        - Early payoff due to curtailments (with fixed payment)
        - Optional recast to reset payment based on current balance and new term
        """
        balance = self.starting_balance
        current_date = self.starting_date
        total_term = self.loan.term
        draw_period = self.loan.draw_period_months
        repay_term = self.loan.repayment_term_months or (total_term - draw_period)
        extra_amt = self.loan.extra_payment_amount
        frequency = self.loan.extra_payment_frequency or 'monthly'

        for month in range(self.start_month, total_term + 1):
            current_date += timedelta(days=30)
            date_str = current_date.strftime('%Y-%m-%d')

            rate, reset_triggered = self._get_effective_rate(date_str, month)
            interest = Decimal(calculate_interest(balance, rate, 30, self.loan.compounding)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if self.loan.is_heloc:
                if month <= draw_period:
                    # HELOC draw phase: interest-only
                    payment = interest
                    principal = Decimal("0.00")
                else:
                    # HELOC repayment phase: dynamically compute amortizing payment
                    monthly_rate = rate / Decimal("12") / Decimal("100")
                    remaining_term = repay_term - (month - draw_period - 1)
                    if remaining_term <= 0:
                        payment = interest
                        principal = Decimal("0.00")
                    else:
                        payment = (balance * monthly_rate / (1 - (1 + monthly_rate) ** -remaining_term)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        principal = (payment - interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                recast_now = month in self.recast_schedule
                if recast_now or (self.loan.is_arm and reset_triggered):
                    remaining_term = self.recast_schedule.get(month) or (self.original_term - month + 1)
                    monthly_rate = rate / Decimal("12") / Decimal("100")
                    if monthly_rate == 0:
                        payment = balance / Decimal(remaining_term)
                    else:
                        payment = (balance * monthly_rate / (1 - (1 + monthly_rate) ** -remaining_term))
                    self.scheduled_payment = payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                payment = self.scheduled_payment or Decimal("0.00")
                principal = (payment - interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            extra = (
                (extra_amt * Decimal("26") / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if frequency == 'biweekly' else extra_amt
            )

            insurance = self._calculate_insurance(balance, month)
            total_principal = principal + extra

            if total_principal > balance:
                total_principal = balance
                principal = total_principal - extra
                payment = (principal + interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_payment = (payment + insurance + extra).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ending_balance = Decimal("0.00")
            else:
                total_payment = (payment + insurance + extra).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ending_balance = max((balance - total_principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), Decimal("0.00"))

            self.schedule.append({
                "Month": month,
                "Date": date_str,
                "Beginning Balance": float(balance),
                "Payment": float(payment),
                "Principal": float(principal),
                "Interest": float(interest),
                "PMI/MIP": float(insurance),
                "Extra Payment": float(extra),
                "Total Payment": float(total_payment),
                "Ending Balance": float(ending_balance),
                "Effective Rate": float(rate)
            })

            balance = ending_balance

            if balance <= Decimal("0.00") or (self.balloon_month and month == self.balloon_month):
                self.early_payoff_month = month
                break

    def to_dataframe(self):
        """
        Convert amortization schedule to DataFrame.

        Returns
        -------
        pd.DataFrame
            Amortization schedule.
        """
        return pd.DataFrame(self.schedule)

    def to_csv(self, filepath):
        """
        Export amortization schedule to CSV.

        Parameters
        ----------
        filepath : str
            Output path for CSV file.
        """
        self.to_dataframe().to_csv(filepath, index=False)
