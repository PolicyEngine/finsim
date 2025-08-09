"""Portfolio simulation with tax-aware Monte Carlo modeling."""

import numpy as np
from typing import Dict, Tuple, Optional
from .tax import TaxCalculator
from .mortality import get_mortality_rates


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
    
    # Annuity parameters
    has_annuity: bool,
    annuity_type: str,
    annuity_annual: float,
    annuity_guarantee_years: int,
    
    # Consumption
    net_consumption_need: float,
    
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
    Run Monte Carlo simulation of portfolio evolution with taxes.
    
    Returns dictionary with:
    - portfolio_paths: (n_simulations, n_years+1) array of portfolio values
    - failure_year: (n_simulations,) array of year when portfolio depleted
    - alive_mask: (n_simulations, n_years+1) array of survival status
    - annuity_income: (n_simulations, n_years) array of annuity payments
    - dividend_income: (n_simulations, n_years) array of dividend income
    - capital_gains: (n_simulations, n_years) array of realized capital gains
    - gross_withdrawals: (n_simulations, n_years) array of gross withdrawals
    - taxes_paid: (n_simulations, n_years) array of taxes paid
    - net_withdrawals: (n_simulations, n_years) array of net withdrawals
    - cost_basis: (n_simulations,) array of final cost basis
    """
    
    # Initialize tax calculator
    tax_calc = TaxCalculator(state=state, year=2025)
    
    # Get mortality rates if needed
    mortality_rates = get_mortality_rates() if include_mortality else {}
    
    # Initialize arrays
    portfolio_paths = np.zeros((n_simulations, n_years + 1))
    portfolio_paths[:, 0] = initial_portfolio
    
    # Track cost basis for capital gains calculations
    cost_basis = np.full(n_simulations, initial_portfolio)
    
    # Track components for analysis
    dividend_income = np.zeros((n_simulations, n_years))
    capital_gains = np.zeros((n_simulations, n_years))
    gross_withdrawals = np.zeros((n_simulations, n_years))
    taxes_paid = np.zeros((n_simulations, n_years))
    net_withdrawals = np.zeros((n_simulations, n_years))
    
    failure_year = np.full(n_simulations, n_years + 1)
    alive_mask = np.ones((n_simulations, n_years + 1), dtype=bool)
    
    # Track annuity income
    annuity_income = np.zeros((n_simulations, n_years))
    
    # Track effective tax rates from prior year
    prior_year_etr = np.ones(n_simulations) * 0.20  # Start with 20% assumption
    
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
        
        # Investment returns - Geometric Brownian Motion (GBM)
        # The standard model in finance: dS/S = μdt + σdW
        # For annual steps: S(t+1) = S(t) * exp((μ - σ²/2) + σZ)
        mu = expected_return / 100  # Convert percentage to decimal
        sigma = return_volatility / 100
        
        # Generate standard normal random variables
        z = np.random.standard_normal(n_simulations)
        
        # GBM growth factor with volatility drag correction
        log_returns = (mu - 0.5 * sigma**2) + sigma * z
        growth_factor = np.exp(log_returns)
        
        # Portfolio evolution (only for living people)
        current_portfolio = portfolio_paths[:, year-1]
        # Only grow portfolios for those still alive
        portfolio_after_growth = np.where(
            alive_mask[:, year],
            current_portfolio * growth_factor,
            current_portfolio  # Dead people's estates don't grow
        )
        
        # Dividends (only for living people's portfolios)
        dividends = np.where(
            alive_mask[:, year],
            current_portfolio * (dividend_yield / 100),
            0  # Dead people's estates don't generate dividends
        )
        dividend_income[:, year-1] = dividends
        
        # Calculate actual withdrawal needed (only for living)
        actual_net_need = np.zeros(n_simulations)
        actual_net_need[active] = np.maximum(0, net_consumption_need - dividends[active])
        
        # Estimate gross withdrawal using prior year's tax rate
        actual_gross_withdrawal = np.zeros(n_simulations)
        actual_gross_withdrawal[active] = actual_net_need[active] / (1 - prior_year_etr[active])
        actual_gross_withdrawal = np.maximum(0, actual_gross_withdrawal)
        
        # Track withdrawals
        gross_withdrawals[:, year-1] = actual_gross_withdrawal
        
        # Calculate realized capital gains
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
        
        # Calculate actual taxes
        if active.any():
            total_ss_and_pension = social_security + pension + annuity_income[:, year-1]
            ages_array = np.full(n_simulations, age)
            
            tax_results = tax_calc.calculate_batch_taxes(
                capital_gains_array=realized_gains,
                social_security_array=total_ss_and_pension,
                ages=ages_array,
                filing_status="SINGLE",
                dividend_income_array=dividends
            )
            
            taxes_paid[:, year-1] = tax_results['total_tax']
            
            # Update effective tax rate for next year
            total_income = actual_gross_withdrawal + dividends
            prior_year_etr = np.where(total_income > 0,
                                      tax_results['total_tax'] / total_income,
                                      0.20)
            prior_year_etr = np.clip(prior_year_etr, 0.0, 0.50)
        
        # Net withdrawals after tax
        net_withdrawals[:, year-1] = actual_gross_withdrawal - taxes_paid[:, year-1]
        
        # New portfolio value (dividends already used to reduce withdrawals)
        new_portfolio = portfolio_after_growth - actual_gross_withdrawal
        
        # Check for failures
        newly_failed = (current_portfolio > 0) & (new_portfolio < 0)
        failure_year[newly_failed & (failure_year > n_years)] = year
        
        # Update portfolio
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
        'taxes_paid': taxes_paid,
        'net_withdrawals': net_withdrawals,
        'cost_basis': cost_basis
    }