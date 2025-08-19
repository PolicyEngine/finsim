#!/usr/bin/env python3
"""Calculate mortality-adjusted IRR with 10% higher mortality risk."""

import numpy as np
import numpy_financial as npf
from finsim.mortality import get_mortality_rates

# Annuity cost and payments
ANNUITY_COST = 527_530
ANNUITY_A_ANNUAL = 42_195.48
ANNUITY_B_ANNUAL = 48_693.36
ANNUITY_C_ANNUAL = 64_765.44

print("=" * 80)
print("MORTALITY-ADJUSTED IRR - 10% HIGHER MORTALITY RISK")
print("=" * 80)
print(f"\nFor 65-year-old male with 10% higher mortality than baseline")
print(f"Initial Cost: ${ANNUITY_COST:,}")
print()

# Get baseline mortality rates and increase by 10%
baseline_mortality = get_mortality_rates("Male")
higher_mortality = {age: min(rate * 1.1, 1.0) for age, rate in baseline_mortality.items()}

def calculate_mortality_adjusted_cashflows(annual_payment, mortality_rates, guarantee_years=0, is_lifetime=True, max_years=40):
    """
    Calculate expected cash flows considering mortality.
    """
    starting_age = 65
    prob_alive = 1.0
    expected_cashflows = [-ANNUITY_COST]
    survival_probs = [1.0]
    
    for year in range(1, max_years + 1):
        age = starting_age + year
        mort_rate = mortality_rates.get(age - 1, 0)
        prob_alive = prob_alive * (1 - mort_rate)
        survival_probs.append(prob_alive)
        
        if is_lifetime:
            if year <= guarantee_years:
                expected_payment = annual_payment
            else:
                expected_payment = annual_payment * prob_alive
        else:
            if year <= guarantee_years:
                expected_payment = annual_payment
            else:
                expected_payment = 0
        
        expected_cashflows.append(expected_payment)
        
        if prob_alive < 0.001 and year > guarantee_years:
            break
    
    return expected_cashflows, survival_probs

print("1. COMPARISON: BASELINE vs 10% HIGHER MORTALITY")
print("-" * 40)

# Calculate for both baseline and higher mortality
cashflows_baseline, survival_baseline = calculate_mortality_adjusted_cashflows(
    ANNUITY_A_ANNUAL, baseline_mortality, guarantee_years=15, is_lifetime=True
)
cashflows_higher, survival_higher = calculate_mortality_adjusted_cashflows(
    ANNUITY_A_ANNUAL, higher_mortality, guarantee_years=15, is_lifetime=True
)

irr_baseline = npf.irr(cashflows_baseline) * 100
irr_higher = npf.irr(cashflows_higher) * 100

print("\nSurvival Probabilities from Age 65:")
print("\n Age  | Baseline | 10% Higher Mortality | Difference")
print("-" * 55)

key_ages = [70, 75, 80, 82, 85, 90, 95]
for age in key_ages:
    years = age - 65
    if years < min(len(survival_baseline), len(survival_higher)):
        baseline_prob = survival_baseline[years] * 100
        higher_prob = survival_higher[years] * 100
        diff = higher_prob - baseline_prob
        print(f"  {age:3d} |   {baseline_prob:5.1f}% |      {higher_prob:5.1f}%        | {diff:+6.1f}%")

print("\n2. IRR COMPARISON - ALL ANNUITIES")
print("-" * 40)

# Annuity A with higher mortality
expected_total_a_baseline = sum(cashflows_baseline[1:])
expected_total_a_higher = sum(cashflows_higher[1:])

print(f"\nAnnuity A (Lifetime with 15-yr guarantee):")
print(f"  Baseline mortality IRR:    {irr_baseline:.2f}%")
print(f"  10% higher mortality IRR:  {irr_higher:.2f}%")
print(f"  IRR difference:            {irr_higher - irr_baseline:+.2f}%")
print(f"  Expected total (baseline): ${expected_total_a_baseline:,.0f}")
print(f"  Expected total (higher):   ${expected_total_a_higher:,.0f}")
print(f"  Difference:                ${expected_total_a_higher - expected_total_a_baseline:,.0f}")

# Annuity B and C (unaffected by mortality)
cashflows_b = [-ANNUITY_COST] + [ANNUITY_B_ANNUAL] * 15
irr_b = npf.irr(cashflows_b) * 100

cashflows_c = [-ANNUITY_COST] + [ANNUITY_C_ANNUAL] * 10
irr_c = npf.irr(cashflows_c) * 100

