# FinSim: Financial Simulation Tool

```{image} https://img.shields.io/pypi/v/finsim
:alt: PyPI version
```

```{image} https://img.shields.io/github/actions/workflow/status/PolicyEngine/finsim/test.yml
:alt: Test Status
```

```{image} https://img.shields.io/codecov/c/github/PolicyEngine/finsim
:alt: Coverage
```

## Overview

FinSim is a comprehensive financial simulation tool for comparing structured settlement annuities with index fund investments, accounting for taxes, Social Security benefits, and mortality risk.

## Key Features

- **Monte Carlo Simulations**: Model thousands of potential market scenarios
- **Tax-Aware Calculations**: Integrate PolicyEngine-US for accurate federal and state taxes
- **Annuity Analysis**: Calculate IRR with mortality weighting for life-contingent options
- **Social Security Projections**: Include COLA adjustments based on SSA uprating
- **Interactive Visualizations**: Explore results with Streamlit dashboard

## Installation

```bash
pip install finsim
```

For Python 3.13+:

```bash
pip install "finsim[app]"  # Include Streamlit dependencies
```

## Quick Example

```python
from finsim import MonteCarloSimulator

# Simulate index fund investment
sim = MonteCarloSimulator(
    initial_capital=500_000,
    monthly_withdrawal=3_500,
    annual_return_mean=0.08,  # 8% expected return
    annual_return_std=0.158,  # 15.8% volatility
)

results = sim.simulate(n_months=360)  # 30 years
print(f"Depletion probability: {results['depletion_probability']:.1%}")
```

## Use Cases

FinSim is designed for:

- **Settlement Planning**: Compare lump-sum vs annuity options
- **Retirement Analysis**: Model withdrawal strategies with tax impacts
- **Risk Assessment**: Understand probability of portfolio depletion
- **Tax Optimization**: Find tax-efficient withdrawal amounts

## Components

```{tableofcontents}
```