"""Simulation logic for the FinSim application."""

import numpy as np
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path to import finsim
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from finsim.stacked_simulation import (
        create_scenario_config,
        simulate_stacked_scenarios,
        analyze_confidence_thresholds as finsim_analyze_confidence
    )
    FINSIM_AVAILABLE = True
except ImportError:
    FINSIM_AVAILABLE = False
    print("Warning: finsim module not available, using mock data")


def run_single_simulation(
    scenario: Dict[str, Any],
    spending_level: int,
    parameters: Dict[str, Any],
    include_components: bool = False
) -> Dict[str, Any]:
    """Run a single simulation for a scenario and spending level."""
    
    if not FINSIM_AVAILABLE:
        # Return mock data for testing
        np.random.seed(42)
        success_rate = max(0, min(1, 1 - (spending_level - 30000) / 100000 + np.random.normal(0, 0.1)))
        
        return {
            'success_rate': round(success_rate, 3),
            'median_final': int(250000 + np.random.normal(0, 50000)),
            'p10_final': int(50000 + np.random.normal(0, 10000)),
            'p90_final': int(750000 + np.random.normal(0, 100000)),
            'years_survived_median': 30,
            'years_survived_p10': 25,
            'years_survived_p90': 30
        }
    
    # Create scenario config
    scenario_config = create_scenario_config(
        name=scenario['name'],
        initial_portfolio=scenario['initial_portfolio'],
        has_annuity=scenario['has_annuity'],
        annuity_type=scenario.get('annuity_type'),
        annuity_annual=scenario.get('annuity_annual', 0),
        annuity_guarantee_years=scenario.get('annuity_guarantee_years', 0)
    )
    
    # Run simulation
    results = simulate_stacked_scenarios(
        scenarios=[scenario_config],
        spending_levels=[spending_level],
        n_simulations=2000,
        n_years=30,
        base_params=parameters,
        include_percentiles=True,
        random_seed=42
    )
    
    if results:
        result = results[0]
        return {
            'success_rate': result['success_rate'],
            'median_final': result['median_final'],
            'p10_final': result['p10_final'],
            'p90_final': result['p90_final'],
            'years_survived_median': result.get('years_survived_median', 30),
            'years_survived_p10': result.get('years_survived_p10', 25),
            'years_survived_p90': result.get('years_survived_p90', 30)
        }
    
    return {
        'success_rate': 0,
        'median_final': 0,
        'p10_final': 0,
        'p90_final': 0,
        'years_survived_median': 0,
        'years_survived_p10': 0,
        'years_survived_p90': 0
    }


def run_batch_simulation(
    scenarios: List[Dict[str, Any]],
    spending_levels: List[int],
    parameters: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Run batch simulations for multiple scenarios and spending levels."""
    
    if not FINSIM_AVAILABLE:
        # Return mock data for testing
        results = []
        for scenario in scenarios:
            for spending in spending_levels:
                np.random.seed(42 + spending)
                success_rate = max(0, min(1, 1 - (spending - 30000) / 100000 + np.random.normal(0, 0.05)))
                results.append({
                    'scenario': scenario['id'],
                    'scenario_name': scenario['name'],
                    'spending': spending,
                    'success_rate': round(success_rate, 3),
                    'median_final': int(250000 + np.random.normal(0, 50000)),
                    'p10_final': int(50000 + np.random.normal(0, 10000)),
                    'p90_final': int(750000 + np.random.normal(0, 100000))
                })
        return results
    
    # Create scenario configs
    scenario_configs = []
    for scenario in scenarios:
        config = create_scenario_config(
            name=scenario['name'],
            initial_portfolio=scenario['initial_portfolio'],
            has_annuity=scenario['has_annuity'],
            annuity_type=scenario.get('annuity_type'),
            annuity_annual=scenario.get('annuity_annual', 0),
            annuity_guarantee_years=scenario.get('annuity_guarantee_years', 0)
        )
        scenario_configs.append(config)
    
    # Run stacked simulations
    results = simulate_stacked_scenarios(
        scenarios=scenario_configs,
        spending_levels=spending_levels,
        n_simulations=2000,
        n_years=30,
        base_params=parameters,
        include_percentiles=True,
        random_seed=42
    )
    
    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            'scenario': result['scenario'].lower().replace(' ', '_').replace('+', ''),
            'scenario_name': result['scenario'],
            'spending': result['spending'],
            'success_rate': result['success_rate'],
            'median_final': result['median_final'],
            'p10_final': result['p10_final'],
            'p90_final': result['p90_final']
        })
    
    return formatted_results


def analyze_confidence_thresholds(
    scenarios: List[Dict[str, Any]],
    confidence_levels: List[int],
    parameters: Dict[str, Any]
) -> Dict[str, Dict[str, int]]:
    """Analyze confidence thresholds for scenarios."""
    
    if not FINSIM_AVAILABLE:
        # Return mock data for testing
        results = {}
        for scenario in scenarios:
            results[scenario['id']] = {}
            base_spending = 70000 if scenario['has_annuity'] else 60000
            for conf in confidence_levels:
                # Higher confidence = lower spending
                adjustment = (90 - conf) * 500
                results[scenario['id']][str(conf)] = base_spending - adjustment
        return results
    
    # Define spending levels to test
    spending_levels = list(range(30000, 105000, 5000))
    
    # Run batch simulation
    batch_results = run_batch_simulation(scenarios, spending_levels, parameters)
    
    # Analyze thresholds for each scenario
    results = {}
    for scenario in scenarios:
        scenario_results = [r for r in batch_results if r['scenario'] == scenario['id']]
        
        thresholds = {}
        for conf in confidence_levels:
            target_success = conf / 100.0
            
            # Find the highest spending with success rate >= target
            best_spending = 30000
            for result in scenario_results:
                if result['success_rate'] >= target_success:
                    best_spending = max(best_spending, result['spending'])
            
            thresholds[str(conf)] = best_spending
        
        results[scenario['id']] = thresholds
    
    return results