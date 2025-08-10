# Inflation Indexing in FinSim

FinSim properly accounts for inflation in retirement planning simulations using different inflation indices for different purposes, matching real-world practices.

## Inflation Rates Used

### 1. Social Security COLA (Cost-of-Living Adjustment)
- **Index**: CPI-W (Consumer Price Index for Urban Wage Earners and Clerical Workers)
- **Default Rate**: 2.3% annually
- **Application**: Social Security benefits are adjusted annually
- **Parameter**: `social_security_cola_rate`
- **Source**: Based on SSA's uprating schedule from PolicyEngine-US

### 2. General Consumption Inflation
- **Index**: C-CPI-U (Chained Consumer Price Index for All Urban Consumers)
- **Default Rate**: 2.5% annually
- **Application**: Annual consumption/expenses grow with this rate
- **Parameter**: `consumption_inflation_rate`
- **Source**: Based on long-term C-CPI-U averages from BLS

### 3. Employment Income Growth
- **Index**: Nominal wage growth (includes inflation + real wage growth)
- **Default Rate**: 0% (user-specified)
- **Application**: Wages before retirement
- **Parameter**: `employment_growth_rate`
- **Note**: Typically 3-4% to include both inflation and productivity gains

## Why Different Rates?

The U.S. government uses different inflation measures for different purposes:

- **CPI-W** for Social Security: Measures inflation experienced by wage earners and clerical workers. Historically runs slightly lower than CPI-U.

- **C-CPI-U** for general inflation: A more accurate measure that accounts for consumer substitution between goods when prices change. Used for tax brackets since 2018.

- **Nominal wage growth**: Includes both inflation and real wage growth from productivity improvements.

## Historical Differences

Over the long term:
- CPI-W averages around 2.3% annually
- C-CPI-U averages around 2.5% annually  
- Nominal wage growth averages 3-4% annually

These small differences compound significantly over a 30+ year retirement.

## Implementation Details

```python
# Year-by-year adjustments in portfolio_simulation.py

# Social Security with COLA (CPI-W based)
years_of_cola = year - 1
cola_factor = (1 + social_security_cola_rate / 100) ** years_of_cola
current_social_security = social_security * cola_factor

# Consumption with inflation (C-CPI-U based)
years_of_inflation = year - 1
inflation_factor = (1 + consumption_inflation_rate / 100) ** years_of_inflation
current_consumption = annual_consumption * inflation_factor

# Employment income growth (nominal)
years_of_growth = year - 1
growth_factor = (1 + employment_growth_rate / 100) ** years_of_growth
wages = employment_income * growth_factor
```

## Customization

Users can override the default rates based on their expectations:

```python
simulate_portfolio(
    # ... other parameters ...
    social_security_cola_rate=2.0,  # More conservative COLA
    consumption_inflation_rate=3.0,  # Higher inflation expectation
    employment_growth_rate=4.0,      # Nominal wage growth
)
```

## Future Enhancements

The `inflation.py` module includes support for using actual CPI data from PolicyEngine-US when available, allowing simulations to use historical inflation rates for backtesting or more sophisticated projections based on current economic conditions.