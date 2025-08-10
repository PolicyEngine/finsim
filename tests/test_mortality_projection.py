"""Tests for advanced mortality projection module."""

import pytest
import numpy as np
from finsim.mortality_projection import (
    MortalityProjector,
    MortalityProjectionParams,
    get_mortality_projector
)


class TestMortalityProjection:
    def test_basic_mortality_rates(self):
        """Test that base mortality rates are reasonable."""
        projector = MortalityProjector()
        
        # Test male mortality at different ages
        male_65 = projector.get_projected_mortality_rate(65, "Male", 2024)
        male_75 = projector.get_projected_mortality_rate(75, "Male", 2024)
        male_85 = projector.get_projected_mortality_rate(85, "Male", 2024)
        
        # Check rates are in expected ranges
        assert 0.015 <= male_65 <= 0.02
        assert 0.035 <= male_75 <= 0.045
        assert 0.09 <= male_85 <= 0.11
        
        # Check rates increase with age
        assert male_75 > male_65
        assert male_85 > male_75
    
    def test_gender_differences(self):
        """Test that female mortality is lower than male."""
        projector = MortalityProjector()
        
        ages = [50, 60, 70, 80, 90]
        for age in ages:
            male_rate = projector.get_projected_mortality_rate(age, "Male", 2024)
            female_rate = projector.get_projected_mortality_rate(age, "Female", 2024)
            assert female_rate <= male_rate, f"Female should have lower mortality at age {age}"
    
    def test_mortality_improvements(self):
        """Test that future mortality is lower due to improvements."""
        projector = MortalityProjector()
        
        # Compare mortality in 2024 vs 2034
        rate_2024 = projector.get_projected_mortality_rate(65, "Male", 2024)
        rate_2034 = projector.get_projected_mortality_rate(65, "Male", 2034)
        
        # Future mortality should be lower
        assert rate_2034 < rate_2024
        
        # Check improvement is roughly 10% over 10 years (1% per year)
        expected_improvement = (1 - 0.01) ** 10
        assert abs(rate_2034 / rate_2024 - expected_improvement) < 0.01
    
    def test_improvement_tapering(self):
        """Test that mortality improvements taper off at old ages."""
        params = MortalityProjectionParams(
            mortality_improvement_rate=0.02,
            max_improvement_age=85
        )
        projector = MortalityProjector(params)
        
        # Young age should get full improvement
        rate_60_2024 = projector.get_projected_mortality_rate(60, "Male", 2024)
        rate_60_2034 = projector.get_projected_mortality_rate(60, "Male", 2034)
        improvement_60 = 1 - rate_60_2034 / rate_60_2024
        
        # Old age should get reduced improvement
        rate_95_2024 = projector.get_projected_mortality_rate(95, "Male", 2024)
        rate_95_2034 = projector.get_projected_mortality_rate(95, "Male", 2034)
        improvement_95 = 1 - rate_95_2034 / rate_95_2024
        
        # Improvement should be less at age 95
        assert improvement_95 < improvement_60
    
    def test_socioeconomic_adjustment(self):
        """Test wealth-based mortality adjustments."""
        # High wealth should have lower mortality
        high_wealth = get_mortality_projector("high")
        average_wealth = get_mortality_projector("average")
        low_wealth = get_mortality_projector("low")
        
        age = 65
        year = 2025
        
        high_rate = high_wealth.get_projected_mortality_rate(age, "Male", year)
        avg_rate = average_wealth.get_projected_mortality_rate(age, "Male", year)
        low_rate = low_wealth.get_projected_mortality_rate(age, "Male", year)
        
        # Check ordering
        assert high_rate < avg_rate < low_rate
        
        # Check multipliers are applied correctly
        assert abs(high_rate / avg_rate - 0.7) < 0.01
        assert abs(low_rate / avg_rate - 1.2) < 0.01
    
    def test_simulate_survival(self):
        """Test Monte Carlo survival simulation."""
        projector = MortalityProjector()
        
        # Simulate 1000 paths for 30 years
        alive = projector.simulate_survival(
            current_age=65,
            gender="Male",
            n_years=30,
            n_simulations=1000
        )
        
        # Check shape
        assert alive.shape == (1000, 31)  # 31 = initial + 30 years
        
        # Everyone starts alive
        assert np.all(alive[:, 0])
        
        # Survival should decrease over time
        survival_rates = alive.mean(axis=0)
        for i in range(1, len(survival_rates)):
            assert survival_rates[i] <= survival_rates[i-1]
        
        # Reasonable survival to age 95 (30 years from 65)
        final_survival = survival_rates[-1]
        assert 0.1 < final_survival < 0.4  # 10-40% survive to 95
    
    def test_life_expectancy(self):
        """Test life expectancy calculations."""
        projector = MortalityProjector()
        
        # Male life expectancy at 65
        le_male_65 = projector.get_life_expectancy(65, "Male")
        assert 15 < le_male_65 < 20  # Typically 17-19 years
        
        # Female life expectancy at 65
        le_female_65 = projector.get_life_expectancy(65, "Female")
        assert 18 < le_female_65 < 23  # Typically 19-21 years
        
        # Female should be higher
        assert le_female_65 > le_male_65
        
        # Life expectancy should decrease with age
        le_male_75 = projector.get_life_expectancy(75, "Male")
        assert le_male_75 < le_male_65 - 10  # Less than 10 years consumed
    
    def test_extreme_ages(self):
        """Test handling of extreme ages."""
        projector = MortalityProjector()
        
        # Very young age
        rate_18 = projector.get_projected_mortality_rate(18, "Male", 2025)
        assert rate_18 < 0.002  # Very low mortality
        
        # Very old age
        rate_110 = projector.get_projected_mortality_rate(110, "Male", 2025)
        assert rate_110 > 0.8  # Very high mortality
        
        # Past max age
        rate_125 = projector.get_projected_mortality_rate(125, "Male", 2025)
        assert rate_125 == 1.0  # Certain death
    
    def test_interpolation(self):
        """Test interpolation for ages not in table."""
        projector = MortalityProjector()
        
        # Age 65 is in table
        rate_65 = projector.get_projected_mortality_rate(65, "Male", 2024)
        
        # Age 66 is in table
        rate_66 = projector.get_projected_mortality_rate(66, "Male", 2024)
        
        # Age 65.5 should be interpolated
        rate_65_5 = projector.get_projected_mortality_rate(65.5, "Male", 2024)
        
        # Should be between the two
        assert rate_65 < rate_65_5 < rate_66
        
        # Should be roughly halfway
        expected = (rate_65 + rate_66) / 2
        assert abs(rate_65_5 - expected) < 0.0001
    
    def test_cohort_effect(self):
        """Test that cohort effects are properly applied."""
        projector = MortalityProjector()
        
        # Someone age 65 in 2025
        person1_rate = projector.get_projected_mortality_rate(75, "Male", 2035)
        
        # Someone age 65 in 2035 (10 years younger cohort)
        person2_rate = projector.get_projected_mortality_rate(65, "Male", 2035)
        
        # The younger cohort at 65 should have lower mortality than
        # the older cohort had at 65
        base_rate_65 = projector.get_projected_mortality_rate(65, "Male", 2025)
        
        assert person2_rate < base_rate_65