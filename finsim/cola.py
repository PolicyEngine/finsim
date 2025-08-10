"""Social Security COLA calculations using actual SSA uprating from PolicyEngine-US.

Uses the actual SSA uprating schedule which includes:
- Historical CPI-W based adjustments through 2024
- CBO projections for 2025-2035
"""

import numpy as np
from typing import Optional


# Hardcoded SSA uprating values from PolicyEngine-US
# Source: policyengine_us/parameters/gov/ssa/uprating.yaml
SSA_UPRATING = {
    2022: 268.421,
    2023: 291.901,
    2024: 301.236,
    2025: 310.866,
    2026: 318.155,
    2027: 326.149,
    2028: 332.241,
    2029: 339.431,
    2030: 346.917,
    2031: 354.6,
    2032: 362.579,
    2033: 370.656,
    2034: 379.028,
    2035: 387.598,
}

# Hardcoded C-CPI-U values from PolicyEngine-US  
# Source: policyengine_us/parameters/gov/bls/cpi/c_cpi_u.yaml
C_CPI_U = {
    2024: 171.910,
    2025: 176.7,  # February 2025 value (for 2026 tax parameters)
    2026: 180.5,
    2027: 184.1,
    2028: 187.8,
    2029: 191.5,
    2030: 195.3,
    2031: 199.1,
    2032: 203.1,
    2033: 207.1,
    2034: 211.2,
    2035: 215.4,
}

def get_ssa_cola_factors(start_year: int, n_years: int) -> np.ndarray:
    """Get Social Security COLA factors using actual SSA uprating schedule.
    
    Args:
        start_year: Starting year of simulation
        n_years: Number of years to simulate
        
    Returns:
        Array of cumulative COLA factors (1.0 for year 1, then compounding)
    """
    cola_factors = np.ones(n_years)
    
    # Use hardcoded values first, then try PolicyEngine-US for extended years
    base_uprating = None
    
    for year_idx in range(n_years):
        current_year = start_year + year_idx
        
        if current_year in SSA_UPRATING:
            # Use hardcoded value
            uprating = SSA_UPRATING[current_year]
        else:
            # Try to get from PolicyEngine-US for years beyond 2035
            try:
                from policyengine_us import Microsimulation
                from policyengine_core.periods import instant
                
                # Only create simulation once
                if 'sim' not in locals():
                    sim = Microsimulation(dataset="cps_2024")
                    parameters = sim.tax_benefit_system.parameters
                
                period = instant(f"{current_year}-01-01")
                uprating = parameters.gov.ssa.uprating(period)
            except:
                # For years beyond available data, use 2.2% annual growth (long-term average)
                if year_idx > 0:
                    prev_year = start_year + year_idx - 1
                    if prev_year in SSA_UPRATING:
                        uprating = SSA_UPRATING[prev_year] * 1.022
                    else:
                        uprating = cola_factors[year_idx - 1] * 1.022
                else:
                    uprating = SSA_UPRATING.get(2035, 387.598) * ((current_year - 2035) * 0.022 + 1)
        
        if base_uprating is None:
            base_uprating = uprating
            cola_factors[year_idx] = 1.0
        else:
            # Calculate cumulative factor from base year
            cola_factors[year_idx] = uprating / base_uprating
    
    return cola_factors


def get_consumption_inflation_factors(start_year: int, n_years: int) -> np.ndarray:
    """Get consumption inflation factors using C-CPI-U from PolicyEngine-US.
    
    Args:
        start_year: Starting year of simulation
        n_years: Number of years to simulate
        
    Returns:
        Array of cumulative inflation factors (1.0 for year 1, then compounding)
    """
    inflation_factors = np.ones(n_years)
    
    # Use hardcoded values first, then extrapolate if needed
    base_cpi = None
    
    for year_idx in range(n_years):
        current_year = start_year + year_idx
        
        if current_year in C_CPI_U:
            # Use hardcoded value
            cpi = C_CPI_U[current_year]
        else:
            # For years beyond available data, use 2.0% annual growth (Fed target)
            if year_idx > 0:
                prev_year = start_year + year_idx - 1
                if prev_year in C_CPI_U:
                    cpi = C_CPI_U[prev_year] * 1.020
                else:
                    # Use previous calculated value
                    cpi = base_cpi * inflation_factors[year_idx - 1] * 1.020
            else:
                cpi = C_CPI_U.get(2035, 215.4) * ((current_year - 2035) * 0.020 + 1)
        
        if base_cpi is None:
            base_cpi = cpi
            inflation_factors[year_idx] = 1.0
        else:
            # Calculate cumulative factor from base year
            inflation_factors[year_idx] = cpi / base_cpi
    
    return inflation_factors


if __name__ == "__main__":
    print("Testing SSA COLA and C-CPI-U from PolicyEngine-US")
    print("=" * 60)
    
    try:
        # Test SSA COLA
        cola_factors = get_ssa_cola_factors(2025, 10)
        print("\nSSA COLA factors (2025-2034):")
        for i in range(10):
            year = 2025 + i
            if i == 0:
                print(f"  {year}: {cola_factors[i]:.3f} (base year)")
            else:
                annual_rate = (cola_factors[i] / cola_factors[i-1] - 1) * 100
                print(f"  {year}: {cola_factors[i]:.3f} ({annual_rate:.1f}% annual, {(cola_factors[i]-1)*100:.1f}% cumulative)")
        
        # Test C-CPI-U
        inflation_factors = get_consumption_inflation_factors(2025, 10)
        print("\nC-CPI-U inflation factors (2025-2034):")
        for i in range(10):
            year = 2025 + i
            if i == 0:
                print(f"  {year}: {inflation_factors[i]:.3f} (base year)")
            else:
                annual_rate = (inflation_factors[i] / inflation_factors[i-1] - 1) * 100
                print(f"  {year}: {inflation_factors[i]:.3f} ({annual_rate:.1f}% annual, {(inflation_factors[i]-1)*100:.1f}% cumulative)")
                
    except ImportError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")