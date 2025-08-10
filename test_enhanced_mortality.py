"""Test enhanced mortality features in FinSim."""

from finsim.portfolio_simulation import simulate_portfolio
import numpy as np


def test_enhanced_mortality():
    """Compare portfolio outcomes with basic vs enhanced mortality."""
    
    # Common parameters
    base_params = {
        'n_simulations': 1000,
        'n_years': 35,
        'initial_portfolio': 1_000_000,
        'current_age': 65,
        'include_mortality': True,
        'social_security': 30_000,
        'pension': 20_000,
        'employment_income': 0,
        'retirement_age': 65,
        'has_annuity': False,
        'annuity_type': 'Life Only',
        'annuity_annual': 0,
        'annuity_guarantee_years': 0,
        'annual_consumption': 80_000,
        'expected_return': 7.0,
        'return_volatility': 15.0,
        'dividend_yield': 2.0,
        'state': 'NY',
        'gender': 'Male',
        'has_spouse': False
    }
    
    print("Testing Enhanced Mortality in FinSim")
    print("=" * 60)
    
    # Test 1: Basic SSA mortality
    print("\nScenario 1: Basic SSA Mortality (65-year-old male)")
    print("-" * 40)
    results_basic = simulate_portfolio(**base_params)
    
    portfolio_at_death = []
    for i in range(base_params['n_simulations']):
        death_mask = ~results_basic['alive_mask'][i, :]
        if np.any(death_mask):
            death_year = np.where(death_mask)[0][0]
            if death_year > 0:
                portfolio_at_death.append(results_basic['portfolio_paths'][i, death_year-1])
    
    if portfolio_at_death:
        print(f"Median estate at death: ${np.median(portfolio_at_death):,.0f}")
        print(f"25th percentile: ${np.percentile(portfolio_at_death, 25):,.0f}")
        print(f"75th percentile: ${np.percentile(portfolio_at_death, 75):,.0f}")
    
    # Count survivors
    survivors_at_end = np.sum(results_basic['alive_mask'][:, -1])
    print(f"Survivors after {base_params['n_years']} years: {survivors_at_end}/{base_params['n_simulations']} ({100*survivors_at_end/base_params['n_simulations']:.1f}%)")
    
    # Test 2: Enhanced mortality - healthy high-income non-smoker
    print("\nScenario 2: Enhanced Mortality - Healthy High-Income Non-Smoker")
    print("-" * 40)
    enhanced_healthy_params = {
        **base_params,
        'use_enhanced_mortality': True,
        'smoker': False,
        'income_percentile': 80,
        'health_status': 'good'
    }
    results_healthy = simulate_portfolio(**enhanced_healthy_params)
    
    portfolio_at_death_healthy = []
    for i in range(base_params['n_simulations']):
        death_mask = ~results_healthy['alive_mask'][i, :]
        if np.any(death_mask):
            death_year = np.where(death_mask)[0][0]
            if death_year > 0:
                portfolio_at_death_healthy.append(results_healthy['portfolio_paths'][i, death_year-1])
    
    if portfolio_at_death_healthy:
        print(f"Median estate at death: ${np.median(portfolio_at_death_healthy):,.0f}")
        print(f"25th percentile: ${np.percentile(portfolio_at_death_healthy, 25):,.0f}")
        print(f"75th percentile: ${np.percentile(portfolio_at_death_healthy, 75):,.0f}")
    
    survivors_healthy = np.sum(results_healthy['alive_mask'][:, -1])
    print(f"Survivors after {base_params['n_years']} years: {survivors_healthy}/{base_params['n_simulations']} ({100*survivors_healthy/base_params['n_simulations']:.1f}%)")
    
    # Test 3: Enhanced mortality - smoker with poor health
    print("\nScenario 3: Enhanced Mortality - Smoker with Poor Health")
    print("-" * 40)
    enhanced_poor_params = {
        **base_params,
        'use_enhanced_mortality': True,
        'smoker': True,
        'income_percentile': 25,
        'health_status': 'poor'
    }
    results_poor = simulate_portfolio(**enhanced_poor_params)
    
    portfolio_at_death_poor = []
    for i in range(base_params['n_simulations']):
        death_mask = ~results_poor['alive_mask'][i, :]
        if np.any(death_mask):
            death_year = np.where(death_mask)[0][0]
            if death_year > 0:
                portfolio_at_death_poor.append(results_poor['portfolio_paths'][i, death_year-1])
    
    if portfolio_at_death_poor:
        print(f"Median estate at death: ${np.median(portfolio_at_death_poor):,.0f}")
        print(f"25th percentile: ${np.percentile(portfolio_at_death_poor, 25):,.0f}")
        print(f"75th percentile: ${np.percentile(portfolio_at_death_poor, 75):,.0f}")
    
    survivors_poor = np.sum(results_poor['alive_mask'][:, -1])
    print(f"Survivors after {base_params['n_years']} years: {survivors_poor}/{base_params['n_simulations']} ({100*survivors_poor/base_params['n_simulations']:.1f}%)")
    
    # Summary comparison
    print("\n" + "=" * 60)
    print("SUMMARY: Impact of Health and Lifestyle on Portfolio Outcomes")
    print("=" * 60)
    
    if portfolio_at_death and portfolio_at_death_healthy:
        healthy_advantage = np.median(portfolio_at_death_healthy) - np.median(portfolio_at_death)
        print(f"\nHealthy lifestyle advantage over baseline:")
        print(f"  Median estate difference: ${healthy_advantage:,.0f}")
        print(f"  Additional survivors: {survivors_healthy - survivors_at_end}")
    
    if portfolio_at_death and portfolio_at_death_poor:
        poor_disadvantage = np.median(portfolio_at_death) - np.median(portfolio_at_death_poor)
        print(f"\nPoor health disadvantage vs baseline:")
        print(f"  Median estate difference: -${poor_disadvantage:,.0f}")
        print(f"  Fewer survivors: {survivors_at_end - survivors_poor}")
    
    print("\nNote: Enhanced mortality accounts for individual characteristics")
    print("while properly calibrating to population averages (Bayesian approach).")


if __name__ == "__main__":
    test_enhanced_mortality()