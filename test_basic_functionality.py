"""Basic functionality test for FinSim without pytest."""

import numpy as np
from finsim.portfolio_simulation import simulate_portfolio
from finsim.cola import get_ssa_cola_factors, get_consumption_inflation_factors


def test_inflation_factors():
    """Test that inflation factors are calculated correctly."""
    print("Testing inflation factors...")
    
    # Test SSA COLA factors
    cola_factors = get_ssa_cola_factors(2025, 5)
    assert len(cola_factors) == 5
    assert cola_factors[0] == 1.0  # Base year
    assert cola_factors[1] > 1.0  # Should have COLA
    
    # Verify known values (from PolicyEngine-US)
    # 2026 COLA should be ~2.3%
    expected_2026 = 1.023
    assert abs(cola_factors[1] - expected_2026) < 0.01, f"2026 COLA factor {cola_factors[1]} != {expected_2026}"
    
    # Test C-CPI-U factors
    inflation_factors = get_consumption_inflation_factors(2025, 5)
    assert len(inflation_factors) == 5
    assert inflation_factors[0] == 1.0  # Base year
    assert inflation_factors[1] > 1.0  # Should have inflation
    
    print("✓ Inflation factors working correctly")
    return True


def test_basic_simulation():
    """Test basic portfolio simulation runs."""
    print("Testing basic portfolio simulation...")
    
    params = {
        'n_simulations': 100,
        'n_years': 10,
        'initial_portfolio': 1_000_000,
        'current_age': 65,
        'include_mortality': True,
        'social_security': 30_000,
        'pension': 10_000,
        'employment_income': 0,
        'retirement_age': 65,
        'has_annuity': False,
        'annuity_type': 'Life Only',
        'annuity_annual': 0,
        'annuity_guarantee_years': 0,
        'annual_consumption': 60_000,
        'expected_return': 7.0,
        'return_volatility': 15.0,
        'dividend_yield': 2.0,
        'state': 'CA',
        'gender': 'Male',
    }
    
    results = simulate_portfolio(**params)
    
    # Check key results exist
    assert 'portfolio_paths' in results
    assert 'failure_year' in results
    assert 'alive_mask' in results
    
    # Check shapes
    assert results['portfolio_paths'].shape == (100, 11)  # n_sims x (n_years + 1)
    assert results['failure_year'].shape == (100,)
    assert results['alive_mask'].shape == (100, 11)
    
    # Check portfolios start at initial value
    assert np.all(results['portfolio_paths'][:, 0] == 1_000_000)
    
    # Check some survived
    survivors = np.sum(results['alive_mask'][:, -1])
    assert survivors > 0, "No one survived the simulation"
    
    print(f"✓ Basic simulation working ({survivors}/100 survived)")
    return True


def test_inflation_applied():
    """Test that inflation is applied to consumption and Social Security."""
    print("Testing inflation application...")
    
    params = {
        'n_simulations': 1,  # Single path for easier testing
        'n_years': 10,
        'initial_portfolio': 2_000_000,
        'current_age': 65,
        'include_mortality': False,  # No mortality for simpler test
        'social_security': 30_000,
        'pension': 0,
        'employment_income': 0,
        'retirement_age': 65,
        'has_annuity': False,
        'annuity_type': 'Life Only',
        'annuity_annual': 0,
        'annuity_guarantee_years': 0,
        'annual_consumption': 50_000,
        'expected_return': 0.0,  # No returns to isolate inflation effect
        'return_volatility': 0.0,
        'dividend_yield': 0.0,
        'state': 'CA',
        'gender': 'Male',
    }
    
    results = simulate_portfolio(**params)
    
    # With inflation, later withdrawals should be higher
    # (consumption grows with C-CPI-U, SS grows with CPI-W)
    withdrawals = results['gross_withdrawals'][0]
    
    # First year withdrawal should be consumption - SS
    # (approximately, ignoring taxes)
    first_withdrawal = withdrawals[0]
    expected_first = 50_000 - 30_000  # consumption - SS
    
    # Last year withdrawal should be higher due to inflation
    last_withdrawal = withdrawals[-1]
    
    # Should have increased by roughly 10-20% over 10 years
    assert last_withdrawal > first_withdrawal, "Withdrawals didn't increase with inflation"
    
    inflation_increase = (last_withdrawal - first_withdrawal) / first_withdrawal
    assert inflation_increase > 0.10, f"Inflation increase {inflation_increase:.1%} seems too low"
    
    print(f"✓ Inflation applied correctly ({inflation_increase:.1%} increase over 10 years)")
    return True


def test_spouse_functionality():
    """Test spouse functionality works."""
    print("Testing spouse functionality...")
    
    params = {
        'n_simulations': 50,
        'n_years': 10,
        'initial_portfolio': 1_500_000,
        'current_age': 65,
        'include_mortality': True,
        'social_security': 25_000,
        'pension': 0,
        'employment_income': 0,
        'retirement_age': 65,
        'has_annuity': False,
        'annuity_type': 'Life Only',
        'annuity_annual': 0,
        'annuity_guarantee_years': 0,
        'annual_consumption': 80_000,
        'expected_return': 6.0,
        'return_volatility': 12.0,
        'dividend_yield': 2.0,
        'state': 'CA',
        'gender': 'Male',
        # Spouse parameters
        'has_spouse': True,
        'spouse_age': 63,
        'spouse_gender': 'Female',
        'spouse_social_security': 20_000,
        'spouse_pension': 5_000,
        'spouse_employment_income': 0,
        'spouse_retirement_age': 65,
    }
    
    results = simulate_portfolio(**params)
    
    # Check spouse alive mask exists
    assert 'spouse_alive_mask' in results
    assert results['spouse_alive_mask'].shape == (50, 11)
    
    # Some spouses should survive
    spouse_survivors = np.sum(results['spouse_alive_mask'][:, -1])
    assert spouse_survivors > 0, "No spouses survived"
    
    print(f"✓ Spouse functionality working ({spouse_survivors}/50 spouses survived)")
    return True


if __name__ == "__main__":
    print("Running FinSim basic functionality tests")
    print("=" * 60)
    
    tests = [
        test_inflation_factors,
        test_basic_simulation,
        test_inflation_applied,
        test_spouse_functionality,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All tests passed! ✓")
    else:
        print(f"Some tests failed. Please investigate.")
        exit(1)