# MortgageModeler

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/arunkpe/mortgagemodeler/actions)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/arunkpe/mortgagemodeler/HEAD)
[![PyPI](https://img.shields.io/pypi/v/mortgagemodeler)](https://pypi.org/project/mortgagemodeler/)

**MortgageModeler** is a professional-grade Python toolkit and CLI for simulating, analyzing, and comparing mortgage loans. Supports **fixed-rate**, **ARM**, **FHA**, **VA**, **USDA**, and **HELOC** loans with advanced logic for **recasting**, **refinancing**, **extra payment plans**, and **APR and breakeven analysis**.

All features — from extra payments and ARM resets to refinance and recast — are available in both the CLI and Python API, making MortgageModeler ideal for scripting, financial modeling, or interactive analysis.

## Why MortgageModeler?

Most open-source tools in the mortgage and personal finance space are either overly simplistic or narrowly focused on generic amortization tables. **MortgageModeler** goes far beyond as tou can see in the features set and possible analytics.

---

## Table of Contents

- [Features](#features)
- [Supported Loan Types](#supported-loan-types)
- [Quick Start](#quick-start)
- [Analytics](#analytics)
- [CLI Usage](#cli-usage)
- [Modeling Capabilities](#modeling-capabilities)
- [Scenario Analysis](#scenario-analysis-out-of-the-box)
- [Use Cases](#use-cases)
- [Requirements](#requirements)
- [Install](#install)
- [License](#license)

---

## Features

- **Amortization schedule** generation (monthly, biweekly support)
- **Extra payments** and frequency modeling
- **Recast** support with lump-sum payment logic
- **Refinance** modeling with closing costs and term reset
- **Breakeven point** analysis for refinance decisions
- **Effective APR** comparison with points and fees
- **Visualization** of amortization curves and scenario comparisons
- **ARM caps/floors** and forward curve simulation. Supports every commercial ARM loan type
- Compatible with **FHA**, **VA**, **USDA**, and **HELOC** logic
- **Matplotlib visualizations** and CSV/JSON export
- Powerful **CLI and Python API**

---

###  Supported Loan Types

| Loan Type | Description                                      |
| --------- | ------------------------------------------------ |
| `fixed`   | Standard fixed-rate mortgage                     |
| `arm`     | Adjustable-Rate Mortgage (hybrid types like 5/6) |
| `fha`     | FHA-backed with upfront & monthly MIP            |
| `va`      | VA loan with guarantee fee                       |
| `usda`    | USDA loan with annual fee and upfront guarantee  |
| `heloc`   | Home Equity Line with draw/repayment period      |


---

## Quick Start

### Installation

```bash
pip install mortgagemodeler
```
Or from source

```bash
git clone https://github.com/yourusername/mortgagemodeler.git
cd mortgagemodeler
pip install -r requirements.txt
```

---

## Analytics

### ARM vs Fixed-Rate Mortgage Analysis

Explore our in-depth notebook that simulates and compares multiple ARM structures vs a 30-year fixed loan using realistic SOFR forward rates:

▶️ [View Notebook](examples/Mortgage_Types.ipynb)
[![Launch in Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/arunkpe/mortgagemodeler/HEAD?filepath=examples/Mortgage_Types.ipynb)

Highlights:
- Realistic hybrid ARM types (3/1, 5/1, 7/6, etc.)
- Total cost to exit after 5 years (payments + balance)
- Clear matplotlib visuals 


### Explore Mortgage Types

Compare amortization schedules, interest paths, and exit costs across loan types like Fixed, FHA, VA, and HELOC.

▶️ [View Full Notebook »](examples/LoanTypes.ipynb)

---

## CLI Usage

### Complex Scenario Modeling on ARM Loans

```bash
     mortgagemodeler amortize --type arm \                 # Amortize an ARM loan
     --balance 800000 --rate 5.25 --term 360 \             # Starting Rate @5.25% on $800,000 Loan Amount
     --margin 2.5   --arm-structure 3/1 --index SOFR \     # 3/1 ARM SOFR Indexed Margin = 2.5%
     --index-curve '{"2027-07-01": 4.0}'             \     # Feed Custom Index spot/forward curve - term length
     --curtailments 300000@42   --recast-month 45    \     # Apply $300,000 curtailment in month 42 and recast 
     --months 60                                     \     # Show 60 month amortization table
```

### Amortization

```bash
    mortgagemodeler amortize \
    --balance 400000 \
    --rate 6.25 \
    --term 360 \
    --type fixed \
    --extra-payment 200 \
    --output amortization.csv
```

### Recast

```bash
    mortgagemodeler amortize \
    --balance 400000 \
    --rate 6.25 \
    --term 360 \
    --recast-date 2026-06-01 
```

### Compare Scenarios

```bash
    mortgagemodeler plot \
    --scenarios 400000 6.25 360 \
    --scenarios 400000 5.75 240
```

### Effective APR

```bash
    mortgagemodeler compare-apr \
    --principal 400000 \
    --rate 6.25 \
    --term 360 \
    --points 1.0 \
    --fees 4500
```

### Refinance Breakeven

```bash
    mortgagemodeler breakeven \
    --monthly-savings 150 \
    --closing-costs 4500
```
---

### Library API Usage

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

---


###  Modeling Capabilities

| Capability                  | Description                                            |
| --------------------------- | ------------------------------------------------------ |
| **Extra Payments**          | Monthly or biweekly, configurable amount and frequency |
| **Recast Support**          | Trigger payment recalculation. Integrated amortizer    |
| **Refinance**               | New rate/term, fees rolled in or out, APR adjusted     |
| **APR Calculation**         | Effective APR including points and costs               |
| **Breakeven Analysis**      | Time to recoup refi closing costs                      |
| **Forward Rate Simulation** | SOFR-based projections for ARM/HELOC                   |
| **Balloon Payments**        | Optional final lump sum triggers schedule termination  |
| **Custom Start Month**      | Support mid-life entry for ongoing loans               |

---

### Core Features

| Feature                        | Description                                                                                   |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| **Fixed and Hybrid ARM Logic** | Full support for 3/1, 5/1, 5/5, 7/6, 10/6, etc., with caps/floors, margin, and index handling |
| **Forward Curve Injection**    | Supports forward rate curve per index (e.g., SOFR) for ARMs and HELOCs                        |
| **Custom Recast Engine**       | Lump-sum principal payments trigger term shortening or payment resets                         |
| **Refinance Engine**           | Seamlessly refis into new term/rate, with closing costs, points, and amortization reset       |
| **APR Calculation**            | Computes effective APR accounting for points and closing fees                                 |
| **Breakeven Calculator**       | Determines months-to-breakeven for refis using net savings vs. closing costs                  |
| **Loan Lifecycle Modeling**    | Supports mid-life entry with current balance and date overrides                               |
| **Balloon Payment Support**    | Optional early termination of amortization with balance due at balloon month                  |
| **Draw + Repayment Phases**    | HELOCs modeled with draw period + fully amortized repayment phase                             |
| **Payment Frequency Control**  | Monthly and biweekly support, including interest alignment                                    |
| **CSV and JSON Export**        | Full amortization schedule can be exported for further analysis                               |
| **Matplotlib Visualizations**  | Built-in plotting for amortization curves, cumulative interest, and scenario comparisons      |

---

### Built-in Scenario Analysis

| Capability                       | Description                                                                                    |
| -------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Compare Multiple Scenarios**   | Analyze and visualize amortization differences across loan types, rates, and terms             |
| **Exit Horizon Cost Modeling**   | Compute total borrower cost at any month (payments + remaining balance)                        |
| **Dynamic Rate Paths**           | Inject realistic forward curves to stress ARM and HELOC loans under rising or falling rates    |
| **Rate Shock Testing**           | Simulate interest rate shocks and their impact on payments, interest, and balance trajectories |
| **LTV/PTI Stress Layering**      | (Planned) Integrate borrower income/house value assumptions to model qualification dynamics    |
| **Investment vs Owner-Occupant** | Use recast/refi logic to simulate different borrower strategies (aggressive payoff vs refi)    |
| **Cash Flow Visibility**         | Monthly tracking of principal, interest, insurance, and extra payments                         |

---

### Use Cases

| Scenario                      | Description                                                                                                                                                                                  |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Fixed vs ARM Decision**     | Simulate and visualize whether a 5/1 or 7/6 ARM outperforms a 30-year fixed loan if the borrower exits in 5–7 years. Compare interest costs, payment trajectories, and refinance thresholds. |
| **Extra Payment Strategies**  | Evaluate how an extra \$250/month or biweekly payments impact the term, total interest paid, and time to payoff.                                                                             |
| **Recast vs Refinance**       | Model lump-sum recast vs full refinance with closing costs. Quantify tradeoffs between interest savings, lower payments, and costs.                                                          |
| **Rate Shock Testing**        | Apply SOFR-based forward curves or inject manual interest rate paths (e.g. +3% over 3 years) to test payment sensitivity in ARM and HELOC scenarios.                                         |
| **FHA vs Conventional**       | Contrast FHA loans with upfront and monthly MIP against a conventional loan with PMI. Examine when FHA is more favorable.                                                                    |
| **HELOC Cash Flow Planning**  | Model draw vs repayment phases in a HELOC. Add custom rate curves and extra payments to see how quickly the borrower can exit.                                                               |
| **Balloon Mortgage Planning** | (Planned) Understand how a 7/23 or 5/25 balloon affects long-term affordability and required refinance options.                                                                              |
| **First-Time Buyer Toolkit**  | Build customized profiles (e.g. 3.5% down FHA vs 10% down conventional) and simulate cash needed, monthly payment, and 5-year outlook.                                                       |

---

### Requirements

Python 3.10+
click
pandas
matplotlib
seaborn
numpy_financial
tabulate
python-dotenv

---


### License

This project is licensed under the [MIT License](LICENSE).

---

### Author

Arun Kumar
