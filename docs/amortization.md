# Amortization Engine

The amortization engine is the core of the loan simulator. It generates month-by-month breakdowns of principal, interest, insurance, and balance.

---

## Monthly Schedule

For each loan, the amortizer calculates:

- **Beginning Balance**: Outstanding principal at the start of the month
- **Scheduled Payment**: Fixed or recalculated payment due
- **Interest Component**: Based on daily rate × balance
- **Principal Component**: Payment minus interest
- **PMI / MIP**: Mortgage insurance for FHA/USDA if applicable
- **Ending Balance**: Balance after applying principal
- **Date**: Computed from the loan start and calendar logic

---

## Example Output

```text
| Month | Date       | Beginning Balance | Payment | Principal | Interest | PMI/MIP | Ending Balance |
|-------|------------|------------------:|--------:|----------:|---------:|--------:|----------------:|
| 1     | 2025-07-01 |          400,000  | 2,398.20|   398.20  | 2,000.00 |     0.00|      399,602.00 |
```

---

## Compounding Conventions

By default, the amortizer uses `30E/360` (standard mortgage convention), but other methods like `ACT/365` may be introduced later.

---

## Extra Payments

You can simulate accelerated payoff by specifying:

- `--extra-payment 200`
- `--extra-frequency monthly` or `biweekly`

These extra principal contributions reduce the ending balance faster and shorten the loan term.

---

## Recasting

Recasting reduces the monthly payment after a **lump-sum** principal injection.

```bash
mortgage amortize --recast-date 2027-01-01 --lump-sum 10000
```

- Payment is recomputed over the **remaining term**
- Interest savings are realized immediately

---

## Refinancing

The engine can simulate a **refi** mid-stream:

```bash
mortgage amortize --refinance-date 2027-01-01 --new-rate 5.25 --new-term 300 --refi-fees 2500
```

This closes out the current loan and starts a new one with the updated parameters, optionally rolling closing costs into the balance.

---

## PMI, MIP, USDA Fees

Depending on loan type:

- **FHA**: 1.75% upfront MIP added to loan; 0.85% annual MIP paid monthly
- **USDA**: 1.00% upfront guarantee fee + 0.35% annual fee
- **VA**: 2.25% funding fee added to loan; no monthly PMI

These are automatically modeled by the `Loan` class at instantiation.

---

## Visualization

To view your amortization curve:

```bash
mortgage plot --scenarios 400000 6.0 360 --scenarios 400000 5.25 360
```

This compares remaining balances over time across scenarios.

---

## Output

Use `--output schedule.csv` to export the full amortization schedule to CSV for further analysis.

---

📎 Next: [Scenario Comparisons](scenarios.md)
