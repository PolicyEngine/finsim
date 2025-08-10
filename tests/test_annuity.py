"""Tests for annuity module."""

import numpy as np
import pytest

from finsim.annuity import AnnuityCalculator


class TestAnnuityCalculator:
    @pytest.fixture
    def calculator(self):
        """Create a basic annuity calculator."""
        return AnnuityCalculator(
            purchase_price=100_000,
            payout_rate=0.05,
            payment_type="Life Contingent with Guarantee",
            guarantee_period=10,
        )

    def test_initialization(self, calculator):
        """Test AnnuityCalculator initialization."""
        assert calculator.purchase_price == 100_000
        assert calculator.payout_rate == 0.05
        assert calculator.payment_type == "Life Contingent with Guarantee"
        assert calculator.guarantee_period == 10

    def test_annual_payout(self, calculator):
        """Test annual payout calculation."""
        payout = calculator.annual_payout
        assert payout == 100_000 * 0.05
        assert payout == 5_000

    def test_monthly_payout(self, calculator):
        """Test monthly payout calculation."""
        monthly = calculator.monthly_payout
        assert monthly == 5_000 / 12
        assert abs(monthly - 416.67) < 0.01

    def test_calculate_npv_basic(self, calculator):
        """Test NPV calculation."""
        npv = calculator.calculate_npv(
            discount_rate=0.03, years=20, survival_rates=None  # No mortality
        )

        # With 5k annual payout for 20 years at 3% discount
        # This should be positive since payout rate > discount rate
        assert npv > 0
        assert npv < 100_000  # But less than purchase price

    def test_calculate_npv_with_mortality(self, calculator):
        """Test NPV with mortality adjustments."""
        # Mock survival rates (declining)
        survival_rates = np.linspace(1.0, 0.5, 20)

        npv_with_mortality = calculator.calculate_npv(
            discount_rate=0.03, years=20, survival_rates=survival_rates
        )

        npv_without_mortality = calculator.calculate_npv(
            discount_rate=0.03, years=20, survival_rates=None
        )

        # NPV should be lower with mortality
        assert npv_with_mortality < npv_without_mortality

    def test_irr_calculation(self, calculator):
        """Test IRR calculation."""
        irr = calculator.calculate_irr(years=20)

        # IRR should be close to payout rate for simple case
        # (Actually slightly less due to finite period)
        assert 0.03 < irr < 0.05

    def test_compare_with_portfolio(self, calculator):
        """Test comparison with portfolio investment."""
        comparison = calculator.compare_with_portfolio(
            expected_return=0.07, volatility=0.15, years=20, n_simulations=100
        )

        # Should return comparison metrics
        assert "annuity_npv" in comparison
        assert "portfolio_mean" in comparison
        assert "portfolio_median" in comparison
        assert "probability_annuity_better" in comparison

        # With 7% expected return, portfolio should usually beat 5% annuity
        assert comparison["portfolio_mean"] > comparison["annuity_npv"]

    def test_different_payment_types(self):
        """Test different payment types."""
        # Fixed Period
        calc_fixed = AnnuityCalculator(
            purchase_price=100_000,
            payout_rate=0.05,
            payment_type="Fixed Period",
            guarantee_period=15,
        )
        assert calc_fixed.payment_type == "Fixed Period"

        # Life Only
        calc_life = AnnuityCalculator(
            purchase_price=100_000, payout_rate=0.05, payment_type="Life Only", guarantee_period=0
        )
        assert calc_life.payment_type == "Life Only"

    def test_high_payout_rate(self):
        """Test with high payout rate."""
        calc = AnnuityCalculator(
            purchase_price=100_000, payout_rate=0.10, payment_type="Life Only"  # 10% payout
        )

        assert calc.annual_payout == 10_000

        # IRR should be higher
        irr = calc.calculate_irr(years=15)
        assert irr > 0.07

    def test_zero_guarantee_period(self):
        """Test with no guarantee period."""
        calc = AnnuityCalculator(
            purchase_price=100_000, payout_rate=0.05, payment_type="Life Only", guarantee_period=0
        )

        # With high mortality in early years, NPV should be lower
        survival_rates = np.array([1.0, 0.5, 0.25, 0.1, 0.05])
        npv = calc.calculate_npv(discount_rate=0.03, years=5, survival_rates=survival_rates)

        # Should be much less than purchase price
        assert npv < 50_000
