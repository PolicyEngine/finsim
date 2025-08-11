#!/usr/bin/env python3
"""
Analyze individual simulation trajectories to understand how they evolve
"""

import numpy as np
import pandas as pd
from finsim.portfolio_simulation import simulate_portfolio

# Replicate exact parameters from screenshot
params = {
    'n_simulations': 1000,
    'n_years': 30,
    'initial_portfolio': 500_000,
    'current_age': 65,
    'include_mortality': True,
    'gender': 'Male',
    'social_security': 24_000,
    'pension': 0,
    'employment_income': 0,
    'retirement_age': 65,
    'annual_consumption': 60_000,
    'expected_return': 7.0,
    'return_volatility': 15.0,
    'dividend_yield': 2.0,
    'state': 'CA',
    'has_annuity': False,
}

print("SIMULATION TRAJECTORY ANALYSIS")
print("=" * 80)
print(f"Parameters:")
print(f"  Portfolio: ${params['initial_portfolio']:,}")
print(f"  Spending: ${params['annual_consumption']:,}/year")
print(f"  Social Security: ${params['social_security']:,}/year (with COLA)")
print(f"  Initial withdrawal need: ${params['annual_consumption'] - params['social_security']:,}/year")
print()

# Run simulation with seed for reproducibility
np.random.seed(42)
results = simulate_portfolio(**params)

# Extract all the data arrays
portfolio_paths = results['portfolio_paths']
failure_year = results['failure_year']
alive_mask = results['alive_mask']
dividend_income = results['dividend_income']
capital_gains = results['capital_gains']
gross_withdrawals = results['gross_withdrawals']
taxes_owed = results['taxes_owed']
taxes_paid = results['taxes_paid']

# Find interesting trajectories
final_values = portfolio_paths[:, -1]
success_mask = failure_year > 30

# Find median performer (closest to median final value)
median_final = np.median(final_values)
if median_final == 0:
    # Find median failure time among failures
    failures_only = failure_year[failure_year <= 30]
    median_failure_year = np.median(failures_only)
    # Find simulation that failed closest to median failure year
    distances = np.abs(failure_year - median_failure_year)
    distances[failure_year > 30] = 999  # Exclude successes
    median_sim = np.argmin(distances)
    print(f"Median trajectory: Simulation #{median_sim} (failed in year {failure_year[median_sim]:.0f})")
else:
    distances = np.abs(final_values - median_final)
    median_sim = np.argmin(distances)
    print(f"Median trajectory: Simulation #{median_sim} (final value ${final_values[median_sim]:,.0f})")

# Also find a success case and early failure for comparison
success_sims = np.where(success_mask)[0]
failure_sims = np.where(~success_mask)[0]

if len(success_sims) > 0:
    # Find median success
    success_finals = final_values[success_sims]
    median_success_val = np.median(success_finals)
    success_distances = np.abs(final_values - median_success_val)
    success_distances[~success_mask] = 999999
    success_sim = np.argmin(success_distances)

if len(failure_sims) > 0:
    # Find early failure (25th percentile of failure times)
    early_failure_year = np.percentile(failure_year[failure_sims], 25)
    fail_distances = np.abs(failure_year - early_failure_year)
    fail_distances[success_mask] = 999
    early_fail_sim = np.argmin(fail_distances)

print("\n" + "=" * 80)
print("DETAILED TRAJECTORY: MEDIAN CASE")
print("=" * 80)

