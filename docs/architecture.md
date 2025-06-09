# Architecture

This section documents the internal structure and modular design of the **MortgageAmortization** library.

---

## Module Overview

```
MortgageAmortization/
├── cli/                    # CLI entry point (Click-based)
│   └── cli.py
├── mortgagemodeler/       # Core modeling logic
│   ├── loan.py            # Loan class with support for fixed, FHA, VA, ARM, etc.
│   ├── amortizer.py       # Generates amortization schedules
│   └── __init__.py
├── utils/                 # Shared utilities
│   ├── rates.py           # Loads forward rates (e.g. SOFR)
│   ├── plotting.py        # Visualization tools (matplotlib, seaborn)
│   ├── metrics.py         # Breakeven, APR, and comparison logic
│   └── __init__.py
├── scripts/               # One-off examples or scenario generators
│   └── example.py
├── examples/              # Precomputed scenario outputs (CSV)
├── data/                  # Default input data (e.g., forward rate files)
│   └── macroeconforward.txt
├── docs/                  # Documentation site (mkdocs)
│   └── ...
├── README.md              # Top-level usage and getting started
├── LICENSE
├── pyproject.toml         # Project configuration
└── requirements.txt
```

---

## Design Principles

- **Explicit loan types**: `Loan.from_fha()`, `Loan.from_va()`, `Loan.from_arm_type()` ensure transparent and validated instantiation.
- **Modular architecture**: CLI, plotting, and amortization logic are cleanly decoupled.
- **Vectorized performance**: amortization schedules are computed with efficient looped logic; future versions may use NumPy.
- **CLI-first philosophy**: Everything callable via `python -m cli.cli <command>`

---

## Class Relationships

```text
Loan              → configuration + rate assumptions
 ↓
LoanAmortizer     → builds amortization DataFrame
 ↓
plotting.py       → visualizes results
metrics.py        → computes analytics
cli.py            → wraps all above via Click
```

---

## Extendability

You can easily:

- Add new loan types (`Loan.from_new_type(...)`)
- Introduce custom rate sources (modify `rates.py`)
- Export more CSV metrics (extend `LoanAmortizer`)
- Wire in monthly tax/insurance, DTI logic, or cash-out refinances

---

## Planned Improvements

- JSON/YAML scenario configuration
- Interactive web UI (streamlit, fastapi-react)
- Monte Carlo interest rate scenarios
- Automated mortgage strategy comparison engine

---

For CLI usage, see [index.md](index.md). For modeling assumptions, see [loan_types.md](loan_types.md).
