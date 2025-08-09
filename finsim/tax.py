"""Vectorized tax calculations using PolicyEngine-US microdata."""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from policyengine_us import Microsimulation
from policyengine_core.data import Dataset
import h5py
import tempfile
from pathlib import Path


class MonteCarloDataset(Dataset):
    """
    Custom dataset for Monte Carlo simulations.
    Each simulation path becomes a separate household.
    """
    
    name = "monte_carlo_dataset"
    label = "Monte Carlo simulation dataset"
    data_format = Dataset.TIME_PERIOD_ARRAYS
    
    def __init__(
        self,
        n_scenarios: int,
        capital_gains_array: np.ndarray,
        social_security_array: np.ndarray,
        ages: np.ndarray,
        state: str = "CA",
        year: int = 2025,
        filing_status: str = "SINGLE"
    ):
        """
        Initialize Monte Carlo dataset.
        
        Args:
            n_scenarios: Number of Monte Carlo scenarios
            capital_gains_array: Array of capital gains for each scenario
            social_security_array: Array of SS benefits for each scenario
            ages: Array of ages for each scenario
            state: State code
            year: Tax year
            filing_status: Filing status
        """
        self.n_scenarios = n_scenarios
        self.capital_gains = capital_gains_array
        self.social_security = social_security_array
        self.ages = ages
        self.state = state
        self.year = year
        self.filing_status = filing_status
        
        # Use temporary file for dataset
        self.tmp_file = tempfile.NamedTemporaryFile(suffix='.h5', delete=False)
        self.file_path = Path(self.tmp_file.name)
        
        super().__init__()
        
    def generate(self) -> None:
        """Generate the dataset with all Monte Carlo scenarios."""
        
        # Create entity IDs
        person_ids = np.arange(self.n_scenarios)
        household_ids = np.arange(self.n_scenarios)
        tax_unit_ids = np.arange(self.n_scenarios)
        family_ids = np.arange(self.n_scenarios)
        spm_unit_ids = np.arange(self.n_scenarios)
        marital_unit_ids = np.arange(self.n_scenarios)
        
        # Create weights (all equal for Monte Carlo)
        weights = np.ones(self.n_scenarios)
        
        # Map filing status to enum value
        filing_status_map = {
            "SINGLE": 1,
            "JOINT": 2,
            "SEPARATE": 3,
            "HEAD_OF_HOUSEHOLD": 4,
            "WIDOW": 5
        }
        filing_status_values = np.full(
            self.n_scenarios, 
            filing_status_map.get(self.filing_status, 1)
        )
        
        # State FIPS code mapping (simplified - add more as needed)
        state_fips_map = {
            "CA": 6, "NY": 36, "TX": 48, "FL": 12, 
            "IL": 17, "PA": 42, "OH": 39, "MI": 26
        }
        state_code = state_fips_map.get(self.state, 6)
        
        # Build the dataset dictionary
        # All variables use year time period for consistency
        data = {
            # Person variables
            "person_id": {self.year: person_ids},
            "person_household_id": {self.year: household_ids},  # Membership arrays also use year
            "person_tax_unit_id": {self.year: tax_unit_ids},
            "person_family_id": {self.year: family_ids},
            "person_spm_unit_id": {self.year: spm_unit_ids},
            "person_marital_unit_id": {self.year: marital_unit_ids},
            "person_weight": {self.year: weights},
            "age": {self.year: self.ages},
            
            # Income variables
            "long_term_capital_gains": {self.year: self.capital_gains},
            "social_security": {self.year: self.social_security},
            "social_security_retirement": {self.year: self.social_security},
            
            # Set other income to zero
            "employment_income": {self.year: np.zeros(self.n_scenarios)},
            "interest_income": {self.year: np.zeros(self.n_scenarios)},
            "dividend_income": {self.year: np.zeros(self.n_scenarios)},
            
            # Household variables
            "household_id": {self.year: household_ids},
            "household_weight": {self.year: weights},
            "household_state_fips": {self.year: np.full(self.n_scenarios, state_code)},
            
            # Tax unit variables
            "tax_unit_id": {self.year: tax_unit_ids},
            "tax_unit_weight": {self.year: weights},
            "filing_status": {self.year: filing_status_values},
            
            # Family variables
            "family_id": {self.year: family_ids},
            "family_weight": {self.year: weights},
            
            # SPM unit variables
            "spm_unit_id": {self.year: spm_unit_ids},
            "spm_unit_weight": {self.year: weights},
            
            # Marital unit variables
            "marital_unit_id": {self.year: marital_unit_ids},
            "marital_unit_weight": {self.year: weights},
        }
        
        # Save the dataset
        self.save_dataset(data)
    
    def cleanup(self) -> None:
        """Clean up temporary file."""
        if hasattr(self, 'tmp_file'):
            try:
                self.file_path.unlink()
            except:
                pass


