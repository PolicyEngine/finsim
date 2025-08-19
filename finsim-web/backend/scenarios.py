"""Scenario configurations for the FinSim application."""

# Settlement parameters
TOTAL_SETTLEMENT = 677_530
ANNUITY_COST = 527_530
IMMEDIATE_CASH = TOTAL_SETTLEMENT - ANNUITY_COST

# Annuity annual payments
ANNUITY_A_ANNUAL = 3_516.29 * 12  # $42,195
ANNUITY_B_ANNUAL = 4_057.78 * 12  # $48,693
ANNUITY_C_ANNUAL = 5_397.12 * 12  # $64,765

SCENARIOS = [
    {
        'id': 'stocks_only',
        'name': '100% Stocks (VT)',
        'description': 'Full investment in globally diversified stock index',
        'has_annuity': False,
        'initial_portfolio': TOTAL_SETTLEMENT,
        'annuity_annual': 0,
        'annuity_type': None,
        'annuity_guarantee_years': 0
    },
    {
        'id': 'annuity_a',
        'name': 'Annuity A + Stocks',
        'description': 'Life annuity with 15-year guarantee plus stocks',
        'has_annuity': True,
        'initial_portfolio': IMMEDIATE_CASH,
        'annuity_annual': ANNUITY_A_ANNUAL,
        'annuity_type': 'Life Contingent with Guarantee',
        'annuity_guarantee_years': 15
    },
    {
        'id': 'annuity_b',
        'name': 'Annuity B + Stocks',
        'description': '15-year fixed period annuity plus stocks',
        'has_annuity': True,
        'initial_portfolio': IMMEDIATE_CASH,
        'annuity_annual': ANNUITY_B_ANNUAL,
        'annuity_type': 'Fixed Period',
        'annuity_guarantee_years': 15
    },
    {
        'id': 'annuity_c',
        'name': 'Annuity C + Stocks',
        'description': '10-year fixed period annuity plus stocks',
        'has_annuity': True,
        'initial_portfolio': IMMEDIATE_CASH,
        'annuity_annual': ANNUITY_C_ANNUAL,
        'annuity_type': 'Fixed Period',
        'annuity_guarantee_years': 10
    }
]