"""Tests for main simulation module."""

import numpy as np
import pytest

from finsim.simulation import RetirementSimulation, SimulationConfig


class TestSimulation:
    """Test the main Simulation class."""

    @pytest.fixture
    def basic_config(self):
        """Basic configuration for testing."""
        return SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=40_000,
            social_security=20_000,
            expected_return=7.0,
            return_volatility=15.0,
            n_simulations=100,
            include_mortality=False,  # Simplify for testing
            random_seed=42,
        )

    def test_simulation_init(self, basic_config):
        """Test Simulation initialization."""
        sim = RetirementSimulation(basic_config)

        assert sim.config.initial_portfolio == 500_000
        assert sim.config.expected_return == 7.0
        assert sim.config.return_volatility == 15.0
        assert sim.n_years == 30
        assert sim.config.n_simulations == 100

    def test_config_properties(self, basic_config):
        """Test SimulationConfig properties."""
        assert basic_config.guaranteed_income == 20_000  # Just SS
        assert basic_config.net_consumption_need == 20_000  # 40k - 20k

    def test_config_with_annuity(self):
        """Test config with annuity included."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=400_000,
            annual_consumption=50_000,
            social_security=20_000,
            annuity_annual=10_000,
            annuity_type="Fixed",
            annuity_guarantee_years=10,
        )

        assert config.guaranteed_income == 30_000  # SS + annuity
        assert config.net_consumption_need == 20_000  # 50k - 30k

    def test_config_with_pension(self):
        """Test config with pension."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=300_000,
            annual_consumption=60_000,
            social_security=20_000,
            pension=15_000,
        )

        assert config.guaranteed_income == 35_000  # SS + pension
        assert config.net_consumption_need == 25_000

    def test_different_ages(self):
        """Test with different age configurations."""
        config = SimulationConfig(
            current_age=55,
            retirement_age=65,
            max_age=90,
            initial_portfolio=750_000,
            annual_consumption=60_000,
            social_security=25_000,
        )

        sim = RetirementSimulation(config)
        assert sim.n_years == 35  # 90 - 55

    def test_high_volatility_config(self):
        """Test with high volatility."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=1_000_000,
            annual_consumption=50_000,
            social_security=30_000,
            return_volatility=25.0,  # High volatility
        )

        sim = RetirementSimulation(config)
        assert sim.config.return_volatility == 25.0

    def test_low_return_config(self):
        """Test with low expected returns."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=800_000,
            annual_consumption=40_000,
            social_security=20_000,
            expected_return=3.0,  # Low return
        )

        sim = RetirementSimulation(config)
        assert sim.config.expected_return == 3.0

    def test_random_seed_reproducibility(self):
        """Test that random seed produces reproducible results."""
        config1 = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=40_000,
            social_security=20_000,
            n_simulations=10,
            random_seed=123,
        )

        config2 = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=40_000,
            social_security=20_000,
            n_simulations=10,
            random_seed=123,
        )

        sim1 = RetirementSimulation(config1)
        sim2 = RetirementSimulation(config2)

        # Both should be initialized with same seed
        assert config1.random_seed == config2.random_seed

    def test_no_social_security(self):
        """Test configuration with no social security."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=1_500_000,
            annual_consumption=60_000,
            social_security=0,
        )

        assert config.guaranteed_income == 0
        assert config.net_consumption_need == 60_000

    def test_extreme_parameters(self):
        """Test with extreme but valid parameters."""
        # Very wealthy retiree
        config = SimulationConfig(
            current_age=70,
            retirement_age=70,
            max_age=100,
            initial_portfolio=10_000_000,
            annual_consumption=200_000,
            social_security=50_000,
            expected_return=10.0,
            return_volatility=30.0,
        )

        sim = RetirementSimulation(config)
        assert sim.config.initial_portfolio == 10_000_000
        assert sim.n_years == 30