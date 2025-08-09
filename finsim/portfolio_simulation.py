"""Portfolio simulation with next-year tax payment (more realistic)."""

import numpy as np
from typing import Dict, Optional
from scipy import stats
from .tax import TaxCalculator
from .mortality import get_mortality_rates
from .return_generator import ReturnGenerator


def simulate_portfolio(
    # Basic parameters
    n_simulations: int,
    n_years: int,
    initial_portfolio: float,
    
    # Age and mortality
    current_age: int,
    include_mortality: bool,
    
    # Income sources
    social_security: float,
    pension: float,
    employment_income: float,  # Wages and salaries
    retirement_age: int,  # Age when employment income stops
    
    # Annuity parameters
    has_annuity: bool,
    annuity_type: str,
    annuity_annual: float,
    annuity_guarantee_years: int,
    
    # Consumption
    annual_consumption: float,  # Total consumption need (not net)
    
    # Market parameters
    expected_return: float,
    return_volatility: float,
    dividend_yield: float,
    
    # Tax parameters
    state: str,
    
    # Progress callback
    progress_callback: Optional[callable] = None
) -> Dict[str, np.ndarray]:
    """
    Run Monte Carlo simulation with next-year tax payment.
    
    Key difference: We withdraw exactly what we need for consumption each year,
    then pay taxes the following year from that year's withdrawal.
    This is more realistic and avoids circular dependency.
    """
    
    # Initialize tax calculator
    tax_calc = TaxCalculator(state=state, year=2025)
    
    # Get mortality rates if needed
    mortality_rates = get_mortality_rates() if include_mortality else {}
    
    # Generate all returns upfront using the return generator
    # This fixes the bug where returns were getting repeated
    return_gen = ReturnGenerator(
        expected_return=expected_return / 100,
        volatility=return_volatility / 100
    )
    growth_factors_matrix = return_gen.generate_returns(n_simulations, n_years)
    
    # Initialize arrays
    portfolio_paths = np.zeros((n_simulations, n_years + 1))
    portfolio_paths[:, 0] = initial_portfolio
    
    # Track cost basis for capital gains calculations
    cost_basis = np.full(n_simulations, initial_portfolio)
    
    # Track components for analysis
    dividend_income = np.zeros((n_simulations, n_years))
    capital_gains = np.zeros((n_simulations, n_years))
    gross_withdrawals = np.zeros((n_simulations, n_years))
    taxes_owed = np.zeros((n_simulations, n_years))  # Taxes calculated this year
    taxes_paid = np.zeros((n_simulations, n_years))  # Taxes actually paid this year
    net_withdrawals = np.zeros((n_simulations, n_years))
    
    failure_year = np.full(n_simulations, n_years + 1)
    alive_mask = np.ones((n_simulations, n_years + 1), dtype=bool)
    
    # Track annuity income
    annuity_income = np.zeros((n_simulations, n_years))
    
    # Track prior year's tax liability (to be paid this year)
    prior_year_tax_liability = np.zeros(n_simulations)
    
    # Simulate each year
    for year in range(1, n_years + 1):
        age = current_age + year
        
        # Progress callback with partial results
        if progress_callback:
            progress_callback(year, n_years, age, {
                'portfolio_paths': portfolio_paths
            })
        
        # Calculate annuity income for this year
        if has_annuity:
            if annuity_type == "Fixed Period":
                gets_annuity = year <= annuity_guarantee_years
                annuity_income[:, year-1] = annuity_annual if gets_annuity else 0
            elif annuity_type == "Life Only":
                annuity_income[:, year-1] = np.where(alive_mask[:, year-1], annuity_annual, 0)
            else:  # Life Contingent with Guarantee
                in_guarantee = year <= annuity_guarantee_years
                annuity_income[:, year-1] = np.where(
                    alive_mask[:, year-1] | in_guarantee,
                    annuity_annual, 0
                )
        
        # Mortality
        if include_mortality and age > current_age:
            mort_rate = mortality_rates.get(age, 0)
            death_this_year = np.random.random(n_simulations) < mort_rate
            alive_mask[death_this_year, year:] = False
        
        # Only simulate for those still alive and not failed
        active = alive_mask[:, year] & (portfolio_paths[:, year-1] > 0)
        
        # Get pre-generated growth factors for this year
        growth_factor = growth_factors_matrix[:, year-1]
        
        
        # Portfolio evolution (only for living people)
        current_portfolio = portfolio_paths[:, year-1]
        portfolio_after_growth = np.where(
            alive_mask[:, year],
            current_portfolio * growth_factor,
            current_portfolio  # Dead people's estates don't grow
        )
        
        # Dividends (only for living people's portfolios)
        dividends = np.where(
            alive_mask[:, year],
            current_portfolio * (dividend_yield / 100),
            0
        )
        dividend_income[:, year-1] = dividends
        
        # Calculate withdrawal needed for consumption AND last year's taxes
        # This is the KEY CHANGE - we pay last year's taxes from this year's withdrawal
        
        # Employment income (stops at retirement age)
        wages = employment_income if age < retirement_age else 0
        
        guaranteed_income = social_security + pension + annuity_income[:, year-1] + wages
        total_income_available = guaranteed_income + dividends
        
        # What we need to withdraw = consumption + last year's taxes - available income
        withdrawal_need = np.zeros(n_simulations)
        withdrawal_need[active] = np.maximum(
            0,
            annual_consumption + prior_year_tax_liability[active] - total_income_available[active]
        )
        
        # This is our actual gross withdrawal (no tax gross-up needed!)
        actual_gross_withdrawal = withdrawal_need
        gross_withdrawals[:, year-1] = actual_gross_withdrawal
        
        # Calculate realized capital gains for tax purposes
        gain_fraction = np.where(current_portfolio > 0,
                                np.maximum(0, (current_portfolio - cost_basis) / current_portfolio),
                                0)
        realized_gains = actual_gross_withdrawal * gain_fraction
        capital_gains[:, year-1] = realized_gains
        
        # Update cost basis
        withdrawal_fraction = np.where(current_portfolio > 0,
                                      actual_gross_withdrawal / current_portfolio,
                                      0)
        cost_basis = cost_basis * (1 - withdrawal_fraction)
        
        # Calculate taxes owed on THIS YEAR's income (to be paid NEXT year)
        if active.any():
            total_ss_and_pension = social_security + pension + annuity_income[:, year-1]
            ages_array = np.full(n_simulations, age)
            
            # Employment income for tax calculation
            employment_income_array = np.full(n_simulations, wages)
            
            tax_results = tax_calc.calculate_batch_taxes(
                capital_gains_array=realized_gains,
                social_security_array=total_ss_and_pension,
                ages=ages_array,
                filing_status="SINGLE",
                dividend_income_array=dividends,
                employment_income_array=employment_income_array
            )
            
            # Store tax liability for next year
            taxes_owed[:, year-1] = tax_results['total_tax']
            prior_year_tax_liability = tax_results['total_tax'].copy()
        
        # Record taxes actually paid this year (from last year's liability)
        if year > 1:
            taxes_paid[:, year-1] = taxes_owed[:, year-2]
        
        # Net withdrawals (what's available for consumption after paying last year's taxes)
        net_withdrawals[:, year-1] = actual_gross_withdrawal - taxes_paid[:, year-1]
        
        # New portfolio value
        new_portfolio = portfolio_after_growth - actual_gross_withdrawal
        
        
        # Check for failures
        newly_failed = (current_portfolio > 0) & (new_portfolio < 0)
        failure_year[newly_failed & (failure_year > n_years)] = year
        
        # Update portfolio
        # Remove artificial cap - let the 4-sigma clipping handle extremes
        portfolio_paths[:, year] = np.maximum(0, new_portfolio)
    
    # Calculate estate values at death
    estate_at_death = np.full(n_simulations, np.nan)
    for i in range(n_simulations):
        death_years = np.where(~alive_mask[i, :])[0]
        if len(death_years) > 0:
            death_year = death_years[0]
            if death_year > 0:
                estate_at_death[i] = portfolio_paths[i, death_year-1]
    
    return {
        'portfolio_paths': portfolio_paths,
        'failure_year': failure_year,
        'alive_mask': alive_mask,
        'estate_at_death': estate_at_death,
        'annuity_income': annuity_income,
        'dividend_income': dividend_income,
        'capital_gains': capital_gains,
        'gross_withdrawals': gross_withdrawals,
        'taxes_owed': taxes_owed,
        'taxes_paid': taxes_paid,
        'net_withdrawals': net_withdrawals,
        'cost_basis': cost_basis
    }