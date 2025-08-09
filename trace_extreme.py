#!/usr/bin/env python3
"""Trace through an extreme simulation to understand the bug."""

import numpy as np
from scipy import stats

# Set seed for reproducibility
np.random.seed(906)  # Use same seed as extreme simulation 906

# Parameters
n_years = 30
initial_portfolio = 500000
mu = 0.07
sigma = 0.15
dividend_yield = 0.02
annual_consumption = 60000
social_security = 24000

print("Tracing extreme portfolio growth step by step")
print("=" * 60)

portfolio = initial_portfolio
cost_basis = initial_portfolio

for year in range(1, min(11, n_years + 1)):  # First 10 years
    print(f"\n--- Year {year} ---")
    print(f"Starting portfolio: ${portfolio:,.0f}")
    
    # Generate return (using same logic as simulation)
    # This is what the CURRENT code does:
    z = np.random.randn(1)[0]
    
    # Check for moderate extreme (5% chance)
    if np.random.random() < 0.05:
        sign = 1 if z > 0 else -1
        magnitude = np.random.uniform(2, 3)
        z = sign * magnitude
        print(f"  Moderate extreme event! z = {z:.2f}")
    
    # Check for rare extreme (0.5% chance)
    if np.random.random() < 0.005:
        sign = np.random.choice([-1, 1])
        magnitude = np.random.uniform(3, 3.5)
        z = sign * magnitude
        print(f"  RARE extreme event! z = {z:.2f}")
    
    z_clipped = np.clip(z, -3.5, 3.5)
    
    log_return = (mu - 0.5 * sigma**2) + sigma * z_clipped
    growth_factor = np.exp(log_return)
    
    print(f"  z-score: {z:.2f} (clipped: {z_clipped:.2f})")
    print(f"  Growth factor: {growth_factor:.3f} ({(growth_factor-1)*100:.1f}% return)")
    
    # Apply growth
    portfolio_after_growth = portfolio * growth_factor
    print(f"  After growth: ${portfolio_after_growth:,.0f}")
    
    # Calculate dividends (2% of pre-growth portfolio)
    dividends = portfolio * dividend_yield
    print(f"  Dividends: ${dividends:,.0f}")
    
    # Calculate withdrawal need
    total_income = social_security + dividends
    withdrawal_need = max(0, annual_consumption - total_income)
    print(f"  Income available: ${total_income:,.0f} (SS + dividends)")
    print(f"  Withdrawal needed: ${withdrawal_need:,.0f}")
    
    # Update portfolio
    portfolio = portfolio_after_growth - withdrawal_need
    print(f"  Final portfolio: ${portfolio:,.0f}")
    
    # Check if withdrawal is approaching zero
    if withdrawal_need < 1000:
        print(f"  ⚠️ Withdrawals nearly zero - portfolio will compound freely!")

print(f"\n" + "=" * 60)
print(f"After {year} years: ${portfolio:,.0f}")

# Show what happens with maximum returns
print("\n" + "=" * 60)
print("What if we get max returns (z=3.5) repeatedly?")
test_portfolio = initial_portfolio
max_growth = np.exp((mu - 0.5 * sigma**2) + sigma * 3.5)
print(f"Max growth factor per year: {max_growth:.3f} ({(max_growth-1)*100:.1f}% return)")

for y in [5, 10, 20, 30]:
    # Rough calculation ignoring withdrawals
    value = initial_portfolio * (max_growth ** y)
    print(f"After {y} years of max returns: ${value:,.0f}")