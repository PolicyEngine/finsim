"""Tests for main simulation module."""


import numpy as np
import pytest


class TestSimulation:
    """Test the main Simulation class."""

    @pytest.fixture
    def basic_config(self):
        """Basic configuration for testing."""
        return {
            'initial_portfolio': 500_000,
            'annual_contribution': 0,
            'expected_return': 0.07,
            'volatility': 0.15,
            'years': 30,
            'simulations': 100,
            'annual_withdrawal': 40_000,
            'inflation_rate': 0.02
        }

    def test_simulation_init(self, basic_config):
        """Test Simulation initialization."""
        from finsim.simulation import Simulation

        sim = Simulation(**basic_config)

        assert sim.initial_portfolio == 500_000
        assert sim.expected_return == 0.07
        assert sim.volatility == 0.15
        assert sim.years == 30
        assert sim.simulations == 100

    def test_run_simulation(self, basic_config):
        """Test running a basic simulation."""
        from finsim.simulation import Simulation

        sim = Simulation(**basic_config)
        results = sim.run()

        # Check results structure
        assert 'portfolio_values' in results
        assert 'success_rate' in results
        assert 'percentiles' in results

        # Check shapes
        assert results['portfolio_values'].shape == (100, 31)  # simulations x (years+1)

        # Success rate should be between 0 and 1
        assert 0 <= results['success_rate'] <= 1

        # Should have standard percentiles
        assert len(results['percentiles']) >= 3

    def test_simulation_with_contributions(self, basic_config):
        """Test simulation with annual contributions."""
        from finsim.simulation import Simulation

        config = basic_config.copy()
        config['annual_contribution'] = 10_000
        config['annual_withdrawal'] = 0  # No withdrawals

        sim = Simulation(**config)
        results = sim.run()

        # With contributions and no withdrawals, should grow
        final_values = results['portfolio_values'][:, -1]
        initial_value = config['initial_portfolio']

        # Most simulations should end higher
        assert np.median(final_values) > initial_value

    def test_simulation_with_inflation(self, basic_config):
        """Test that inflation affects withdrawals."""
        from finsim.simulation import Simulation

        # Run with inflation
        config_with_inflation = basic_config.copy()
        config_with_inflation['inflation_rate'] = 0.03
        sim_inflation = Simulation(**config_with_inflation)
        results_inflation = sim_inflation.run()

        # Run without inflation
        config_no_inflation = basic_config.copy()
        config_no_inflation['inflation_rate'] = 0
        sim_no_inflation = Simulation(**config_no_inflation)
        results_no_inflation = sim_no_inflation.run()

        # Inflation should reduce success rate (withdrawals grow)
        assert (results_inflation['success_rate'] <=
                results_no_inflation['success_rate'])

    def test_monte_carlo_variability(self, basic_config):
        """Test that Monte Carlo produces variable results."""
        from finsim.simulation import Simulation

        sim = Simulation(**basic_config)
        results = sim.run()

        final_values = results['portfolio_values'][:, -1]

        # Should have variability in outcomes
        assert np.std(final_values) > 0

        # Should have both successes and failures with reasonable parameters
        successes = final_values > 0
        if basic_config['simulations'] > 50:
            # With 100 simulations, shouldn't all succeed or all fail
            assert 0.1 < np.mean(successes) < 0.9

    def test_percentile_calculations(self, basic_config):
        """Test percentile calculations."""
        from finsim.simulation import Simulation

        sim = Simulation(**basic_config)
        results = sim.run()

        percentiles = results['percentiles']

        # Should include key percentiles
        assert '5th' in percentiles or 5 in percentiles
        assert '50th' in percentiles or 50 in percentiles
        assert '95th' in percentiles or 95 in percentiles

        # Percentiles should be ordered
        if isinstance(list(percentiles.keys())[0], int):
            p5 = percentiles[5]
            p50 = percentiles[50]
            p95 = percentiles[95]
        else:
            p5 = percentiles['5th']
            p50 = percentiles['50th']
            p95 = percentiles['95th']

        # 5th < 50th < 95th at final year
        assert p5[-1] <= p50[-1] <= p95[-1]

    def test_success_rate_calculation(self, basic_config):
        """Test success rate calculation."""
        from finsim.simulation import Simulation

        # High withdrawal for more failures
        config = basic_config.copy()
        config['annual_withdrawal'] = 100_000

        sim = Simulation(**config)
        results = sim.run()

        # Calculate success rate manually
        final_values = results['portfolio_values'][:, -1]
        manual_success_rate = np.mean(final_values > 0)

        # Should match calculated success rate
        assert abs(results['success_rate'] - manual_success_rate) < 0.01

    def test_zero_volatility(self, basic_config):
        """Test simulation with zero volatility (deterministic)."""
        from finsim.simulation import Simulation

        config = basic_config.copy()
        config['volatility'] = 0
        config['simulations'] = 10  # Fewer needed since deterministic

        sim = Simulation(**config)
        results = sim.run()

        # All simulations should have similar outcomes
        final_values = results['portfolio_values'][:, -1]

        # With zero volatility, all paths should be very similar
        if len(final_values) > 1:
            assert np.std(final_values) / np.mean(final_values + 1) < 0.01

    def test_negative_returns(self, basic_config):
        """Test simulation with negative expected returns."""
        from finsim.simulation import Simulation

        config = basic_config.copy()
        config['expected_return'] = -0.05  # Negative returns
        config['annual_withdrawal'] = 20_000  # Modest withdrawals

        sim = Simulation(**config)
        results = sim.run()

        # Should handle negative returns
        assert results['success_rate'] >= 0

        # Most should fail with negative returns and withdrawals
        assert results['success_rate'] < 0.5

    def test_extreme_parameters(self):
        """Test simulation with extreme parameters."""
        from finsim.simulation import Simulation

        # Very short time horizon
        sim_short = Simulation(
            initial_portfolio=100_000,
            years=1,
            simulations=10,
            expected_return=0.07,
            volatility=0.15,
            annual_withdrawal=50_000
        )
        results_short = sim_short.run()
        assert results_short['portfolio_values'].shape == (10, 2)

        # Very high volatility
        sim_volatile = Simulation(
            initial_portfolio=100_000,
            years=10,
            simulations=50,
            expected_return=0.07,
            volatility=0.80,  # 80% volatility
            annual_withdrawal=5_000
        )
        results_volatile = sim_volatile.run()

        # Should have very wide range of outcomes
        final_values = results_volatile['portfolio_values'][:, -1]
        if np.any(final_values > 0):
            max_val = np.max(final_values)
            min_pos_val = np.min(final_values[final_values > 0])
            assert max_val / (min_pos_val + 1) > 10
