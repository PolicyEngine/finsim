# Retirement Simulation

FinSim provides a comprehensive Monte Carlo simulation framework for retirement planning with accurate tax modeling through PolicyEngine-US integration.

## Core Components

### Simulation Configuration

The `SimulationConfig` class defines all parameters for a retirement simulation:

```python
from finsim.simulation import SimulationConfig

config = SimulationConfig(
    # Demographics
    current_age=65,
    retirement_age=65,
    max_age=95,
    gender="Male",
    
    # Financial position
    initial_portfolio=500_000,
    
    # Annual income & spending (real dollars)
    annual_consumption=60_000,
    social_security=24_000,
    pension=12_000,
    
    # Market assumptions
    expected_return=5.0,  # % real return
    return_volatility=16.0,  # % volatility
    dividend_yield=2.0,  # % dividend yield
    
    # Simulation settings
    n_simulations=1000,
    include_mortality=True
)
```

### Annuity Options

FinSim supports three types of annuity structures:

1. **Fixed Period**: Payments for a specified number of years
2. **Life Only**: Payments continue while the retiree is alive
3. **Life Contingent with Guarantee**: Payments for life with a minimum guarantee period

```python
config = SimulationConfig(
    # ... other parameters ...
    annuity_annual=42_000,  # $3,500/month
    annuity_type="Life Contingent with Guarantee",
    annuity_guarantee_years=15
)
```

## Monte Carlo Simulation

The simulation uses Geometric Brownian Motion (GBM) to model portfolio returns:

$$dS/S = \mu dt + \sigma dW$$

Where:
- $\mu$ is the expected return (drift)
- $\sigma$ is the volatility
- $dW$ is a Brownian motion increment

```python
from finsim.simulation import RetirementSimulation

sim = RetirementSimulation(config)
results = sim.run_monte_carlo()

print(f"Success rate: {results.success_rate:.1%}")
print(f"Median final portfolio: ${results.percentiles[50][-1]:,.0f}")
```

## Mortality Risk

FinSim uses SSA Period Life Tables (2021) for mortality modeling:

```python
from finsim.mortality import get_mortality_rate, calculate_survival_curve

# Get mortality rate for a 75-year-old male
mort_rate = get_mortality_rate(age=75, gender="Male")
print(f"Annual mortality rate: {mort_rate:.3%}")

# Calculate survival curve from 65 to 95
survival_probs = calculate_survival_curve(65, 95, gender="Female")
```

## Tax Calculations

FinSim integrates with PolicyEngine-US for accurate federal and state tax calculations:

```python
from finsim.tax import TaxCalculator

calc = TaxCalculator(state="CA", year=2024)

# Calculate taxes on retirement income
taxes = calc.calculate_taxes(
    ordinary_income=50_000,
    qualified_dividends=5_000,
    long_term_capital_gains=10_000
)
```

## Results Analysis

The simulation returns comprehensive results including:

- Portfolio survival rates
- Percentile distributions (10th, 25th, 50th, 75th, 90th)
- Annual cash flows (dividends, withdrawals, taxes)
- Failure year distribution
- Mortality-adjusted outcomes

```python
# Analyze results
successful_scenarios = results.failure_years > config.max_age - config.current_age
median_final = np.median(results.portfolio_paths[successful_scenarios, -1])

print(f"Success rate: {results.success_rate:.1%}")
print(f"Median final value (successful only): ${median_final:,.0f}")
```

## Example: Complete Simulation

```python
from finsim.simulation import SimulationConfig, RetirementSimulation
import numpy as np

# Configure simulation
config = SimulationConfig(
    current_age=65,
    max_age=95,
    initial_portfolio=1_000_000,
    annual_consumption=80_000,
    social_security=30_000,
    expected_return=5.0,
    return_volatility=16.0,
    n_simulations=10_000
)

# Run simulation
sim = RetirementSimulation(config)
results = sim.run_monte_carlo()

# Analyze outcomes
print(f"Success rate: {results.success_rate:.1%}")
print(f"10th percentile final: ${results.percentiles[10][-1]:,.0f}")
print(f"Median final: ${results.percentiles[50][-1]:,.0f}")
print(f"90th percentile final: ${results.percentiles[90][-1]:,.0f}")

# Failure analysis
failures = results.failure_years[results.failure_years <= 30]
if len(failures) > 0:
    print(f"Median failure age: {config.current_age + np.median(failures):.0f}")
```