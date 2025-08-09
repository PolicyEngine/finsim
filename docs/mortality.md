# Mortality Data

FinSim uses official Social Security Administration (SSA) Period Life Tables for accurate mortality modeling in retirement simulations.

## Data Source

The mortality data comes from the SSA Period Life Table 2021, the most recent available data:
- Source: [SSA Table 4C6](https://www.ssa.gov/oact/STATS/table4c6.html)
- Coverage: Ages 65-100
- Gender-specific rates for males and females

## Using Mortality Data

### Basic Usage

```python
from finsim.mortality import get_mortality_rate, get_mortality_rates

# Get mortality rate for a specific age
rate_male_75 = get_mortality_rate(age=75, gender="Male")
print(f"75-year-old male mortality rate: {rate_male_75:.3%}")

# Get all mortality rates for a gender
male_rates = get_mortality_rates(gender="Male")
female_rates = get_mortality_rates(gender="Female")
```

### Survival Curves

Calculate cumulative survival probabilities:

```python
from finsim.mortality import calculate_survival_curve
import matplotlib.pyplot as plt

# Calculate survival from age 65 to 100
ages = range(65, 101)
male_survival = calculate_survival_curve(65, 100, gender="Male")
female_survival = calculate_survival_curve(65, 100, gender="Female")

# Plot survival curves
plt.figure(figsize=(10, 6))
plt.plot(ages, male_survival, label="Male", color="blue")
plt.plot(ages, female_survival, label="Female", color="red")
plt.xlabel("Age")
plt.ylabel("Probability of Survival")
plt.title("Survival Probability from Age 65")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

## Data Management

### Updating Mortality Data

The mortality data can be updated using the data fetcher:

```python
from finsim.data_fetcher import SSAMortalityFetcher

# Fetch latest data from SSA
fetcher = SSAMortalityFetcher()
male_mortality, female_mortality = fetcher.fetch_tables()

# Save to JSON file
fetcher.save_to_json()
```

### Fallback Data

If the SSA website is unavailable, the fetcher uses hardcoded 2021 data as a fallback to ensure the package always works.

## Mortality Statistics

Key statistics from the SSA 2021 Period Life Table:

| Age | Male Mortality Rate | Female Mortality Rate |
|-----|-------------------|---------------------|
| 65  | 1.60%            | 1.05%              |
| 70  | 2.48%            | 1.64%              |
| 75  | 3.84%            | 2.65%              |
| 80  | 6.07%            | 4.37%              |
| 85  | 9.76%            | 7.25%              |
| 90  | 15.83%           | 11.99%             |
| 95  | 25.46%           | 19.62%             |
| 100 | 40.03%           | 31.47%             |

## Life Expectancy

Based on the SSA 2021 data:

```python
from finsim.mortality import calculate_life_expectancy

# Calculate remaining life expectancy
life_exp_male_65 = calculate_life_expectancy(65, gender="Male")
life_exp_female_65 = calculate_life_expectancy(65, gender="Female")

print(f"65-year-old male life expectancy: {life_exp_male_65:.1f} years")
print(f"65-year-old female life expectancy: {life_exp_female_65:.1f} years")
```

## Integration with Simulations

Mortality risk is automatically incorporated in retirement simulations:

```python
from finsim.simulation import SimulationConfig, RetirementSimulation

config = SimulationConfig(
    current_age=65,
    max_age=100,
    gender="Female",
    include_mortality=True,  # Enable mortality modeling
    # ... other parameters
)

sim = RetirementSimulation(config)
results = sim.run_monte_carlo()

# Results account for probability of death each year
```

## Technical Notes

1. **Interpolation**: For ages not directly in the table, linear interpolation is used
2. **Extrapolation**: For ages beyond 100, the age 100 mortality rate is used
3. **Updates**: The data can be refreshed by running the fetcher when SSA releases new tables
4. **Validation**: All mortality rates are validated to be between 0 and 1, and generally increasing with age