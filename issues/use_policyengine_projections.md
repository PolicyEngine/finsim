# Issue: Replace hardcoded inflation values with PolicyEngine-US API

## Current State
Currently, `finsim/cola.py` hardcodes SSA uprating and C-CPI-U values from PolicyEngine-US because:
1. The current PolicyEngine-US parameters only extend to 2035
2. Many retirement simulations need 30+ year projections (to 2055+)

## Hardcoded Values
```python
# From cola.py
SSA_UPRATING = {
    2022: 268.421,
    2023: 291.901,
    ...
    2035: 387.598,
}

C_CPI_U = {
    2024: 171.910,
    2025: 176.7,
    ...
    2035: 215.4,
}
```

## Solution
Once PolicyEngine/policyengine-us#6384 is merged (extends projections to 2100), update `cola.py` to:

1. Remove hardcoded dictionaries
2. Use PolicyEngine-US API directly:

```python
def get_ssa_cola_factors(start_year: int, n_years: int) -> np.ndarray:
    from policyengine_us import Microsimulation
    from policyengine_core.periods import instant
    
    sim = Microsimulation(dataset="cps_2024")
    parameters = sim.tax_benefit_system.parameters
    
    cola_factors = np.ones(n_years)
    base_uprating = None
    
    for year_idx in range(n_years):
        current_year = start_year + year_idx
        period = instant(f"{current_year}-01-01")
        uprating = parameters.gov.ssa.uprating(period)
        
        if base_uprating is None:
            base_uprating = uprating
            cola_factors[year_idx] = 1.0
        else:
            cola_factors[year_idx] = uprating / base_uprating
    
    return cola_factors
```

## Benefits
- Always uses latest projections from PolicyEngine-US
- Automatically incorporates CBO forecast updates
- Consistent with tax calculations
- No manual maintenance needed

## Dependencies
- Requires PolicyEngine-US with PR #6384 merged
- PR extends uprating/CPI projections to 2100

## Files to Update
- `finsim/cola.py`: Remove hardcoded values, use API
- `docs/inflation_indexing.md`: Update to note dynamic sourcing

## Testing
Ensure that:
1. Projections match for years 2025-2035 (current hardcoded range)
2. Projections extend smoothly beyond 2035
3. Performance is acceptable (may need caching if API calls are slow)