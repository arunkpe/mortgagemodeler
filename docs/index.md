# Mortgage Tools

A modular, CLI-driven Python library for modeling amortization schedules, refinancing, recasting, and loan comparison — including support for fixed, ARM, FHA, VA, USDA, and HELOC loans.

---

## Features

- Full amortization schedule with principal, interest, PMI/MIP
- FHA, VA, USDA loan modeling with fees and guarantees
- Support for ARM and HELOC logic with margin, index, and caps
- Recast and refinance simulations
- Effective APR and breakeven analysis
- CLI interface for automation and scripting
- Built-in plotting of amortization scenarios

---

## Installation

```bash
git clone https://github.com/arunkpe/mortgage-tools.git
cd mortgage-tools
pip install -r requirements.txt
```

To enable CLI usage from anywhere:

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
```

---

## Quickstart

Generate a fixed-rate amortization schedule:

```bash
python -m cli.cli amortize \
  --type fixed \
  --balance 400000 \
  --rate 6.0 \
  --term 360
```

Compare two loan scenarios:

```bash
python -m cli.cli plot \
  --scenarios 400000 6.0 360 \
  --scenarios 400000 5.5 360 
```

---

## Documentation Structure

- [Usage Guide](usage.md) — CLI commands and examples
- [Loan Types](loan_types.md) — Details on fixed, ARM, FHA, VA, USDA, HELOC
- [Scenarios](scenarios.md) — Visualizations and tradeoff analysis
- [CLI Reference](cli.md) — All CLI options in one place

---

## License

This project is licensed under the terms of the [MIT License](license.md)

---

## Contributing

PRs and feature suggestions welcome — please open an issue first if you'd like to discuss a change or enhancement.

```bash
# Lint and check
black . && flake8

# Run CLI with debug logging
python -m cli.cli amortize --help
```

---

## Author

Built with care by [Arun Kumar](https://github.com/arunkpe), inspired by real mortgage modeling use cases in consumer finance and credit decisioning.
