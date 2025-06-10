import click
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import json
import pandas as pd

from mortgagemodeler import Loan, LoanAmortizer
from mortgagemodeler.utils import (
    effective_apr,
    plot_amortization_curve,
    compare_scenarios,
    breakeven_analysis,
    parse_curtailments
)

load_dotenv()

PRODUCT_MAP = {
    "3/6": (3, 6),
    "3/1": (3, 12),
    "5/1": (5, 12),
    "5/6": (5, 6),
    "5/5": (5, 60),
    "7/6": (7, 6),
    "7/1": (7, 12),
    "10/6": (10, 6),
    "10/1": (10, 12)
}

@click.group(help="""
Mortgage Tools CLI

Model fixed, ARM, FHA, VA, USDA, and HELOC loans — including amortization, recast, refinance,
APR comparison, and breakeven analysis.

Example usage:
  mortgage amortize --type fixed --balance 400000 --rate 6.0 --term 360
  mortgage plot --scenarios 400000 6.0 360 --scenarios 400000 5.5 360
""")
def cli():
    pass

@cli.command("amortize", help="Generate amortization schedule with support for extra payments, recast, refinance, JSON output, plots, effective APR, and financed discount points.")
@click.option('--balance', type=float, required=True, help="Initial loan balance before points.")
@click.option('--rate', type=float, required=True, help="Annual interest rate (nominal APR).")
@click.option('--term', type=int, required=True, help="Loan term in months.")
@click.option('--type', 'loan_type', type=click.Choice(['fixed', 'arm', 'heloc', 'fha', 'va', 'usda']), default='fixed', help="Loan type.")
@click.option('--index', default=None, help="Index name (e.g. SOFR) for ARM or HELOC.")
@click.option('--margin', type=float, default=0.0, help="Margin for ARM/HELOC.")
@click.option('--arm-structure',type=str,default=None,help="ARM structure as 'X/Y' where X is fixed period in years and Y is reset frequency in months. Example: '5/6' for a 5/6 ARM.")
@click.option('--caps', nargs=3, type=float, default=(2.0, 1.0, 5.0), help="ARM caps: initial, periodic, lifetime.")
@click.option('--floors', nargs=3, type=float, default=(0.0, 0.0, 0.0), help="ARM floors: initial, periodic, lifetime.")
@click.option('--draw-period', type=int, default=120, help="Draw period for HELOC.")
@click.option('--repayment-term', type=int, default=240, help="Repayment term for HELOC.")
@click.option('--start-date', default=None, help="Origination date in YYYY-MM-DD format. Defaults to today.")
@click.option('--extra-payment', type=float, default=0.0, help="Extra recurring monthly payment.")
@click.option('--curtailments', type=str, default=None,help="Comma-separated extra payments like '100000@73,50000@85'.")
@click.option('--extra-frequency', type=click.Choice(['monthly', 'biweekly']), default='monthly', help="Frequency of extra payments.")
@click.option('--recast-date', default=None, help="Date to recast loan (YYYY-MM-DD).")
@click.option('--recast-month', type=int, default=None, help="Month to recast loan (relative to start, e.g. 43). Overrides --recast-date.")
@click.option('--lump-sum', type=float, default=0.0, help="Lump sum applied at recast.")
@click.option('--refinance-date', default=None, help="Date of refinance (YYYY-MM-DD).")
@click.option('--new-rate', type=float, default=None, help="New interest rate for refinance.")
@click.option('--new-term', type=int, default=None, help="New loan term in months for refinance.")
@click.option('--refi-fees', type=float, default=0.0, help="Closing costs added at refinance.")
@click.option('--points', type=float, default=0.0, help="Discount points paid upfront as % of loan balance.")
@click.option('--finance-points', is_flag=True, default=False, help="Roll points into loan balance if set.")
@click.option('--show-apr', is_flag=True, default=False, help="Display effective APR in CLI output.")
@click.option('--output', default=None, help="Path to save amortization CSV.")
@click.option('--json-output', type=click.Path(), default=None, help="Path to save amortization JSON.")
@click.option('--plot', is_flag=True, help="Display amortization plot.")
@click.option('--start-month', type=int, default=1, help="Start amortization from this month (default: 1).")
@click.option('--starting-balance', type=float, default=None, help="Loan balance at start-month (default: original balance).")
@click.option('--starting-date', default=None, help="Start date override in YYYY-MM-DD (default: origination date).")
@click.option('--index-curve', type=str, default=None, help="Inline JSON of date:rate pairs (e.g. '{\"2030-07-01\": 6.25, \"2031-07-01\": 6.75}').")
@click.option('--index-curve-file', type=click.Path(exists=True), default=None, help="Optional CSV or JSON with custom date:rate schedule.")
@click.option('--balloon-month', type=int, default=None, help="Month at which a balloon payment is due. Schedule stops and balance is due.")
@click.option('--months', type=int, default=None, help="Limit output to first N months")




