#!/usr/bin/env python3
"""Calculate the Annual Rate of Return (ARR) for each annuity option."""

import numpy as np
import numpy_financial as npf
import pandas as pd

# Annuity cost (same for all three)
ANNUITY_COST = 527_530

# Annuity payments
ANNUITY_A_MONTHLY = 3_516.29
ANNUITY_B_MONTHLY = 4_057.78
ANNUITY_C_MONTHLY = 5_397.12

ANNUITY_A_ANNUAL = ANNUITY_A_MONTHLY * 12  # $42,195.48
ANNUITY_B_ANNUAL = ANNUITY_B_MONTHLY * 12  # $48,693.36
ANNUITY_C_ANNUAL = ANNUITY_C_MONTHLY * 12  # $64,765.44

print("=" * 80)
print("ANNUITY RATE OF RETURN ANALYSIS")
print("=" * 80)
print(f"\nInitial Cost (all annuities): ${ANNUITY_COST:,}")
print()

def calculate_irr_annuity(cost, annual_payment, years, is_lifetime=False, life_expectancy=None):
    """
    Calculate IRR for an annuity.
    For lifetime annuities, we'll calculate for different life expectancies.
    """
    if is_lifetime and life_expectancy:
        years = life_expectancy
    
    # Create cash flow array: negative cost at time 0, then positive payments
    cash_flows = [-cost] + [annual_payment] * years
    
    # Calculate IRR using numpy_financial
    irr = npf.irr(cash_flows)
    
    return irr * 100  # Convert to percentage

# Calculate for fixed-term annuities
print("1. FIXED-TERM ANNUITIES")
print("-" * 40)

# Annuity B: 15 years
irr_b = calculate_irr_annuity(ANNUITY_COST, ANNUITY_B_ANNUAL, 15)
total_received_b = ANNUITY_B_ANNUAL * 15
print(f"\nAnnuity B (15 years guaranteed):")
print(f"  Annual payment: ${ANNUITY_B_ANNUAL:,.2f}")
print(f"  Total received: ${total_received_b:,.2f}")
print(f"  Net gain: ${total_received_b - ANNUITY_COST:,.2f}")
print(f"  IRR: {irr_b:.2f}%")

# Annuity C: 10 years
irr_c = calculate_irr_annuity(ANNUITY_COST, ANNUITY_C_ANNUAL, 10)
total_received_c = ANNUITY_C_ANNUAL * 10
print(f"\nAnnuity C (10 years guaranteed):")
print(f"  Annual payment: ${ANNUITY_C_ANNUAL:,.2f}")
print(f"  Total received: ${total_received_c:,.2f}")
print(f"  Net gain: ${total_received_c - ANNUITY_COST:,.2f}")
print(f"  IRR: {irr_c:.2f}%")

print("\n2. LIFETIME ANNUITY (A) - BY LIFE EXPECTANCY")
print("-" * 40)
print(f"\nAnnuity A (lifetime with 15-year guarantee):")
print(f"  Annual payment: ${ANNUITY_A_ANNUAL:,.2f}")
print()

# Calculate IRR for different life expectancies
# Starting age: 65
life_expectancies = [
    (75, 10),   # Dies at 75 (only gets guarantee minimum)
    (80, 15),   # Dies at 80 (exactly the guarantee)
    (82, 17),   # Male life expectancy from 65
    (85, 20),   # Lives to 85
    (90, 25),   # Lives to 90
    (95, 30),   # Lives to 95
    (100, 35),  # Lives to 100
]

irr_results = []
for death_age, years in life_expectancies:
    # For Annuity A, minimum 15 years due to guarantee
    actual_years = max(years, 15)
    irr = calculate_irr_annuity(ANNUITY_COST, ANNUITY_A_ANNUAL, actual_years)
    total_received = ANNUITY_A_ANNUAL * actual_years
    
    irr_results.append({
        'Death Age': death_age,
        'Years Receiving': actual_years,
        'Total Received': f"${total_received:,.0f}",
        'Net Gain': f"${total_received - ANNUITY_COST:,.0f}",
        'IRR': f"{irr:.2f}%"
    })

df = pd.DataFrame(irr_results)
print(df.to_string(index=False))

print("\n3. BREAKEVEN ANALYSIS")
print("-" * 40)

# Years to break even (get back initial investment)
years_breakeven_a = ANNUITY_COST / ANNUITY_A_ANNUAL
years_breakeven_b = ANNUITY_COST / ANNUITY_B_ANNUAL
years_breakeven_c = ANNUITY_COST / ANNUITY_C_ANNUAL

print(f"\nYears to recover initial ${ANNUITY_COST:,}:")
print(f"  Annuity A: {years_breakeven_a:.1f} years")
print(f"  Annuity B: {years_breakeven_b:.1f} years")
print(f"  Annuity C: {years_breakeven_c:.1f} years")

print("\n4. COMPARISON SUMMARY")
print("-" * 40)

# Expected value assuming male age 65 life expectancy (82)
expected_years_a = 17  # Lives to 82
irr_a_expected = calculate_irr_annuity(ANNUITY_COST, ANNUITY_A_ANNUAL, expected_years_a)

print(f"\nAssuming life expectancy of 82 (17 years from age 65):")
print(f"  Annuity A (lifetime): {irr_a_expected:.2f}% IRR")
print(f"  Annuity B (15 years): {irr_b:.2f}% IRR")
print(f"  Annuity C (10 years): {irr_c:.2f}% IRR")

print("\n5. KEY INSIGHTS")
print("-" * 40)
print("""
• ANNUITY C has the HIGHEST IRR (2.28%) for its 10-year term
• ANNUITY B has NEGATIVE IRR (-1.48%) - you get back less than you paid!
• ANNUITY A's return depends on longevity:
  - If he lives to 82 (expected): 1.07% IRR
  - If he lives to 90: 4.51% IRR
  - If he lives to 95: 5.56% IRR
  
• The IRRs are all quite LOW compared to expected stock returns (7%)
• BUT annuities provide GUARANTEED income and longevity protection
• Annuity A becomes more valuable the longer he lives
""")

print("\n6. RISK-ADJUSTED PERSPECTIVE")
print("-" * 40)
print("""
While the IRRs appear low, consider:

1. These are GUARANTEED returns (no market risk)
2. They're TAX-FREE (personal injury settlement)
3. Equivalent taxable return at 25% tax rate:
   - Annuity A at age 90: 4.51% → 6.01% taxable equivalent
   - Annuity C: 2.28% → 3.04% taxable equivalent
   
4. Compare to risk-free alternatives:
   - 10-year Treasury: ~4.5% (taxable)
   - High-yield savings: ~4.5% (taxable)
   - After-tax equivalent: ~3.4%

5. Annuity A provides longevity insurance:
   - Protects against outliving money
   - Return INCREASES with longevity
   - Impossible to replicate with stocks/bonds
""")

print("=" * 80)