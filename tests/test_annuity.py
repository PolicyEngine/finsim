"""Tests for annuity module."""

import pytest
import numpy as np
from finsim.annuity import (
    calculate_annuity_payout,
    calculate_present_value,
    compare_annuity_investment
)


class TestAnnuity:
    def test_calculate_annuity_payout(self):
        """Test annuity payout calculation."""
        # $100,000 purchase price, 5% rate, 20 years
        payout = calculate_annuity_payout(
            purchase_price=100_000,
            interest_rate=0.05,
            years=20
        )
        
        # Should be around $8,024 per year
        assert 7_500 < payout < 8_500
        
        # Test that higher rates give higher payouts
        payout_high = calculate_annuity_payout(100_000, 0.07, 20)
        assert payout_high > payout
        
        # Test that longer periods give lower payouts
        payout_long = calculate_annuity_payout(100_000, 0.05, 30)
        assert payout_long < payout
    
    def test_calculate_annuity_payout_edge_cases(self):
        """Test edge cases for annuity payout."""
        # Zero purchase price
        payout = calculate_annuity_payout(0, 0.05, 20)
        assert payout == 0
        
        # Very short period
        payout = calculate_annuity_payout(100_000, 0.05, 1)
        assert payout > 100_000  # Should be principal + interest
        
        # Zero interest rate
        payout = calculate_annuity_payout(100_000, 0, 10)
        assert payout == 10_000  # Should be simple division
    
    def test_calculate_present_value(self):
        """Test present value calculation."""
        # $10,000 per year for 10 years at 5%
        pv = calculate_present_value(
            cash_flow=10_000,
            interest_rate=0.05,
            years=10
        )
        
        # Should be around $77,217
        assert 75_000 < pv < 80_000
        
        # Higher discount rate should give lower PV
        pv_high_rate = calculate_present_value(10_000, 0.10, 10)
        assert pv_high_rate < pv
        
        # Longer period should give higher PV (more cash flows)
        pv_long = calculate_present_value(10_000, 0.05, 20)
        assert pv_long > pv
    
    def test_calculate_present_value_edge_cases(self):
        """Test edge cases for present value."""
        # Zero cash flow
        pv = calculate_present_value(0, 0.05, 10)
        assert pv == 0
        
        # Zero interest rate
        pv = calculate_present_value(10_000, 0, 10)
        assert pv == 100_000  # Simple multiplication
        
        # Single period
        pv = calculate_present_value(10_000, 0.05, 1)
        assert abs(pv - 10_000 / 1.05) < 0.01
    
    def test_compare_annuity_investment_basic(self):
        """Test basic annuity vs investment comparison."""
        results = compare_annuity_investment(
            initial_amount=100_000,
            annuity_rate=0.05,
            investment_return=0.07,
            investment_volatility=0.15,
            years=20,
            n_simulations=100
        )
        
        # Check structure
        assert 'annuity_total' in results
        assert 'investment_mean' in results
        assert 'investment_median' in results
        assert 'investment_percentiles' in results
        assert 'probability_annuity_wins' in results
        
        # Annuity total should be deterministic
        expected_annuity = results['annuity_payout'] * 20
        assert abs(results['annuity_total'] - expected_annuity) < 1
        
        # Investment should have reasonable distribution
        assert results['investment_mean'] > 0
        assert results['investment_median'] > 0
        assert len(results['investment_percentiles']) == 3
    
    def test_compare_annuity_investment_probabilities(self):
        """Test probability calculations in comparison."""
        # High investment return should favor investment
        results_high_return = compare_annuity_investment(
            initial_amount=100_000,
            annuity_rate=0.04,
            investment_return=0.10,  # Much higher than annuity
            investment_volatility=0.10,
            years=20,
            n_simulations=500
        )
        
        # Investment should usually win
        assert results_high_return['probability_annuity_wins'] < 0.3
        
        # Low investment return should favor annuity
        results_low_return = compare_annuity_investment(
            initial_amount=100_000,
            annuity_rate=0.06,
            investment_return=0.03,  # Much lower than annuity
            investment_volatility=0.20,
            years=20,
            n_simulations=500
        )
        
        # Annuity should usually win
        assert results_low_return['probability_annuity_wins'] > 0.7
    
    def test_compare_with_consumption(self):
        """Test comparison with consumption included."""
        results = compare_annuity_investment(
            initial_amount=100_000,
            annuity_rate=0.05,
            investment_return=0.07,
            investment_volatility=0.15,
            years=20,
            n_simulations=100,
            annual_consumption=5_000  # Consume $5k per year
        )
        
        # Both should be lower with consumption
        no_consumption = compare_annuity_investment(
            initial_amount=100_000,
            annuity_rate=0.05,
            investment_return=0.07,
            investment_volatility=0.15,
            years=20,
            n_simulations=100,
            annual_consumption=0
        )
        
        assert results['annuity_total'] < no_consumption['annuity_total']
        assert results['investment_mean'] < no_consumption['investment_mean']
    
    def test_life_contingent_annuity(self):
        """Test life-contingent annuity features."""
        # This would test mortality-adjusted annuities
        # For now, just test that the structure supports it
        results = compare_annuity_investment(
            initial_amount=100_000,
            annuity_rate=0.05,
            investment_return=0.07,
            investment_volatility=0.15,
            years=20,
            n_simulations=100,
            include_mortality=True,
            starting_age=65
        )
        
        # Should still return valid results
        assert 'annuity_total' in results
        assert 'investment_mean' in results
    
    def test_guaranteed_period_annuity(self):
        """Test annuity with guaranteed period."""
        # Would test that annuity pays even if person dies during guarantee
        # This is more of an integration test with portfolio_simulation
        pass  # Placeholder for future implementation
    
    def test_inflation_adjustment(self):
        """Test inflation-adjusted annuities."""
        # Test with inflation adjustment
        results_with_inflation = compare_annuity_investment(
            initial_amount=100_000,
            annuity_rate=0.05,
            investment_return=0.07,
            investment_volatility=0.15,
            years=20,
            n_simulations=100,
            inflation_rate=0.02
        )
        
        results_no_inflation = compare_annuity_investment(
            initial_amount=100_000,
            annuity_rate=0.05,
            investment_return=0.07,
            investment_volatility=0.15,
            years=20,
            n_simulations=100,
            inflation_rate=0
        )
        
        # Real returns should be lower with inflation
        if 'real_annuity_total' in results_with_inflation:
            assert (results_with_inflation['real_annuity_total'] < 
                   results_no_inflation['annuity_total'])