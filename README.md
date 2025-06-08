# Mortgage Tools

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/arunkpe/mortgagemodeler/actions)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/arunkpe/mortgagemodeler/HEAD)

A professional-grade Python toolkit and CLI for simulating, analyzing, and comparing mortgage loans. Supports fixed-rate, ARM, FHA, VA, USDA, and HELOC loans with rich features like **recasting**, **refinancing**, **extra payment plans**, and **effective APR and breakeven analysis**.

---

## Features

- **Amortization schedule** generation (monthly, biweekly support)
- **Extra payments** and frequency modeling
- **Recast** support with lump-sum payment logic
- **Refinance** modeling with closing costs and term reset
- **Breakeven point** analysis for refinance decisions
- **Effective APR** comparison with points and fees
- **Visualization** of amortization curves and scenario comparisons
-  Compatible with advanced loan types (FHA, VA, USDA, HELOC, ARM)

---

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/mortgagemodeler.git
cd mortgagemodeler
pip install -r requirements.txt
```

## CLI Usage

### Amortization

```bash
    python cli.py amortize \
    --balance 400000 \
    --rate 6.25 \
    --term 360 \
    --type fixed \
    --extra-payment 200 \
    --extra-frequency monthly \
    --output amortization.csv
```

### Recast

```bash
    python cli.py amortize \
    --balance 400000 \
    --rate 6.25 \
    --term 360 \
    --recast-date 2026-06-01 \
    --lump-sum 10000
```

### Recast

```bash
    python cli.py amortize \
    --balance 400000 \
    --rate 6.25 \
    --term 360 \
    --recast-date 2026-06-01 \
    --lump-sum 10000
```

### Refinance

```bash
    python cli.py amortize \
    --balance 400000 \
    --rate 6.25 \
    --term 360 \
    --refinance-date 2026-06-01 \
    --new-rate 5.75 \
    --refi-fees 4500
```

### Compare Scenarios

```bash
    python cli.py plot \
    --scenarios 400000 6.25 360 \
    --scenarios 400000 5.75 240
```

### Effective APR

```bash
    python cli.py compare-apr \
    --principal 400000 \
    --rate 6.25 \
    --term 360 \
    --points 1.0 \
    --fees 4500
```

### Refinance Breakeven

```bash
    python cli.py breakeven \
    --monthly-savings 150 \
    --closing-costs 4500
```

### Library Usage

```python
    from mortgage_tools.loan import Loan
    from mortgage_tools.amortizer import LoanAmortizer

    loan = Loan(
        principal=400000,
        rate=6.25,
        term_months=360,
        origination_date=date.today(),
        loan_type='fixed',
        extra_payment_amount=200,
        extra_payment_frequency='monthly'
    )

    amortizer = LoanAmortizer(loan)
    df = amortizer.to_dataframe()
    df.head()
```

###  Supported Loan Types

| Loan Type | Description                                      |
| --------- | ------------------------------------------------ |
| `fixed`   | Standard fixed-rate mortgage                     |
| `arm`     | Adjustable-Rate Mortgage (hybrid types like 5/6) |
| `fha`     | FHA-backed with upfront & monthly MIP            |
| `va`      | VA loan with guarantee fee                       |
| `usda`    | USDA loan with annual fee and upfront guarantee  |
| `heloc`   | Home Equity Line with draw/repayment period      |


### Requirements

Python 3.10+
click
pandas
matplotlib
seaborn
numpy_financial
tabulate
python-dotenv

### Install

```bash
pip install -r requirements.txt
```

### License

This project is licensed under the [MIT License](LICENSE).


### Author

Arun Kumar

