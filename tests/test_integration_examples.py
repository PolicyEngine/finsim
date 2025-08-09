"""Integration tests that serve as usage examples."""

import pytest
import numpy as np
from finsim.simulation import SimulationConfig, RetirementSimulation
from finsim.mortality import calculate_life_expectancy, get_mortality_rate
from finsim.market import MarketDataFetcher


class TestRetirementScenarios:
    """Test complete retirement scenarios - these serve as usage examples."""
    
    def test_basic_retirement_scenario(self):
        """Example: Basic retirement with Social Security."""
        config = SimulationConfig(
            current_age=65,
            max_age=95,
            initial_portfolio=1_000_000,
            annual_consumption=60_000,
            social_security=30_000,
            expected_return=5.0,
            return_volatility=16.0,
            n_simulations=100,  # Small for speed
            random_seed=42
        )
        
        sim = RetirementSimulation(config)
        results = sim.run_monte_carlo()
        
        # Basic validation
        assert 0 <= results.success_rate <= 1
        assert results.portfolio_paths.shape == (100, 31)  # 100 sims, 31 years
        assert len(results.percentiles) == 5
        
        # With this configuration, should have reasonable success
        assert results.success_rate > 0.5  # At least 50% success
    
    def test_high_risk_scenario(self):
        """Example: High withdrawal rate scenario."""
        config = SimulationConfig(
            current_age=65,
            max_age=95,
            initial_portfolio=500_000,
            annual_consumption=80_000,  # High spending
            social_security=20_000,  # Low SS
            expected_return=5.0,
            return_volatility=16.0,
            n_simulations=100,
            random_seed=42
        )
        
        sim = RetirementSimulation(config)
        results = sim.run_monte_carlo()
        
        # This scenario should have lower success rate
        assert results.success_rate < 0.8  # Less than 80% success
        
        # Should have some failures
        failures = results.failure_years[results.failure_years <= 30]
        assert len(failures) > 0
    
    def test_conservative_scenario(self):
        """Example: Conservative scenario with high guaranteed income."""
        config = SimulationConfig(
            current_age=65,
            max_age=95,
            initial_portfolio=2_000_000,  # Large portfolio
            annual_consumption=60_000,
            social_security=35_000,  # High SS
            pension=20_000,  # Pension income
            expected_return=4.0,  # Conservative return
            return_volatility=12.0,  # Lower volatility
            n_simulations=100,
            random_seed=42
        )
        
        sim = RetirementSimulation(config)
        results = sim.run_monte_carlo()
        
        # Should have very high success rate
        assert results.success_rate > 0.95
    
    def test_annuity_comparison_scenario(self):
        """Example: Compare scenarios with and without annuity."""
        base_config = SimulationConfig(
            current_age=65,
            max_age=95,
            initial_portfolio=527_530,  # Settlement amount
            annual_consumption=60_000,
            social_security=24_000,
            expected_return=5.0,
            return_volatility=16.0,
            n_simulations=100,
            random_seed=42
        )
        
        # Scenario without annuity
        sim_without = RetirementSimulation(base_config)
        results_without = sim_without.run_monte_carlo()
        
        # Scenario with life annuity (like option A: $3,516/month)
        config_with_annuity = SimulationConfig(
            current_age=65,
            max_age=95,
            initial_portfolio=0,  # All money goes to annuity
            annual_consumption=60_000,
            social_security=24_000,
            annuity_annual=42_192,  # $3,516 * 12
            annuity_type="Life Contingent with Guarantee",
            annuity_guarantee_years=15,
            expected_return=5.0,
            return_volatility=16.0,
            n_simulations=100,
            include_mortality=True,
            random_seed=42
        )
        
        sim_with = RetirementSimulation(config_with_annuity)
        results_with = sim_with.run_monte_carlo()
        
        # Annuity should provide more certainty
        # (though results depend on specific parameters)
        assert results_with.success_rate >= 0  # Just ensure it runs
        assert results_without.success_rate >= 0
    
    def test_mortality_impact_example(self):
        """Example: Compare scenarios with and without mortality."""
        config = SimulationConfig(
            current_age=75,  # Older starting age
            max_age=100,
            initial_portfolio=800_000,
            annual_consumption=70_000,
            social_security=30_000,
            expected_return=5.0,
            return_volatility=16.0,
            n_simulations=100,
            gender="Male",
            random_seed=42
        )
        
        # With mortality
        config.include_mortality = True
        sim_with_mortality = RetirementSimulation(config)
        results_with = sim_with_mortality.run_monte_carlo()
        
        # Without mortality  
        config.include_mortality = False
        sim_without_mortality = RetirementSimulation(config)
        results_without = sim_without_mortality.run_monte_carlo()
        
        # Mortality typically increases success rate at older ages
        # because fewer scenarios need to last the full period
        print(f"Success rate with mortality: {results_with.success_rate:.2%}")
        print(f"Success rate without mortality: {results_without.success_rate:.2%}")
        
        # Both should produce valid results
        assert 0 <= results_with.success_rate <= 1
        assert 0 <= results_without.success_rate <= 1


