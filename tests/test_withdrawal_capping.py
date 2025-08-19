"""Test that withdrawals are properly capped at portfolio value."""

import numpy as np
import pytest

from finsim.portfolio_simulation import simulate_portfolio


def test_withdrawals_should_not_exceed_portfolio():
    """Withdrawals should never exceed available portfolio balance."""
    params = {
        "n_simulations": 100,
        "n_years": 5,
        "initial_portfolio": 50_000,  # Small portfolio
        "current_age": 65,
        "include_mortality": False,
        "gender": "Male",
        "social_security": 24_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 80_000,  # High spending
        "expected_return": 0.0,  # No growth to simplify
        "return_volatility": 0.0,  # No volatility to simplify
        "dividend_yield": 0.0,
        "state": "CA",
        "has_annuity": False,
    }

    np.random.seed(42)
    results = simulate_portfolio(**params)

    portfolio_paths = results["portfolio_paths"]
    gross_withdrawals = results["gross_withdrawals"]

    # Check each year
    for year in range(params["n_years"]):
        portfolio_at_start = portfolio_paths[:, year]
        withdrawal = (
            gross_withdrawals[:, year] if year < gross_withdrawals.shape[1] else 0
        )

        # Withdrawals should never exceed portfolio
        # This test will FAIL with current implementation
        over_withdrawals = (
            withdrawal > portfolio_at_start + 0.01
        )  # Small tolerance for rounding

        if np.any(over_withdrawals):
            over_withdraw_amount = (
                withdrawal[over_withdrawals] - portfolio_at_start[over_withdrawals]
            )
            max_over = np.max(over_withdraw_amount)

            pytest.fail(
                f"Year {year+1}: {np.sum(over_withdrawals)} simulations withdrew more than available.\n"
                f"Max over-withdrawal: ${max_over:,.0f}\n"
                f"Example: Portfolio=${portfolio_at_start[over_withdrawals][0]:,.0f}, "
                f"Withdrawal=${withdrawal[over_withdrawals][0]:,.0f}"
            )


def test_consumption_adjustment_when_broke():
    """When portfolio is depleted, household should live on guaranteed income only."""
    params = {
        "n_simulations": 1,
        "n_years": 10,
        "initial_portfolio": 10_000,  # Very small
        "current_age": 65,
        "include_mortality": False,
        "gender": "Male",
        "social_security": 24_000,
        "pension": 10_000,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 80_000,
        "expected_return": 0.0,
        "return_volatility": 0.0,
        "dividend_yield": 0.0,
        "state": "CA",
        "has_annuity": False,
    }

    np.random.seed(42)
    results = simulate_portfolio(**params)

    # After portfolio depletes, withdrawal should be 0
    # and household lives on SS + pension only
    portfolio = results["portfolio_paths"][0]
    withdrawals = results["gross_withdrawals"][0]

    # Find when portfolio hits 0
    zero_year = np.where(portfolio == 0)[0]
    if len(zero_year) > 0:
        first_zero = zero_year[0]

        # After depletion, withdrawals should be 0
        for year in range(first_zero, len(withdrawals)):
            assert (
                withdrawals[year] == 0
            ), f"Year {year+1}: Withdrawal should be 0 when broke, but was ${withdrawals[year]:,.0f}"

        print(
            f"✓ Correctly stops withdrawing after portfolio depletes in year {first_zero}"
        )


def test_final_year_withdrawal_cap():
    """In final year, withdrawal should be capped at remaining portfolio."""
    params = {
        "n_simulations": 100,
        "n_years": 3,
        "initial_portfolio": 100_000,
        "current_age": 65,
        "include_mortality": False,
        "gender": "Male",
        "social_security": 20_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 50_000,
        "expected_return": 5.0,
        "return_volatility": 10.0,
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": False,
    }

    np.random.seed(42)
    results = simulate_portfolio(**params)

    # In any year, if portfolio < withdrawal need, should only withdraw what's available
    portfolio_paths = results["portfolio_paths"]
    gross_withdrawals = results["gross_withdrawals"]

    for sim in range(params["n_simulations"]):
        for year in range(params["n_years"] - 1):
            portfolio = portfolio_paths[sim, year]
            withdrawal = gross_withdrawals[sim, year]

            if portfolio > 0 and withdrawal > portfolio:
                pytest.fail(
                    f"Sim {sim}, Year {year+1}: Withdrew ${withdrawal:,.0f} "
                    f"but only had ${portfolio:,.0f} available"
                )
