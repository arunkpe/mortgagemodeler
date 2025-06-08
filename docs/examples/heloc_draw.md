# HELOC Draw + Repayment Example

Simulating a $100,000 HELOC with a 10-year interest-only draw and 15-year repayment.

## Loan Parameters

- Type: HELOC
- Balance: $100,000
- Index: SOFR
- Margin: 2.5%
- Draw Period: 120 months (10 years)
- Repayment Term: 180 months
- Total Term: 300 months

## CLI Command

```bash
python -m cli.cli amortize \
  --type heloc \
  --balance 100000 \
  --rate 6.5 \
  --term 300 \
  --index SOFR \
  --margin 2.5 \
  --draw-period 120 \
  --repayment-term 180
```

## Timeline

<li> Draw Phase (0–120 months): Interest-only payments
<li> Repayment Phase (121–300 months): Fully amortizing principal + interest



