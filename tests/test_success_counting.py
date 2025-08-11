"""Test that success rate is calculated correctly."""

import numpy as np
import pytest
from finsim.portfolio_simulation import simulate_portfolio


def test_death_not_counted_as_success():
    """Death with money should not be counted as success."""
    # Use high age for guaranteed deaths
    params = {
        "n_simulations": 50,
        "n_years": 10,  # Short simulation
        "initial_portfolio": 10_000_000,  # Large portfolio to avoid running out
        "current_age": 95,  # Very old to ensure deaths
        "include_mortality": True,
        "gender": "Male",
        "social_security": 0,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 95,
        "annual_consumption": 50_000,  # Low consumption relative to portfolio
        "expected_return": 5.0,
        "return_volatility": 10.0,
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": False,
    }
    
    np.random.seed(42)
    results = simulate_portfolio(**params)
    
    # Check how success is counted
    failure_year = results["failure_year"]
    alive_at_end = results["alive_mask"][:, -1]
    portfolio_at_end = results["portfolio_paths"][:, -1]
    
    # Get the new success_mask if available
    if "success_mask" in results:
        current_success_count = np.sum(results["success_mask"])
    else:
        # Old (incorrect) method
        current_success_count = np.sum(failure_year > params["n_years"])
    
    # Correct success definition: alive at end with money
    correct_success_count = np.sum(alive_at_end & (portfolio_at_end > 0))
    
    # Deaths should be significant at age 95-105
    death_count = np.sum(~alive_at_end)
    assert death_count > 10, f"Expected many deaths at age 95-105, got {death_count}"
    
    # Success count should only include those alive at end
    # This test will fail with current implementation
    assert current_success_count == correct_success_count, (
        f"Success count ({current_success_count}) should equal alive with money ({correct_success_count}). "
        f"Deaths: {death_count}, Deaths with money: {np.sum((~alive_at_end) & (portfolio_at_end > 0))}"
    )


def test_cola_vs_cpi_inflation():
    """Test that COLA and CPI-U have different rates."""
    from finsim.cola import get_ssa_cola_factors, get_consumption_inflation_factors
    
    # Get 30-year projections
    cola = get_ssa_cola_factors(2025, 30)
    cpi = get_consumption_inflation_factors(2025, 30)
    
    # Calculate average annual rates
    cola_annual_rates = []
    cpi_annual_rates = []
    
    for i in range(1, 30):
        cola_rate = (cola[i] / cola[i-1] - 1) * 100
        cpi_rate = (cpi[i] / cpi[i-1] - 1) * 100
        cola_annual_rates.append(cola_rate)
        cpi_annual_rates.append(cpi_rate)
    
    avg_cola = np.mean(cola_annual_rates)
    avg_cpi = np.mean(cpi_annual_rates)
    
    # SSA COLA (CPI-W based) is typically higher than C-CPI-U
    # C-CPI-U accounts for substitution effects
    assert avg_cola > avg_cpi, f"COLA ({avg_cola:.2f}%) should be > C-CPI-U ({avg_cpi:.2f}%)"
    
    # The difference should be meaningful (typically 0.2-0.3% per year)
    difference = avg_cola - avg_cpi
    assert 0.1 < difference < 0.5, f"COLA-CPI difference ({difference:.2f}%) seems wrong"


def test_simulation_consistency():
    """Test that simulation results are consistent across runs with same seed."""
    params = {
        "n_simulations": 100,
        "n_years": 30,
        "initial_portfolio": 500_000,
        "current_age": 65,
        "include_mortality": True,
        "gender": "Male",
        "social_security": 24_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 60_000,
        "expected_return": 7.0,
        "return_volatility": 15.0,
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": False,
    }
    
    # Run twice with same seed
    np.random.seed(42)
    results1 = simulate_portfolio(**params)
    
    np.random.seed(42)
    results2 = simulate_portfolio(**params)
    
    # Should get identical results
    assert np.array_equal(results1["portfolio_paths"], results2["portfolio_paths"])
    assert np.array_equal(results1["failure_year"], results2["failure_year"])
    
    # Success rates should match
    success1 = np.sum(results1["failure_year"] > 30)
    success2 = np.sum(results2["failure_year"] > 30)
    assert success1 == success2


def test_variation_across_seeds():
    """Test that different seeds give reasonable variation."""
    params = {
        "n_simulations": 1000,
        "n_years": 30,
        "initial_portfolio": 500_000,
        "current_age": 65,
        "include_mortality": True,
        "gender": "Male",
        "social_security": 24_000,
        "pension": 0,
        "employment_income": 0,
        "retirement_age": 65,
        "annual_consumption": 60_000,
        "expected_return": 7.0,
        "return_volatility": 15.0,
        "dividend_yield": 2.0,
        "state": "CA",
        "has_annuity": False,
    }
    
    success_rates = []
    for seed in range(5):
        np.random.seed(seed)
        results = simulate_portfolio(**params)
        success_rate = 100 * np.sum(results["failure_year"] > 30) / params["n_simulations"]
        success_rates.append(success_rate)
        print(f"Seed {seed}: {success_rate:.1f}%")
    
    # Standard error for 1000 simulations should be ~1.5% for 40% success rate
    # So range should be reasonable (not 34% to 42%)
    std_dev = np.std(success_rates)
    assert std_dev < 3.0, f"Too much variation: std dev = {std_dev:.1f}%"