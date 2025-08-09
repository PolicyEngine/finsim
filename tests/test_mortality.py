"""Tests for mortality module."""

import pytest
import numpy as np
from finsim.mortality import get_mortality_rates, calculate_survival_curve, calculate_life_expectancy


class TestMortality:
    def test_get_mortality_rates(self):
        """Test that mortality rates are loaded correctly."""
        rates = get_mortality_rates()
        
        # Check it's a dictionary
        assert isinstance(rates, dict)
        
        # Check some key ages exist
        assert 65 in rates
        assert 75 in rates
        assert 85 in rates
        
        # Check rates are reasonable (between 0 and 1)
        for age, rate in rates.items():
            assert 0 <= rate <= 1
        
        # Check rates increase with age (generally)
        assert rates[85] > rates[65]
        assert rates[90] > rates[70]
    
    def test_mortality_rates_reasonable(self):
        """Test that mortality rates are in expected ranges."""
        rates = get_mortality_rates()
        
        # Age 65 should have relatively low mortality
        assert 0.01 <= rates[65] <= 0.03
        
        # Age 85 should have higher mortality
        assert 0.05 <= rates[85] <= 0.15
        
        # Age 100+ should have very high mortality
        if 100 in rates:
            assert rates[100] >= 0.2
    
    def test_calculate_survival_curve(self):
        """Test survival curve calculation."""
        # Test for ages 65 to 95
        survival_curve = calculate_survival_curve(65, 95, "Male")
        
        # Check shape
        assert len(survival_curve) == 31  # 65 to 95 inclusive
        
        # Should start at 1.0 (100% survival at start)
        assert survival_curve[0] == 1.0
        
        # Should decrease monotonically
        for i in range(1, len(survival_curve)):
            assert survival_curve[i] <= survival_curve[i-1]
        
        # Should have significant mortality by age 95
        assert survival_curve[-1] < 0.5  # Less than 50% survive to 95
    
    def test_calculate_life_expectancy(self):
        """Test life expectancy calculation."""
        # Life expectancy at 65
        le_65 = calculate_life_expectancy(65, "Male")
        
        # Should be reasonable (typically 15-20 years for 65-year-old male)
        assert 10 < le_65 < 25
        
        # Life expectancy should decrease with age
        le_75 = calculate_life_expectancy(75, "Male")
        assert le_75 < le_65
        
        # Women typically have higher life expectancy
        le_65_female = calculate_life_expectancy(65, "Female")
        assert le_65_female > le_65
    
    def test_gender_differences(self):
        """Test that gender affects mortality rates."""
        rates_male = get_mortality_rates("Male")
        rates_female = get_mortality_rates("Female")
        
        # At most ages, female mortality should be lower
        ages_to_check = [65, 75, 85]
        for age in ages_to_check:
            if age in rates_male and age in rates_female:
                assert rates_female[age] <= rates_male[age]
    
    def test_survival_curve_gender(self):
        """Test survival curves differ by gender."""
        survival_male = calculate_survival_curve(65, 90, "Male")
        survival_female = calculate_survival_curve(65, 90, "Female")
        
        # Female survival should generally be higher
        # Check at age 85 (20 years from 65)
        assert survival_female[20] > survival_male[20]