class TaxCalculator:
    """
    Calculate taxes for multiple Monte Carlo scenarios simultaneously.
    """
    
    def __init__(
        self,
        state: str = "CA",
        year: int = 2025
    ):
        """
        Initialize vectorized tax calculator.
        
        Args:
            state: Two-letter state code
            year: Tax year
        """
        self.state = state
        self.year = year
    
    def calculate_batch_taxes(
        self,
        capital_gains_array: np.ndarray,
        social_security_array: np.ndarray,
        ages: np.ndarray,
        filing_status: str = "SINGLE"
    ) -> Dict[str, np.ndarray]:
        """
        Calculate taxes for a batch of scenarios.
        
        Args:
            capital_gains_array: Capital gains for each scenario
            social_security_array: Social Security benefits for each scenario
            ages: Ages for each scenario
            filing_status: Filing status (same for all scenarios)
            
        Returns:
            Dictionary with tax arrays for each component
        """
        n_scenarios = len(capital_gains_array)
        
        # Create custom dataset
        dataset = MonteCarloDataset(
            n_scenarios=n_scenarios,
            capital_gains_array=capital_gains_array,
            social_security_array=social_security_array,
            ages=ages,
            state=self.state,
            year=self.year,
            filing_status=filing_status
        )
        
        try:
            # Generate the dataset
            dataset.generate()
            
            # Create microsimulation
            sim = Microsimulation(dataset=dataset)
            
            # Calculate all tax components at once
            results = {
                'federal_income_tax': sim.calculate("income_tax", self.year).values,
                'state_income_tax': sim.calculate("state_income_tax", self.year).values,
                'taxable_social_security': sim.calculate("taxable_social_security", self.year).values,
                'adjusted_gross_income': sim.calculate("adjusted_gross_income", self.year).values,
                'taxable_income': sim.calculate("taxable_income", self.year).values,
                'standard_deduction': sim.calculate("standard_deduction", self.year).values,
                'household_net_income': sim.calculate("household_net_income", self.year).values,
            }
            
            # Calculate total tax and effective rate
            results['total_tax'] = results['federal_income_tax'] + results['state_income_tax']
            
            total_income = capital_gains_array + social_security_array
            results['effective_tax_rate'] = np.where(
                total_income > 0,
                results['total_tax'] / total_income,
                0
            )
            
            return results
            
        finally:
            # Clean up temporary dataset
            dataset.cleanup()
    
    def calculate_withdrawal_taxes_vectorized(
        self,
        withdrawal_matrix: np.ndarray,
        taxable_fraction_matrix: np.ndarray,
        social_security_array: np.ndarray,
        ages: np.ndarray,
        filing_status: str = "SINGLE"
    ) -> Dict[str, np.ndarray]:
        """
        Calculate taxes for a matrix of withdrawals over time.
        
        Args:
            withdrawal_matrix: Withdrawals for each scenario and month (n_scenarios x n_months)
            taxable_fraction_matrix: Taxable fraction for each scenario and month
            social_security_array: Annual SS benefits for each scenario
            ages: Starting ages for each scenario
            filing_status: Filing status
            
        Returns:
            Dictionary with tax arrays over time
        """
        n_scenarios, n_months = withdrawal_matrix.shape
        n_years = n_months // 12 + 1
        
        # Initialize result arrays
        annual_taxes = np.zeros((n_scenarios, n_years))
        annual_federal = np.zeros((n_scenarios, n_years))
        annual_state = np.zeros((n_scenarios, n_years))
        
        for year_idx in range(n_years):
            # Calculate annual withdrawals and capital gains
            month_start = year_idx * 12
            month_end = min(month_start + 12, n_months)
            
            if month_start >= n_months:
                break
            
            # Sum withdrawals for the year
            annual_withdrawals = withdrawal_matrix[:, month_start:month_end].sum(axis=1)
            
            # Average taxable fraction for the year
            avg_taxable_fraction = taxable_fraction_matrix[:, month_start:month_end].mean(axis=1)
            
            # Calculate capital gains
            capital_gains = annual_withdrawals * avg_taxable_fraction
            
            # Adjust ages for current year
            current_ages = ages + year_idx
            
            # Calculate taxes for this year
            tax_results = self.calculate_batch_taxes(
                capital_gains_array=capital_gains,
                social_security_array=social_security_array,
                ages=current_ages,
                filing_status=filing_status
            )
            
            annual_taxes[:, year_idx] = tax_results['total_tax']
            annual_federal[:, year_idx] = tax_results['federal_income_tax']
            annual_state[:, year_idx] = tax_results['state_income_tax']
        
        return {
            'annual_total_tax': annual_taxes,
            'annual_federal_tax': annual_federal,
            'annual_state_tax': annual_state
        }


def calculate_monte_carlo_after_tax_income(
    gross_withdrawals: np.ndarray,
    taxable_fractions: np.ndarray,
    social_security_benefits: float,
    age: int,
    state: str = "CA",
    filing_status: str = "SINGLE"
) -> np.ndarray:
    """
    Convenience function to calculate after-tax income for Monte Carlo paths.
    
    Args:
        gross_withdrawals: Annual gross withdrawals for each scenario
        taxable_fractions: Taxable fraction for each scenario
        social_security_benefits: Annual SS benefits
        age: Current age
        state: State code
        filing_status: Filing status
        
    Returns:
        Array of after-tax income for each scenario
    """
    n_scenarios = len(gross_withdrawals)
    
    # Calculate capital gains
    capital_gains = gross_withdrawals * taxable_fractions
    
    # Create arrays for SS and age
    ss_array = np.full(n_scenarios, social_security_benefits)
    age_array = np.full(n_scenarios, age)
    
    # Calculate taxes
    calc = TaxCalculator(state=state)
    tax_results = calc.calculate_batch_taxes(
        capital_gains_array=capital_gains,
        social_security_array=ss_array,
        ages=age_array,
        filing_status=filing_status
    )
    
    # Return after-tax income
    return gross_withdrawals - tax_results['total_tax']