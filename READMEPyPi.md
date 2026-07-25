# MortgageModeler

**Mortgage Modeler** is a professional-grade mortgage modeling toolkit and CLI for simulating, analyzing, and comparing U.S. home loans — built for analysts, fintech engineers, and power users.

[![PyPI](https://img.shields.io/pypi/v/mortgagemodeler)](https://pypi.org/project/mortgagemodeler/)
[![GitHub](https://img.shields.io/badge/github-arunkpe/mortgagemodeler-blue)](https://github.com/arunkpe/mortgagemodeler)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/arunkpe/mortgagemodeler/HEAD?labpath=notebooks%2FFixed_vs_ARM.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/pypi/pyversions/mortgagemodeler)
---

## Overview

**MortgageModeler** provides in-depth mortgage analytics in Python, including:

- Amortization, payment, and payoff schedules
- Fixed, ARM, FHA, VA, USDA, and HELOC loan structures
- Recast and refinance logic with closing cost modeling
- Forward rate curve simulation and ARM caps/floors
- Effective APR and refinance breakeven point calculation
- CLI and API for scripting, exploration, or integration
- Composable modeling: combine ARM resets, forward rate paths, recast, refinance, and extra payments in one simulation

---

## Supported Features

- Flexible amortization modeling for fixed, ARM, FHA, VA, USDA, and HELOC loans
- Support for extra payments, lump sums, recasts, and refinance scenarios
- Forward rate simulation for ARMs with full cap/floor/margin logic
- Recast support based on lump-sum triggers or scheduled month
- Refinance modeling with rate/term changes and closing costs
- Effective APR calculation including points and fees
- Breakeven analysis to evaluate refinance timing
- CSV and JSON export of full amortization schedules
- Matplotlib-based amortization plotting
- Command-line interface (`mortgagemodeler`) and Python API

---
## Why MortgageModeler?

MortgageModeler was built for modern housing finance analysis — blending precision, flexibility, and transparency. Whether you're a fintech developer modeling loans, a homeowner exploring refinance timing, or a credit analyst stress-testing ARM resets, this library gives you full control and reproducibility — via Python or CLI.

---

## Supported loan types:

- `fixed`
- `arm`
- `fha`
- `va`
- `usda`
- `heloc`

---

## Installation

```bash
pip install mortgagemodeler
```

---

## Quickstart

Using the Python API:

```python
from mortgagemodeler import Loan, LoanAmortizer

loan = Loan(principal=400000, rate=0.0625, term_months=360, origination_date="2023-01-01")
amortizer = LoanAmortizer(loan)
amortizer.plot()
```

---

## CLI Usage

### Run amortization calculations and models via CLI:

```bash
mortgagemodeler amortize --balance 400000 --rate 6.25 --term 360 --type arm \
--index SOFR --margin 2.75 --arm-structure 5 6 --caps 2 1 5 --floors 0 0 0 \
--start-date 2023-01-01 --extra-payment 100 --show-apr --plot
```

### Run complex scenarios including custom index, model curtailments and recast

```bash
mortgagemodeler amortize   --type arm   --balance 800000   --rate 5.25 \ 
--term 360   --margin 2.5   --arm-structure 3/1   --index-curve '{"2027-07-01": 4.0}' \
--index SOFR   --months 60   --curtailments 300000@42   --recast-month 45
 ```

### Explore rich command line 

Use `--help` to see all available options.

```bash
mortgagemodeler amortize --help
```

---

## Example Notebooks

Check github repowhich  includes ready-to-run Jupyter examples in the `examples/` folder:

- **Fixed_vs_ARM.ipynb**: Compare fixed vs adjustable-rate loan paths
- **FHA_vs_Conventional.ipynb**: Analyze MIP vs PMI cost impact
- **Refinance_Breakeven.ipynb**: Estimate the optimal time to refinance

Launch directly in Binder: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/arunkpe/mortgagemodeler/HEAD?labpath=notebooks%2FFixed_vs_ARM.ipynb)

---

## License

MIT License © 2025 Arun Kumar