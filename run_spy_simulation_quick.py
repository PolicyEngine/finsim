#!/usr/bin/env python
"""
Quick SPY (S&P 500) settlement analysis simulation with progress tracking.
"""

import numpy as np
import pandas as pd
import time
from finsim.stacked_simulation import (
    create_scenario_config,
    simulate_stacked_scenarios,
    analyze_confidence_thresholds,
    summarize_confidence_thresholds
)

# Settlement parameters
TOTAL_SETTLEMENT = 677_530
ANNUITY_COST = 527_530
IMMEDIATE_CASH = TOTAL_SETTLEMENT - ANNUITY_COST

# Annuity annual payments
ANNUITY_A_ANNUAL = 3_516.29 * 12  # $42,195
ANNUITY_B_ANNUAL = 4_057.78 * 12  # $48,693
ANNUITY_C_ANNUAL = 5_397.12 * 12  # $64,765

print("=" * 70)
print("PERSONAL INJURY SETTLEMENT ANALYSIS - SPY (S&P 500)")
print("QUICK VERSION - 500 simulations for faster results")
print("=" * 70)
print(f"\nTotal Settlement: ${TOTAL_SETTLEMENT:,}")
print(f"Annuity Cost: ${ANNUITY_COST:,}")
print(f"Immediate Cash: ${IMMEDIATE_CASH:,}")

# Create scenario configurations with SPY naming
scenarios = [
    create_scenario_config(
        name="100% Stocks (SPY)",
        initial_portfolio=TOTAL_SETTLEMENT,
        has_annuity=False
    ),
    create_scenario_config(
        name="Annuity A + SPY",
        initial_portfolio=IMMEDIATE_CASH,
        has_annuity=True,
        annuity_type="Life Contingent with Guarantee",
        annuity_annual=ANNUITY_A_ANNUAL,
        annuity_guarantee_years=15
    ),
    create_scenario_config(
        name="Annuity B + SPY",
        initial_portfolio=IMMEDIATE_CASH,
        has_annuity=True,
        annuity_type="Fixed Period",
        annuity_annual=ANNUITY_B_ANNUAL,
        annuity_guarantee_years=15
    ),
    create_scenario_config(
        name="Annuity C + SPY",
        initial_portfolio=IMMEDIATE_CASH,
        has_annuity=True,
        annuity_type="Fixed Period",
        annuity_annual=ANNUITY_C_ANNUAL,
        annuity_guarantee_years=10
    )
]

# Base parameters adjusted for SPY characteristics
base_params = {
    "current_age": 65,
    "gender": "Male",
    "social_security": 24_000,
    "pension": 0,
    "employment_income": 0,
    "retirement_age": 65,
    "expected_return": 7.5,  # SPY: 7.5% vs VT: 7.0%
    "return_volatility": 17.0,  # SPY: 17% vs VT: 18%
    "dividend_yield": 2.0,  # SPY: 2.0% vs VT: 1.8%
    "state": "CA",
    "include_mortality": True,
}

print("\nSPY Market Parameters:")
print(f"  Expected Return: {base_params['expected_return']}% (VT: 7.0%)")
print(f"  Volatility: {base_params['return_volatility']}% (VT: 18.0%)")
print(f"  Dividend Yield: {base_params['dividend_yield']}% (VT: 1.8%)")

# Use fewer spending levels for quicker testing
spending_levels = list(range(40_000, 85_000, 5_000))

print("\n" + "=" * 70)
print("RUNNING QUICK SIMULATION")
print("=" * 70)
print(f"Testing {len(spending_levels)} spending levels: ${min(spending_levels):,} to ${max(spending_levels):,}")
print(f"Running {len(scenarios)} scenarios with 500 simulations each")
print("Starting simulation...\n")

start_time = time.time()

# Run simulations
results = simulate_stacked_scenarios(
    scenarios=scenarios,
    spending_levels=spending_levels,
    n_simulations=500,  # Reduced for quick test
    n_years=30,
    base_params=base_params,
    include_percentiles=True,
    random_seed=42
)

elapsed = time.time() - start_time
print(f"\nSimulation completed in {elapsed:.1f} seconds")
print(f"Processed {len(results)} scenario-spending combinations")

# Analyze confidence thresholds
confidence_levels = [90, 75, 50]
scenario_names = [s["name"] for s in scenarios]

# Create summary table
summary_df = summarize_confidence_thresholds(
    results=results,
    scenarios=scenario_names,
    confidence_levels=confidence_levels
)

print("\n" + "=" * 70)
print("SUSTAINABLE SPENDING AT KEY CONFIDENCE LEVELS (SPY)")
print("=" * 70)
print("(All amounts in 2025 dollars)\n")

# Format and display summary
formatted_summary = summary_df.copy()
for col in formatted_summary.columns[1:]:
    formatted_summary[col] = formatted_summary[col].apply(lambda x: f"${x:,.0f}")

print(formatted_summary.to_string(index=False))

# Quick comparison at 90% confidence
print("\n" + "=" * 70)
print("90% CONFIDENCE COMPARISON (SPY)")
print("=" * 70)

best_spending = 0
best_scenario = ""

for scenario_name in scenario_names:
    thresholds = analyze_confidence_thresholds(results, scenario_name, [90])
    spending = thresholds[90]
    print(f"{scenario_name}: ${spending:,.0f}/year")
    
    if spending > best_spending:
        best_spending = spending
        best_scenario = scenario_name

print(f"\n→ Best option at 90% confidence: {best_scenario}")
print(f"  Sustainable spending: ${best_spending:,.0f}/year")

print("\n" + "=" * 70)
print("SPY CHARACTERISTICS vs VT")
print("=" * 70)
print("• Higher expected return should improve sustainable spending")
print("• Lower volatility should provide more consistent outcomes")
print("• US-only exposure (less diversification than VT)")
print("• Historically strong S&P 500 performance")

print("\n" + "=" * 70)
print("Note: This is a quick simulation with 500 runs.")
print("For more accurate results, run the full simulation with 2,000+ runs.")
print("=" * 70)