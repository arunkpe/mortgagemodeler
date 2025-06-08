import click
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
import matplotlib.pyplot as plt

from mortgage_tools import Loan, LoanAmortizer
from utils import (
    effective_apr,
    plot_amortization_curve,
    compare_scenarios,
    breakeven_analysis
)

load_dotenv()

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

@cli.command("amortize", help="Generate amortization schedule with support for extra payments, recast, and refinance.")
@click.option('--balance', type=float, required=True, help="Initial loan balance.")
@click.option('--rate', type=float, required=True, help="Annual interest rate (nominal APR).")
@click.option('--term', type=int, required=True, help="Loan term in months.")
@click.option('--type', 'loan_type', type=click.Choice(['fixed', 'arm', 'heloc', 'fha', 'va', 'usda']), default='fixed', help="Loan type.")
@click.option('--index', default=None, help="Index name (e.g. SOFR) for ARM or HELOC.")
@click.option('--margin', type=float, default=0.0, help="Margin for ARM/HELOC.")
@click.option('--draw-period', type=int, default=120, help="Draw period for HELOC.")
@click.option('--repayment-term', type=int, default=240, help="Repayment term for HELOC.")
@click.option('--start-date', default=None, help="Start date in YYYY-MM-DD format. Defaults to today.")
@click.option('--extra-payment', type=float, default=0.0, help="Extra monthly payment.")
@click.option('--extra-frequency', type=click.Choice(['monthly', 'biweekly']), default='monthly', help="Frequency of extra payment.")
@click.option('--recast-date', default=None, help="Date to recast loan (YYYY-MM-DD).")
@click.option('--lump-sum', type=float, default=0.0, help="Lump sum for recast.")
@click.option('--refinance-date', default=None, help="Date of refinance (YYYY-MM-DD).")
@click.option('--new-rate', type=float, default=None, help="New interest rate for refinance.")
@click.option('--new-term', type=int, default=None, help="New loan term in months for refinance.")
@click.option('--refi-fees', type=float, default=0.0, help="Closing costs for refinance.")
@click.option('--output', default=None, help="Path to save amortization CSV.")
def amortize(**kwargs):
    start = datetime.strptime(kwargs['start_date'], '%Y-%m-%d').date() if kwargs['start_date'] else datetime.today().date()
    loan = Loan(
        principal=Decimal(str(kwargs['balance'])),
        term_months=kwargs['term'],
        rate=Decimal(str(kwargs['rate'])),
        origination_date=start,
        loan_type=kwargs['loan_type'].lower(),
        compounding='30E/360',
        draw_period_months=kwargs['draw_period'] if kwargs['loan_type'] == 'heloc' else None,
        repayment_term_months=kwargs['repayment_term'] if kwargs['loan_type'] == 'heloc' else None,
        extra_payment_amount=kwargs['extra_payment'],
        extra_payment_frequency=kwargs['extra_frequency']
    )

    if kwargs['loan_type'] in ['arm', 'heloc'] and kwargs['index']:
        loan.set_indexed_rate(kwargs['index'], kwargs['margin'])

    if kwargs['recast_date'] and kwargs['lump_sum'] > 0:
        loan.recast(kwargs['lump_sum'], datetime.strptime(kwargs['recast_date'], '%Y-%m-%d').date())

    if kwargs['refinance_date'] and kwargs['new_rate'] is not None:
        loan = loan.refinance(
            new_rate=kwargs['new_rate'],
            refinance_date=datetime.strptime(kwargs['refinance_date'], '%Y-%m-%d').date(),
            new_term=kwargs['new_term'],
            fees=kwargs['refi_fees']
        )

    amortizer = LoanAmortizer(loan)
    df = amortizer.to_dataframe()
    click.echo(df.head(12).to_markdown(index=False))
    if kwargs['output']:
        amortizer.to_csv(kwargs['output'])
        click.echo(f"Saved to {kwargs['output']}")

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

if __name__ == '__main__':
    cli()
