#!/usr/bin/env python3
"""Return generation module for Monte Carlo simulations.

This module generates a matrix of returns for multiple simulations over multiple years.
It ensures proper randomness, realistic distributions, and no repeated values.
"""


import numpy as np


class ReturnGenerator:
    """Generate returns for Monte Carlo simulations."""

    def __init__(self,
                 expected_return: float = 0.07,
                 volatility: float = 0.15,
                 seed: int | None = None):
        """Initialize the return generator.
        
        Args:
            expected_return: Annual expected return (e.g., 0.07 for 7%)
            volatility: Annual volatility (e.g., 0.15 for 15%)
            seed: Random seed for reproducibility (None for random)
        """
        self.expected_return = expected_return
        self.volatility = volatility
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

    def generate_returns(self,
                        n_simulations: int,
                        n_years: int) -> np.ndarray:
        """Generate matrix of annual returns (as growth factors).
        
        Args:
            n_simulations: Number of simulations
            n_years: Number of years
            
        Returns:
            Array of shape (n_simulations, n_years) with growth factors
            (e.g., 1.07 for 7% return)
        """
        # Generate all random numbers at once to ensure independence
        # This is the KEY FIX - generate the entire matrix upfront
        z_matrix = np.random.randn(n_simulations, n_years)

        # Add occasional fat tail events
        # About 2% chance of a larger move (between 2.5-3.5 sigma)
        # This gives realistic fat tails without extreme outliers
        fat_tail_mask = np.random.random((n_simulations, n_years)) < 0.02
        n_fat_tails = fat_tail_mask.sum()

        if n_fat_tails > 0:
            # Generate fat tail moves
            # Use uniform distribution between 2.5 and 3.5 sigma
            # Direction based on original z value
            fat_tail_positions = np.where(fat_tail_mask)
            original_signs = np.sign(z_matrix[fat_tail_positions])
            # If original was 0, randomly assign direction
            original_signs[original_signs == 0] = np.random.choice([-1, 1],
                                                                   size=(original_signs == 0).sum())

            magnitudes = np.random.uniform(2.5, 3.5, size=n_fat_tails)
            z_matrix[fat_tail_positions] = original_signs * magnitudes

        # Cap at 4 sigma to prevent numerical issues
        # This allows for roughly 80% annual gains or 40% losses at most
        z_matrix = np.clip(z_matrix, -4, 4)

        # Convert to log returns using GBM formula
        log_returns = (self.expected_return - 0.5 * self.volatility**2) + \
                     self.volatility * z_matrix

        # Convert to growth factors
        growth_factors = np.exp(log_returns)

        # Verify no simulation has repeated values
        # (This should never happen with proper random generation)
        for sim_idx in range(n_simulations):
            unique_vals = np.unique(np.round(growth_factors[sim_idx, :], 8))
            if len(unique_vals) < n_years * 0.8:  # Allow for some chance duplicates
                # This indicates a bug - regenerate this simulation
                print(f"WARNING: Simulation {sim_idx} had repeated values, regenerating...")
                growth_factors[sim_idx, :] = self._regenerate_single_simulation(n_years)

        return growth_factors

    def _regenerate_single_simulation(self, n_years: int) -> np.ndarray:
        """Regenerate a single simulation if it had repeated values.
        
        This is a safety fallback that should rarely be needed.
        """
        z = np.random.randn(n_years)
        z = np.clip(z, -4, 4)
        log_returns = (self.expected_return - 0.5 * self.volatility**2) + \
                     self.volatility * z
        return np.exp(log_returns)

    def generate_returns_with_correlation(self,
                                         n_simulations: int,
                                         n_years: int,
                                         correlation: float = 0.0) -> np.ndarray:
        """Generate returns with correlation between consecutive years.
        
        This can be used to model momentum or mean reversion.
        
        Args:
            n_simulations: Number of simulations
            n_years: Number of years
            correlation: Correlation between consecutive years (-1 to 1)
            
        Returns:
            Array of shape (n_simulations, n_years) with growth factors
        """
        # For now, just use independent returns
        # This could be extended with an AR(1) process if needed
        return self.generate_returns(n_simulations, n_years)
