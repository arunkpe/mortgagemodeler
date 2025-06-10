from datetime import date
from decimal import Decimal
from typing import Optional, Union, Tuple, Dict


class Loan:
    """Base Loan class supporting various mortgage types.

    Parameters
    ----------
    principal : float
        Original loan amount.
    term_months : int
        Loan term in months.
    rate : float
        Nominal annual interest rate (APR).
    origination_date : datetime.date
        Date the loan originated.
    loan_type : str, optional
        Type of loan: 'fixed', 'arm', 'fha', 'heloc', 'va', 'usda'. Default is 'fixed'.
    compounding : str, optional
        Interest compounding method (e.g., '30E/360', 'A/365F'). Default is '30E/360'.
    pmi : bool, optional
        Whether the loan includes Private Mortgage Insurance. Default is False.
    draw_period_months : int, optional
        Number of months for interest-only draw period (HELOCs).
    repayment_term_months : int, optional
        Repayment phase after draw period (HELOCs).
    extra_payment_amount : float or Decimal, optional
        Fixed recurring extra payment amount.
    extra_payment_frequency : str, optional
        Frequency of extra payments ('monthly', 'biweekly').
    """

    # Core attributes
    principal: Decimal
    original_balance: Decimal
    term: int
    rate: Decimal
    origination_date: date
    loan_type: str
    compounding: str
    is_pmi: bool
    is_fixed: bool

    # ARM-related attributes
    is_arm: bool
    index: Optional[str]
    margin: Decimal
    arm_structure: Optional[Tuple[int, int]]
    forward_curve: Optional[Dict[str, float]]
    rate_bounds: Dict[str, Decimal]

    # HELOC
    draw_period_months: int
    repayment_term_months: int
    is_heloc: bool

    # FHA
    is_fha: bool
    fha_upfront: Decimal
    fha_monthly: Decimal

    # VA/USDA
    is_va: bool
    is_usda: bool
    guarantee_fee: Decimal
    usda_annual_fee: Decimal

    # Extra payments
    extra_payment_amount: Decimal
    extra_payment_frequency: Optional[str]

    def __init__(self, principal, term_months, rate, origination_date: date,
                 loan_type='fixed', compounding='30E/360', pmi=False,
                 draw_period_months: Optional[int] = None, repayment_term_months: Optional[int] = None,
                 arm_structure: Optional[Tuple[int, int]] = None,
                 extra_payment_amount: Optional[Union[float, Decimal]] = None,
                 extra_payment_frequency: Optional[str] = None,
                 margin: Optional[Union[float, Decimal]] = None):
        self.principal = Decimal(str(principal))
        self.original_balance = Decimal(str(principal))
        self.term = term_months
        self.rate = Decimal(str(rate))
        self.origination_date = origination_date
        self.loan_type = loan_type
        self.compounding = compounding
        self.is_pmi = pmi
        self.is_fixed = loan_type == 'fixed'

        # ARM attributes
        self.is_arm = loan_type == 'arm'
        self.index = None
        self.margin = Decimal(str(margin)) if margin is not None else Decimal("0.00")
        self.arm_structure = arm_structure if self.is_arm else None
        self.forward_curve = None
        self.rate_bounds = {
            'initial_cap': Decimal("2.0"),
            'periodic_cap': Decimal("1.0"),
            'lifetime_cap': Decimal("5.0"),
            'initial_floor': Decimal("0.0"),
            'periodic_floor': Decimal("0.0"),
            'lifetime_floor': Decimal("0.0"),
        }

        # HELOC support
        self.draw_period_months = draw_period_months or 0
        self.repayment_term_months = repayment_term_months or 0
        self.is_heloc = loan_type == 'heloc'

        # FHA support
        self.is_fha = loan_type == 'fha'
        self.fha_upfront = Decimal("0.0175")  # 1.75% upfront MIP default
        self.fha_monthly = Decimal("0.0085") / 12  # 0.85% annualized
        if self.is_fha:
            self.principal += self.principal * self.fha_upfront

        # VA/USDA support
        self.is_va = loan_type == 'va'
        self.is_usda = loan_type == 'usda'
        self.guarantee_fee = Decimal("0.0225") if self.is_va else Decimal("0.01")
        self.usda_annual_fee = Decimal("0.0035") if self.is_usda else Decimal("0.00")
        if self.is_va or self.is_usda:
            self.principal += self.principal * self.guarantee_fee
        if self.is_va or self.is_usda:
            self.is_pmi = False

        # Extra payment
        self.extra_payment_amount = Decimal(str(extra_payment_amount)) if extra_payment_amount else Decimal("0.00")
        self.extra_payment_frequency = extra_payment_frequency

    @classmethod
    def fixed(cls, principal, term, rate, origination_date, **kwargs):
        """Construct a fixed-rate loan."""
        return cls(
            principal=principal,
            term_months=term,
            rate=rate,
            origination_date=origination_date,
            loan_type='fixed',
            **kwargs
        )

    @classmethod
    def from_arm(cls, principal, term, arm_type, index, margin, origination_date,
                 rate=None, caps=(2, 1, 5), floors=(0, 0, 0), forward_curve=None):
        """
        Construct an ARM loan with index, margin, caps/floors, and optional forward curve.

        Parameters
        ----------
        arm_type : str
            Format like '5/6' where 5 = fixed period (years), 6 = reset frequency (months).
        index : str
            Name of reference index (e.g., 'SOFR').
        margin : float
            Spread above index.
        origination_date : date
            Loan start date.
        rate : float, optional
            Initial rate; if not given, inferred from index + margin.
        caps : tuple
            (initial cap, periodic cap, lifetime cap)
        floors : tuple
            (initial floor, periodic floor, lifetime floor)
        forward_curve : dict, optional
            Optional dict of {date: rate} to override index source.
        """
        fixed, freq = map(int, arm_type.split('/'))

        if rate is None:
            orig_str = origination_date.strftime('%Y-%m-%d')
            base_rate = Decimal(str(forward_curve.get(orig_str, 0.0))) if forward_curve else Decimal("0.0")
            start_rate = base_rate + Decimal(str(margin))
        else:
            start_rate = Decimal(str(rate))

        loan = cls(
            principal=principal,
            term_months=term,
            rate=start_rate,
            origination_date=origination_date,
            loan_type='arm',
            arm_structure=(fixed, freq)
        )
        loan.index = index.upper()
        loan.margin = Decimal(str(margin))
        loan.forward_curve = forward_curve or {}
        loan.rate_bounds = {
            'initial_cap': Decimal(str(caps[0])),
            'periodic_cap': Decimal(str(caps[1])),
            'lifetime_cap': Decimal(str(caps[2])),
            'initial_floor': Decimal(str(floors[0])),
            'periodic_floor': Decimal(str(floors[1])),
            'lifetime_floor': Decimal(str(floors[2])),
        }
        return loan

    def is_reset_month_a(self, month_number: int) -> bool:
        """
        Determine whether the given month number is a rate reset month for an ARM.

        Parameters
        ----------
        month_number : int
            The 1-based month index of the loan schedule.

        Returns
        -------
        bool
            True if the month is a reset month; False otherwise.
        """
        if not self.is_arm or not self.arm_structure:
            return False
        fixed_months = self.arm_structure[0] * 12
        reset_freq = self.arm_structure[1]
        return (month_number > fixed_months) and ((month_number - fixed_months) % reset_freq == 0)


    def is_reset_month(self, month):
        """Check if this month triggers an ARM rate reset"""
        if self.loan_type != 'arm'  or not self.arm_structure:
            return False
        
        fixed_months = self.arm_structure[0] * 12  # 36 for 3/1 ARM
        if month <= fixed_months:
            return False
        
        reset_freq_months = self.arm_structure[1] * 12  # 12 for annual resets
        return (month - fixed_months - 1) % reset_freq_months == 0


    def set_indexed_rate(self, index_name: str, margin: float, caps=(2, 1, 5)):
        """Configure index-based rate adjustment (for ARMs or HELOCs).

        Parameters
        ----------
        index_name : str
            Name of the index (e.g., 'SOFR', 'PRIME').
        margin : float
            Rate margin added to index.
        caps : tuple
            Tuple of (initial cap, periodic cap, lifetime cap).
        """
        self.index = index_name.upper()
        self.margin = Decimal(str(margin))
        self.caps = {'initial': caps[0], 'periodic': caps[1], 'lifetime': caps[2]}

    def refinance(self, new_rate: float, refinance_date: date, new_term: Optional[int] = None, fees: float = 0.0):
        """Creates a new Loan object simulating a refinance at a given date."""
        return Loan(
            principal=self.principal + Decimal(str(fees)),
            term_months=new_term or self.term,
            rate=new_rate,
            origination_date=refinance_date,
            loan_type=self.loan_type,
            compounding=self.compounding,
            pmi=self.is_pmi,
            draw_period_months=self.draw_period_months,
            repayment_term_months=self.repayment_term_months,
            extra_payment_amount=float(self.extra_payment_amount),
            extra_payment_frequency=self.extra_payment_frequency,
            arm_structure=self.arm_structure if self.loan_type == 'arm' else None,
        )

    def recast(self, lump_sum: float, recast_date: date):
        """Apply a lump-sum principal reduction and update loan balance."""
        self.principal -= Decimal(str(lump_sum))
        self.origination_date = recast_date
        self.original_balance = self.principal

    def apply_extra_payment(self, amount: float, frequency: str):
        """Set up recurring extra payments."""
        self.extra_payment_amount = Decimal(str(amount))
        self.extra_payment_frequency = frequency

    def to_dict(self):
        """Return core loan parameters as dictionary (for CLI or plotting use)."""
        return {
            "principal": float(self.principal),
            "term_months": self.term,
            "rate": float(self.rate),
            "start_date": self.origination_date.isoformat(),
            "type": self.loan_type.upper(),
            "is_fixed": self.is_fixed,
            "is_arm": self.is_arm,
            "is_fha": self.is_fha,
            "is_va": self.is_va,
            "is_usda": self.is_usda,
            "is_heloc": self.is_heloc,
            "has_pmi": self.is_pmi,
            "extra_payment_amount": float(self.extra_payment_amount),
            "extra_payment_frequency": self.extra_payment_frequency
        }
