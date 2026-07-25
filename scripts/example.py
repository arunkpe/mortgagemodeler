# scripts/example.py — regenerate the example CSVs in examples/

import os
from datetime import date
from mortgagemodeler import Loan, LoanAmortizer

EXAMPLES = [
    ("fixed_30yr_6.5.csv", Loan(250000, 360, 6.5, date(2024, 1, 1))),
    ("fha_30yr.csv", Loan(250000, 360, 6.25, date(2024, 1, 1), loan_type='fha')),
    ("va_15yr.csv", Loan(200000, 180, 5.5, date(2024, 1, 1), loan_type='va')),
    ("with_extra.csv", Loan(300000, 360, 6.25, date(2024, 1, 1), extra_payment_amount=200.0, extra_payment_frequency='monthly')),
]

os.makedirs("examples", exist_ok=True)

for filename, loan in EXAMPLES:
    amortizer = LoanAmortizer(loan)
    df = amortizer.to_dataframe()
    df.to_csv(f"examples/{filename}", index=False)
    print(f"Saved {filename}")
