#!/usr/bin/env python
"""
Run the SPY (S&P 500) settlement analysis simulation.
"""

import numpy as np
import pandas as pd
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
print("=" * 70)
print(f"\nTotal Settlement: ${TOTAL_SETTLEMENT:,}")
print(f"Annuity Cost: ${ANNUITY_COST:,}")
print(f"Immediate Cash: ${IMMEDIATE_CASH:,}")
print(f"\nAnnuity A: ${ANNUITY_A_ANNUAL:,.0f}/year (life with 15-yr guarantee)")
print(f"Annuity B: ${ANNUITY_B_ANNUAL:,.0f}/year (15 years)")
print(f"Annuity C: ${ANNUITY_C_ANNUAL:,.0f}/year (10 years)")

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
    "expected_return": 7.5,  # 7.5% expected return for SPY (vs 7.0% for VT)
    "return_volatility": 17.0,  # 17% volatility for SPY (vs 18% for VT)
    "dividend_yield": 2.0,  # 2.0% dividend yield for SPY (vs 1.8% for VT)
    "state": "CA",
    "include_mortality": True,
}

print("\n" + "=" * 70)
print("SPY PARAMETERS")
print("=" * 70)
print(f"Expected Return: {base_params['expected_return']}% (VT: 7.0%)")
print(f"Volatility: {base_params['return_volatility']}% (VT: 18.0%)")
print(f"Dividend Yield: {base_params['dividend_yield']}% (VT: 1.8%)")

# Define spending levels
spending_levels = list(range(30_000, 105_000, 5_000))

print("\n" + "=" * 70)
print("RUNNING SIMULATIONS")
print("=" * 70)
print(f"Testing {len(spending_levels)} spending levels: ${min(spending_levels):,} to ${max(spending_levels):,}")
print(f"Running {len(scenarios)} scenarios with 2,000 simulations each")
print("This may take a few minutes...")

# Run simulations with verbose output
results = simulate_stacked_scenarios(
    scenarios=scenarios,
    spending_levels=spending_levels,
    n_simulations=2000,
    n_years=30,
    base_params=base_params,
    include_percentiles=True,
    random_seed=42,
    verbose=True  # Add verbose flag for progress updates
)

print(f"\nCompleted {len(results)} scenario-spending combinations")

# Analyze confidence thresholds
confidence_levels = [90, 75, 50, 25, 10]
scenario_names = [s["name"] for s in scenarios]

# Create summary table
summary_df = summarize_confidence_thresholds(
    results=results,
    scenarios=scenario_names,
    confidence_levels=confidence_levels
)

print("\n" + "=" * 70)
print("SUSTAINABLE SPENDING AT VARIOUS CONFIDENCE LEVELS (SPY)")
print("=" * 70)
print("(All amounts in 2025 dollars)\n")

# Format and display summary
formatted_summary = summary_df.copy()
for col in formatted_summary.columns[1:]:
    formatted_summary[col] = formatted_summary[col].apply(lambda x: f"${x:,.0f}")

print(formatted_summary.to_string(index=False))

# Analyze key confidence levels
print("\n" + "=" * 70)
print("KEY FINDINGS (SPY)")
print("=" * 70)

for confidence in [90, 75, 50]:
    print(f"\nAt {confidence}% confidence level:")
    best_spending = 0
    best_scenario = ""
    
    for scenario_name in scenario_names:
        thresholds = analyze_confidence_thresholds(results, scenario_name, [confidence])
        spending = thresholds[confidence]
        print(f"  {scenario_name}: ${spending:,.0f}/year")
        
        if spending > best_spending:
            best_spending = spending
            best_scenario = scenario_name
    
    print(f"  → Best option: {best_scenario}")

# Portfolio outcomes at 90% confidence
df = pd.DataFrame(results)
print("\n" + "=" * 70)
print("PORTFOLIO OUTCOMES AT 90% CONFIDENCE SPENDING (SPY)")
print("=" * 70)

for scenario_name in scenario_names:
    thresholds = analyze_confidence_thresholds(results, scenario_name, [90])
    target_spending = thresholds[90]
    
    scenario_results = df[df["scenario"] == scenario_name]
    closest_idx = (scenario_results["spending"] - target_spending).abs().idxmin()
    result = scenario_results.loc[closest_idx]
    
    print(f"\n{scenario_name} at ${target_spending:,.0f}/year:")
    print(f"  Success rate: {result['success_rate']:.1%}")
    print(f"  Median final portfolio: ${result['median_final']:,.0f}")
    print(f"  10th percentile: ${result['p10_final']:,.0f}")
    print(f"  90th percentile: ${result['p90_final']:,.0f}")

print("\n" + "=" * 70)
print("SPY vs VT COMPARISON")
print("=" * 70)
print("\nSPY Advantages:")
print("  • Higher expected return (7.5% vs 7.0%)")
print("  • Lower volatility (17% vs 18%)")
print("  • Higher dividend yield (2.0% vs 1.8%)")
print("  • Should result in better sustainable spending levels")
print("\nSPY Considerations:")
print("  • US-only exposure (no international diversification)")
print("  • Large-cap focus (S&P 500 companies)")
print("  • Historically strong performance but concentration risk")

# Save results
df.to_csv('settlement_analysis_spy_results.csv', index=False)
summary_df.to_csv('settlement_spy_confidence_summary.csv', index=False)
print("\n" + "=" * 70)
print("Results saved to:")
print("  • settlement_analysis_spy_results.csv")
print("  • settlement_spy_confidence_summary.csv")
print("=" * 70)