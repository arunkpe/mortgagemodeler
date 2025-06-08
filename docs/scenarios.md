# Scenario Comparison and Analytics

Beyond single-loan amortization, the toolkit supports multi-scenario comparison and financial analytics for evaluating refinance, recast, or early payoff strategies.

---

## 🔁 Multi-Scenario Plotting

You can compare how multiple loan structures perform over time using:

```bash
mortgage plot --scenarios 400000 6.0 360 --scenarios 400000 5.25 360 --scenarios 400000 4.5 180
```

Each scenario is a tuple of:

- **Balance** (e.g. 400000)
- **Interest Rate** (e.g. 5.5%)
- **Term in Months** (e.g. 360)

📈 The output is a plot comparing balance trajectories across all scenarios.

---

## 💡 Breakeven Analysis

This tool estimates when a refinance or lump sum recast becomes financially beneficial:

```bash
mortgage breakeven --monthly-savings 185 --closing-costs 4000
```

Outputs:

```text
Breakeven reached in: 22 months
```

Use this to evaluate how long you need to hold the mortgage to recover refi costs.

---

## 📊 Effective APR Comparison

When paying points or closing costs, the nominal interest rate understates true cost. Use:

```bash
mortgage compare-apr --principal 400000 --rate 6.0 --term 360 --points 1.0 --fees 3000
```

This computes the **IRR-based effective APR**, taking upfront cost into account:

```text
Effective APR: 6.2191%
```

---

## 🧠 Use Cases

- Choose between 30-year and 15-year fixed
- Compare rate buydown vs no-points option
- Evaluate impact of biweekly payments
- Quantify refinance timing sensitivity

---

## 🗃️ CLI and API Interoperability

All analytics functions are available:

- From CLI (e.g. `mortgage breakeven`)
- As Python functions (e.g. `breakeven_analysis(...)`)

---

📎 Next: [Command Line Usage](cli.md)