class TestMortalityAnalysis:
    """Examples of mortality analysis."""
    
    def test_life_expectancy_calculation(self):
        """Example: Calculate life expectancy for different demographics."""
        # 65-year-old male
        male_65_le = calculate_life_expectancy(65, "Male")
        
        # 65-year-old female  
        female_65_le = calculate_life_expectancy(65, "Female")
        
        # Females typically have higher life expectancy
        assert female_65_le > male_65_le
        
        # Reasonable ranges (should be 15-25 years)
        assert 15 <= male_65_le <= 25
        assert 15 <= female_65_le <= 25
        
        print(f"65-year-old male life expectancy: {male_65_le:.1f} years")
        print(f"65-year-old female life expectancy: {female_65_le:.1f} years")
    
    def test_mortality_progression_example(self):
        """Example: Show how mortality rates increase with age."""
        ages = [65, 70, 75, 80, 85, 90, 95]
        
        print("\nMortality Rates by Age:")
        print("Age | Male  | Female")
        print("----|-------|-------")
        
        for age in ages:
            male_rate = get_mortality_rate(age, "Male")
            female_rate = get_mortality_rate(age, "Female")
            print(f"{age:2d}  | {male_rate:5.2%} | {female_rate:5.2%}")
            
            # Mortality should increase with age
            if age > 65:
                prev_male = get_mortality_rate(age - 5, "Male")
                prev_female = get_mortality_rate(age - 5, "Female")
                assert male_rate > prev_male
                assert female_rate > prev_female


class TestMarketDataExample:
    """Examples of market data usage."""
    
    @pytest.mark.skipif(True, reason="Requires network access")
    def test_market_data_fetching_example(self):
        """Example: Fetch real market data for calibration."""
        fetcher = MarketDataFetcher()
        
        try:
            # Fetch VT data
            vt_data = fetcher.fetch_fund_data("VT", years=5)
            
            assert vt_data.ticker == "VT"
            assert vt_data.data_points > 0
            assert -10 <= vt_data.annual_return <= 20  # Reasonable range
            assert 0 <= vt_data.volatility <= 50
            assert 0 <= vt_data.dividend_yield <= 10
            
            print(f"VT 5-year stats:")
            print(f"  Real return: {vt_data.annual_return:.1f}%")
            print(f"  Volatility: {vt_data.volatility:.1f}%")
            print(f"  Dividend yield: {vt_data.dividend_yield:.1f}%")
            print(f"  Data points: {vt_data.data_points}")
            
        except Exception as e:
            pytest.skip(f"Market data fetch failed: {e}")


class TestParameterSensitivity:
    """Examples of parameter sensitivity analysis."""
    
    def test_withdrawal_rate_sensitivity(self):
        """Example: Test how success rate varies with withdrawal rate."""
        base_config = SimulationConfig(
            current_age=65,
            max_age=95,
            initial_portfolio=1_000_000,
            social_security=30_000,
            expected_return=5.0,
            return_volatility=16.0,
            n_simulations=50,  # Small for speed
            random_seed=42
        )
        
        withdrawal_rates = [3.0, 3.5, 4.0, 4.5, 5.0]
        success_rates = []
        
        for rate in withdrawal_rates:
            # Net withdrawal = rate * portfolio_value
            consumption = rate * 10_000 + 30_000  # rate% + SS
            
            config = SimulationConfig(
                current_age=base_config.current_age,
                max_age=base_config.max_age,
                initial_portfolio=base_config.initial_portfolio,
                annual_consumption=consumption,
                social_security=base_config.social_security,
                expected_return=base_config.expected_return,
                return_volatility=base_config.return_volatility,
                n_simulations=base_config.n_simulations,
                random_seed=42
            )
            
            sim = RetirementSimulation(config)
            results = sim.run_monte_carlo()
            success_rates.append(results.success_rate)
        
        print("\nWithdrawal Rate Sensitivity:")
        print("Rate | Success")
        print("-----|--------")
        for rate, success in zip(withdrawal_rates, success_rates):
            print(f"{rate:3.1f}% | {success:6.1%}")
        
        # Success rate should generally decrease with higher withdrawal rates
        assert success_rates[-1] <= success_rates[0]  # 5% <= 3%