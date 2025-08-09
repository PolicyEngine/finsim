#!/usr/bin/env python3
"""Test if random number generation is working correctly."""

import numpy as np

print("Testing random number generation in a loop")
print("=" * 50)

n_sims = 5
n_years = 10

# Track returns for each simulation
returns_matrix = np.zeros((n_sims, n_years))

for year in range(n_years):
    # Generate random numbers (same as in simulation)
    z = np.random.randn(n_sims)
    
    # Calculate returns
    mu = 0.07
    sigma = 0.15
    log_returns = (mu - 0.5 * sigma**2) + sigma * z
    growth_factor = np.exp(log_returns)
    
    returns_matrix[:, year] = (growth_factor - 1) * 100
    
    if year < 3:
        print(f"\nYear {year+1}:")
        print(f"  z values: {z}")
        print(f"  Returns: {returns_matrix[:, year]}")

print("\n" + "=" * 50)
print("Checking if any simulation has constant returns:")

for sim in range(n_sims):
    sim_returns = returns_matrix[sim, :]
    unique_returns = np.unique(np.round(sim_returns, 1))
    if len(unique_returns) < 5:  # Less than 5 unique values in 10 years
        print(f"  Sim {sim}: Only {len(unique_returns)} unique returns! Returns: {sim_returns}")
    else:
        print(f"  Sim {sim}: {len(unique_returns)} unique returns (OK)")

print("\n" + "=" * 50)
print("Now test with the ACTUAL simulation code...")

from finsim.portfolio_simulation import simulate_portfolio

# Run a small simulation
results = simulate_portfolio(
    n_simulations=5,
    n_years=10,
    initial_portfolio=500000,
    current_age=65,
    include_mortality=False,  # Simplify
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

print("\nChecking for constant growth in actual simulation:")
for sim in range(5):
    growth_rates = []
    for year in range(1, 10):
        if portfolio_paths[sim, year-1] > 0:
            growth = portfolio_paths[sim, year] / portfolio_paths[sim, year-1]
            growth_rates.append(growth)
    
    unique_growth = np.unique(np.round(growth_rates, 3))
    if len(unique_growth) < 3:
        print(f"  Sim {sim}: PROBLEM! Only {len(unique_growth)} unique growth rates")
        print(f"    Growth rates: {growth_rates[:5]}")
    else:
        print(f"  Sim {sim}: OK - {len(unique_growth)} unique growth rates")