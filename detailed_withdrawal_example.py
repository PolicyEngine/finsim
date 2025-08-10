#!/usr/bin/env python3
"""
Detailed example showing withdrawal mechanics and full data tracking.
This demonstrates a scenario where withdrawals are needed.
"""

import numpy as np
import pandas as pd
from finsim.portfolio_simulation import simulate_portfolio

# Parameters for someone who needs withdrawals
params = {
    'n_simulations': 3,  # 3 simulations to show variance
    'n_years': 5,
    'initial_portfolio': 500_000,  # Smaller portfolio
    'current_age': 65,
    'retirement_age': 65,
    
    # Income sources (less than consumption)
    'social_security': 20_000,
    'pension': 5_000,
    'employment_income': 0,
    
    # Higher spending need
    'annual_consumption': 80_000,  # Much higher than income
    
    # Market assumptions
    'expected_return': 7.0,
    'return_volatility': 15.0,
    'dividend_yield': 2.0,
    
    # Other parameters
    'state': 'CA',
    'include_mortality': True,  # Include mortality
    'gender': 'Male',
    
    # No annuity
    'has_annuity': False,
    'annuity_type': 'Life Only',
    'annuity_annual': 0,
    'annuity_guarantee_years': 0,
    'has_spouse': False,
}

print("DETAILED WITHDRAWAL SIMULATION WITH FULL DATA TRACKING")
print("=" * 80)
print("\nScenario: Retiree with high consumption relative to guaranteed income")
print(f"  Portfolio: ${params['initial_portfolio']:,.0f}")
print(f"  Social Security + Pension: ${params['social_security'] + params['pension']:,.0f}/year")
print(f"  Consumption Need: ${params['annual_consumption']:,.0f}/year")
print(f"  Shortfall: ${params['annual_consumption'] - params['social_security'] - params['pension']:,.0f}/year (before dividends)")
print()

# Run simulation
np.random.seed(42)
results = simulate_portfolio(**params)

print("FULL DATA STRUCTURE:")
print("-" * 80)
print("\nAll arrays tracked for EVERY simulation and EVERY year:")
print()

# Show the complete data structure for all simulations
for sim in range(params['n_simulations']):
    print(f"\nSIMULATION {sim + 1}:")
    print("-" * 40)
    
    # Check if person died
    death_year = None
    if not results['alive_mask'][sim, -1]:
        death_indices = np.where(~results['alive_mask'][sim, :])[0]
        if len(death_indices) > 0:
            death_year = death_indices[0]
    
    # Check if portfolio failed
    failure_year = results['failure_year'][sim]
    if failure_year <= params['n_years']:
        print(f"  *** PORTFOLIO FAILED IN YEAR {failure_year} ***")
    if death_year is not None:
        print(f"  *** DEATH IN YEAR {death_year} ***")
    
    # Create DataFrame for this simulation
    df_data = {
        'Year': list(range(1, params['n_years'] + 1)),
        'Age': [params['current_age'] + i + 1 for i in range(params['n_years'])],
        'Alive': results['alive_mask'][sim, 1:],
        'Portfolio_Start': results['portfolio_paths'][sim, :-1],
        'Dividends': results['dividend_income'][sim, :],
        'Gross_Withdrawal': results['gross_withdrawals'][sim, :],
        'Capital_Gains': results['capital_gains'][sim, :],
        'Tax_Owed': results['taxes_owed'][sim, :],
        'Tax_Paid': results['taxes_paid'][sim, :],
        'Portfolio_End': results['portfolio_paths'][sim, 1:],
    }
    
    df = pd.DataFrame(df_data)
    pd.set_option('display.float_format', '{:,.0f}'.format)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(df.to_string(index=False))
    
    # Final cost basis
    print(f"  Final Cost Basis: ${results['cost_basis'][sim]:,.0f}")
    
    if death_year is not None and death_year > 0:
        print(f"  Estate at Death: ${results['estate_at_death'][sim]:,.0f}")

print("\n" + "=" * 80)
print("AGGREGATED STATISTICS ACROSS ALL SIMULATIONS:")
print("-" * 80)

# Calculate statistics
n_failures = np.sum(results['failure_year'] <= params['n_years'])
n_deaths = np.sum(~results['alive_mask'][:, -1])
avg_final_portfolio = np.mean(results['portfolio_paths'][:, -1])
median_final_portfolio = np.median(results['portfolio_paths'][:, -1])

print(f"\nOutcomes:")
print(f"  Portfolio Failures: {n_failures}/{params['n_simulations']} ({100*n_failures/params['n_simulations']:.0f}%)")
print(f"  Deaths: {n_deaths}/{params['n_simulations']} ({100*n_deaths/params['n_simulations']:.0f}%)")
print(f"  Average Final Portfolio: ${avg_final_portfolio:,.0f}")
print(f"  Median Final Portfolio: ${median_final_portfolio:,.0f}")

# Average withdrawal patterns
avg_withdrawals = np.mean(results['gross_withdrawals'], axis=0)
avg_cap_gains = np.mean(results['capital_gains'], axis=0)
avg_taxes = np.mean(results['taxes_owed'], axis=0)

print(f"\nAverage Annual Flows:")
for year in range(params['n_years']):
    print(f"  Year {year+1}: Withdrawal=${avg_withdrawals[year]:,.0f}, "
          f"Cap Gains=${avg_cap_gains[year]:,.0f}, "
          f"Tax=${avg_taxes[year]:,.0f}")

print("\n" + "=" * 80)
print("KEY OBSERVATIONS ON DATA TRACKING:")
print("-" * 80)
print("""
1. COMPLETE SIMULATION STATE: For each of the 3 simulations, we track:
   - Full portfolio path (start and end values each year)
   - All cash flows (dividends, withdrawals, taxes)
   - Mortality status (alive/dead each year)
   - Capital gains realization
   - Cost basis evolution

2. TAX MECHANICS VISIBLE:
   - Tax_Owed: Calculated on current year's income
   - Tax_Paid: Previous year's tax liability paid this year
   - Note the one-year lag between owed and paid

3. WITHDRAWAL MECHANICS:
   - Gross_Withdrawal: Amount taken from portfolio
   - Capital_Gains: Taxable portion of withdrawal
   - Cost basis tracking ensures accurate gain calculation

4. MONTE CARLO VARIATION:
   - Each simulation has different returns (same expected value)
   - Mortality is randomly determined per SSA tables
   - Some paths fail, some succeed

5. POLICYENGINE INTEGRATION:
   - Taxes calculated using actual US tax code
   - Includes federal and state taxes
   - Handles Social Security taxation thresholds
   - Accounts for standard deductions, tax brackets, etc.
""")