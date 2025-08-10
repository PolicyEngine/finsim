#!/usr/bin/env python3
"""Test that annuity_type=None doesn't cause errors when has_annuity=False"""

from finsim.portfolio_simulation import simulate_portfolio

# Test 1: No annuity with annuity_type=None (should work now)
params1 = {
    'n_simulations': 10,
    'n_years': 5,
    'initial_portfolio': 500_000,
    'current_age': 65,
    'include_mortality': False,
    'social_security': 30_000,
    'pension': 10_000,
    'employment_income': 0,
    'retirement_age': 65,
    'annual_consumption': 60_000,
    'expected_return': 7.0,
    'return_volatility': 15.0,
    'dividend_yield': 2.0,
    'state': 'CA',
    'has_annuity': False,
    # annuity_type not specified - should use default
}

print("Test 1: No annuity, annuity_type not specified...")
result1 = simulate_portfolio(**params1)
print(f"✅ Success! Portfolio after 5 years (mean): ${result1['portfolio_paths'][:, -1].mean():,.0f}")

# Test 2: Has annuity with valid type
params2 = params1.copy()
params2['has_annuity'] = True
params2['annuity_type'] = 'Life Only'
params2['annuity_annual'] = 20_000

print("\nTest 2: Has annuity with valid type...")
result2 = simulate_portfolio(**params2)
print(f"✅ Success! Annuity income year 1: ${result2['annuity_income'][0, 0]:,.0f}")

# Test 3: Has annuity with invalid type (should fail)
params3 = params1.copy()
params3['has_annuity'] = True
params3['annuity_type'] = 'Invalid Type'
params3['annuity_annual'] = 20_000

print("\nTest 3: Has annuity with invalid type...")
try:
    result3 = simulate_portfolio(**params3)
    print("❌ Should have failed but didn't!")
except ValueError as e:
    print(f"✅ Correctly failed with: {e}")

print("\nAll tests completed successfully!")