"""Tests for Monte Carlo simulator."""

import pytest
import numpy as np
from finsim.monte_carlo import MonteCarloSimulator


class TestMonteCarloSimulator:
    """Test suite for MonteCarloSimulator."""
    
    def test_initialization(self):
        """Test simulator initialization with default and custom parameters."""
        # Default initialization
        sim = MonteCarloSimulator(
            initial_capital=100_000,
            monthly_withdrawal=1_000
        )
        assert sim.initial_capital == 100_000
        assert sim.monthly_withdrawal == 1_000
        assert sim.annual_return_mean == 0.08
        assert sim.annual_return_std == 0.158
        assert sim.n_simulations == 10_000
        
        # Custom initialization
        sim2 = MonteCarloSimulator(
            initial_capital=500_000,
            monthly_withdrawal=3_000,
            annual_return_mean=0.10,
            annual_return_std=0.20,
            n_simulations=5_000
        )
        assert sim2.annual_return_mean == 0.10
        assert sim2.n_simulations == 5_000
    
    def test_simulation_output_structure(self):
        """Test that simulation returns expected output structure."""
        sim = MonteCarloSimulator(
            initial_capital=100_000,
            monthly_withdrawal=500,
            n_simulations=100,
            seed=42
        )
        
        results = sim.simulate(n_months=12)
        
        # Check output keys
        assert 'paths' in results
        assert 'final_values' in results
        assert 'depletion_month' in results
        assert 'percentiles' in results
        assert 'depletion_probability' in results
        assert 'mean_final_value' in results
        assert 'median_final_value' in results
        
        # Check shapes
        assert results['paths'].shape == (100, 13)  # n_simulations x (n_months + 1)
        assert len(results['final_values']) == 100
        assert len(results['depletion_month']) == 100
        
        # Check percentiles
        assert 'p5' in results['percentiles']
        assert 'p50' in results['percentiles']
        assert 'p95' in results['percentiles']
    
    def test_no_withdrawal_growth(self):
        """Test that portfolio grows with no withdrawals."""
        sim = MonteCarloSimulator(
            initial_capital=100_000,
            monthly_withdrawal=0,
            annual_return_mean=0.08,
            annual_return_std=0.0,  # No volatility for deterministic test
            n_simulations=1,
            seed=42
        )
        
        results = sim.simulate(n_months=12)
        
        # With 8% annual return and no volatility, should grow
        expected_final = 100_000 * (1.08 ** (12/12))
        assert results['final_values'][0] > 100_000
        # Allow some tolerance for monthly compounding
        assert abs(results['final_values'][0] - expected_final) / expected_final < 0.01
    
    def test_high_withdrawal_depletion(self):
        """Test that high withdrawals lead to depletion."""
        sim = MonteCarloSimulator(
            initial_capital=100_000,
            monthly_withdrawal=20_000,  # Very high withdrawal
            annual_return_mean=0.08,
            n_simulations=100,
            seed=42
        )
        
        results = sim.simulate(n_months=12)
        
        # Should deplete quickly
        assert results['depletion_probability'] > 0.9
        assert np.median(results['depletion_month']) < 6
    
    def test_safe_withdrawal_rate_calculation(self):
        """Test safe withdrawal rate calculation."""
        sim = MonteCarloSimulator(
            initial_capital=1_000_000,
            monthly_withdrawal=0,  # Will be set by method
            n_simulations=1_000,
            seed=42
        )
        
        safe_withdrawal = sim.calculate_safe_withdrawal_rate(
            n_months=360,  # 30 years
            target_success_rate=0.95
        )
        
        # 4% rule suggests ~3,333/month for 1M
        # With 95% success rate, should be somewhat conservative
        assert 2_000 < safe_withdrawal < 5_000
        
        # Verify it actually achieves target success rate
        sim.monthly_withdrawal = safe_withdrawal
        results = sim.simulate(n_months=360)
        success_rate = 1 - results['depletion_probability']
        assert 0.94 < success_rate < 0.96
    
    def test_dividend_reinvestment(self):
        """Test dividend reinvestment vs withdrawal."""
        sim_reinvest = MonteCarloSimulator(
            initial_capital=100_000,
            monthly_withdrawal=1_000,
            annual_dividend_yield=0.024,  # 2.4% yield
            n_simulations=100,
            seed=42
        )
        
        sim_no_reinvest = MonteCarloSimulator(
            initial_capital=100_000,
            monthly_withdrawal=1_000,
            annual_dividend_yield=0.024,
            n_simulations=100,
            seed=42
        )
        
        results_reinvest = sim_reinvest.simulate(n_months=120, reinvest_dividends=True)
        results_no_reinvest = sim_no_reinvest.simulate(n_months=120, reinvest_dividends=False)
        
        # Reinvesting should lead to higher final values on average
        assert results_reinvest['mean_final_value'] > results_no_reinvest['mean_final_value']
    
    def test_reproducibility_with_seed(self):
        """Test that seed makes results reproducible."""
        sim1 = MonteCarloSimulator(
            initial_capital=100_000,
            monthly_withdrawal=1_000,
            n_simulations=100,
            seed=12345
        )
        
        sim2 = MonteCarloSimulator(
            initial_capital=100_000,
            monthly_withdrawal=1_000,
            n_simulations=100,
            seed=12345
        )
        
        results1 = sim1.simulate(n_months=60)
        results2 = sim2.simulate(n_months=60)
        
        # Should be identical
        np.testing.assert_array_equal(results1['paths'], results2['paths'])
        np.testing.assert_array_equal(results1['final_values'], results2['final_values'])