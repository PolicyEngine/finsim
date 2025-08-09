"""Tests for Tax Calculator."""

import pytest
import numpy as np
from finsim.tax_calculator import TaxCalculator


class TestTaxCalculator:
    """Test suite for TaxCalculator."""
    
    def test_initialization(self):
        """Test calculator initialization."""
        calc = TaxCalculator()
        assert calc.state == "CA"
        assert calc.year == 2025
        
        calc2 = TaxCalculator(state="NY", year=2024)
        assert calc2.state == "NY"
        assert calc2.year == 2024
    
    def test_zero_income_zero_tax(self):
        """Test that zero income results in zero tax."""
        calc = TaxCalculator()
        
        results = calc.calculate_taxes(
            capital_gains=0,
            social_security_benefits=0,
            age=65
        )
        
        assert results['federal_income_tax'] == 0
        assert results['state_income_tax'] == 0
        assert results['total_tax'] == 0
        assert results['effective_tax_rate'] == 0
    
    def test_senior_deductions_apply(self):
        """Test that senior deductions reduce taxable income."""
        calc = TaxCalculator(year=2025)
        
        # Small capital gains that should be covered by deductions
        results = calc.calculate_taxes(
            capital_gains=10_000,
            social_security_benefits=0,
            age=65  # Qualifies for senior deductions
        )
        
        # Standard deduction + senior deduction + OBBBA should shield this
        assert results['federal_income_tax'] == 0
        
        # Compare with younger person
        results_young = calc.calculate_taxes(
            capital_gains=10_000,
            social_security_benefits=0,
            age=40  # No senior deductions
        )
        
        # Young person should have higher taxable income
        assert results_young['taxable_income'] > results['taxable_income']
    
    def test_social_security_taxation_threshold(self):
        """Test Social Security taxation thresholds."""
        calc = TaxCalculator()
        
        # Low income - SS should not be taxable
        results_low = calc.calculate_taxes(
            capital_gains=5_000,
            social_security_benefits=24_000,
            age=65
        )
        
        # High income - SS should be partially taxable
        results_high = calc.calculate_taxes(
            capital_gains=50_000,
            social_security_benefits=24_000,
            age=65
        )
        
        assert results_high['taxable_social_security'] > results_low['taxable_social_security']
        # Up to 85% can be taxable
        assert results_high['taxable_social_security'] <= 24_000 * 0.85
    
    def test_california_no_ss_tax(self):
        """Test that California doesn't tax Social Security."""
        calc = TaxCalculator(state="CA")
        
        results = calc.calculate_taxes(
            capital_gains=0,
            social_security_benefits=50_000,
            age=65
        )
        
        # CA doesn't tax SS, so state tax should be 0
        # (assuming no other income)
        assert results['state_income_tax'] == 0
    
    def test_withdrawal_to_match_after_tax(self):
        """Test calculation of gross withdrawal for target after-tax."""
        calc = TaxCalculator()
        
        target = 50_000  # Want $50k after tax
        
        gross, tax_details = calc.calculate_withdrawal_to_match_after_tax(
            target_after_tax=target,
            social_security_benefits=24_000,
            age=65,
            taxable_fraction=0.2  # 20% is capital gains
        )
        
        # Gross should be more than target
        assert gross > target
        
        # After-tax should be close to target
        after_tax = gross - tax_details['total_tax']
        assert abs(after_tax - target) < 2  # Within $2 tolerance
    
    def test_higher_taxable_fraction_needs_more_withdrawal(self):
        """Test that higher taxable fraction requires larger withdrawal."""
        calc = TaxCalculator()
        
        target = 50_000
        
        gross_low, _ = calc.calculate_withdrawal_to_match_after_tax(
            target_after_tax=target,
            social_security_benefits=24_000,
            age=65,
            taxable_fraction=0.1  # 10% taxable
        )
        
        gross_high, _ = calc.calculate_withdrawal_to_match_after_tax(
            target_after_tax=target,
            social_security_benefits=24_000,
            age=65,
            taxable_fraction=0.5  # 50% taxable
        )
        
        # Higher taxable fraction should require more gross withdrawal
        assert gross_high > gross_low
    
    def test_social_security_cola_projection(self):
        """Test Social Security COLA projections."""
        calc = TaxCalculator()
        
        initial = 24_000
        projections = calc.project_social_security_with_cola(
            initial_benefit=initial,
            n_years=10,
            cola_rate=0.03  # 3% COLA
        )
        
        assert len(projections) == 10
        assert projections[0] == initial
        # Should grow by 3% per year
        assert abs(projections[1] - initial * 1.03) < 0.01
        assert abs(projections[9] - initial * (1.03 ** 9)) < 0.01
    
    def test_effective_tax_rate_calculation(self):
        """Test effective tax rate calculation."""
        calc = TaxCalculator()
        
        results = calc.calculate_taxes(
            capital_gains=100_000,
            social_security_benefits=24_000,
            age=65
        )
        
        total_income = 100_000 + 24_000
        expected_rate = results['total_tax'] / total_income
        
        assert abs(results['effective_tax_rate'] - expected_rate) < 0.001
        # Rate should be reasonable (not over 50%)
        assert 0 <= results['effective_tax_rate'] < 0.5