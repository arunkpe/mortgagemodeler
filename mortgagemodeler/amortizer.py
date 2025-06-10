from datetime import datetime
from dateutil.relativedelta import relativedelta

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

import pandas as pd

from mortgagemodeler.utils.interest import calculate_interest
from mortgagemodeler.utils.rates import RateReader

from typing import Optional, Dict

class RateSource(Enum):
    CUSTOM = 'custom'
    INDEX = 'index'
    STATIC = 'static'

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
    - custom_rate_schedule: absolute override for month-specific rates (e.g., step-up / step-down mods).
    - loan.forward_curve: optional base index rates used in ARM resets (index + margin capped).
    - If neither forward_curve or custom_rate_schedule is provided, the loan's starting rate is assumed to persist
    """

    def __init__(
        self, loan, custom_rate_schedule=None, start_month=1,
        starting_balance=None, starting_date=None, balloon_month=None, curtailments=None,
        recast_schedule = None
    ):
        self.loan = loan
        self.schedule = []
        self.initial_rate = loan.rate
        self.last_rate = loan.rate
        self.custom_rate_schedule: Dict[str, float] = custom_rate_schedule if custom_rate_schedule else {}

        self.rates = RateReader() if loan.loan_type in ['arm', 'heloc'] else None

        self.start_month = start_month
        self.starting_balance = Decimal(starting_balance) if starting_balance else loan.principal
        self.starting_date = starting_date or loan.origination_date
        self.balloon_month = balloon_month

        self.original_term = loan.term
        self.recast_schedule = recast_schedule or {}  # Dict of {month: new_term}
        self.curtailments = curtailments or {}  


        if self.custom_rate_schedule:
            self.rate_source = RateSource.CUSTOM
        elif loan.forward_curve and len(loan.forward_curve) > 0:
            self.rate_source = RateSource.INDEX
        else:
            self.rate_source = RateSource.STATIC
        print(f"[DEBUG INIT] Rate source selected: {self.rate_source}", flush=True)

        if not loan.is_heloc:
            monthly_rate = self.initial_rate / Decimal("12") / Decimal("100")
            self.scheduled_payment = (self.starting_balance * monthly_rate / (1 - (1 + monthly_rate) ** -loan.term)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            self.scheduled_payment = None

        self._build_amortization() # type: ignore

    def apply_recast(self, month: int, new_term: Optional[int] = None):
        """
        Schedule a manual recast at a specific month.

        Parameters
        ----------
        month : int
            The amortization month index (1-based) when recast should occur.
        new_term : int, optional
            Optional new term in months to use for recalculating payment.
            If None, defaults to remaining months from that point.
        """
        self.recast_schedule[month] = new_term

    def _calculate_insurance(self, balance: Decimal, month: int) -> Decimal:
        """
        Calculate monthly mortgage insurance premium for FHA, USDA, or PMI.

        Parameters
        ----------
        balance : Decimal
            Current outstanding balance of the loan.
        month : int
            Current amortization month index (1-based).

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

    def _get_effective_rate(self, date_str: str, month: int):
        """
        Determine the applicable interest rate for a given date.

        Handles:
        - Custom rate overrides from schedule
        - Static fixed rates for standard loans
        - Indexed lookups for ARMs and HELOCs using forward curve or RateReader
        - Respects ARM periodic caps, lifetime caps, and floors

        Parameters
        ----------
        date_str : str
            Date string (YYYY-MM-DD) for rate lookup.
        month : int
            Amortization month index (1-based).

        Returns
        -------
        (Decimal, bool)
            Tuple of (annual rate as Decimal, whether reset occurred)
        """
        if self.rate_source == RateSource.CUSTOM and date_str in self.custom_rate_schedule:
            return Decimal(str(self.custom_rate_schedule[date_str])), False

        if self.rate_source == RateSource.STATIC or self.loan.loan_type == 'fixed':
            return self.loan.rate, False

        curr_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        base_rate = None
        is_index_used = False

        if self.loan.forward_curve:
            sorted_dates = sorted(self.loan.forward_curve.keys())
            for fwd_date_str in reversed(sorted_dates):
                fwd_date = datetime.strptime(fwd_date_str, "%Y-%m-%d").date()
                if curr_date >= fwd_date:
                    base_rate = Decimal(str(self.loan.forward_curve[fwd_date_str]))
                    is_index_used = True
                    break
        elif self.rates is not None:
            try:
                base_rate = Decimal(str(self.rates.get_rate(self.loan.index, date_str)))
                is_index_used = True
            except Exception:
                pass

        if base_rate is None:
            base_rate = self.last_rate

        if is_index_used:
            proposed = (base_rate + self.loan.margin).quantize(Decimal("0.0001"))
        else:
            proposed = base_rate.quantize(Decimal("0.0001"))

        if self.loan.loan_type == 'heloc':
            if proposed != self.last_rate:
                self.last_rate = proposed
                return proposed, True
            return self.last_rate, False

        if self.loan.loan_type == 'arm':
            if self.loan.is_reset_month(month):
                rate_bounds = self.loan.rate_bounds or {}
                cap = Decimal(rate_bounds.get('periodic_cap', '1.0'))
                upper = self.last_rate + cap
                lower = self.last_rate - cap
                capped = min(max(proposed, lower), upper)

                max_life = Decimal(rate_bounds.get('lifetime_cap', '5.0'))
                min_life = Decimal(rate_bounds.get('lifetime_floor', '0.0'))
                capped = min(max(capped, self.initial_rate - min_life), self.initial_rate + max_life)

                self.last_rate = capped
                print(f"[DEBUG] Month {month} Reset → Index: {base_rate}, Margin: {self.loan.margin}, Proposed: {proposed}, Capped: {capped}")
                return capped, True

            return self.last_rate, False

        return self.loan.rate, False

    def _build_amortization(self):
        """
        Constructs full amortization schedule month-by-month.

        Handles:
        - HELOC draw phase and repayment schedule
        - Mortgage insurance (PMI, MIP, USDA)
        - Extra principal payments (fixed or biweekly)
        - ARM rate resets and cap/floor logic
        - Balloon cutoffs and early payoff
        - Curtailments that reduce balance directly
        - Optional recast to reset payment based on new balance and remaining term
        """
        balance = self.starting_balance
        current_date = self.starting_date
        total_term = self.loan.term
        draw_period = self.loan.draw_period_months
        repay_term = self.loan.repayment_term_months or (total_term - draw_period)
        extra_amt = self.loan.extra_payment_amount
        frequency = self.loan.extra_payment_frequency or 'monthly'

        for month in range(self.start_month, total_term + 1):
            # 1. Record the balance at the beginning of the month
            beginning_balance = balance
            current_date += relativedelta(months=1)
            date_str = current_date.strftime('%Y-%m-%d')

            # 2. Apply curtailment BEFORE computing interest or payment
            extra_payment = Decimal("0.00")
            if month in self.curtailments:
                extra_payment = Decimal(str(self.curtailments[month]))
                balance -= extra_payment

            # 3. Get effective interest rate using forward curve + caps/floors
            # This function internally handles ARM reset logic and flags
            rate, reset_triggered = self._get_effective_rate(date_str, month)
            self.last_rate = rate  # Always update for continuity

            # 4. Compute monthly interest (after curtailment)
            interest = Decimal(calculate_interest(balance, rate, 30, self.loan.compounding)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # 5. Compute scheduled payment (HELOC vs. amortizing loan)
            if self.loan.is_heloc:
                # Handle interest-only during draw phase
                if month <= draw_period:
                    payment = interest
                    principal = Decimal("0.00")
                else:
                    # HELOC repayment phase: recalculate based on remaining term
                    months_into_repayment = month - draw_period
                    remaining_term = max(0, repay_term - months_into_repayment)
                    if remaining_term <= 0:
                        payment = interest
                        principal = Decimal("0.00")
                    else:
                        monthly_rate = rate / Decimal("12") / Decimal("100")
                        payment = (balance * monthly_rate / (1 - (1 + monthly_rate) ** -remaining_term)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        principal = (payment - interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                # Amortizing loan (ARM or fixed): recalculate payment on reset or recast
                recast_now = month in self.recast_schedule
                if recast_now or reset_triggered:
                    remaining_term = self.recast_schedule.get(month) or (self.original_term - month + 1)
                    monthly_rate = rate / Decimal("12") / Decimal("100")
                    if monthly_rate == 0:
                        payment = balance / Decimal(remaining_term)
                    else:
                        payment = (balance * monthly_rate / (1 - (1 + monthly_rate) ** -remaining_term))
                    self.scheduled_payment = payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                # Use last known scheduled payment
                payment = self.scheduled_payment or Decimal("0.00")
                principal = (payment - interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # 6. Add any extra scheduled principal payments (monthly or biweekly)
            extra = (
                (extra_amt * Decimal("26") / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if frequency == 'biweekly' else extra_amt
            )

            # 7. Calculate insurance (PMI/MIP/USDA fees, etc.)
            insurance = self._calculate_insurance(balance, month)

            # 8. Ensure we don’t overpay in final months
            total_principal = principal + extra
            if total_principal > balance:
                total_principal = balance
                extra = min(extra, balance)
                principal = total_principal - extra
                payment = (principal + interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_payment = (payment + insurance + extra).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ending_balance = Decimal("0.00")
            else:
                total_payment = (payment + insurance + extra).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ending_balance = max((balance - total_principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), Decimal("0.00"))

            # 9. Save amortization record
            self.schedule.append({
                "Month": month,
                "Date": date_str,
                "Beginning Balance": float(beginning_balance),
                "Payment": float(payment),
                "Principal": float(principal),
                "Interest": float(interest),
                "PMI/MIP": float(insurance),
                "Extra Payment": float(extra),
                "Total Payment": float(total_payment),
                "Ending Balance": float(ending_balance),
                "Effective Rate": float(rate)
            })

            # 10. Update balance for next month
            balance = ending_balance

            # 11. Stop if paid off or balloon cutoff hit
            if balance <= Decimal("0.00") or (self.balloon_month and month == self.balloon_month):
                self.early_payoff_month = month
                break

    def to_dataframe(self):
        return pd.DataFrame(self.schedule)

    def to_csv(self, filepath):
        self.to_dataframe().to_csv(filepath, index=False)