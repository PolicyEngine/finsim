"""
FinSim - Financial Simulation Package
=====================================

A comprehensive financial simulation tool for comparing annuities, 
investments, and retirement strategies with tax-aware Monte Carlo modeling.

Main Components:
- MonteCarloSimulator: Run probabilistic investment simulations
- TaxCalculator: Calculate taxes using PolicyEngine-US
- AnnuityCalculator: Analyze and compare annuity options

Example:
    >>> from finsim import MonteCarloSimulator
    >>> sim = MonteCarloSimulator(initial_capital=500_000, monthly_withdrawal=3_000)
    >>> results = sim.simulate(n_months=360)
    >>> print(f"Depletion probability: {results['depletion_probability']:.1%}")
"""

__version__ = "0.1.0"

from .monte_carlo import MonteCarloSimulator
from .tax_calculator import TaxCalculator
from .annuity import AnnuityCalculator
from .enhanced_monte_carlo import EnhancedMonteCarloSimulator
from .vectorized_tax import (
    VectorizedTaxCalculator,
    MonteCarloDataset,
    calculate_monte_carlo_after_tax_income
)

__all__ = [
    "MonteCarloSimulator",
    "TaxCalculator", 
    "AnnuityCalculator",
    "EnhancedMonteCarloSimulator",
    "VectorizedTaxCalculator",
    "MonteCarloDataset",
    "calculate_monte_carlo_after_tax_income"
]