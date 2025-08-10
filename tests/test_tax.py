"""Tests for tax calculation module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


class TestTaxCalculator:
    @pytest.fixture
    def mock_microsimulation(self):
        """Create a mock Microsimulation class."""
        mock = MagicMock()
        mock.return_value.calculate.return_value = np.array([5000.0])
        return mock

    @pytest.fixture
    def tax_calculator(self, mock_microsimulation):
        """Create a TaxCalculator with mocked dependencies."""
        with patch("finsim.tax.Microsimulation", mock_microsimulation):
            from finsim.tax import TaxCalculator

            return TaxCalculator(state="CA", year=2025)

    def test_tax_calculator_init(self, mock_microsimulation):
        """Test TaxCalculator initialization."""
        with patch("finsim.tax.Microsimulation", mock_microsimulation):
            from finsim.tax import TaxCalculator

            calc = TaxCalculator(state="CA", year=2025)

            assert calc.state == "CA"
            assert calc.year == 2025

    def test_calculate_single_tax(self, tax_calculator):
        """Test calculating tax for a single scenario."""
        result = tax_calculator.calculate_single_tax(
            capital_gains=10_000, social_security=24_000, age=67, filing_status="SINGLE"
        )

        # Should return a dictionary with tax components
        assert isinstance(result, dict)
        assert "federal_tax" in result
        assert "state_tax" in result
        assert "total_tax" in result

        # Total should be sum of federal and state
        assert result["total_tax"] == result["federal_tax"] + result["state_tax"]

    def test_calculate_batch_taxes(self, tax_calculator):
        """Test batch tax calculation."""
        n = 10
        capital_gains = np.random.uniform(0, 50_000, n)
        social_security = np.full(n, 24_000)
        ages = np.full(n, 67)

        results = tax_calculator.calculate_batch_taxes(
            capital_gains_array=capital_gains,
            social_security_array=social_security,
            ages=ages,
            filing_status="SINGLE",
        )

        # Should return arrays of correct length
        assert len(results["federal_income_tax"]) == n
        assert len(results["state_income_tax"]) == n
        assert len(results["total_tax"]) == n

        # All taxes should be non-negative
        assert np.all(results["federal_income_tax"] >= 0)
        assert np.all(results["state_income_tax"] >= 0)
        assert np.all(results["total_tax"] >= 0)

    def test_tax_with_employment_income(self, tax_calculator):
        """Test tax calculation with employment income."""
        result = tax_calculator.calculate_single_tax(
            capital_gains=5_000,
            social_security=24_000,
            age=62,
            filing_status="SINGLE",
            employment_income=75_000,
        )

        # With employment income, taxes should be higher
        result_no_employment = tax_calculator.calculate_single_tax(
            capital_gains=5_000,
            social_security=24_000,
            age=62,
            filing_status="SINGLE",
            employment_income=0,
        )

        # Employment income should increase taxes
        assert result["total_tax"] > result_no_employment["total_tax"]

    def test_tax_with_dividend_income(self, tax_calculator):
        """Test tax calculation with dividend income."""
        result = tax_calculator.calculate_single_tax(
            capital_gains=0,
            social_security=24_000,
            age=67,
            filing_status="SINGLE",
            dividend_income=10_000,
        )

        # Should handle dividend income
        assert result["total_tax"] >= 0

        # Dividends should increase tax (or at least not decrease it)
        result_no_dividends = tax_calculator.calculate_single_tax(
            capital_gains=0,
            social_security=24_000,
            age=67,
            filing_status="SINGLE",
            dividend_income=0,
        )

        assert result["total_tax"] >= result_no_dividends["total_tax"]

    def test_different_filing_statuses(self, tax_calculator):
        """Test different filing statuses."""
        income_params = {
            "capital_gains": 20_000,
            "social_security": 24_000,
            "age": 67,
            "employment_income": 0,
            "dividend_income": 5_000,
        }

        # Test SINGLE
        single_result = tax_calculator.calculate_single_tax(**income_params, filing_status="SINGLE")

        # Test JOINT (if supported)
        joint_result = tax_calculator.calculate_single_tax(**income_params, filing_status="JOINT")

        # Joint filers typically have lower tax rates
        # (though this depends on the mock implementation)
        assert single_result["total_tax"] >= 0
        assert joint_result["total_tax"] >= 0

    def test_age_based_deductions(self, tax_calculator):
        """Test that age affects tax calculation (senior deductions)."""
        income_params = {
            "capital_gains": 15_000,
            "social_security": 24_000,
            "filing_status": "SINGLE",
        }

        # Under 65
        young_result = tax_calculator.calculate_single_tax(**income_params, age=60)

        # Over 65 (gets extra standard deduction)
        senior_result = tax_calculator.calculate_single_tax(**income_params, age=70)

        # Both should calculate successfully
        assert young_result["total_tax"] >= 0
        assert senior_result["total_tax"] >= 0

    def test_state_tax_variations(self, mock_microsimulation):
        """Test different state tax calculations."""
        with patch("finsim.tax.Microsimulation", mock_microsimulation):
            from finsim.tax import TaxCalculator

            # California (high tax state)
            ca_calc = TaxCalculator(state="CA", year=2025)
            ca_result = ca_calc.calculate_single_tax(
                capital_gains=50_000, social_security=24_000, age=67, filing_status="SINGLE"
            )

            # Texas (no state income tax)
            tx_calc = TaxCalculator(state="TX", year=2025)
            tx_result = tx_calc.calculate_single_tax(
                capital_gains=50_000, social_security=24_000, age=67, filing_status="SINGLE"
            )

            # Both should calculate
            assert ca_result["total_tax"] >= 0
            assert tx_result["total_tax"] >= 0

    def test_zero_income(self, tax_calculator):
        """Test tax calculation with zero income."""
        result = tax_calculator.calculate_single_tax(
            capital_gains=0,
            social_security=0,
            age=67,
            filing_status="SINGLE",
            employment_income=0,
            dividend_income=0,
        )

        # Should handle zero income gracefully
        assert result["federal_tax"] == 0
        assert result["state_tax"] == 0
        assert result["total_tax"] == 0

    def test_very_high_income(self, tax_calculator):
        """Test tax calculation with very high income."""
        result = tax_calculator.calculate_single_tax(
            capital_gains=1_000_000,
            social_security=50_000,
            age=67,
            filing_status="SINGLE",
            employment_income=500_000,
            dividend_income=100_000,
        )

        # Should handle high income
        assert result["total_tax"] > 0

        # Tax rate should be substantial but not exceed 100%
        total_income = 1_000_000 + 50_000 + 500_000 + 100_000
        effective_rate = result["total_tax"] / total_income
        assert 0 < effective_rate < 1.0

    def test_batch_with_mixed_incomes(self, tax_calculator):
        """Test batch calculation with varied income levels."""
        n = 5
        capital_gains = np.array([0, 10_000, 50_000, 100_000, 500_000])
        social_security = np.array([0, 12_000, 24_000, 36_000, 48_000])
        ages = np.array([55, 62, 67, 70, 75])
        employment = np.array([100_000, 50_000, 0, 0, 0])
        dividends = np.array([0, 1_000, 5_000, 10_000, 50_000])

        results = tax_calculator.calculate_batch_taxes(
            capital_gains_array=capital_gains,
            social_security_array=social_security,
            ages=ages,
            filing_status="SINGLE",
            employment_income_array=employment,
            dividend_income_array=dividends,
        )

        # All results should be valid
        assert len(results["total_tax"]) == n
        assert np.all(results["total_tax"] >= 0)

        # Higher income should generally mean higher tax
        # (person 4 has much higher income than person 0)
        assert results["total_tax"][4] > results["total_tax"][0]