def analyze_trajectory(sim_idx, label):
    """Analyze a single simulation trajectory"""
    print(f"\n{label} (Simulation #{sim_idx}):")
    print("-" * 60)
    
    # Create year-by-year breakdown
    data = []
    
    # Track cost basis
    initial_basis = params['initial_portfolio']
    cost_basis = initial_basis
    
    for year in range(31):  # 0 to 30
        age = params['current_age'] + year
        portfolio = portfolio_paths[sim_idx, year]
        
        if year < 30:  # We have data for these
            div = dividend_income[sim_idx, year] if year < len(dividend_income[0]) else 0
            withdrawal = gross_withdrawals[sim_idx, year] if year < len(gross_withdrawals[0]) else 0
            cap_gains = capital_gains[sim_idx, year] if year < len(capital_gains[0]) else 0
            tax_owed = taxes_owed[sim_idx, year] if year < len(taxes_owed[0]) else 0
            tax_paid = taxes_paid[sim_idx, year] if year < len(taxes_paid[0]) else 0
            alive = alive_mask[sim_idx, year]
            
            # Calculate implied return
            if year > 0:
                prev_portfolio = portfolio_paths[sim_idx, year-1]
                if prev_portfolio > 0:
                    # Portfolio return = (end + withdrawals - start) / start
                    implied_return = (portfolio + withdrawal - prev_portfolio) / prev_portfolio
                else:
                    implied_return = 0
            else:
                implied_return = 0
            
            # Update cost basis (rough approximation)
            if withdrawal > 0 and cost_basis > 0 and portfolio > 0:
                withdrawal_fraction = withdrawal / (portfolio + withdrawal)
                cost_basis = cost_basis * (1 - withdrawal_fraction)
            
            data.append({
                'Year': year,
                'Age': age,
                'Portfolio': portfolio,
                'Dividends': div,
                'Withdrawal': withdrawal,
                'Cap_Gains': cap_gains,
                'Tax_Owed': tax_owed,
                'Tax_Paid': tax_paid,
                'Return%': implied_return * 100,
                'Alive': alive
            })
    
    df = pd.DataFrame(data)
    
    # Show key years
    key_years = [0, 5, 10, 15, 20, 25, 30]
    print("\nKey Years:")
    print(df[df['Year'].isin(key_years)][['Year', 'Age', 'Portfolio', 'Withdrawal', 'Cap_Gains', 'Tax_Paid', 'Return%']].to_string(index=False))
    
    # Summarize what happened
    print(f"\nSummary:")
    if failure_year[sim_idx] <= 30:
        print(f"  ❌ FAILED in year {failure_year[sim_idx]:.0f} (age {65 + failure_year[sim_idx]:.0f})")
    else:
        print(f"  ✅ SUCCESS - maintained portfolio through age 95")
        print(f"  Final portfolio: ${portfolio_paths[sim_idx, -1]:,.0f}")
    
    if not alive_mask[sim_idx, -1]:
        death_year = np.where(~alive_mask[sim_idx, :])[0][0]
        print(f"  💀 Died in year {death_year} (age {65 + death_year})")
    
    # Calculate some statistics
    total_withdrawn = np.sum(gross_withdrawals[sim_idx, :])
    total_taxes = np.sum(taxes_paid[sim_idx, :])
    total_dividends = np.sum(dividend_income[sim_idx, :])
    
    print(f"\nLifetime totals:")
    print(f"  Total withdrawn: ${total_withdrawn:,.0f}")
    print(f"  Total taxes paid: ${total_taxes:,.0f}")
    print(f"  Total dividends: ${total_dividends:,.0f}")
    
    # Show the critical years around failure
    if failure_year[sim_idx] <= 30:
        fail_yr = int(failure_year[sim_idx])
        print(f"\nYears around failure:")
        start_yr = max(0, fail_yr - 3)
        end_yr = min(30, fail_yr + 1)
        print(df[start_yr:end_yr][['Year', 'Age', 'Portfolio', 'Withdrawal', 'Return%']].to_string(index=False))

# Analyze the median case
analyze_trajectory(median_sim, "MEDIAN TRAJECTORY")

# Compare with a success case
if len(success_sims) > 0:
    print("\n" + "=" * 80)
    analyze_trajectory(success_sim, "MEDIAN SUCCESS CASE")

# Compare with an early failure
if len(failure_sims) > 0:
    print("\n" + "=" * 80)
    analyze_trajectory(early_fail_sim, "EARLY FAILURE CASE")

# Overall statistics
print("\n" + "=" * 80)
print("AGGREGATE STATISTICS")
print("=" * 80)
print(f"Success rate: {100*np.mean(success_mask):.1f}%")
print(f"Median final portfolio: ${np.median(final_values):,.0f}")
print(f"Deaths: {np.sum(~alive_mask[:, -1])}/{params['n_simulations']}")

# Distribution of failure years
failures = failure_year[failure_year <= 30]
if len(failures) > 0:
    print(f"\nFailure distribution:")
    print(f"  25th percentile: Year {np.percentile(failures, 25):.0f}")
    print(f"  Median: Year {np.percentile(failures, 50):.0f}")
    print(f"  75th percentile: Year {np.percentile(failures, 75):.0f}")

# Save detailed data for one trajectory
print(f"\nSaving detailed data for median trajectory to CSV...")
median_df = pd.DataFrame({
    'Year': range(31),
    'Age': range(65, 96),
    'Portfolio': portfolio_paths[median_sim, :],
    'Dividends': list(dividend_income[median_sim, :]) + [0],
    'Gross_Withdrawal': list(gross_withdrawals[median_sim, :]) + [0],
    'Capital_Gains': list(capital_gains[median_sim, :]) + [0],
    'Taxes_Owed': list(taxes_owed[median_sim, :]) + [0],
    'Taxes_Paid': list(taxes_paid[median_sim, :]) + [0],
    'Alive': alive_mask[median_sim, :],
})
median_df.to_csv('median_trajectory.csv', index=False)
print("Saved to median_trajectory.csv")