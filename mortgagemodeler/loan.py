from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Union, Tuple, Dict
from mortgagemodeler.utils.date import normalize_date

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

    #: Commercial ARM products mapped to (fixed_period_years, reset_frequency_months).
    #: '5/6' fixes for 5 years then resets every 6 months; '5/5' resets every 5 years.
    ARM_PRODUCT_MAP = {
        '3/1': (3, 12), '3/6': (3, 6),
        '5/1': (5, 12), '5/5': (5, 60), '5/6': (5, 6),
        '7/1': (7, 12), '7/6': (7, 6),
        '10/1': (10, 12), '10/6': (10, 6),
    }

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
        self.origination_date = normalize_date(origination_date)
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
            A commercial ARM product name like '5/6' (5-year fixed period,
            resets every 6 months thereafter). Resolved via ARM_PRODUCT_MAP,
            so '5/1' means annual resets and '5/5' means resets every 5 years,
            matching market convention.
        index : str
            Name of reference index (e.g., 'SOFR').
        margin : float
            Spread above index.
        origination_date : date
            Loan start date.
        rate : float, optional
            Initial rate; if not given, inferred from index + margin.
        caps : tuple
            (initial cap, periodic cap, lifetime cap). Initial/periodic caps
            bound the rate movement at the first/subsequent resets; the
            lifetime cap bounds the rate at initial rate + lifetime cap.
        floors : tuple
            (initial floor, periodic floor, lifetime floor), expressed as
            absolute floor rates (default 0.0 = the rate cannot go negative).
        forward_curve : dict, optional
            Optional dict of {date: rate} to override index source.
        """
        if arm_type in cls.ARM_PRODUCT_MAP:
            fixed, freq = cls.ARM_PRODUCT_MAP[arm_type]
        else:
            raise ValueError(
                f"Unknown ARM structure '{arm_type}'. Supported: {', '.join(sorted(cls.ARM_PRODUCT_MAP))}"
            )

        if rate is None:
            origination_date = normalize_date(origination_date)
            base_rate = Decimal("0.0")
            if forward_curve:
                # Use the most recent curve point on or before origination.
                past = [d for d in sorted(forward_curve)
                        if datetime.strptime(d, '%Y-%m-%d').date() <= origination_date]
                if past:
                    base_rate = Decimal(str(forward_curve[past[-1]]))
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

    def is_reset_month(self, month):
        """Check if this month triggers an ARM rate reset.

        ``arm_structure`` is (fixed_period_years, reset_frequency_months):
        a 5/6 ARM — stored as (5, 6) — first resets at month 61 and every
        6 months thereafter; a 3/1 ARM — stored as (3, 12) — resets annually
        starting at month 37.
        """
        if self.loan_type != 'arm' or not self.arm_structure:
            return False

        fixed_months = self.arm_structure[0] * 12  # e.g. 36 for a 3/1 ARM
        if month <= fixed_months:
            return False

        reset_freq_months = self.arm_structure[1]  # already expressed in months
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
        self.rate_bounds.update({
            'initial_cap': Decimal(str(caps[0])),
            'periodic_cap': Decimal(str(caps[1])),
            'lifetime_cap': Decimal(str(caps[2])),
        })

    def refinance(self, new_rate: float, refinance_date: date, new_term: Optional[int] = None,
                  fees: float = 0.0, balance: Optional[Union[float, Decimal]] = None):
        """Creates a new Loan object simulating a refinance at a given date.

        Parameters
        ----------
        new_rate : float
            Interest rate on the new loan.
        refinance_date : date
            Origination date of the new loan.
        new_term : int, optional
            Term of the new loan in months. Defaults to the current term.
        fees : float
            Closing costs rolled into the new balance.
        balance : float or Decimal, optional
            Outstanding balance being refinanced. Defaults to the current
            principal. Pass the amortized balance as of ``refinance_date``
            for an accurate mid-life refinance.

        Notes
        -----
        Upfront FHA/VA/USDA fees financed at original closing are already in
        the balance and are NOT charged a second time.
        """
        base = Decimal(str(balance)) if balance is not None else self.principal
        new_loan = Loan(
            principal=base,
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
        # The constructor re-applies financed upfront fees for FHA/VA/USDA
        # loan types; a refinance must not pay them twice, so reset the
        # balance to refinanced principal plus closing costs.
        new_loan.principal = base + Decimal(str(fees))
        new_loan.original_balance = new_loan.principal
        return new_loan

    def recast(self, lump_sum: float, recast_date: date):
        """Apply a lump-sum principal reduction and update loan balance.

        ``original_balance`` is intentionally left unchanged: PMI drop-off is
        based on LTV against the original loan amount, not the recast balance.
        """
        self.principal -= Decimal(str(lump_sum))
        self.origination_date = normalize_date(recast_date)

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
