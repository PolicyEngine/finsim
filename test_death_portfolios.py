#!/usr/bin/env python3
"""Test how death affects portfolio values in simulation."""

import numpy as np
from finsim.portfolio_simulation import simulate_portfolio

# Test with high mortality to see what happens
params = {
    "n_simulations": 100,
    "n_years": 30,
    "initial_portfolio": 500_000,
    "current_age": 85,  # Older age for higher mortality
    "include_mortality": True,
    "gender": "Male",
    "social_security": 24_000,
    "pension": 0,
    "employment_income": 0,
    "retirement_age": 85,
    "annual_consumption": 60_000,
    "expected_return": 7.0,
    "return_volatility": 15.0,
    "dividend_yield": 2.0,
    "state": "CA",
    "has_annuity": False,
}

np.random.seed(42)
results = simulate_portfolio(**params)

# Check correlation between death and portfolio values
alive_at_end = results["alive_mask"][:, -1]
final_portfolios = results["portfolio_paths"][:, -1]

print("Death vs Portfolio Analysis:")
print(f"Deaths: {np.sum(~alive_at_end)}/{params['n_simulations']}")
print(f"Average portfolio if alive at end: ${np.mean(final_portfolios[alive_at_end]):,.0f}")
print(f"Average portfolio if dead at end: ${np.mean(final_portfolios[~alive_at_end]):,.0f}")

# Check if death causes portfolio to become 0
estate_at_death = results["estate_at_death"]
dead_with_estate = np.sum((~alive_at_end) & (estate_at_death > 0))
print(f"Dead with non-zero estate: {dead_with_estate}")

# Check what we're counting as successes
failure_year = results["failure_year"]
success_count = np.sum(failure_year > 30)
print(f"\nSuccess counting:")
print(f"Successes (failure_year > 30): {success_count}")
print(f"Portfolio > 0 at end: {np.sum(final_portfolios > 0)}")
print(f"Alive at end: {np.sum(alive_at_end)}")

# Cross-tabulation
print("\nCross-tabulation:")
alive_success = np.sum(alive_at_end & (failure_year > 30))
alive_failure = np.sum(alive_at_end & (failure_year <= 30))
dead_success = np.sum((~alive_at_end) & (failure_year > 30))
dead_failure = np.sum((~alive_at_end) & (failure_year <= 30))

print(f"Alive & Success: {alive_success}")
print(f"Alive & Failure: {alive_failure}")
print(f"Dead & Success: {dead_success}")
print(f"Dead & Failure: {dead_failure}")