def amortize(**kwargs):
    start = datetime.strptime(kwargs['start_date'], '%Y-%m-%d').date() if kwargs['start_date'] else datetime.today().date()
    principal = Decimal(str(kwargs['balance']))

    if kwargs.get('points', 0.0) > 0.0 and kwargs.get('finance_points', False):
        principal += principal * Decimal(str(kwargs['points'])) / Decimal("100")


    arm_key = kwargs.get('arm_structure')
    if arm_key and arm_key not in PRODUCT_MAP:
            raise click.BadParameter(f"Unknown ARM structure '{arm_key}'. Allowed values: {', '.join(PRODUCT_MAP.keys())}")

    caps = kwargs['caps']
    floors = kwargs['floors']
    index_curve = {}

    # Load curve from file or inline JSON (you already do this below, but we need it now)
    if kwargs['index_curve_file']:
        if kwargs['index_curve_file'].endswith('.csv'):
            df = pd.read_csv(kwargs['index_curve_file'])
            if 'date' not in df.columns or 'rate' not in df.columns:
                raise click.ClickException("CSV must have 'date' and 'rate' columns.")
            index_curve = dict(zip(df['date'].astype(str), df['rate'].astype(float)))
        elif kwargs['index_curve_file'].endswith('.json'):
            with open(kwargs['index_curve_file']) as f:
                index_curve_raw = json.load(f)
            index_curve = {k.strip(): float(v) for k, v in index_curve_raw.items()}
    if kwargs.get('index_curve'):
        try:
            index_curve = {k.strip(): float(v) for k, v in json.loads(kwargs['index_curve']).items()}
        except Exception as e:
            raise click.ClickException(f"Invalid index-curve JSON: {e}")

    # Construct the Loan object
    if kwargs['loan_type'] == 'arm':
        if not kwargs['index']:
            raise click.BadParameter("ARM loans require --index to be specified.")

        if not kwargs.get('caps') or kwargs['caps'] == (2.0, 1.0, 5.0):
            click.echo("Using default ARM caps: Initial=2.0%, Periodic=1.0%, Lifetime=5.0%")
        else:
            click.echo(f"ARM caps used: Initial={caps[0]}%, Periodic={caps[1]}%, Lifetime={caps[2]}%")

        if not kwargs.get('floors') or kwargs['floors'] == (0.0, 0.0, 0.0):
            click.echo("Using default ARM floors: Initial=0.0%, Periodic=0.0%, Lifetime=0.0%")
        else:
            click.echo(f"ARM floors used: Initial={floors[0]}%, Periodic={floors[1]}%, Lifetime={floors[2]}%")


        # Use user-provided rate only if they intend to override
        user_rate = Decimal(str(kwargs['rate'])) if 'rate' in kwargs and kwargs['rate'] is not None else None

        loan = Loan.from_arm(
            principal=principal,
            term=kwargs['term'],
            arm_type=kwargs['arm_structure'],
            index=kwargs['index'],
            margin=kwargs['margin'],
            origination_date=start,
            rate=user_rate,
            caps=caps,
            floors=floors,
            forward_curve=index_curve
        )
    elif kwargs['loan_type'] == 'heloc':
        loan = Loan(
            principal=principal,
            term_months=kwargs['term'],
            rate=Decimal(str(kwargs['rate'])),
            origination_date=start,
            loan_type='heloc',
            compounding='30E/360',
            draw_period_months=kwargs['draw_period'],
            repayment_term_months=kwargs['repayment_term'],
            extra_payment_amount=kwargs['extra_payment'],
            extra_payment_frequency=kwargs['extra_frequency'],
            margin=Decimal(str(kwargs['margin']))
        )
        loan.index = kwargs['index']
        loan.forward_curve = index_curve
        loan.rate_bounds.update({
            'initial_cap': Decimal(str(caps[0])),
            'periodic_cap': Decimal(str(caps[1])),
            'lifetime_cap': Decimal(str(caps[2])),
            'initial_floor': Decimal(str(floors[0])),
            'periodic_floor': Decimal(str(floors[1])),
            'lifetime_floor': Decimal(str(floors[2])),
        })
    else:
        # Fixed, FHA, VA, USDA
        loan = Loan(
            principal=principal,
            term_months=kwargs['term'],
            rate=Decimal(str(kwargs['rate'])),
            origination_date=start,
            loan_type=kwargs['loan_type'],
            compounding='30E/360',
            extra_payment_amount=kwargs['extra_payment'],
            extra_payment_frequency=kwargs['extra_frequency']
        )


    recast_schedule = {}

    if kwargs['recast_month'] is not None:
        recast_schedule[kwargs['recast_month']] = kwargs['term'] - kwargs['recast_month'] + 1
    elif kwargs['recast_date']:
        recast_date = datetime.strptime(kwargs['recast_date'], '%Y-%m-%d').date()
        recast_month = (recast_date.year - start.year) * 12 + (recast_date.month - start.month) + 1
        recast_schedule[recast_month] = kwargs['term'] - recast_month + 1

    if kwargs['refinance_date'] and kwargs['new_rate'] is not None:
        loan = loan.refinance(
            new_rate=kwargs['new_rate'],
            refinance_date=datetime.strptime(kwargs['refinance_date'], '%Y-%m-%d').date(),
            new_term=kwargs['new_term'],
            fees=kwargs['refi_fees']
        )


    curtailments = parse_curtailments(kwargs['curtailments']) if kwargs['curtailments'] else {}

    amortizer = LoanAmortizer(
        loan,
        custom_rate_schedule={},
        start_month=kwargs['start_month'],
        starting_balance=kwargs['starting_balance'],
        starting_date=datetime.strptime(kwargs['starting_date'], '%Y-%m-%d').date() if kwargs['starting_date'] else None,
        balloon_month=kwargs.get('balloon_month'),
        curtailments=curtailments,
        recast_schedule= recast_schedule
    )

    df = amortizer.to_dataframe()

    # Format currency columns with $ and commas
    currency_cols = [
        "Payment", "Principal", "Interest", "PMI/MIP", "Extra Payment",
        "Total Payment", "Beginning Balance", "Ending Balance"
    ]
    for col in currency_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"${x:,.2f}")

    trunc_df = df.copy()
    if kwargs['months']:
        trunc_df = trunc_df[trunc_df['Month'] <= kwargs['months']]

    # Display full if months provided, otherwise show first 12 rows
    display_df = trunc_df if kwargs.get("months") else df.head(12)

    # Output as Markdown
    click.echo(display_df.to_markdown(index=False))

    if kwargs['points'] > 0.0 or kwargs['refi_fees'] > 0.0 or kwargs['show_apr']:
        net_proceeds = Decimal(str(kwargs['balance']))
        if not kwargs['finance_points']:
            net_proceeds -= Decimal(str(kwargs['balance'])) * Decimal(str(kwargs['points'])) / Decimal("100")
        net_proceeds -= Decimal(str(kwargs['refi_fees']))
        apr = effective_apr(net_proceeds, kwargs['rate'], kwargs['term'], kwargs['points'], kwargs['refi_fees'])
        click.echo(f"Effective APR: {apr:.4f}%")

    if kwargs['output']:
        amortizer.to_csv(kwargs['output'])
        click.echo(f"Saved CSV to {kwargs['output']}")

    if kwargs['json_output']:
        df.to_json(kwargs['json_output'], orient='records', indent=2)
        click.echo(f"Saved JSON to {kwargs['json_output']}")

    if kwargs['plot']:
        plot_amortization_curve(df)
        plt.show()
    

