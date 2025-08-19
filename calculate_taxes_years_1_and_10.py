"""Calculate taxes on dividends and capital gains for years 1 and 10 of the personal injury settlement scenarios."""

import numpy as np
from finsim.tax import TaxCalculator
from finsim.cola import get_consumption_inflation_factors

# Settlement parameters from notebook
TOTAL_SETTLEMENT = 677_530
ANNUITY_COST = 527_530
IMMEDIATE_CASH = TOTAL_SETTLEMENT - ANNUITY_COST

# Annuity annual payments (tax-free for personal injury)
ANNUITY_A_ANNUAL = 3_516.29 * 12  # $42,195
ANNUITY_B_ANNUAL = 4_057.78 * 12  # $48,693
ANNUITY_C_ANNUAL = 5_397.12 * 12  # $64,765

# Base parameters from notebook
CURRENT_AGE = 65
SOCIAL_SECURITY = 24_000
STATE = "CA"
EXPECTED_RETURN = 7.0 / 100  # 7% expected return
DIVIDEND_YIELD = 1.8 / 100    # 1.8% dividend yield
SPENDING_LEVEL = 65_000       # Use a representative spending level

# Get inflation factors
START_YEAR = 2025
inflation_factors = get_consumption_inflation_factors(START_YEAR, 10)

# Initialize tax calculator
tax_calc = TaxCalculator(state=STATE, year=START_YEAR)

# Define scenarios
scenarios = [
    {
        "name": "100% Stocks (VT)",
        "initial_portfolio": TOTAL_SETTLEMENT,
        "has_annuity": False,
        "annuity_annual": 0,
    },
    {
        "name": "Annuity A + Stocks",
        "initial_portfolio": IMMEDIATE_CASH,
        "has_annuity": True,
        "annuity_annual": ANNUITY_A_ANNUAL,
    },
    {
        "name": "Annuity B + Stocks",
        "initial_portfolio": IMMEDIATE_CASH,
        "has_annuity": True,
        "annuity_annual": ANNUITY_B_ANNUAL,
    },
    {
        "name": "Annuity C + Stocks",
        "initial_portfolio": IMMEDIATE_CASH,
        "has_annuity": True,
        "annuity_annual": ANNUITY_C_ANNUAL,
    },
]

print("=" * 80)
print("TAX ANALYSIS FOR PERSONAL INJURY SETTLEMENT SCENARIOS")
print("=" * 80)
print(f"\nBase assumptions:")
print(f"  - Current age: {CURRENT_AGE}")
print(f"  - Social Security: ${SOCIAL_SECURITY:,}/year")
print(f"  - State: {STATE}")
print(f"  - Expected portfolio return: {EXPECTED_RETURN * 100:.1f}%")
print(f"  - Dividend yield: {DIVIDEND_YIELD * 100:.1f}%")
print(f"  - Annual spending: ${SPENDING_LEVEL:,}")
print(f"  - Filing status: Single")
print("\n" + "=" * 80)

for scenario in scenarios:
    print(f"\n{scenario['name']}:")
    print("-" * 40)
    
    initial_portfolio = scenario["initial_portfolio"]
    annuity_income = scenario["annuity_annual"]
    
    # Note: Personal injury annuities are tax-free, so they don't count as taxable income
    # Only Social Security is potentially taxable guaranteed income
    
    for year in [1, 10]:
        age = CURRENT_AGE + year
        
        # Calculate portfolio value after growth (simplified - using expected return)
        # In reality, this would vary based on actual returns
        portfolio_value = initial_portfolio * ((1 + EXPECTED_RETURN) ** (year - 1))
        
        # Calculate dividends
        dividends = portfolio_value * DIVIDEND_YIELD
        
        # Calculate spending need
        inflation_factor = inflation_factors[year - 1] if year <= len(inflation_factors) else inflation_factors[-1]
        current_spending = SPENDING_LEVEL * inflation_factor
        
        # Total income available (annuity is tax-free, so doesn't reduce withdrawal need for taxes)
        total_guaranteed_income = SOCIAL_SECURITY + annuity_income
        income_for_spending = total_guaranteed_income + dividends
        
        # Calculate withdrawal need
        withdrawal_need = max(0, current_spending - income_for_spending)
        
        # For tax calculation purposes, we need to estimate capital gains
        # Assuming cost basis = initial portfolio, gains accumulate over time
        cost_basis = initial_portfolio
        if portfolio_value > 0 and withdrawal_need > 0:
            # Calculate gain fraction
            unrealized_gains = max(0, portfolio_value - cost_basis)
            gain_fraction = unrealized_gains / portfolio_value if portfolio_value > 0 else 0
            realized_gains = withdrawal_need * gain_fraction
        else:
            realized_gains = 0
        
        # Calculate taxes using PolicyEngine
        # Note: Annuity income is NOT included in social_security_array because it's tax-free
        tax_results = tax_calc.calculate_single_tax(
            capital_gains=realized_gains,
            social_security=SOCIAL_SECURITY,  # Only SS, not annuity
            age=age,
            filing_status="SINGLE",
            employment_income=0,
            dividend_income=dividends,
        )
        
        print(f"\n  Year {year} (Age {age}):")
        print(f"    Portfolio value: ${portfolio_value:,.0f}")
        print(f"    Dividends: ${dividends:,.0f}")
        print(f"    Realized capital gains: ${realized_gains:,.0f}")
        print(f"    ")
        print(f"    Federal tax: ${tax_results['federal_tax']:,.0f}")
        print(f"    State tax (CA): ${tax_results['state_tax']:,.0f}")
        print(f"    Total tax: ${tax_results['total_tax']:,.0f}")
        print(f"    ")
        print(f"    Breakdown by source:")
        print(f"      Tax on dividends + capital gains: ~${tax_results['total_tax']:,.0f}")
        print(f"      (Note: Personal injury annuity is tax-free)")

print("\n" + "=" * 80)
print("\nKEY INSIGHTS:")
print("-" * 40)
print("1. The 100% Stocks scenario has the highest tax burden due to:")
print("   - Larger portfolio generating more dividends")
print("   - Higher capital gains realizations when withdrawing")
print("\n2. Annuity scenarios have lower taxes because:")
print("   - Smaller portfolios (only $150k vs $677k)")
print("   - Personal injury annuities are completely tax-free")
print("   - Less need for taxable withdrawals")
print("\n3. Tax burden increases over time due to:")
print("   - Portfolio growth increasing dividend income")
print("   - Inflation-adjusted spending requiring larger withdrawals")
print("=" * 80)