print(f"\nAnnuity B (15 years guaranteed):")
print(f"  IRR: {irr_b:.2f}% (unchanged - fixed term)")

print(f"\nAnnuity C (10 years guaranteed):")
print(f"  IRR: {irr_c:.2f}% (unchanged - fixed term)")

print("\n3. EXPECTED CASH FLOWS - ANNUITY A WITH HIGHER MORTALITY")
print("-" * 40)
print("\n Year  Age  Survival%  Expected Payment  vs Baseline")
print("-" * 55)

for year in range(1, min(31, len(cashflows_higher))):
    age = 65 + year
    survival = survival_higher[year] * 100
    payment = cashflows_higher[year]
    baseline_payment = cashflows_baseline[year] if year < len(cashflows_baseline) else 0
    diff = payment - baseline_payment
    
    if year <= 15:
        note = " (guaranteed)"
    else:
        note = ""
    
    print(f"  {year:3d}   {age:3d}    {survival:5.1f}%     ${payment:,.0f}{note}    {diff:+,.0f}")

print("\n4. LIFE EXPECTANCY COMPARISON")
print("-" * 40)

# Calculate life expectancy for both scenarios
def calculate_life_expectancy(mortality_rates):
    life_exp = 0
    prob = 1.0
    for age in range(66, 120):
        mort_rate = mortality_rates.get(age - 1, 0)
        prob = prob * (1 - mort_rate)
        life_exp += prob
    return 65 + life_exp

life_exp_baseline = calculate_life_expectancy(baseline_mortality)
life_exp_higher = calculate_life_expectancy(higher_mortality)

print(f"\nLife expectancy from age 65:")
print(f"  Baseline mortality:        {life_exp_baseline:.1f} years")
print(f"  10% higher mortality:      {life_exp_higher:.1f} years")
print(f"  Reduction in life expectancy: {life_exp_baseline - life_exp_higher:.1f} years")

print("\n5. RANKING COMPARISON")
print("-" * 40)

print(f"\nWith BASELINE mortality:")
print(f"  1. Annuity A: {irr_baseline:.2f}% (best)")
print(f"  2. Annuity B: {irr_b:.2f}%")
print(f"  3. Annuity C: {irr_c:.2f}%")

print(f"\nWith 10% HIGHER mortality:")
if irr_higher > irr_b:
    print(f"  1. Annuity A: {irr_higher:.2f}% (still best)")
    print(f"  2. Annuity B: {irr_b:.2f}%")
elif irr_b > irr_higher > irr_c:
    print(f"  1. Annuity B: {irr_b:.2f}% (now best)")
    print(f"  2. Annuity A: {irr_higher:.2f}%")
else:
    print(f"  1. Annuity B: {irr_b:.2f}%")
    print(f"  2. Annuity C: {irr_c:.2f}%") 
    print(f"  3. Annuity A: {irr_higher:.2f}%")
print(f"  3. Annuity C: {irr_c:.2f}%")

print("\n6. IMPLICATIONS FOR DECISION")
print("-" * 40)

print(f"""
KEY FINDINGS WITH 10% HIGHER MORTALITY:

• Annuity A's IRR drops from {irr_baseline:.2f}% to {irr_higher:.2f}% (-{irr_baseline - irr_higher:.2f}%)
• Expected payout drops by ${expected_total_a_baseline - expected_total_a_higher:,.0f}
• Life expectancy reduced by {life_exp_baseline - life_exp_higher:.1f} years

RANKING CHANGE:
• {"Annuity A remains the best option" if irr_higher > irr_b else "Annuity B becomes the best option"}
• The 15-year guarantee protects much of Annuity A's value
• After year 15, lower survival probabilities reduce expected payments

STRATEGIC IMPLICATIONS:
1. Health status is critical for the lifetime annuity decision
2. With health concerns, fixed-term annuities become more attractive
3. The guarantee period provides significant protection
4. Consider medical underwriting for better rates if health is poor

RECOMMENDATION:
• If health is worse than average: {"Still consider Annuity A due to guarantee" if irr_higher > 4.0 else "Lean toward Annuity B"}
• The 15-year guarantee means you need to survive to only age 80 to break even
• {f"{(survival_higher[15] * 100):.0f}% chance of surviving to collect beyond guarantee" if len(survival_higher) > 15 else "Limited survival beyond guarantee"}
""")

print("=" * 80)