from click.testing import CliRunner

from mortgagemodeler.cli import cli


def run(*args):
    return CliRunner().invoke(cli, list(args))


class TestAmortize:
    def test_fixed_loan_outputs_schedule(self):
        r = run("amortize", "--balance", "400000", "--rate", "6.25", "--term", "360",
                "--start-date", "2025-01-01")
        assert r.exit_code == 0, r.output
        assert "$2,462.87" in r.output

    def test_arm_requires_structure(self):
        r = run("amortize", "--balance", "400000", "--rate", "5.25", "--term", "360",
                "--type", "arm", "--index", "SOFR")
        assert r.exit_code != 0
        assert "arm-structure" in r.output

    def test_arm_with_curve_and_recast(self):
        r = run("amortize", "--type", "arm", "--balance", "800000", "--rate", "5.25",
                "--term", "360", "--margin", "2.5", "--arm-structure", "3/1",
                "--index", "SOFR", "--start-date", "2025-07-01",
                "--index-curve", '{"2027-07-01": 4.0}',
                "--curtailments", "300000@42", "--recast-month", "45", "--months", "60")
        assert r.exit_code == 0, r.output

    def test_lump_sum_requires_recast(self):
        r = run("amortize", "--balance", "400000", "--rate", "6.25", "--term", "360",
                "--lump-sum", "50000")
        assert r.exit_code != 0
        assert "recast" in r.output

    def test_lump_sum_recast_lowers_payment(self):
        r = run("amortize", "--balance", "400000", "--rate", "6.25", "--term", "360",
                "--start-date", "2025-01-01", "--recast-month", "24",
                "--lump-sum", "100000", "--months", "36")
        assert r.exit_code == 0, r.output
        # Payment after recast should be well below the original 2462.87
        assert "$1,8" in r.output

    def test_refinance_uses_amortized_balance(self):
        r = run("amortize", "--balance", "400000", "--rate", "6.25", "--term", "360",
                "--start-date", "2025-01-01", "--refinance-date", "2030-01-01",
                "--new-rate", "5.0", "--months", "12")
        assert r.exit_code == 0, r.output
        # Balance at month 60 is ~373.5k, so the refi schedule must start
        # below 375k, not at the original 400k.
        assert "$400,000.00" not in r.output

    def test_show_apr(self):
        r = run("amortize", "--balance", "400000", "--rate", "6.25", "--term", "360",
                "--points", "1.0", "--refi-fees", "4500", "--show-apr")
        assert r.exit_code == 0, r.output
        assert "Effective APR:" in r.output


class TestSimpleCommands:
    def test_payment(self):
        r = run("payment", "--balance", "400000", "--rate", "6.25", "--term", "360")
        assert r.exit_code == 0
        assert "2462.87" in r.output

    def test_breakeven(self):
        r = run("breakeven", "--monthly-savings", "150", "--closing-costs", "4500")
        assert r.exit_code == 0, r.output
        assert "30 months" in r.output

    def test_sweep_nper_formula(self):
        r = run("sweep", "--balance", "100000", "--rate", "6.0", "--monthly", "1000")
        assert r.exit_code == 0, r.output
        assert "139 months" in r.output

    def test_sweep_payment_too_low(self):
        r = run("sweep", "--balance", "100000", "--rate", "6.0", "--monthly", "400")
        assert r.exit_code == 0
        assert "never" in r.output

    def test_compare_apr(self):
        r = run("compare-apr", "--principal", "400000", "--rate", "6.25",
                "--term", "360", "--points", "1.0", "--fees", "4500")
        assert r.exit_code == 0
        assert "Effective APR:" in r.output
