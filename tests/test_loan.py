from datetime import date
from decimal import Decimal

import pytest

from mortgagemodeler import Loan


ORIG = date(2025, 1, 1)


class TestArmResetSchedule:
    def test_5_6_resets_every_6_months_after_60(self):
        arm = Loan.from_arm(400000, 360, "5/6", "SOFR", 2.5, ORIG, rate=5.0)
        resets = [m for m in range(1, 121) if arm.is_reset_month(m)]
        assert resets == [61, 67, 73, 79, 85, 91, 97, 103, 109, 115]

    def test_5_1_resets_annually_after_60(self):
        arm = Loan.from_arm(400000, 360, "5/1", "SOFR", 2.5, ORIG, rate=5.0)
        resets = [m for m in range(1, 121) if arm.is_reset_month(m)]
        assert resets == [61, 73, 85, 97, 109]

    def test_3_1_resets_annually_after_36(self):
        arm = Loan.from_arm(400000, 360, "3/1", "SOFR", 2.5, ORIG, rate=5.0)
        resets = [m for m in range(1, 62) if arm.is_reset_month(m)]
        assert resets == [37, 49, 61]

    def test_5_5_resets_every_5_years(self):
        arm = Loan.from_arm(400000, 360, "5/5", "SOFR", 2.5, ORIG, rate=5.0)
        resets = [m for m in range(1, 200) if arm.is_reset_month(m)]
        assert resets == [61, 121, 181]

    def test_unknown_product_raises(self):
        with pytest.raises(ValueError, match="Unknown ARM structure"):
            Loan.from_arm(400000, 360, "5/2", "SOFR", 2.5, ORIG, rate=5.0)

    def test_no_reset_during_fixed_period(self):
        arm = Loan.from_arm(400000, 360, "7/6", "SOFR", 2.5, ORIG, rate=5.0)
        assert not any(arm.is_reset_month(m) for m in range(1, 85))
        assert arm.is_reset_month(85)


class TestArmConstruction:
    def test_rate_inferred_from_most_recent_curve_point(self):
        curve = {"2024-06-01": 3.0, "2024-12-01": 4.0, "2025-06-01": 5.0}
        arm = Loan.from_arm(400000, 360, "5/1", "SOFR", 2.5, ORIG, rate=None,
                            forward_curve=curve)
        # Most recent point on/before 2025-01-01 is 4.0; +2.5 margin.
        assert arm.rate == Decimal("6.5")

    def test_caps_and_floors_stored(self):
        arm = Loan.from_arm(400000, 360, "5/1", "SOFR", 2.5, ORIG, rate=5.0,
                            caps=(5, 2, 6), floors=(1, 1, 2))
        assert arm.rate_bounds["initial_cap"] == Decimal("5")
        assert arm.rate_bounds["periodic_cap"] == Decimal("2")
        assert arm.rate_bounds["lifetime_cap"] == Decimal("6")
        assert arm.rate_bounds["lifetime_floor"] == Decimal("2")


class TestSetIndexedRate:
    def test_updates_rate_bounds_not_dead_attribute(self):
        loan = Loan(100000, 360, 7.0, ORIG, loan_type="heloc")
        loan.set_indexed_rate("prime", 1.5, caps=(3, 2, 6))
        assert loan.index == "PRIME"
        assert loan.margin == Decimal("1.5")
        assert loan.rate_bounds["lifetime_cap"] == Decimal("6")


class TestUpfrontFees:
    def test_fha_upfront_mip_added_once(self):
        fha = Loan(400000, 360, 6.0, ORIG, loan_type="fha")
        assert fha.principal == Decimal("400000") * Decimal("1.0175")

    def test_va_guarantee_fee_added(self):
        va = Loan(400000, 360, 6.0, ORIG, loan_type="va")
        assert va.principal == Decimal("400000") * Decimal("1.0225")
        assert va.is_pmi is False


class TestRefinance:
    def test_fha_refinance_does_not_double_charge_mip(self):
        fha = Loan(400000, 360, 6.0, ORIG, loan_type="fha")
        original_principal = fha.principal
        refi = fha.refinance(5.0, date(2027, 1, 1))
        assert refi.principal == original_principal

    def test_refinance_uses_supplied_balance_plus_fees(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        refi = loan.refinance(5.5, date(2028, 1, 1), new_term=300,
                              fees=4500, balance=361234.56)
        assert refi.principal == Decimal("361234.56") + Decimal("4500")
        assert refi.term == 300
        assert refi.rate == Decimal("5.5")


class TestRecast:
    def test_recast_reduces_principal_but_keeps_pmi_basis(self):
        loan = Loan(400000, 360, 6.25, ORIG)
        loan.recast(50000, date(2027, 6, 1))
        assert loan.principal == Decimal("350000")
        assert loan.original_balance == Decimal("400000")
