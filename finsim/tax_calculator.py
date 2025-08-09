"""Tax calculation using PolicyEngine-US."""

import numpy as np
from policyengine_us import Simulation
from typing import Dict, Optional, Tuple


class TaxCalculator:
    """Calculate taxes using PolicyEngine-US."""
    
    def __init__(
        self,
        state: str = "CA",
        year: int = 2025
    ):
        """
        Initialize tax calculator.
        
        Args:
            state: Two-letter state code
            year: Tax year
        """
        self.state = state
        self.year = year
        
    def calculate_taxes(
        self,
        capital_gains: float,
        social_security_benefits: float,
        age: int,
        filing_status: str = "SINGLE",
        other_income: float = 0,
        state_and_local_tax_deduction: float = 0
    ) -> Dict[str, float]:
        """
        Calculate federal and state taxes.
        
        Args:
            capital_gains: Long-term capital gains income
            social_security_benefits: Annual Social Security benefits
            age: Taxpayer age
            filing_status: Filing status (SINGLE, JOINT, etc.)
            other_income: Other taxable income
            state_and_local_tax_deduction: SALT deduction amount
            
        Returns:
            Dictionary with tax calculations
        """
        # Create simulation
        situation = {
            "people": {
                "person": {
                    "age": {str(self.year): age},
                    "employment_income": {str(self.year): 0},
                    "long_term_capital_gains": {str(self.year): capital_gains},
                    "social_security": {str(self.year): social_security_benefits},
                    "social_security_retirement": {str(self.year): social_security_benefits},
                    "interest_income": {str(self.year): other_income}
                }
            },
            "families": {
                "family": {
                    "members": ["person"]
                }
            },
            "tax_units": {
                "tax_unit": {
                    "members": ["person"],
                    "filing_status": {str(self.year): filing_status},
                    "state_and_local_tax_before_refund": {str(self.year): state_and_local_tax_deduction}
                }
            },
            "spm_units": {
                "spm_unit": {
                    "members": ["person"]
                }
            },
            "households": {
                "household": {
                    "members": ["person"],
                    "state_name": {str(self.year): self.state}
                }
            }
        }
        
        # Run simulation
        sim = Simulation(situation=situation)
        
        # Calculate various tax components
        results = {
            'federal_income_tax': float(sim.calculate("income_tax", str(self.year))[0]),
            'state_income_tax': float(sim.calculate("state_income_tax", str(self.year))[0]),
            'taxable_social_security': float(sim.calculate("taxable_social_security", str(self.year))[0]),
            'adjusted_gross_income': float(sim.calculate("adjusted_gross_income", str(self.year))[0]),
            'taxable_income': float(sim.calculate("taxable_income", str(self.year))[0]),
            'standard_deduction': float(sim.calculate("standard_deduction", str(self.year))[0]),
            'net_income': float(sim.calculate("household_net_income", str(self.year))[0])
        }
        
        # Calculate total tax
        results['total_tax'] = results['federal_income_tax'] + results['state_income_tax']
        
        # Calculate effective tax rate
        total_income = capital_gains + social_security_benefits + other_income
        if total_income > 0:
            results['effective_tax_rate'] = results['total_tax'] / total_income
        else:
            results['effective_tax_rate'] = 0
        
        return results
    
    def calculate_withdrawal_to_match_after_tax(
        self,
        target_after_tax: float,
        social_security_benefits: float,
        age: int,
        taxable_fraction: float = 0.2,
        max_iterations: int = 20,
        tolerance: float = 1.0
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate gross withdrawal needed to achieve target after-tax income.
        
        Uses iterative approach to find the withdrawal amount that,
        after taxes, provides the desired spending amount.
        
        Args:
            target_after_tax: Desired after-tax income
            social_security_benefits: Annual Social Security benefits
            age: Taxpayer age
            taxable_fraction: Fraction of withdrawal that is taxable gain
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance in dollars
            
        Returns:
            Tuple of (gross_withdrawal, tax_details)
        """
        # Initial guess: assume 15% effective tax rate on gains
        gross_withdrawal = target_after_tax / (1 - 0.15 * taxable_fraction)
        
        for _ in range(max_iterations):
            # Calculate taxable portion
            capital_gains = gross_withdrawal * taxable_fraction
            
            # Calculate taxes
            tax_results = self.calculate_taxes(
                capital_gains=capital_gains,
                social_security_benefits=social_security_benefits,
                age=age
            )
            
            # Calculate after-tax income
            after_tax = gross_withdrawal - tax_results['total_tax']
            
            # Check convergence
            if abs(after_tax - target_after_tax) < tolerance:
                break
            
            # Adjust withdrawal
            adjustment = (target_after_tax - after_tax)
            gross_withdrawal += adjustment
            
            # Ensure positive withdrawal
            gross_withdrawal = max(0, gross_withdrawal)
        
        return gross_withdrawal, tax_results
    
    def project_social_security_with_cola(
        self,
        initial_benefit: float,
        n_years: int,
        cola_rate: float = 0.032
    ) -> np.ndarray:
        """
        Project Social Security benefits with COLA adjustments.
        
        Args:
            initial_benefit: Starting annual benefit
            n_years: Number of years to project
            cola_rate: Annual COLA rate (default 3.2% based on SSA uprating)
            
        Returns:
            Array of projected annual benefits
        """
        years = np.arange(n_years)
        return initial_benefit * (1 + cola_rate) ** years