from datetime import date, datetime
from decimal import Decimal

import pytest

from mortgagemodeler import Loan, LoanAmortizer
from mortgagemodeler.utils import (
    breakeven_analysis,
    compare_scenarios,
    cost_until_exit,
    effective_apr,
    normalize_date,
    parse_curtailments,
    summarize_metrics,
)
from mortgagemodeler.utils.rates import RateReader


ORIG = date(2025, 1, 1)


def make_df(principal=400000, rate=6.25, term=360, **kwargs):
    return LoanAmortizer(Loan(principal, term, rate, ORIG, **kwargs)).to_dataframe()


class TestCostUntilExit:
    def test_returns_totals_and_balance(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        am = LoanAmortizer(loan)
        result = cost_until_exit(am, 60)
        assert result["exit_month"] == 60
        assert result["total_paid"] > 0
        assert result["total_interest"] > 0
        assert 0 < result["ending_balance"] < 400000


class TestCompareScenarios:
    def test_two_scenarios(self):
        out = compare_scenarios(make_df(), make_df(rate=5.75))
        assert list(out.index) == ["Scenario 1", "Scenario 2"]
        assert out.loc["Scenario 2", "Total Interest"] < out.loc["Scenario 1", "Total Interest"]

    def test_three_scenarios_with_labels(self):
        out = compare_scenarios(make_df(), make_df(rate=5.75), make_df(term=240),
                                labels=["a", "b", "c"])
        assert len(out) == 3

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            compare_scenarios()


class TestSummarizeMetrics:
    def test_payoff_month_when_paid_off(self):
        metrics = summarize_metrics(make_df())
        assert metrics["Payoff Month"] == 360
        assert metrics["Final Balance"] == 0.0

    def test_payoff_month_when_never_paid_off(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        df = LoanAmortizer(loan, balloon_month=60).to_dataframe()
        metrics = summarize_metrics(df)
        assert metrics["Payoff Month"] == 60  # falls back to max month, not NaN


class TestBreakevenAnalysis:
    def test_breakeven_from_schedules(self):
        base = make_df()
        refi = make_df(rate=5.25)
        out = breakeven_analysis(refi, base, refi_costs=5000)
        assert out["breakeven_month"] is not None
        assert out["breakeven_month"] > 1
        assert out["net_savings"] > 0


class TestEffectiveApr:
    def test_apr_exceeds_nominal_with_costs(self):
        apr = effective_apr(400000, 6.25, 360, points=1.0, fees=4500)
        assert apr > 6.25

    def test_apr_close_to_nominal_without_costs(self):
        apr = effective_apr(400000, 6.25, 360)
        assert apr == pytest.approx(6.43, abs=0.05)  # monthly compounding effect only


class TestParseCurtailments:
    def test_parses_multiple(self):
        out = parse_curtailments("100000@73,50000@85")
        assert out == {73: Decimal("100000"), 85: Decimal("50000")}

    def test_invalid_raises(self):
        import click
        with pytest.raises(click.ClickException):
            parse_curtailments("garbage")


class TestNormalizeDate:
    def test_accepts_str_datetime_date(self):
        assert normalize_date("2025-01-01") == ORIG
        assert normalize_date(datetime(2025, 1, 1, 12, 30)) == ORIG
        assert normalize_date(ORIG) == ORIG

    def test_rejects_other_types(self):
        with pytest.raises(TypeError):
            normalize_date(20250101)


class TestRateReader:
    def test_missing_file_returns_none_not_zero(self):
        with pytest.warns(UserWarning):
            rr = RateReader(filepath="/nonexistent/rates.txt")
        assert rr.get_rate("SOFR", "2025-08-15") is None

    def test_packaged_file_loads_with_generic_rate_fallback(self):
        rr = RateReader()
        assert rr.rates_df is not None
        val = rr.get_rate("SOFR", "2025-08-15")
        assert val is not None
        assert 0 < val < 20

    def test_date_before_first_observation_returns_none(self):
        rr = RateReader()
        assert rr.get_rate("SOFR", "1990-01-01") is None

    def test_unsupported_index_raises(self):
        rr = RateReader()
        with pytest.raises(ValueError):
            rr.get_rate("NOTANINDEX", "2025-08-15")
