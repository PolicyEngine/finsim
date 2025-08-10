"""Inflation utilities for FinSim.

This module provides inflation adjustment using either:
1. A fixed annual rate (default)
2. Actual C-CPI-U data from PolicyEngine-US (if available)
"""

import numpy as np
from typing import Optional, List


def get_inflation_factors(
    start_year: int,
    n_years: int,
    fixed_rate: float = 2.5,
    use_actual_cpi: bool = False
) -> np.ndarray:
    """Get inflation factors for each year of simulation.
    
    Args:
        start_year: Starting year of simulation
        n_years: Number of years to simulate
        fixed_rate: Fixed annual inflation rate (as percentage, e.g., 2.5 for 2.5%)
        use_actual_cpi: Whether to use actual C-CPI-U data from PolicyEngine
        
    Returns:
        Array of cumulative inflation factors (1.0 for year 1, then compounding)
    """
    inflation_factors = np.ones(n_years)
    
    if use_actual_cpi:
        try:
            # Try to get actual C-CPI-U data from PolicyEngine
            from policyengine_us import Microsimulation
            from policyengine_core.periods import instant
            
            # Create a minimal simulation to access parameters
            sim = Microsimulation(dataset="cps_2024")
            parameters = sim.tax_benefit_system.parameters
            
            # Get C-CPI-U values for each year
            base_cpi = None
            for year in range(n_years):
                current_year = start_year + year
                
                # Get December CPI for each year (or latest available)
                try:
                    # Try December of the year
                    period = instant(f"{current_year}-12-01")
                    cpi = parameters.gov.bls.cpi.c_cpi_u(period)
                except:
                    # Fall back to January of next year if December not available
                    try:
                        period = instant(f"{current_year+1}-01-01")
                        cpi = parameters.gov.bls.cpi.c_cpi_u(period)
                    except:
                        # If future year, use fixed rate
                        if year > 0:
                            inflation_factors[year] = inflation_factors[year-1] * (1 + fixed_rate / 100)
                        continue
                
                if base_cpi is None:
                    base_cpi = cpi
                    inflation_factors[year] = 1.0
                else:
                    inflation_factors[year] = cpi / base_cpi
            
            print(f"Using actual C-CPI-U data from {start_year}")
            return inflation_factors
            
        except ImportError:
            print("PolicyEngine-US not available, using fixed inflation rate")
        except Exception as e:
            print(f"Could not load C-CPI-U data: {e}, using fixed rate")
    
    # Use fixed rate
    for year in range(1, n_years):
        inflation_factors[year] = inflation_factors[year-1] * (1 + fixed_rate / 100)
    
    return inflation_factors


def inflate_value(
    base_value: float,
    year_index: int,
    inflation_factors: np.ndarray
) -> float:
    """Inflate a base value to a specific year.
    
    Args:
        base_value: Value in base year dollars
        year_index: Year index (0-based)
        inflation_factors: Array of cumulative inflation factors
        
    Returns:
        Inflated value
    """
    if year_index < 0 or year_index >= len(inflation_factors):
        return base_value
    
    return base_value * inflation_factors[year_index]


def calculate_real_return(
    nominal_return: float,
    inflation_rate: float
) -> float:
    """Calculate real return from nominal return and inflation.
    
    Uses the Fisher equation: (1 + r_real) = (1 + r_nominal) / (1 + inflation)
    
    Args:
        nominal_return: Nominal return rate (as decimal, e.g., 0.07 for 7%)
        inflation_rate: Inflation rate (as decimal, e.g., 0.025 for 2.5%)
        
    Returns:
        Real return rate (as decimal)
    """
    return (1 + nominal_return) / (1 + inflation_rate) - 1


if __name__ == "__main__":
    # Test inflation calculations
    print("Testing inflation calculations")
    print("=" * 50)
    
    # Test fixed rate
    factors_fixed = get_inflation_factors(2025, 10, fixed_rate=2.5)
    print(f"\nFixed 2.5% inflation over 10 years:")
    for i, factor in enumerate(factors_fixed):
        print(f"  Year {i+1}: {factor:.3f} ({(factor-1)*100:.1f}% cumulative)")
    
    # Test with actual CPI if available
    factors_actual = get_inflation_factors(2020, 5, use_actual_cpi=True)
    print(f"\nActual C-CPI-U from 2020-2024:")
    for i, factor in enumerate(factors_actual):
        print(f"  Year {2020+i}: {factor:.3f} ({(factor-1)*100:.1f}% cumulative)")
    
    # Test real return calculation
    nominal = 0.07  # 7% nominal
    inflation = 0.025  # 2.5% inflation
    real = calculate_real_return(nominal, inflation)
    print(f"\nReal return: {nominal*100:.1f}% nominal - {inflation*100:.1f}% inflation = {real*100:.2f}% real")