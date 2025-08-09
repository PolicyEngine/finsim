"""Tests for retirement simulation module."""

import pytest
import numpy as np
from finsim.simulation import RetirementSimulation, SimulationConfig


class TestSimulationConfig:
    """Test the simulation configuration."""
    
    def test_basic_config(self):
        """Test creating a basic simulation config."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=60_000,
            social_security=24_000,
            pension=0
        )
        
        assert config.current_age == 65
        assert config.retirement_age == 65
        assert config.max_age == 95
        assert config.initial_portfolio == 500_000
        assert config.annual_consumption == 60_000
        assert config.social_security == 24_000
        assert config.pension == 0
    
    def test_config_with_annuity(self):
        """Test config with annuity income."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=60_000,
            social_security=24_000,
            pension=0,
            annuity_annual=42_000,
            annuity_type="Life Contingent with Guarantee",
            annuity_guarantee_years=15
        )
        
        assert config.annuity_annual == 42_000
        assert config.annuity_type == "Life Contingent with Guarantee"
        assert config.annuity_guarantee_years == 15
    
    def test_guaranteed_income_calculation(self):
        """Test that guaranteed income is calculated correctly."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=60_000,
            social_security=24_000,
            pension=12_000,
            annuity_annual=30_000
        )
        
        assert config.guaranteed_income == 66_000  # SS + pension + annuity
        assert config.net_consumption_need == -6_000  # consumption - guaranteed


class TestRetirementSimulation:
    """Test the retirement simulation."""
    
    def test_initialization(self):
        """Test simulation initialization."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65, 
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=60_000,
            social_security=24_000
        )
        
        sim = RetirementSimulation(config)
        
        assert sim.config == config
        assert sim.n_years == 30  # 95 - 65
    
    def test_single_simulation_no_failure(self):
        """Test a single simulation path with no portfolio failure."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=70,  # Short horizon for testing
            initial_portfolio=1_000_000,
            annual_consumption=40_000,
            social_security=20_000,
            expected_return=5.0,
            return_volatility=10.0,
            dividend_yield=2.0,
            effective_tax_rate=15.0,
            include_mortality=False
        )
        
        sim = RetirementSimulation(config)
        np.random.seed(42)  # For reproducibility
        
        result = sim.run_single_simulation()
        
        assert len(result.portfolio_values) == 6  # Years 0-5
        assert result.portfolio_values[0] == 1_000_000
        assert result.failure_year is None or result.failure_year > 5
        assert len(result.dividend_income) == 5
        assert len(result.withdrawals) == 5
    
    def test_monte_carlo_simulation(self):
        """Test Monte Carlo simulation with multiple paths."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=75,
            initial_portfolio=500_000,
            annual_consumption=60_000,
            social_security=24_000,
            expected_return=5.0,
            return_volatility=15.0,
            n_simulations=100
        )
        
        sim = RetirementSimulation(config)
        np.random.seed(42)
        
        results = sim.run_monte_carlo()
        
        assert results.n_simulations == 100
        assert results.portfolio_paths.shape == (100, 11)  # 100 sims, 11 years
        assert 0 <= results.success_rate <= 1
        assert len(results.percentiles) == 5  # 10, 25, 50, 75, 90
    
    def test_mortality_integration(self):
        """Test that mortality affects simulations."""
        config = SimulationConfig(
            current_age=85,
            retirement_age=85,
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=60_000,
            social_security=24_000,
            include_mortality=True,
            gender="Male",
            n_simulations=1000
        )
        
        sim = RetirementSimulation(config)
        np.random.seed(42)
        
        results = sim.run_monte_carlo()
        
        # At age 85+, mortality should affect some simulations
        # Check that not all simulations survive to the end
        final_alive = np.sum(results.alive_mask[:, -1])
        assert final_alive < 1000  # Some should have died
    
    def test_annuity_income_fixed_period(self):
        """Test fixed period annuity income."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=75,
            initial_portfolio=100_000,
            annual_consumption=60_000,
            social_security=20_000,
            annuity_annual=30_000,
            annuity_type="Fixed Period",
            annuity_guarantee_years=5,
            include_mortality=False
        )
        
        sim = RetirementSimulation(config)
        result = sim.run_single_simulation()
        
        # Annuity should pay for first 5 years only
        assert all(result.annuity_income[:5] == 30_000)
        assert all(result.annuity_income[5:] == 0)
    
    def test_annuity_income_life_only(self):
        """Test life-only annuity with mortality."""
        config = SimulationConfig(
            current_age=65,
            retirement_age=65,
            max_age=75,
            initial_portfolio=100_000,
            annual_consumption=60_000,
            social_security=20_000,
            annuity_annual=30_000,
            annuity_type="Life Only",
            include_mortality=True,
            gender="Male",
            n_simulations=100
        )
        
        sim = RetirementSimulation(config)
        np.random.seed(42)
        
        results = sim.run_monte_carlo()
        
        # For scenarios where person dies, annuity should stop
        for i in range(100):
            death_year = np.where(~results.alive_mask[i, :])[0]
            if len(death_year) > 0:
                first_death = death_year[0]
                # Annuity should be 0 after death
                if first_death < 10:
                    assert results.annuity_income[i, first_death:].sum() == 0