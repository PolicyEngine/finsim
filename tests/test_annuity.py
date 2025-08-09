"""Tests for Annuity Calculator."""

import pytest
import numpy as np
import pandas as pd
from finsim.annuity import AnnuityCalculator


class TestAnnuityCalculator:
    """Test suite for AnnuityCalculator."""
    
    def test_initialization(self):
        """Test calculator initialization."""
        calc = AnnuityCalculator()
        assert calc.age == 65
        assert calc.gender == "male"
        
        calc2 = AnnuityCalculator(age=70, gender="female")
        assert calc2.age == 70
        assert calc2.gender == "female"
    
    def test_simple_fixed_annuity_irr(self):
        """Test IRR calculation for fixed-term annuity."""
        calc = AnnuityCalculator()
        
        # Simple case: $100k premium, $1k/month for 10 years
        irr = calc.calculate_irr(
            premium=100_000,
            monthly_payment=1_000,
            guarantee_months=120,
            life_contingent=False
        )
        
        # Total payout is $120k vs $100k premium over 10 years
        # IRR should be positive but modest
        assert 0.01 < irr < 0.05
        
        # Verify with manual calculation
        total_payout = 1_000 * 120
        simple_return = (total_payout / 100_000) ** (1/10) - 1
        assert abs(irr - simple_return) < 0.02  # Should be close
    
    def test_zero_return_annuity(self):
        """Test annuity that returns exactly the premium."""
        calc = AnnuityCalculator()
        
        # $120k premium, $1k/month for 10 years = $120k total
        irr = calc.calculate_irr(
            premium=120_000,
            monthly_payment=1_000,
            guarantee_months=120,
            life_contingent=False
        )
        
        # Should be approximately 0% return
        assert abs(irr) < 0.001
    
    def test_life_contingent_higher_irr(self):
        """Test that life-contingent annuity has different IRR than fixed."""
        calc = AnnuityCalculator(age=65)
        
        premium = 500_000
        monthly = 3_500
        guarantee = 180  # 15 years
        
        irr_fixed = calc.calculate_irr(
            premium=premium,
            monthly_payment=monthly,
            guarantee_months=guarantee,
            life_contingent=False
        )
        
        irr_life = calc.calculate_irr(
            premium=premium,
            monthly_payment=monthly,
            guarantee_months=guarantee,
            life_contingent=True
        )
        
        # Life contingent should have higher expected IRR
        # (payments continue beyond guarantee period)
        assert irr_life > irr_fixed
    
    def test_compare_annuity_options(self):
        """Test comparison of multiple annuity proposals."""
        calc = AnnuityCalculator(age=65)
        
        proposals = [
            {
                'name': 'Option A',
                'premium': 500_000,
                'monthly_payment': 3_000,
                'guarantee_months': 180,
                'life_contingent': True,
                'taxable': False
            },
            {
                'name': 'Option B',
                'premium': 500_000,
                'monthly_payment': 4_000,
                'guarantee_months': 150,
                'life_contingent': False,
                'taxable': False
            }
        ]
        
        df = calc.compare_annuity_options(proposals)
        
        # Check DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'IRR' in df.columns
        assert 'Total Guaranteed' in df.columns
        assert 'Annual Payment' in df.columns
        
        # Option B should have higher guaranteed total
        assert df.loc[df['Name'] == 'Option B', 'Total Guaranteed'].values[0] > \
               df.loc[df['Name'] == 'Option A', 'Total Guaranteed'].values[0]
    
    def test_present_value_calculation(self):
        """Test present value calculation."""
        calc = AnnuityCalculator()
        
        # $1000/month for 10 years at 5% discount rate
        pv = calc.calculate_present_value(
            monthly_payment=1_000,
            months=120,
            discount_rate=0.05
        )
        
        # PV should be less than total payments
        total_payments = 1_000 * 120
        assert pv < total_payments
        
        # With 0% discount rate, PV equals total
        pv_zero = calc.calculate_present_value(
            monthly_payment=1_000,
            months=120,
            discount_rate=0.0
        )
        assert abs(pv_zero - total_payments) < 0.01
    
    def test_mortality_table_lookup(self):
        """Test mortality table data access."""
        calc = AnnuityCalculator(age=65)
        
        # Should have life expectancy data
        assert 65 in calc.MALE_LIFE_TABLE
        life_exp = calc.MALE_LIFE_TABLE[65]
        
        # 65-year-old male life expectancy should be around 17-18 years
        assert 15 < life_exp < 20
        
        # Older ages should have lower life expectancy
        assert calc.MALE_LIFE_TABLE[80] < calc.MALE_LIFE_TABLE[65]
    
    def test_high_return_annuity(self):
        """Test high-return annuity calculation."""
        calc = AnnuityCalculator()
        
        # Very favorable terms: low premium, high payout
        irr = calc.calculate_irr(
            premium=100_000,
            monthly_payment=2_000,
            guarantee_months=120,
            life_contingent=False
        )
        
        # $240k total vs $100k = should be high IRR
        assert irr > 0.07  # Should be over 7%
    
    def test_negative_return_protection(self):
        """Test that calculator handles negative return scenarios."""
        calc = AnnuityCalculator()
        
        # Poor annuity: high premium, low payout
        irr = calc.calculate_irr(
            premium=200_000,
            monthly_payment=500,
            guarantee_months=120,
            life_contingent=False
        )
        
        # Total payout $60k vs $200k premium
        assert irr < 0  # Should be negative return