# Loan Types

This tool supports a range of U.S. mortgage loan types. Each loan has distinct amortization rules, fees, and optional parameters.

---

## Fixed Rate Loans

**Fixed rate loans** maintain the same interest rate over the life of the loan. These are the simplest to model and are ideal for borrowers seeking predictable payments.

- Use with: `--type fixed`
- Optional: `--extra-payment`, `--extra-frequency`

---

## Adjustable Rate Mortgages (ARMs)

**ARMs** begin with a fixed-rate period and then adjust periodically based on an index (e.g. SOFR) plus a margin.

- Use with: `--type arm`
- Configure with: `--index`, `--margin`
- Example: A 5/6 ARM has 5 years fixed, adjusts every 6 months

---

## FHA Loans

**FHA loans** are backed by the Federal Housing Administration. They include:

- Upfront MIP (1.75%) added to principal
- Monthly MIP (0.85% annually by default)
- Lower credit requirements

- Use with: `--type fha`

---

## VA Loans

**VA loans** are for veterans and active-duty military. Features include:

- No PMI
- One-time VA guarantee fee (default 2.25%)
- More flexible underwriting

- Use with: `--type va`

---

## USDA Loans

**USDA loans** support rural homebuyers. They include:

- One-time guarantee fee (1.00% default)
- Annual fee (0.35%) added monthly
- No PMI

- Use with: `--type usda`

---

## HELOCs (Home Equity Line of Credit)

**HELOCs** allow borrowing during a draw period followed by repayment:

- Interest-only draw phase (e.g., 10 years)
- Repayment phase (e.g., 15–20 years)
- Adjustable rates typically tied to PRIME or SOFR

- Use with: `--type heloc`
- Configure draw/repay: `--draw-period`, `--repayment-term`
- ARM-style index support: `--index`, `--margin`

---

## Summary Table

| Loan Type | PMI/MIP | Upfront Fees | Adjustable? | Notes |
|-----------|---------|--------------|-------------|-------|
| Fixed     | Optional| None         | ❌          | Stable and simple |
| ARM       | Optional| None         | ✅          | Rate changes after fixed period |
| FHA       | ✅      | 1.75% MIP     | ❌          | Lower credit, extra fees |
| VA        | ❌      | 2.25% VA Fee  | ❌          | For veterans only |
| USDA      | ❌      | 1.0% Fee + 0.35% annual | ❌ | For rural borrowers |
| HELOC     | ❌      | None         | ✅          | Draw + repay phases |

---

See [CLI Options](index.md) for how to configure each loan type.
