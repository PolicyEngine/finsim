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

# Lazy imports to avoid circular dependencies
__all__ = [
    "MonteCarloSimulator",
    "AnnuityCalculator",
    "TaxCalculator",
    "MonteCarloDataset",
    "ReturnGenerator",
    "simulate_portfolio",
    "get_mortality_rates",
    "apply_mortality",
]

def __getattr__(name):
    """Lazy import of modules to avoid circular dependencies."""
    if name == "MonteCarloSimulator":
        from .monte_carlo import MonteCarloSimulator
        return MonteCarloSimulator
    elif name == "AnnuityCalculator":
        from .annuity import AnnuityCalculator
        return AnnuityCalculator
    elif name == "TaxCalculator":
        from .tax import TaxCalculator
        return TaxCalculator
    elif name == "MonteCarloDataset":
        from .tax import MonteCarloDataset
        return MonteCarloDataset
    elif name == "ReturnGenerator":
        from .return_generator import ReturnGenerator
        return ReturnGenerator
    elif name == "simulate_portfolio":
        from .portfolio_simulation import simulate_portfolio
        return simulate_portfolio
    elif name in ["get_mortality_rates", "apply_mortality"]:
        from .mortality import apply_mortality, get_mortality_rates
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
