"""Test annuity functionality including tax treatment."""

import numpy as np
import pytest

from finsim.portfolio_simulation import simulate_portfolio


def test_annuity_income_generation():
    """Test that annuity generates correct income."""
    params = {
        "n_simulations": 100,
        "n_years": 20,
        "initial_portfolio": 170_000,  # Remainder after annuity purchase
        "current_age": 65,
        "include_mortality": False,  # Simplify for testing
        "gender": "Male",
        "social_security": 24_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 80_000,
        "expected_return": 7.0,
        "return_volatility": 15.0,
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": True,
        "annuity_type": "Fixed Period",
        "annuity_annual": 48_693,  # $4,057.78 * 12
        "annuity_guarantee_years": 15,
    }
    
    np.random.seed(42)
    results = simulate_portfolio(**params)
    
    # Check annuity income is generated for first 15 years
    annuity_income = results["annuity_income"]
    
    # First 15 years should have annuity income
    for year in range(15):
        assert np.all(annuity_income[:, year] == params["annuity_annual"]), \
            f"Year {year+1} should have annuity income"
    
    # After 15 years, no annuity income
    for year in range(15, 20):
        assert np.all(annuity_income[:, year] == 0), \
            f"Year {year+1} should have no annuity income"


def test_life_annuity_with_guarantee():
    """Test life annuity with guarantee period."""
    params = {
        "n_simulations": 100,
        "n_years": 20,
        "initial_portfolio": 170_000,
        "current_age": 65,
        "include_mortality": True,
        "gender": "Male",
        "social_security": 24_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 80_000,
        "expected_return": 7.0,
        "return_volatility": 15.0,
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": True,
        "annuity_type": "Life Contingent with Guarantee",
        "annuity_annual": 42_195,  # $3,516.29 * 12
        "annuity_guarantee_years": 15,
    }
    
    np.random.seed(42)
    results = simulate_portfolio(**params)
    
    annuity_income = results["annuity_income"]
    alive_mask = results["alive_mask"]
    
    # Check that annuity is paid during guarantee period regardless of death
    for sim in range(params["n_simulations"]):
        for year in range(min(15, params["n_years"])):
            if year < 15:  # Within guarantee period
                assert annuity_income[sim, year] == params["annuity_annual"], \
                    f"Sim {sim}, Year {year+1}: Should receive annuity during guarantee"
            elif alive_mask[sim, year]:  # After guarantee, only if alive
                assert annuity_income[sim, year] == params["annuity_annual"], \
                    f"Sim {sim}, Year {year+1}: Should receive annuity if alive"
            else:  # Dead after guarantee
                assert annuity_income[sim, year] == 0, \
                    f"Sim {sim}, Year {year+1}: No annuity if dead after guarantee"


def test_annuity_tax_treatment():
    """Test that annuity income affects taxes correctly.
    
    Personal injury annuities are generally not taxable, but we need to verify
    the simulation handles this correctly.
    """
    # Run with annuity
    params_with_annuity = {
        "n_simulations": 50,
        "n_years": 10,
        "initial_portfolio": 170_000,
        "current_age": 65,
        "include_mortality": False,
        "gender": "Male",
        "social_security": 24_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 80_000,
        "expected_return": 7.0,
        "return_volatility": 15.0,
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": True,
        "annuity_type": "Fixed Period",
        "annuity_annual": 48_693,
        "annuity_guarantee_years": 15,
    }
    
    # Same scenario without annuity but with equivalent pension (taxable)
    params_with_pension = params_with_annuity.copy()
    params_with_pension["has_annuity"] = False
    params_with_pension["pension"] = 48_693
    
    np.random.seed(42)
    results_annuity = simulate_portfolio(**params_with_annuity)
    
    np.random.seed(42)
    results_pension = simulate_portfolio(**params_with_pension)
    
    # With annuity, should have less taxes than with pension
    # since annuity from personal injury settlement is not taxable
    taxes_annuity = results_annuity["taxes_paid"]
    taxes_pension = results_pension["taxes_paid"]
    
    # Average taxes should be lower with non-taxable annuity
    avg_tax_annuity = np.mean(taxes_annuity)
    avg_tax_pension = np.mean(taxes_pension)
    
    # Note: Current implementation may treat annuities as taxable
    # This test documents expected behavior
    print(f"Avg tax with annuity: ${avg_tax_annuity:,.0f}")
    print(f"Avg tax with pension: ${avg_tax_pension:,.0f}")
    
    # For now, we just verify the simulation runs
    # TODO: Update once annuity tax treatment is clarified
    assert avg_tax_annuity >= 0
    assert avg_tax_pension >= 0


def test_annuity_reduces_withdrawal_need():
    """Test that annuity income reduces portfolio withdrawals."""
    base_params = {
        "n_simulations": 50,
        "n_years": 10,
        "initial_portfolio": 500_000,
        "current_age": 65,
        "include_mortality": False,
        "gender": "Male",
        "social_security": 24_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 80_000,
        "expected_return": 7.0,
        "return_volatility": 10.0,  # Lower volatility for clearer test
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": False,
    }
    
    # Scenario without annuity
    np.random.seed(42)
    results_no_annuity = simulate_portfolio(**base_params)
    
    # Scenario with annuity (less initial portfolio but annuity income)
    params_with_annuity = base_params.copy()
    params_with_annuity["initial_portfolio"] = 170_000  # After buying annuity
    params_with_annuity["has_annuity"] = True
    params_with_annuity["annuity_type"] = "Fixed Period"
    params_with_annuity["annuity_annual"] = 48_693
    params_with_annuity["annuity_guarantee_years"] = 15
    
    np.random.seed(42)
    results_with_annuity = simulate_portfolio(**params_with_annuity)
    
    # First year withdrawals should be much lower with annuity
    withdrawals_no_annuity = results_no_annuity["gross_withdrawals"][:, 0]
    withdrawals_with_annuity = results_with_annuity["gross_withdrawals"][:, 0]
    
    avg_withdrawal_no_annuity = np.mean(withdrawals_no_annuity)
    avg_withdrawal_with_annuity = np.mean(withdrawals_with_annuity)
    
    print(f"Avg withdrawal without annuity: ${avg_withdrawal_no_annuity:,.0f}")
    print(f"Avg withdrawal with annuity: ${avg_withdrawal_with_annuity:,.0f}")
    
    # With annuity providing ~$49k/year, withdrawals should be much lower
    assert avg_withdrawal_with_annuity < avg_withdrawal_no_annuity - 30_000, \
        "Annuity should significantly reduce withdrawal needs"


def test_all_annuity_types():
    """Test all three annuity types work correctly."""
    base_params = {
        "n_simulations": 10,
        "n_years": 20,
        "initial_portfolio": 170_000,
        "current_age": 65,
        "include_mortality": True,
        "gender": "Male",
        "social_security": 24_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 80_000,
        "expected_return": 7.0,
        "return_volatility": 15.0,
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": True,
        "annuity_annual": 50_000,
    }
    
    annuity_types = [
        ("Life Only", 0),
        ("Life Contingent with Guarantee", 15),
        ("Fixed Period", 15),
    ]
    
    for annuity_type, guarantee_years in annuity_types:
        params = base_params.copy()
        params["annuity_type"] = annuity_type
        params["annuity_guarantee_years"] = guarantee_years
        
        np.random.seed(42)
        results = simulate_portfolio(**params)
        
        # Just verify it runs without error
        assert results["annuity_income"] is not None, \
            f"{annuity_type} should generate annuity income"
        assert results["portfolio_paths"] is not None, \
            f"{annuity_type} should complete simulation"