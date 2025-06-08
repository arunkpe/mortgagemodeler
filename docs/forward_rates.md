# Forward Rates and Indexed Loans

Many modern loan products (especially ARMs and HELOCs) use benchmark interest rates like **SOFR**, **Prime**, or **1-Year CMT** to determine monthly payments. This module supports both static and forward-looking indexed loans via a structured forward rate file.

---

## Supported Indexes

You can model any loan tied to a published index:

- **SOFR (Secured Overnight Financing Rate)**
- **Prime Rate**
- **Treasury CMT (1Y/5Y/7Y/10Y)**
- Custom indexes (e.g., LIBOR, BSBY, Fed Funds) with your own forward curve

---

## Forward Rate File

The model reads `/utils/data/macroeconforward.txt` which should contain:

```
Date	Index1	Index2	...
2025-07-01	5.30	7.75
2025-08-01	5.32	7.75
...
```

Each row represents projected rates for a future month. All values are expressed in **annualized percent**.

---

## Example: ARM With SOFR Index

```bash
mortgage amortize \
  --type arm \
  --index SOFR \
  --margin 2.75 \
  --balance 400000 \
  --rate 6.0 \
  --term 360
```

- `--rate`: used as the initial teaser rate
- `--index`: specifies which forward rate column to use
- `--margin`: added to the index rate for effective interest
- Monthly rates are pulled from the forward file using the loan's payment schedule

---

## Customizing the Curve

To simulate alternate economic environments, simply replace or modify the forward curve in `macroeconforward.txt`.

You can also support historical rate analysis by creating a combined file like:

```
Date        SOFR
2022-01-01  0.05
...
2025-07-01  5.30
```

---

## Common Use Cases

- Adjustable Rate Mortgages (ARMs)
- HELOC repayment modeling
- Forward-looking refinance feasibility
- Rate shock stress testing

---

See [architecture.md](architecture.md) for implementation details and integration options.
