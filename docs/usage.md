# MortgageModeler Command Line Examples

This document showcases a range of practical CLI examples for the `mortgagemodeler` tool, covering amortization, refinance, APR analysis, ARM resets, HELOC modeling, and plotting.

---

## Basic Fixed-Rate Loan Amortization

```bash
mortgagemodeler amortize \
  --type fixed \
  --balance 400000 \
  --rate 6.0 \
  --term 360
```

## Fixed-Rate with Extra Payments and CSV Output

```bash
mortgagemodeler amortize \
  --type fixed \
  --balance 400000 \
  --rate 6.0 \
  --term 360 \
  --extra-payment 250 \
  --output fixed_loan.csv
```

## FHA Loan with MIP and Effective APR

```bash
mortgagemodeler amortize \
  --type fha \
  --balance 350000 \
  --rate 5.75 \
  --term 360 \
  --points 1.0 \
  --finance-points \
  --show-apr
```

## VA Loan with Shorter Term

```bash
mortgagemodeler amortize \
  --type va \
  --balance 325000 \
  --rate 5.5 \
  --term 240
```

## Manual Recast at Month 60 with Lump Sum

```bash
mortgagemodeler amortize \
  --type fixed \
  --balance 450000 \
  --rate 5.25 \
  --term 360 \
  --recast-date 2029-01-01 \
  --lump-sum 50000 \
  --plot
```

## Refinance at Month 84

```bash
mortgagemodeler amortize \
  --type fixed \
  --balance 400000 \
  --rate 5.75 \
  --term 360 \
  --refinance-date 2031-01-01 \
  --new-rate 4.25 \
  --new-term 300 \
  --refi-fees 4000 \
  --plot
```

## 5/6 ARM Loan with Forward Curve

```bash
mortgagemodeler amortize \
  --type arm \
  --balance 500000 \
  --rate 3.0 \
  --term 360 \
  --index SOFR \
  --margin 2.5 \
  --arm-structure 5 6 \
  --rate-file forward_curve.csv \
  --plot
```

## HELOC with Draw and Repayment Periods

```bash
mortgagemodeler amortize \
  --type heloc \
  --balance 200000 \
  --rate 7.0 \
  --term 360 \
  --draw-period 120 \
  --repayment-term 240 \
  --index SOFR \
  --margin 2.0 \
  --rate-file heloc_curve.csv \
  --plot
```

## Compare Two APR Scenarios

```bash
mortgagemodeler compare-apr \
  --principal 400000 \
  --rate 6.5 \
  --term 360 \
  --points 1.0 \
  --fees 3000
```

## Breakeven Analysis for Refinance

```bash
mortgagemodeler breakeven \
  --monthly-savings 250 \
  --closing-costs 6000
```

## Plot Amortization Curves Across Scenarios

```bash
mortgagemodeler plot \
  --scenarios 400000 6.5 360 \
  --scenarios 400000 5.5 360
```

---

Add your own custom `--rate-file` CSVs or forward curves to simulate realistic ARM/HELOC behavior.
