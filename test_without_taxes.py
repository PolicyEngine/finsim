"""Test FinSim without tax calculations to avoid NumPy 2.0 issues."""

import numpy as np
from finsim.cola import get_ssa_cola_factors, get_consumption_inflation_factors
from finsim.return_generator import ReturnGenerator
from finsim.mortality import get_mortality_rates


def test_inflation_factors():
    """Test inflation factor calculations."""
    print("Testing inflation factors...")
    
    # Test SSA COLA
    cola = get_ssa_cola_factors(2025, 10)
    assert cola[0] == 1.0
    assert abs(cola[1] - 1.023) < 0.01  # 2026 should be ~2.3%
    assert abs(cola[2] - 1.049) < 0.01  # 2027 should be ~4.9% cumulative
    print(f"  SSA COLA: {cola[:5]}")
    
    # Test C-CPI-U
    cpi = get_consumption_inflation_factors(2025, 10)
    assert cpi[0] == 1.0
    assert cpi[1] > 1.0
    print(f"  C-CPI-U: {cpi[:5]}")
    
    print("✓ Inflation factors correct")


def test_return_generator():
    """Test return generation."""
    print("Testing return generator...")
    
    gen = ReturnGenerator(expected_return=0.07, volatility=0.15)
    returns = gen.generate_returns(100, 10)
    
    assert returns.shape == (100, 10)
    assert np.all(returns > 0)  # Should be growth factors
    
    # Check mean is roughly correct (with wide tolerance for randomness)
    mean_return = np.mean(returns) - 1
    assert abs(mean_return - 0.07) < 0.05, f"Mean return {mean_return:.3f} far from 0.07"
    
    print(f"  Mean return: {mean_return:.3f}")
    print(f"  Std dev: {np.std(returns - 1):.3f}")
    print("✓ Return generator working")


def test_mortality():
    """Test mortality rates."""
    print("Testing mortality rates...")
    
    male_rates = get_mortality_rates("Male")
    female_rates = get_mortality_rates("Female")
    
    # Check some known values
    assert male_rates[65] > 0.01  # ~1.6% for 65-year-old male
    assert female_rates[65] < male_rates[65]  # Females have lower mortality
    
    # Check rates increase with age (using ages we know exist)
    assert male_rates[80] > male_rates[70] > male_rates[65]
    
    print(f"  65-year-old male: {male_rates[65]:.3f}")
    print(f"  65-year-old female: {female_rates[65]:.3f}")
    print(f"  80-year-old male: {male_rates[80]:.3f}")
    print("✓ Mortality rates correct")


def test_monte_carlo_simulation():
    """Test basic Monte Carlo without taxes."""
    print("Testing Monte Carlo simulation...")
    
    # Simple wealth evolution without taxes
    n_sims = 1000
    n_years = 20
    initial = 1_000_000
    
    # Generate returns
    gen = ReturnGenerator(expected_return=0.06, volatility=0.12)
    returns = gen.generate_returns(n_sims, n_years)
    
    # Apply inflation to consumption
    consumption_base = 50_000
    inflation = get_consumption_inflation_factors(2025, n_years)
    
    # Simulate wealth paths
    wealth = np.zeros((n_sims, n_years + 1))
    wealth[:, 0] = initial
    
    for year in range(n_years):
        # Growth
        wealth[:, year + 1] = wealth[:, year] * returns[:, year]
        
        # Withdrawal for consumption
        consumption = consumption_base * inflation[year]
        wealth[:, year + 1] = np.maximum(0, wealth[:, year + 1] - consumption)
    
    # Check results
    final_wealth = wealth[:, -1]
    survival_rate = np.mean(final_wealth > 0)
    median_final = np.median(final_wealth[final_wealth > 0]) if survival_rate > 0 else 0
    
    print(f"  Survival rate: {survival_rate:.1%}")
    print(f"  Median final wealth (survivors): ${median_final:,.0f}")
    
    assert survival_rate > 0.5, "Survival rate too low"
    # With 6% returns and $50k consumption, wealth may not grow
    # Just check it's reasonable
    assert median_final > 100_000, "Final wealth too low"
    
    print("✓ Monte Carlo working")


if __name__ == "__main__":
    print("Testing FinSim Core Components (without taxes)")
    print("=" * 60)
    
    tests = [
        test_inflation_factors,
        test_return_generator,
        test_mortality,
        test_monte_carlo_simulation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All core components working!")
        print("\nNote: Tax calculations not tested due to NumPy 2.0 compatibility")
        print("issue with PolicyEngine-US. This will be resolved when")
        print("PolicyEngine-US is updated for NumPy 2.0.")
    else:
        exit(1)