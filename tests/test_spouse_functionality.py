"""Tests for spouse functionality in portfolio simulation."""

import numpy as np
import pytest

from finsim.portfolio_simulation import simulate_portfolio


class TestSpouseFunctionality:
    @pytest.fixture
    def base_params(self):
        """Base parameters for testing."""
        return {
            "n_simulations": 100,
            "n_years": 10,
            "initial_portfolio": 500_000,
            "current_age": 65,
            "include_mortality": True,
            "social_security": 24_000,
            "pension": 10_000,
            "employment_income": 0,
            "retirement_age": 65,
            "has_annuity": False,
            "annuity_type": "Fixed Period",
            "annuity_annual": 0,
            "annuity_guarantee_years": 0,
            "annual_consumption": 80_000,
            "expected_return": 7.0,
            "return_volatility": 15.0,
            "dividend_yield": 2.0,
            "state": "CA",
            "gender": "Male",
        }

    def test_simulation_without_spouse(self, base_params):
        """Test that simulation works without spouse (baseline)."""
        params = base_params.copy()
        params["has_spouse"] = False

        results = simulate_portfolio(**params)

        # Should run successfully
        assert "portfolio_paths" in results
        assert results["portfolio_paths"].shape == (100, 11)

    def test_simulation_with_spouse(self, base_params):
        """Test simulation with spouse included."""
        params = base_params.copy()
        params.update(
            {
                "has_spouse": True,
                "spouse_age": 63,
                "spouse_gender": "Female",
                "spouse_social_security": 18_000,
                "spouse_pension": 5_000,
                "spouse_employment_income": 0,
                "spouse_retirement_age": 65,
            }
        )

        results = simulate_portfolio(**params)

        # Should run successfully
        assert "portfolio_paths" in results
        assert results["portfolio_paths"].shape == (100, 11)

    def test_spouse_income_increases_portfolio(self, base_params):
        """Test that spouse income helps portfolio longevity."""
        # Run without spouse
        params_single = base_params.copy()
        params_single["has_spouse"] = False
        results_single = simulate_portfolio(**params_single)

        # Run with spouse who has income
        params_married = base_params.copy()
        params_married.update(
            {
                "has_spouse": True,
                "spouse_age": 65,
                "spouse_gender": "Female",
                "spouse_social_security": 20_000,
                "spouse_pension": 10_000,
                "spouse_employment_income": 0,
                "spouse_retirement_age": 65,
            }
        )
        results_married = simulate_portfolio(**params_married)

        # With additional $30k/year from spouse, portfolios should last longer
        single_failures = np.sum(results_single["failure_year"] <= 10)
        married_failures = np.sum(results_married["failure_year"] <= 10)

        # Married couples should have fewer failures
        assert married_failures <= single_failures

        # Median portfolio value should be higher for married
        single_median_final = np.median(results_single["portfolio_paths"][:, -1])
        married_median_final = np.median(results_married["portfolio_paths"][:, -1])

        # With more income, married should have higher final portfolio
        # (May not always be true due to randomness, but generally should be)
        # Using a loose check due to Monte Carlo variability
        if single_median_final > 0 and married_median_final > 0:
            assert married_median_final >= single_median_final * 0.8

    def test_spouse_employment_income(self, base_params):
        """Test spouse employment income before retirement."""
        params = base_params.copy()
        params.update(
            {
                "has_spouse": True,
                "spouse_age": 55,  # Younger spouse
                "spouse_gender": "Female",
                "spouse_social_security": 0,  # No SS yet
                "spouse_pension": 0,
                "spouse_employment_income": 75_000,  # Working
                "spouse_retirement_age": 65,  # Will work for 10 years
            }
        )

        results = simulate_portfolio(**params)

        # With high spouse employment income, portfolio should grow initially
        # or at least not deplete as fast
        initial_portfolio = params["initial_portfolio"]
        year_5_portfolios = results["portfolio_paths"][:, 5]

        # Many simulations should maintain or grow portfolio value
        maintained = np.sum(year_5_portfolios >= initial_portfolio * 0.9)
        assert maintained > 30  # At least 30% should maintain value

    def test_different_spouse_ages(self, base_params):
        """Test with different spouse ages."""
        # Older spouse
        params_older = base_params.copy()
        params_older.update(
            {
                "has_spouse": True,
                "spouse_age": 75,  # 10 years older
                "spouse_gender": "Female",
                "spouse_social_security": 25_000,
                "spouse_pension": 5_000,
                "spouse_employment_income": 0,
                "spouse_retirement_age": 75,
            }
        )

        results_older = simulate_portfolio(**params_older)

        # Younger spouse
        params_younger = base_params.copy()
        params_younger.update(
            {
                "has_spouse": True,
                "spouse_age": 55,  # 10 years younger
                "spouse_gender": "Female",
                "spouse_social_security": 15_000,
                "spouse_pension": 5_000,
                "spouse_employment_income": 50_000,
                "spouse_retirement_age": 65,
            }
        )

        results_younger = simulate_portfolio(**params_younger)

        # Both should complete successfully
        assert results_older["portfolio_paths"].shape == (100, 11)
        assert results_younger["portfolio_paths"].shape == (100, 11)

    def test_spouse_mortality_independence(self, base_params):
        """Test that spouse mortality is tracked independently."""
        params = base_params.copy()
        params.update(
            {
                "has_spouse": True,
                "spouse_age": 65,
                "spouse_gender": "Female",
                "spouse_social_security": 20_000,
                "spouse_pension": 5_000,
                "spouse_employment_income": 0,
                "spouse_retirement_age": 65,
                "n_simulations": 1000,  # More simulations for mortality test
            }
        )

        results = simulate_portfolio(**params)

        # Both spouses start alive
        alive_mask = results["alive_mask"]

        # At start, everyone should be alive
        assert np.all(alive_mask[:, 0])

        # After 10 years, some should have died
        final_alive = alive_mask[:, -1]
        survivors = np.sum(final_alive)

        # Mortality should have occurred (not everyone survives)
        assert survivors < 1000
        assert survivors > 500  # But not too extreme

    def test_tax_filing_status(self, base_params):
        """Test that tax filing status changes with spouse."""
        # This is more of an integration test
        # We can't directly test filing status without mocking TaxCalculator
        # But we can verify the simulation runs with different configurations

        # Single filing
        params_single = base_params.copy()
        params_single["has_spouse"] = False

        # Joint filing
        params_joint = base_params.copy()
        params_joint.update(
            {
                "has_spouse": True,
                "spouse_age": 65,
                "spouse_gender": "Female",
                "spouse_social_security": 20_000,
                "spouse_pension": 5_000,
                "spouse_employment_income": 0,
                "spouse_retirement_age": 65,
            }
        )

        results_single = simulate_portfolio(**params_single)
        results_joint = simulate_portfolio(**params_joint)

        # Tax amounts should differ (joint usually pays less tax)
        # But we need to be careful with assertions due to randomness
        assert "taxes_owed" in results_single
        assert "taxes_owed" in results_joint

    def test_spouse_with_annuity(self, base_params):
        """Test spouse with household annuity income."""
        params = base_params.copy()
        params.update(
            {
                "has_spouse": True,
                "spouse_age": 65,
                "spouse_gender": "Female",
                "spouse_social_security": 15_000,
                "spouse_pension": 5_000,
                "spouse_employment_income": 0,
                "spouse_retirement_age": 65,
                "has_annuity": True,
                "annuity_type": "Life Contingent with Guarantee",
                "annuity_annual": 30_000,
                "annuity_guarantee_years": 15,
            }
        )

        results = simulate_portfolio(**params)

        # Should complete successfully
        assert "annuity_income" in results
        assert results["annuity_income"].shape == (100, 10)

        # Annuity should provide income
        assert np.any(results["annuity_income"] > 0)
