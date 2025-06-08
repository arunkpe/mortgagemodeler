from datetime import date
from decimal import Decimal
from typing import Optional, Union


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
    def __init__(self, principal, term_months, rate, origination_date: date,
                 loan_type='fixed', compounding='30E/360', pmi=False,
                 draw_period_months: Optional[int] = None, repayment_term_months: Optional[int] = None,
                 extra_payment_amount: Optional[Union[float, Decimal]] = None,
                 extra_payment_frequency: Optional[str] = None):
        self.principal = Decimal(principal)
        self.original_balance = Decimal(principal)
        self.term = term_months
        self.rate = Decimal(rate)
        self.origination_date = origination_date
        self.loan_type = loan_type
        self.compounding = compounding
        self.is_pmi = pmi

        # ARM attributes
        self.index = None
        self.margin = Decimal("0.00")
        self.arm_structure = None
        self.caps = {'initial': None, 'periodic': None, 'lifetime': None}

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
        self.extra_payment_amount = Decimal(extra_payment_amount) if extra_payment_amount else Decimal("0.00")
        self.extra_payment_frequency = extra_payment_frequency

    @classmethod
    def from_fha(cls, principal, term, rate, origination_date):
        """Construct an FHA loan object."""
        return cls(principal, term, rate, origination_date, loan_type='fha')

    @classmethod
    def from_va(cls, principal, term, rate, origination_date):
        """Construct a VA loan object."""
        return cls(principal, term, rate, origination_date, loan_type='va')

    @classmethod
    def from_usda(cls, principal, term, rate, origination_date):
        """Construct a USDA loan object."""
        return cls(principal, term, rate, origination_date, loan_type='usda')

    @classmethod
    def from_arm_type(cls, arm_type: str, principal, term, rate, origination_date):
        """Construct an ARM loan from a hybrid ARM string (e.g., '5/6').

        Parameters
        ----------
        arm_type : str
            Format is '{fixed_period}/{adjustment_freq}' in years/months.
        """
        fixed, freq = map(int, arm_type.split('/'))
        loan = cls(principal, term, rate, origination_date, loan_type='arm')
        loan.arm_structure = (fixed, freq)
        return loan

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
        self.margin = Decimal(margin)
        self.caps = {'initial': caps[0], 'periodic': caps[1], 'lifetime': caps[2]}

    def refinance(self, new_rate: float, refinance_date: date, new_term: Optional[int] = None, fees: float = 0.0):
        """Creates a new Loan object simulating a refinance at a given date.

        Parameters
        ----------
        new_rate : float
            New interest rate.
        refinance_date : date
            Date of refinance (must match amortizer schedule).
        new_term : int, optional
            Optional new loan term in months.
        fees : float, optional
            Optional closing costs added to balance.

        Returns
        -------
        Loan
            New refinanced Loan object.
        """
        return Loan(
            principal=self.principal + Decimal(fees),
            term_months=new_term or self.term,
            rate=new_rate,
            origination_date=refinance_date,
            loan_type=self.loan_type,
            compounding=self.compounding,
            pmi=self.is_pmi,
            draw_period_months=self.draw_period_months,
            repayment_term_months=self.repayment_term_months,
            extra_payment_amount=float(self.extra_payment_amount),
            extra_payment_frequency=self.extra_payment_frequency
        )

    def recast(self, lump_sum: float, recast_date: date):
        """Apply a lump-sum principal reduction and update loan balance.

        Parameters
        ----------
        lump_sum : float
            Amount to reduce from principal.
        recast_date : date
            Date the recast is executed.
        """
        self.principal -= Decimal(lump_sum)
        self.origination_date = recast_date
        self.original_balance = self.principal

    def apply_extra_payment(self, amount: float, frequency: str):
        """Set up recurring extra payments.

        Parameters
        ----------
        amount : float
            Extra payment amount to apply.
        frequency : str
            Payment frequency, e.g., 'monthly', 'biweekly'.
        """
        self.extra_payment_amount = Decimal(str(amount))
        self.extra_payment_frequency = frequency

    def to_dict(self):
        """Return core loan parameters as dictionary (for CLI or plotting use)."""
        return {
            "principal": float(self.principal),
            "term_months": self.term,
            "rate": float(self.rate),
            "start_date": self.origination_date.isoformat(),
            "type": self.loan_type.upper()
        }
