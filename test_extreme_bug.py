#!/usr/bin/env python3
"""Test script to reproduce the extreme value bug."""

from finsim.portfolio_simulation import simulate_portfolio
import numpy as np

print("Testing portfolio simulation for extreme value bug...")
print("=" * 60)

# Run simulation with same parameters as the app
results = simulate_portfolio(
    n_simulations=100,  # Smaller for faster testing
    n_years=10,  # Shorter for faster testing
    initial_portfolio=500000,
    current_age=65,
    include_mortality=True,
    social_security=24000,
    pension=0,
    has_annuity=False,
    annuity_type='Fixed Period',
    annuity_annual=0,
    annuity_guarantee_years=0,
    annual_consumption=60000,
    expected_return=7.0,
    return_volatility=15.0,
    dividend_yield=2.0,
    state='CA'
)

portfolio_paths = results['portfolio_paths']
final_values = portfolio_paths[:, -1]

# Check for extreme values
percentiles = np.percentile(final_values, [50, 90, 95, 99, 100])
print(f"\nFinal portfolio percentiles:")
print(f"  Median: ${percentiles[0]:,.0f}")
print(f"  90th: ${percentiles[1]:,.0f}")
print(f"  95th: ${percentiles[2]:,.0f}")
print(f"  99th: ${percentiles[3]:,.0f}")
print(f"  Max: ${percentiles[4]:,.0f}")

# Check if any exceed $1B (shouldn't happen in 10 years)
extreme_count = np.sum(final_values > 1e9)
if extreme_count > 0:
    print(f"\n⚠️ WARNING: {extreme_count} simulations exceed $1B!")
    print("This indicates the bug is still present.")
else:
    print("\n✓ No extreme values detected")