@cli.command("compare-apr", help="Compare effective APR accounting for points and fees.")
@click.option('--principal', type=float, required=True, help="Loan amount.")
@click.option('--rate', type=float, required=True, help="Nominal APR.")
@click.option('--term', type=int, required=True, help="Loan term in months.")
@click.option('--points', type=float, default=0.0, help="Discount points as percent.")
@click.option('--fees', type=float, default=0.0, help="Additional closing costs.")
def compare_apr_cmd(principal, rate, term, points, fees):
    apr = effective_apr(principal, rate, term, points, fees)
    click.echo(f"Effective APR: {apr:.4f}%")

@cli.command("breakeven", help="Compute breakeven point (in months) for refinancing.")
@click.option('--monthly-savings', type=float, required=True, help='Monthly savings after refinance.')
@click.option('--closing-costs', type=float, required=True, help='One-time refinance closing costs.')
def breakeven_cmd(monthly_savings, closing_costs):
    month, net_savings, monthly = breakeven_analysis(monthly_savings, closing_costs)
    click.echo(f"Breakeven reached in: {month} months (Net savings: ${net_savings:.2f})")

@cli.command("plot", help="Compare amortization curves for multiple loan scenarios.")
@click.option('--scenarios', type=(float, float, int), multiple=True, required=True,
              help='Each scenario is (balance, rate, term). Specify multiple times.')
