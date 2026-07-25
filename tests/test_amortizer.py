from datetime import date
from decimal import Decimal

import pytest

from mortgagemodeler import Loan, LoanAmortizer


ORIG = date(2025, 1, 1)


class TestFixedLoan:
    def test_payment_matches_closed_form(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        df = LoanAmortizer(loan).to_dataframe()
        assert df.iloc[0]["Payment"] == pytest.approx(2462.87, abs=0.01)

    def test_full_payoff_at_term(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        df = LoanAmortizer(loan).to_dataframe()
        assert len(df) == 360
        assert df.iloc[-1]["Ending Balance"] == 0.0

    def test_extra_payment_shortens_term(self):
        loan = Loan(400000, 360, 6.25, ORIG,
                    extra_payment_amount=200, extra_payment_frequency="monthly")
        df = LoanAmortizer(loan).to_dataframe()
        assert df.iloc[-1]["Month"] < 360
        assert df.iloc[-1]["Ending Balance"] == 0.0

    def test_biweekly_extra_is_26_over_12_equivalent(self):
        loan = Loan(400000, 360, 6.25, ORIG,
                    extra_payment_amount=100, extra_payment_frequency="biweekly")
        df = LoanAmortizer(loan).to_dataframe()
        assert df.iloc[0]["Extra Payment"] == pytest.approx(216.67, abs=0.01)


class TestMidLifeEntry:
    def test_payment_amortizes_remaining_term(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        am = LoanAmortizer(loan, start_month=121, starting_balance=300000)
        df = am.to_dataframe()
        # 300k over the remaining 240 months @ 6.25% is ~2192.83/mo
        assert df.iloc[0]["Payment"] == pytest.approx(2192.83, abs=0.05)
        assert df.iloc[-1]["Month"] == 360
        assert df.iloc[-1]["Ending Balance"] == 0.0


class TestArmRateBehavior:
    def make_arm(self, caps=(5, 1, 6), curve=None, rate=4.0, margin=3.0):
        return Loan.from_arm(400000, 360, "3/1", "SOFR", margin, ORIG,
                             rate=rate, caps=caps, forward_curve=curve or {})

    def test_initial_cap_governs_first_reset(self):
        # Index 9.0 + margin 3.0 = 12.0 proposed; initial cap 5 allows 4->9.
        arm = self.make_arm(curve={"2025-01-01": 1.0, "2027-06-01": 9.0})
        df = LoanAmortizer(arm).to_dataframe()
        by_month = df.set_index("Month")["Effective Rate"]
        assert by_month[36] == 4.0
        assert by_month[37] == 9.0

    def test_periodic_cap_governs_later_resets_and_lifetime_ceiling_holds(self):
        arm = self.make_arm(curve={"2025-01-01": 1.0, "2027-06-01": 9.0})
        df = LoanAmortizer(arm).to_dataframe()
        by_month = df.set_index("Month")["Effective Rate"]
        assert by_month[49] == 10.0          # 9 + periodic cap 1, == ceiling
        assert by_month[61] == 10.0          # lifetime ceiling 4 + 6
        assert df["Effective Rate"].max() <= 10.0

    def test_rates_can_fall_below_initial_rate(self):
        # Proposed 1.0 + 2.0 = 3.0; initial rate 6.0. Floors default to 0,
        # so the rate steps down by the caps each reset.
        arm = Loan.from_arm(400000, 360, "3/1", "SOFR", 2.0, ORIG, rate=6.0,
                            caps=(2, 1, 5), forward_curve={"2026-01-01": 1.0})
        df = LoanAmortizer(arm).to_dataframe()
        by_month = df.set_index("Month")["Effective Rate"]
        assert by_month[37] == 4.0   # first reset: -2 (initial cap)
        assert by_month[49] == 3.0   # second reset: -1 (periodic cap), floor 0
        assert by_month[61] == 3.0   # at proposed rate now

    def test_payment_recalculates_on_reset(self):
        arm = self.make_arm(curve={"2025-01-01": 1.0, "2027-06-01": 9.0})
        df = LoanAmortizer(arm).to_dataframe()
        by_month = df.set_index("Month")["Payment"]
        assert by_month[37] > by_month[36]


class TestHeloc:
    def make_heloc(self, curve, lifetime_cap="5.0"):
        h = Loan(100000, 360, 7.0, ORIG, loan_type="heloc",
                 draw_period_months=12, repayment_term_months=348)
        h.index = "SOFR"
        h.forward_curve = curve
        h.rate_bounds["lifetime_cap"] = Decimal(lifetime_cap)
        return h

    def test_draw_phase_is_interest_only(self):
        h = self.make_heloc({})
        df = LoanAmortizer(h).to_dataframe()
        draw = df[df["Month"] <= 12]
        assert (draw["Principal"] == 0.0).all()
        assert (draw["Payment"] == draw["Interest"]).all()

    def test_lifetime_cap_clamps_repricing(self):
        # Curve proposes 15%; ceiling is initial 7 + cap 5 = 12.
        h = self.make_heloc({"2025-06-01": 15.0})
        df = LoanAmortizer(h).to_dataframe()
        assert df["Effective Rate"].max() == 12.0

    def test_pays_off_by_end_of_repayment(self):
        h = self.make_heloc({})
        df = LoanAmortizer(h).to_dataframe()
        assert df.iloc[-1]["Ending Balance"] == 0.0


class TestCurtailmentAndRecast:
    def test_curtailment_reduces_balance_and_interest(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        base = LoanAmortizer(loan).to_dataframe().set_index("Month")
        cur = LoanAmortizer(loan, curtailments={12: 50000}).to_dataframe().set_index("Month")
        assert cur.loc[12, "Ending Balance"] < base.loc[12, "Ending Balance"] - 49000
        assert cur.loc[12, "Interest"] < base.loc[12, "Interest"]

    def test_recast_after_curtailment_lowers_payment(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        am = LoanAmortizer(loan, curtailments={42: 100000},
                           recast_schedule={45: 360 - 45 + 1})
        df = am.to_dataframe().set_index("Month")
        assert df.loc[46, "Payment"] < df.loc[41, "Payment"]
        assert df.iloc[-1]["Ending Balance"] == 0.0


class TestBalloon:
    def test_balloon_stops_schedule(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        am = LoanAmortizer(loan, balloon_month=60)
        df = am.to_dataframe()
        assert df.iloc[-1]["Month"] == 60
        assert am.early_payoff_month == 60
        assert df.iloc[-1]["Ending Balance"] > 0


class TestInsurance:
    def test_fha_monthly_mip_charged(self):
        fha = Loan(400000, 360, 6.0, ORIG, loan_type="fha")
        df = LoanAmortizer(fha).to_dataframe()
        assert df.iloc[0]["PMI/MIP"] > 0

    def test_pmi_drops_at_78_ltv(self):
        loan = Loan(400000, 360, 6.25, ORIG, pmi=True)
        df = LoanAmortizer(loan).to_dataframe()
        assert df.iloc[0]["PMI/MIP"] > 0
        assert df.iloc[-1]["PMI/MIP"] == 0.0


class TestDayCount:
    def test_actual_365_accrues_more_in_31_day_month(self):
        # Jan 2025 has 31 days: A/365F should accrue 31/365.
        loan = Loan(400000, 360, 6.25, ORIG, compounding="A/365F")
        df = LoanAmortizer(loan).to_dataframe()
        expected = 400000 * 0.0625 * 31 / 365
        assert df.iloc[0]["Interest"] == pytest.approx(expected, abs=0.01)

    def test_30e_360_uses_flat_30_days(self):
        loan = Loan(400000, 360, 6.25, ORIG, compounding="30E/360")
        df = LoanAmortizer(loan).to_dataframe()
        expected = 400000 * 0.0625 * 30 / 360
        assert df.iloc[0]["Interest"] == pytest.approx(expected, abs=0.01)
