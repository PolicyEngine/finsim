"""Tests for annuity module."""

import pandas as pd
import pytest

from finsim.annuity import AnnuityCalculator


class TestAnnuityCalculator:
    @pytest.fixture
    def calculator(self):
        """Create a basic annuity calculator."""
        return AnnuityCalculator(age=65, gender="male")

    def test_initialization(self, calculator):
        """Test AnnuityCalculator initialization."""
        assert calculator.age == 65
        assert calculator.gender == "male"
        assert 65 in calculator.MALE_LIFE_TABLE

    def test_calculate_irr_fixed_term(self, calculator):
        """Test IRR calculation for fixed term annuity."""
        # $100k premium, $500/month for 20 years
        irr = calculator.calculate_irr(
            premium=100_000,
            monthly_payment=500,
            guarantee_months=240,  # 20 years
            life_contingent=False,
        )

        # Should get about 1.85% annual return
        assert isinstance(irr, float)
        assert -1 < irr < 1  # Reasonable IRR range

    def test_calculate_irr_life_contingent(self, calculator):
        """Test IRR calculation for life contingent annuity."""
        irr = calculator.calculate_irr(
            premium=100_000,
            monthly_payment=600,
            guarantee_months=120,  # 10 year guarantee
            life_contingent=True,
        )

        assert isinstance(irr, float)
        assert -1 < irr < 1

    def test_calculate_irr_no_guarantee(self, calculator):
        """Test IRR with no guarantee period."""
        # Non-life contingent with no guarantee should return -1 (complete loss)
        irr = calculator.calculate_irr(
            premium=100_000,
            monthly_payment=500,
            guarantee_months=0,
            life_contingent=False,
        )
        assert irr == -1.0

    def test_compare_annuity_options(self, calculator):
        """Test comparing multiple annuity options."""
        proposals = [
            {
                "name": "Option A",
                "premium": 100_000,
                "monthly_payment": 500,
                "guarantee_months": 240,
                "life_contingent": False,
                "taxable": False,
            },
            {
                "name": "Option B",
                "premium": 100_000,
                "monthly_payment": 600,
                "guarantee_months": 120,
                "life_contingent": True,
                "taxable": False,
            },
        ]

        df = calculator.compare_annuity_options(proposals)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "IRR" in df.columns
        assert "Total Guaranteed" in df.columns
        assert df.iloc[0]["Name"] == "Option A"
        assert df.iloc[0]["Monthly Payment"] == 500

    def test_calculate_present_value(self, calculator):
        """Test present value calculation."""
        # $500/month for 10 years at 5% discount rate
        pv = calculator.calculate_present_value(
            monthly_payment=500, months=120, discount_rate=0.05
        )

        assert isinstance(pv, float)
        assert pv > 0
        # PV should be less than total payments due to discounting
        assert pv < 500 * 120

    def test_calculate_present_value_zero_rate(self, calculator):
        """Test PV with zero discount rate."""
        pv = calculator.calculate_present_value(
            monthly_payment=500, months=120, discount_rate=0.0
        )
        # With zero discount rate, PV equals total payments
        assert pv == 500 * 120

    def test_different_ages(self):
        """Test calculator with different ages."""
        calc_70 = AnnuityCalculator(age=70, gender="male")
        calc_80 = AnnuityCalculator(age=80, gender="male")

        # Both should initialize properly
        assert calc_70.age == 70
        assert calc_80.age == 80

        # Life expectancy should be lower for older age
        assert calc_70.MALE_LIFE_TABLE[70] > calc_80.MALE_LIFE_TABLE[80]

    def test_irr_convergence_fallback(self, calculator):
        """Test IRR calculation fallback methods."""
        # Test case that might challenge convergence
        irr = calculator.calculate_irr(
            premium=1_000_000,
            monthly_payment=100,  # Very low payout
            guarantee_months=240,
            life_contingent=False,
        )
        # Should still return a value (very negative)
        assert isinstance(irr, float)
        assert irr < 0  # Should be negative return
