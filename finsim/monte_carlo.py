"""Monte Carlo simulation for index fund investments."""

import numpy as np
import pandas as pd
from typing import Tuple, Optional


class MonteCarloSimulator:
    """Monte Carlo simulator for index fund investments."""
    
    def __init__(
        self,
        initial_capital: float,
        monthly_withdrawal: float,
        annual_return_mean: float = 0.08,
        annual_return_std: float = 0.158,
        annual_dividend_yield: float = 0.02,
        n_simulations: int = 10_000,
        seed: Optional[int] = None
    ):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            initial_capital: Starting investment amount
            monthly_withdrawal: Monthly withdrawal amount (can be negative for contributions)
            annual_return_mean: Expected annual return (default 8% for VT)
            annual_return_std: Annual return standard deviation (default 15.8% for VT)
            annual_dividend_yield: Annual dividend yield (default 2%)
            n_simulations: Number of simulation paths
            seed: Random seed for reproducibility
        """
        self.initial_capital = initial_capital
        self.monthly_withdrawal = monthly_withdrawal
        self.annual_return_mean = annual_return_mean
        self.annual_return_std = annual_return_std
        self.annual_dividend_yield = annual_dividend_yield
        self.n_simulations = n_simulations
        
        if seed is not None:
            np.random.seed(seed)
    
    def simulate(
        self,
        n_months: int,
        reinvest_dividends: bool = True
    ) -> dict:
        """
        Run Monte Carlo simulation.
        
        Args:
            n_months: Number of months to simulate
            reinvest_dividends: Whether to reinvest dividends
            
        Returns:
            Dictionary with simulation results including:
                - paths: Array of portfolio values over time (n_simulations x n_months+1)
                - final_values: Final portfolio values for each simulation
                - depletion_month: Month of depletion for each simulation (inf if never depleted)
                - percentiles: Key percentiles of final values
                - depletion_probability: Probability of portfolio depletion
        """
        # Convert annual parameters to monthly
        monthly_return_mean = self.annual_return_mean / 12
        monthly_return_std = self.annual_return_std / np.sqrt(12)
        monthly_dividend_yield = self.annual_dividend_yield / 12
        
        # Initialize portfolio paths
        paths = np.zeros((self.n_simulations, n_months + 1))
        paths[:, 0] = self.initial_capital
        
        # Track depletion month for each simulation
        depletion_month = np.full(self.n_simulations, np.inf)
        
        # Generate random returns for all simulations and months at once
        returns = np.random.normal(
            monthly_return_mean, 
            monthly_return_std, 
            (self.n_simulations, n_months)
        )
        
        # Simulate each month
        for month in range(n_months):
            current_value = paths[:, month]
            
            # Skip if already depleted
            active = current_value > 0
            
            if not np.any(active):
                break
            
            # Calculate dividends
            dividends = current_value * monthly_dividend_yield
            
            # Apply returns (capital appreciation)
            growth = current_value * returns[:, month]
            
            # Calculate new value
            if reinvest_dividends:
                new_value = current_value + growth + dividends - self.monthly_withdrawal
            else:
                # If not reinvesting, dividends are withdrawn along with regular withdrawal
                new_value = current_value + growth - (self.monthly_withdrawal - dividends)
            
            # Handle depletion
            depleted = (current_value > 0) & (new_value <= 0)
            depletion_month[depleted & (depletion_month == np.inf)] = month + 1
            
            # Set negative values to zero
            new_value = np.maximum(new_value, 0)
            
            paths[:, month + 1] = new_value
        
        # Calculate statistics
        final_values = paths[:, -1]
        
        return {
            'paths': paths,
            'final_values': final_values,
            'depletion_month': depletion_month,
            'percentiles': {
                'p5': np.percentile(final_values, 5),
                'p25': np.percentile(final_values, 25),
                'p50': np.percentile(final_values, 50),
                'p75': np.percentile(final_values, 75),
                'p95': np.percentile(final_values, 95)
            },
            'depletion_probability': np.mean(depletion_month < np.inf),
            'mean_final_value': np.mean(final_values),
            'median_final_value': np.median(final_values)
        }
    
    def calculate_safe_withdrawal_rate(
        self,
        n_months: int,
        target_success_rate: float = 0.95,
        tolerance: float = 0.001
    ) -> float:
        """
        Calculate safe withdrawal rate using binary search.
        
        Args:
            n_months: Investment horizon in months
            target_success_rate: Desired probability of not depleting (default 95%)
            tolerance: Convergence tolerance
            
        Returns:
            Monthly withdrawal amount that achieves target success rate
        """
        # Binary search for safe withdrawal rate
        low = 0
        high = self.initial_capital / n_months * 2  # Conservative upper bound
        
        while high - low > tolerance:
            mid = (low + high) / 2
            self.monthly_withdrawal = mid
            
            results = self.simulate(n_months)
            success_rate = 1 - results['depletion_probability']
            
            if success_rate < target_success_rate:
                high = mid
            else:
                low = mid
        
        return (low + high) / 2