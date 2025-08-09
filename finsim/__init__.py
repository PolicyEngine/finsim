"""
FinSim - Financial Simulation Package
=====================================

A comprehensive financial simulation tool for comparing annuities and
investments with tax-aware Monte Carlo modeling via PolicyEngine-US.

Main Components:
- MonteCarloSimulator: Tax-aware Monte Carlo with optional GARCH
- AnnuityCalculator: Analyze and compare annuity options
- TaxCalculator: Batch tax calculations via PolicyEngine-US

Example:
    >>> from finsim import MonteCarloSimulator
    >>> sim = MonteCarloSimulator(
    ...     initial_capital=500_000,
    ...     target_after_tax_monthly=3_500,
    ...     social_security_monthly=2_000,
    ...     age=65
    ... )
    >>> results = sim.simulate(n_years=30)
    >>> print(f"Depletion probability: {results['depletion_probability']:.1%}")
"""

__version__ = "0.1.0"

from .monte_carlo import MonteCarloSimulator
from .annuity import AnnuityCalculator
from .tax import TaxCalculator, MonteCarloDataset

__all__ = [
    "MonteCarloSimulator",
    "AnnuityCalculator",
    "TaxCalculator",
    "MonteCarloDataset"
]