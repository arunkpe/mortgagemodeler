# Command Line Interface (CLI)

The toolkit includes a powerful CLI for simulating amortization schedules, comparing refinance options, and visualizing scenarios. Install dependencies and run the CLI directly.

---

## Getting Started

Once installed (see [README](index.md)), you can invoke the CLI:

```bash
python -m cli.cli [command] [options]
```

Or install a shortcut entry point:

```bash
pip install -e .
mortgage --help
```

---

## Available Commands

| Command            | Purpose                                   |
|--------------------|-------------------------------------------|
| `amortize`         | Generate amortization schedule            |
| `compare-apr`      | Compute effective APR with points/fees    |
| `breakeven`        | Evaluate refinance breakeven month        |
| `plot`             | Compare multiple loan scenarios visually  |

---

## Amortization Example

```bash
mortgage amortize \
  --type fixed \
  --balance 400000 \
  --rate 6.0 \
  --term 360
```

Generates a monthly amortization schedule and shows first 12 rows.

---

## Recast and Refinance

Add optional flags to simulate real-world events:

```bash
mortgage amortize \
  --type fixed \
  --balance 400000 \
  --rate 6.0 \
  --term 360 \
  --extra-payment 300 \
  --recast-date 2027-01-01 \
  --lump-sum 10000 \
  --refinance-date 2029-07-01 \
  --new-rate 5.25 \
  --new-term 240
```

---

## Effective APR Comparison

```bash
mortgage compare-apr \
  --principal 400000 \
  --rate 6.0 \
  --term 360 \
  --points 1.0 \
  --fees 2500
```

Returns the **effective APR** based on net loan proceeds and IRR.

---

## Breakeven Analysis

```bash
mortgage breakeven \
  --monthly-savings 180 \
  --closing-costs 3500
```

Tells you how many months it takes for the refinance savings to break even.

---

## Multi-Scenario Comparison

```bash
mortgage plot \
  --scenarios 400000 6.0 360 \
  --scenarios 400000 5.25 360 
```

Visually compares principal and interest paths across loan structures.

---

## Output Options

- `--output FILE.csv` saves amortization to disk
- `--start-date YYYY-MM-DD` controls loan origination date
- `--extra-frequency [monthly|biweekly]` for recurring extra payments

---

📎 Next: [Examples and Recipes](examples.md)
