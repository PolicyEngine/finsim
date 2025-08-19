#!/usr/bin/env python3
"""Analyze why Annuity A outperforms B and C at high confidence levels."""

import numpy as np
import pandas as pd

# Settlement parameters
TOTAL_SETTLEMENT = 677_530
IMMEDIATE_CASH = 150_000  # What's left to invest after buying annuity

# Annuity details
ANNUITY_A_ANNUAL = 42_195  # Life with 15-year guarantee
ANNUITY_B_ANNUAL = 48_693  # 15 years only
ANNUITY_C_ANNUAL = 64_765  # 10 years only

# Other income
SOCIAL_SECURITY = 24_000

print("=" * 80)
print("WHY ANNUITY A OUTPERFORMS B AND C")
print("=" * 80)

print("\n1. ANNUITY STRUCTURE COMPARISON")
print("-" * 40)
print(f"Annuity A: ${ANNUITY_A_ANNUAL:,}/year FOR LIFE (with 15-yr guarantee)")
print(f"Annuity B: ${ANNUITY_B_ANNUAL:,}/year for 15 years ONLY")
print(f"Annuity C: ${ANNUITY_C_ANNUAL:,}/year for 10 years ONLY")
print(f"\nAll scenarios keep ${IMMEDIATE_CASH:,} in stocks")

print("\n2. THE CRITICAL DIFFERENCE: LIFETIME INCOME")
print("-" * 40)
print("After the guarantee period ends:")
print(f"  • Annuity A: Still pays ${ANNUITY_A_ANNUAL:,}/year until death")
print(f"  • Annuity B: Payments STOP after year 15")
print(f"  • Annuity C: Payments STOP after year 10")

print("\n3. INCOME ANALYSIS BY PERIOD")
print("-" * 40)

# Years 1-10: All annuities paying
print("\nYears 1-10 (all annuities active):")
print(f"  Total income with Annuity A: ${SOCIAL_SECURITY + ANNUITY_A_ANNUAL:,}")
print(f"  Total income with Annuity B: ${SOCIAL_SECURITY + ANNUITY_B_ANNUAL:,}")
print(f"  Total income with Annuity C: ${SOCIAL_SECURITY + ANNUITY_C_ANNUAL:,}")
print(f"  → Annuity C provides ${(ANNUITY_C_ANNUAL - ANNUITY_A_ANNUAL):,} more/year")

# Years 11-15: C stops
print("\nYears 11-15 (Annuity C stopped):")
print(f"  Total income with Annuity A: ${SOCIAL_SECURITY + ANNUITY_A_ANNUAL:,}")
print(f"  Total income with Annuity B: ${SOCIAL_SECURITY + ANNUITY_B_ANNUAL:,}")
print(f"  Total income with Annuity C: ${SOCIAL_SECURITY:,} (annuity ended!)")
print(f"  → Annuity C loses ${ANNUITY_C_ANNUAL:,}/year of income")

# Years 16+: Only A continues
print("\nYears 16-30 (Only Annuity A continues):")
print(f"  Total income with Annuity A: ${SOCIAL_SECURITY + ANNUITY_A_ANNUAL:,}")
print(f"  Total income with Annuity B: ${SOCIAL_SECURITY:,} (annuity ended!)")
print(f"  Total income with Annuity C: ${SOCIAL_SECURITY:,} (annuity ended!)")
print(f"  → B and C must fund ${ANNUITY_B_ANNUAL:,}-${ANNUITY_C_ANNUAL:,} from portfolio")

print("\n4. PORTFOLIO DEPLETION RISK")
print("-" * 40)

# Calculate required portfolio withdrawals after annuities end
spending_need = 60_000  # Approximate sustainable spending level

print(f"\nAssuming ${spending_need:,}/year spending need:")

# Years 16+ for Annuity B
years_16_plus_withdrawal_B = spending_need - SOCIAL_SECURITY
print(f"\nAnnuity B after year 15:")
print(f"  Needs from portfolio: ${years_16_plus_withdrawal_B:,}/year")
print(f"  That's ${years_16_plus_withdrawal_B * 15:,} over 15 years (before growth)")

# Years 11+ for Annuity C  
years_11_plus_withdrawal_C = spending_need - SOCIAL_SECURITY
print(f"\nAnnuity C after year 10:")
print(f"  Needs from portfolio: ${years_11_plus_withdrawal_C:,}/year")
print(f"  That's ${years_11_plus_withdrawal_C * 20:,} over 20 years (before growth)")

# Annuity A
withdrawal_A = max(0, spending_need - SOCIAL_SECURITY - ANNUITY_A_ANNUAL)
print(f"\nAnnuity A (entire period):")
print(f"  Needs from portfolio: ${withdrawal_A:,}/year or less")
print(f"  Portfolio can grow with minimal withdrawals")

print("\n5. THE MATH: WHY A WINS AT HIGH CONFIDENCE")
print("-" * 40)

print("\nStarting portfolio for all annuity scenarios: ${:,}".format(IMMEDIATE_CASH))

# Simple analysis assuming 5% real returns
real_return = 0.05
years = 30

# Annuity A: minimal withdrawals
portfolio_A_simple = IMMEDIATE_CASH * (1 + real_return) ** years
print(f"\nAnnuity A (minimal withdrawals):")
print(f"  Portfolio after 30 years (5% real): ${portfolio_A_simple:,.0f}")

# Annuity B: heavy withdrawals after year 15
# Rough approximation
portfolio_B_year15 = IMMEDIATE_CASH * (1 + real_return) ** 15
annual_withdrawal_B = years_16_plus_withdrawal_B
remaining_years = 15
# Depletes quickly
print(f"\nAnnuity B (heavy withdrawals after year 15):")
print(f"  Portfolio at year 15: ${portfolio_B_year15:,.0f}")
print(f"  Then withdrawing ${annual_withdrawal_B:,}/year")
print(f"  → Depletes much faster, especially in down markets")

print("\n6. KEY INSIGHTS")
print("-" * 40)
print("""
1. LIFETIME PROTECTION: Annuity A provides income for life, B and C don't

2. PORTFOLIO PRESERVATION: 
   - Annuity A: Portfolio mostly grows (minimal withdrawals)
   - Annuity B & C: Portfolio depletes rapidly after guarantees end

3. SEQUENCE OF RETURNS RISK:
   - Annuity A: Protected - annuity covers most spending needs
   - Annuity B & C: Exposed - must withdraw heavily in years 11-30

4. LONGEVITY RISK:
   - Annuity A: Fully protected - payments continue for life
   - Annuity B & C: Exposed - no income after guarantees expire

5. AT 90% CONFIDENCE:
   - Need to survive market downturns AND live a long time
   - Annuity A's lifetime income is crucial for this scenario
   - B and C fail when markets are bad AND you live past 80-85
""")

print("=" * 80)
print("BOTTOM LINE:")
print("Annuity A's LIFETIME income stream makes it superior for high-confidence")
print("retirement planning, even though it pays less initially than B or C.")
print("=" * 80)