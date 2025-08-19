#!/usr/bin/env python
"""
Simple test of SPY simulation with minimal parameters.
"""

import numpy as np
from finsim.stacked_simulation import create_scenario_config, simulate_stacked_scenarios

print("Testing SPY simulation with minimal parameters...")

# Just test one scenario with a few spending levels
scenarios = [
    create_scenario_config(
        name="100% SPY Test",
        initial_portfolio=677_530,
        has_annuity=False
    )
]

base_params = {
    "current_age": 65,
    "gender": "Male", 
    "social_security": 24_000,
    "pension": 0,
    "employment_income": 0,
    "retirement_age": 65,
    "expected_return": 7.5,  # SPY return
    "return_volatility": 17.0,  # SPY volatility
    "dividend_yield": 2.0,  # SPY dividend
    "state": "CA",
    "include_mortality": True,
}

# Just 3 spending levels
spending_levels = [50_000, 60_000, 70_000]

print(f"Running 1 scenario, 3 spending levels, 100 simulations...")
print(f"SPY parameters: {base_params['expected_return']}% return, {base_params['return_volatility']}% volatility")

try:
    results = simulate_stacked_scenarios(
        scenarios=scenarios,
        spending_levels=spending_levels,
        n_simulations=100,
        n_years=30,
        base_params=base_params,
        include_percentiles=False,
        random_seed=42
    )
    
    print("\nResults:")
    for r in results:
        print(f"  Spending ${r['spending']:,}: {r['success_rate']:.1%} success rate")
    
    print("\nSimulation completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()