# Quick Start Guide

## Installation

Install FinSim using pip:

```bash
pip install finsim
```

For the full application with visualization:

```bash
pip install "finsim[app]"
```

## Basic Usage

### Monte Carlo Simulation

```python
from finsim import MonteCarloSimulator

# Create simulator
sim = MonteCarloSimulator(
    initial_capital=1_000_000,
    monthly_withdrawal=4_000,
    annual_return_mean=0.07,
    annual_return_std=0.15
)

# Run simulation
results = sim.simulate(n_months=360)  # 30 years

# View results
print(f"Depletion probability: {results['depletion_probability']:.1%}")
print(f"Median final value: ${results['median_final_value']:,.0f}")
```

### Tax Calculations

```python
from finsim import TaxCalculator

# Initialize calculator
tax_calc = TaxCalculator(state="CA", year=2025)

# Calculate taxes on investment withdrawals
taxes = tax_calc.calculate_taxes(
    capital_gains=50_000,
    social_security_benefits=24_000,
    age=65
)

print(f"Federal tax: ${taxes['federal_income_tax']:,.0f}")
print(f"State tax: ${taxes['state_income_tax']:,.0f}")
print(f"Effective rate: {taxes['effective_tax_rate']:.1%}")
```

### Annuity Analysis

```python
from finsim import AnnuityCalculator

# Create calculator
annuity_calc = AnnuityCalculator(age=65)

# Calculate IRR for an annuity
irr = annuity_calc.calculate_irr(
    premium=500_000,
    monthly_payment=3_500,
    guarantee_months=180,  # 15 years
    life_contingent=True
)

print(f"Expected IRR: {irr:.1%}")
```

## Running the Streamlit App

If you have the app dependencies installed:

```bash
streamlit run app.py
```

This launches an interactive dashboard where you can:
1. Input your financial details
2. Enter annuity proposals
3. View Monte Carlo simulations
4. Compare tax impacts
5. Analyze depletion risks

## Next Steps

- Read the [Monte Carlo Guide](monte_carlo.md) for advanced simulation options
- Learn about [Tax Calculations](tax_calculations.md) and optimization
- Explore [Annuity Analysis](annuities.md) features
- See [Examples](examples.md) for real-world scenarios