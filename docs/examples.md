# Examples and Recipes

This page demonstrates practical usage of the mortgage CLI toolkit across a variety of common scenarios: fixed-rate loans, adjustable-rate structures, FHA/USDA government-backed products, and common financial decisions like recasting or refinancing.

---

## Basic Fixed-Rate Loan

```bash
mortgage amortize \
  --type fixed \
  --balance 350000 \
  --rate 5.75 \
  --term 360
```

Generates a standard 30-year amortization schedule with level payments.

---

## FHA Loan With MIP

```bash
mortgage amortize \
  --type fha \
  --balance 275000 \
  --rate 6.125 \
  --term 360
```

Includes upfront and monthly FHA mortgage insurance premiums (MIP).

---

## Loan With Extra Principal Payments

```bash
mortgage amortize \
  --type fixed \
  --balance 450000 \
  --rate 6.25 \
  --term 360 \
  --extra-payment 300 \
  --extra-frequency monthly
```

Accelerates amortization and reduces total interest.

---

## Simulating a Recast

```bash
mortgage amortize \
  --type fixed \
  --balance 300000 \
  --rate 6.0 \
  --term 360 \
  --recast-date 2027-06-01 \
  --lump-sum 25000
```

Applies a lump sum recast 2 years in, reducing monthly payments.

---

## Refinance Scenario

```bash
mortgage amortize \
  --type fixed \
  --balance 400000 \
  --rate 6.5 \
  --term 360 \
  --refinance-date 2028-01-01 \
  --new-rate 5.25 \
  --new-term 300 \
  --refi-fees 5000
```

Refinance into a lower rate with closing costs added to the new loan.

---

## Compare Effective APR With Discount Points

```bash
mortgage compare-apr \
  --principal 400000 \
  --rate 6.5 \
  --term 360 \
  --points 1.0 \
  --fees 3000
```

Shows how buying points affects cost of borrowing.

---

## Refinance Breakeven Calculation

```bash
mortgage breakeven \
  --monthly-savings 175 \
  --closing-costs 4000
```

Returns the number of months to breakeven on a refinance.

---

## Compare Scenarios (Graph)

```bash
mortgage plot \
  --scenarios 400000 6.5 360 \
  --scenarios 400000 5.5 360 \
  --scenarios 400000 4.5 180
```

Visually compares multiple amortization curves.

---

## Saving CSV Output

```bash
mortgage amortize \
  --type fixed \
  --balance 400000 \
  --rate 6.25 \
  --term 360 \
  --output examples/loan_fixed_400k.csv
```

---

See the [loan_types](loan_types.md) page for a summary of all supported products.
