# Usage Guide

This guide walks through how to use the `MortgageAmortization` CLI tool to simulate, analyze, and compare different mortgage loan structures.

---

## Amortization Schedule

Generate a fixed-rate amortization schedule:

```bash
python -m cli.cli amortize \
  --type fixed \
  --balance 400000 \
  --rate 6.0 \
  --term 360
```

Optional arguments:

- `--extra-payment 200`
- `--extra-frequency monthly`
- `--recast-date 2026-01-01 --lump-sum 10000`
- `--refinance-date 2026-01-01 --new-rate 5.25 --new-term 240 --refi-fees 3500`
- `--output amortization.csv`

---

## ARM and HELOC

Simulate an ARM loan with index-based rate adjustments:

```bash
python -m cli.cli amortize \
  --type arm \
  --index SOFR \
  --margin 2.75 \
  --balance 400000 \
  --rate 5.0 \
  --term 360
```

Simulate a HELOC draw + repayment phase:

```bash
python -m cli.cli amortize \
  --type heloc \
  --balance 200000 \
  --rate 7.5 \
  --term 360 \
  --draw-period 120 \
  --repayment-term 240
```

---

## Compare Scenarios

Visualize amortization curves across multiple loan options:

```bash
python -m cli.cli plot \
  --scenarios 400000 6.0 360 \
  --scenarios 400000 5.5 360 \
  --scenarios 400000 5.0 240
```

---

## Effective APR

Compare true APR including points and fees:

```bash
python -m cli.cli compare-apr \
  --principal 400000 \
  --rate 5.75 \
  --term 360 \
  --points 1.0 \
  --fees 4500
```

---

## Breakeven Calculator

Find breakeven point of a refinance:

```bash
python -m cli.cli breakeven \
  --monthly-savings 225 \
  --closing-costs 3500
```

Returns the number of months until refi pays off.

---

## Other Tips

- Output data to CSV via `--output filename.csv`
- Dates must be in `YYYY-MM-DD` format
- ARM simulations pull index rates from local data (see `utils/data/macroeconforward.txt`)

---

For more, explore:

- [Loan Types Overview](loan_types.md)
- [Full CLI Reference](cli.md)
