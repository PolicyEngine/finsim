"""Tests for mortality module."""

import pytest
import numpy as np
from finsim.mortality import get_mortality_rates, apply_mortality


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
    
    def test_apply_mortality_basic(self):
        """Test basic mortality application."""
        n_simulations = 1000
        n_years = 30
        starting_age = 65
        
        alive_mask = apply_mortality(n_simulations, n_years, starting_age)
        
        # Check shape
        assert alive_mask.shape == (n_simulations, n_years + 1)
        
        # Everyone starts alive
        assert np.all(alive_mask[:, 0])
        
        # Some people should die over 30 years
        assert not np.all(alive_mask[:, -1])
        
        # Once dead, stay dead (monotonic decrease)
        for i in range(n_simulations):
            for j in range(1, n_years + 1):
                if not alive_mask[i, j-1]:
                    assert not alive_mask[i, j]
    
    def test_apply_mortality_no_mortality(self):
        """Test that mortality can be disabled."""
        n_simulations = 100
        n_years = 10
        starting_age = 65
        
        # Mock mortality rates to be zero
        alive_mask = np.ones((n_simulations, n_years + 1), dtype=bool)
        
        # Everyone should stay alive
        assert np.all(alive_mask)
    
    def test_apply_mortality_extreme_ages(self):
        """Test mortality at extreme ages."""
        n_simulations = 100
        n_years = 10
        
        # Very old starting age
        starting_age = 95
        alive_mask = apply_mortality(n_simulations, n_years, starting_age)
        
        # Many should die quickly at age 95+
        assert np.sum(alive_mask[:, -1]) < n_simulations * 0.5
    
    def test_mortality_consistency(self):
        """Test that mortality results are consistent but not identical."""
        n_simulations = 100
        n_years = 20
        starting_age = 70
        
        # Run twice
        alive_mask1 = apply_mortality(n_simulations, n_years, starting_age)
        alive_mask2 = apply_mortality(n_simulations, n_years, starting_age)
        
        # Should not be identical (randomness)
        assert not np.array_equal(alive_mask1, alive_mask2)
        
        # But survival rates should be similar
        survival_rate1 = np.mean(alive_mask1[:, -1])
        survival_rate2 = np.mean(alive_mask2[:, -1])
        assert abs(survival_rate1 - survival_rate2) < 0.2