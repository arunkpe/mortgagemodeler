# FHA Loan Example (30-Year Fixed)

This example shows the amortization for a $300,000 FHA loan over 30 years with a 6.25% interest rate.

## Loan Parameters

- Type: FHA
- Principal: $300,000
- Term: 360 months (30 years)
- Rate: 6.25%
- FHA Upfront MIP: 1.75%
- Monthly MIP: 0.85%

## CLI Command

```bash
python -m cli.cli amortize \
  --type fha \
  --balance 300000 \
  --rate 6.25 \
  --term 360
```

## Preview 

| Month | Date       | Beginning Balance | Payment | Principal | Interest | PMI/MIP | Total Payment | Ending Balance |
|-------|------------|------------------:|--------:|----------:|---------:|--------:|---------------:|----------------:|
|   1   | YYYY-MM-DD |         305250.00 | 1879.63 |   328.13  | 1586.55  |  35.00  |      1920.63   |      304921.87  |
...

Note: Full amortization table can be exported with --output examples/fha_30yr.csv.