def plot_cmd(scenarios):
    loans = [
        Loan(principal=Decimal(str(p)), rate=Decimal(str(r)), term_months=t,
             origination_date=datetime.today().date()) for (p, r, t) in scenarios
    ]
    dfs = [LoanAmortizer(loan).to_dataframe() for loan in loans]
    compare_scenarios(*dfs)
    plt.show()

# --- NEW SUBCOMMANDS ---

@cli.command("payment", help="Show fixed monthly payment given rate, balance, and term.")
@click.option('--balance', type=float, required=True)
@click.option('--rate', type=float, required=True)
@click.option('--term', type=int, required=True)
def payment_cmd(balance, rate, term):
    r = Decimal(rate) / Decimal("100") / Decimal("12")
    pmt = Decimal(balance) * r / (1 - (1 + r) ** -term)
    click.echo(f"Monthly Payment: ${pmt.quantize(Decimal('0.01'))}")

@cli.command("recast", help="Recast loan balance with optional new term.")
@click.option('--balance', type=float, required=True)
@click.option('--rate', type=float, required=True)
@click.option('--term', type=int, required=False)
def recast_cmd(balance, rate, term):
    r = Decimal(rate) / Decimal("100") / Decimal("12")
    t = term if term else 360
    pmt = Decimal(balance) * r / (1 - (1 + r) ** -t)
    click.echo(f"Recast Payment: ${pmt.quantize(Decimal('0.01'))} (Term: {t} months)")

@cli.command("sweep", help="Sweep balance using fixed monthly amount to determine payoff term.")
@click.option('--balance', type=float, required=True)
@click.option('--rate', type=float, required=True)
@click.option('--monthly', type=float, required=True)
def sweep_cmd(balance, rate, monthly):
    r = Decimal(rate) / Decimal("100") / Decimal("12")
    p = Decimal(monthly)
    if p <= Decimal(balance) * r:
        click.echo("Payment too low to cover interest. Balance will never be paid off.")
        return
    n = -(Decimal("1") / r) * (1 - (Decimal(balance) * r / p)).ln() / (1 + r).ln()
    click.echo(f"Balance paid off in: {int(n)} months")

if __name__ == '__main__':
    cli()
