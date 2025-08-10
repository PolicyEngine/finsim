"""Core mortality class - the simple API everyone can use.

This is Level 1-2: Basic tables with optional personal adjustments.
No statistics knowledge required.
"""

import numpy as np
from typing import Optional, Literal, Union, Tuple
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class MortalityFactors:
    """Personal factors that affect mortality.
    
    All fields are optional - only specify what you know.
    """
    # Demographics
    gender: Literal["male", "female"] = "male"
    
    # Health
    health: Literal["excellent", "good", "average", "poor"] = "average"
    smoker: bool = False
    bmi: Optional[float] = None  # 18.5-25 is normal
    
    # Socioeconomic  
    education: Literal["high_school", "bachelors", "graduate", None] = None
    income_percentile: Optional[int] = None  # 1-99
    
    # Behaviors
    exercise: Literal["none", "moderate", "regular", None] = None
    alcohol: Literal["none", "moderate", "heavy", None] = None
    
    def get_multiplier(self) -> float:
        """Convert factors to mortality multiplier.
        
        Based on peer-reviewed research:
        - Chetty et al. (2016): Income effects
        - Mehta & Preston (2016): Education effects
        - And many others...
        """
        mult = 1.0
        
        # Health status (±30% from Rogers et al. 2000)
        health_mults = {
            "excellent": 0.7,
            "good": 0.85, 
            "average": 1.0,
            "poor": 1.3
        }
        mult *= health_mults[self.health]
        
        # Smoking (1.8x from Carter et al. 2015)
        if self.smoker:
            mult *= 1.8
            
        # Income (Chetty et al. 2016)
        if self.income_percentile:
            if self.income_percentile >= 80:
                mult *= 0.75
            elif self.income_percentile <= 20:
                mult *= 1.25
                
        # Education (Hummer & Hernandez 2013)
        if self.education:
            edu_mults = {
                "high_school": 1.15,
                "bachelors": 0.92,
                "graduate": 0.88
            }
            mult *= edu_mults.get(self.education, 1.0)
            
        # Exercise (Moore et al. 2012)
        if self.exercise:
            exercise_mults = {
                "none": 1.2,
                "moderate": 0.95,
                "regular": 0.85
            }
            mult *= exercise_mults.get(self.exercise, 1.0)
            
        return mult


class Mortality:
    """Simple mortality calculations.
    
    Examples:
        # Simplest - just age
        mort = Mortality()
        prob = mort.q(65)  # 1-year death probability at 65
        
        # With gender
        mort = Mortality(gender="female")
        life_exp = mort.e(65)  # Life expectancy at 65
        
        # With personal factors
        mort = Mortality(
            gender="female",
            factors=MortalityFactors(
                health="good",
                income_percentile=75
            )
        )
        survival = mort.survival(65, 95)  # Survival curve from 65 to 95
    """
    
    def __init__(self,
                 gender: Literal["male", "female"] = "male",
                 factors: Optional[MortalityFactors] = None,
                 improvement_rate: float = 0.01,
                 base_year: int = 2021):
        """Initialize mortality calculator.
        
        Args:
            gender: Biological sex for base rates
            factors: Personal mortality factors
            improvement_rate: Annual mortality improvement (0.01 = 1%)
            base_year: Year of base mortality table
        """
        self.gender = gender
        self.factors = factors or MortalityFactors(gender=gender)
        self.improvement_rate = improvement_rate
        self.base_year = base_year
        self._base_rates = self._load_base_rates()
        
    def _load_base_rates(self) -> dict:
        """Load base mortality rates (SSA 2021)."""
        # In production, load from data files
        # For now, using simplified SSA 2021 tables
        
        if self.gender == "male":
            return {
                0: 0.00598, 1: 0.00039, 5: 0.00013, 10: 0.00014,
                15: 0.00045, 20: 0.00104, 25: 0.00150, 30: 0.00187,
                35: 0.00241, 40: 0.00322, 45: 0.00446, 50: 0.00533,
                55: 0.00803, 60: 0.01158, 65: 0.01604, 70: 0.02476,
                75: 0.03843, 80: 0.06069, 85: 0.09764, 90: 0.15829,
                95: 0.25457, 100: 0.40032, 105: 0.60868, 110: 0.88489
            }
        else:
            return {
                0: 0.00493, 1: 0.00033, 5: 0.00010, 10: 0.00011,
                15: 0.00021, 20: 0.00036, 25: 0.00046, 30: 0.00063,
                35: 0.00088, 40: 0.00128, 45: 0.00192, 50: 0.00324,
                55: 0.00494, 60: 0.00748, 65: 0.01052, 70: 0.01642,
                75: 0.02653, 80: 0.04365, 85: 0.07247, 90: 0.11991,
                95: 0.19620, 100: 0.31467, 105: 0.48856, 110: 0.72299
            }
    
    @lru_cache(maxsize=1000)
    def q(self, age: int, years_forward: int = 0) -> float:
        """Probability of death within one year.
        
        Args:
            age: Current age
            years_forward: Years in future (for projections)
            
        Returns:
            Probability of death before next birthday (qx)
        """
        # Interpolate base rate
        ages = sorted(self._base_rates.keys())
        rates = [self._base_rates[a] for a in ages]
        base_q = np.interp(age, ages, rates)
        
        # Apply improvements
        if years_forward > 0:
            improvement = (1 - self.improvement_rate) ** years_forward
            base_q *= improvement
            
        # Apply personal factors
        base_q *= self.factors.get_multiplier()
        
        return min(1.0, base_q)
    
    def p(self, age: int, years_forward: int = 0) -> float:
        """Probability of survival for one year.
        
        Args:
            age: Current age
            years_forward: Years in future
            
        Returns:
            Probability of surviving to next birthday (px)
        """
        return 1 - self.q(age, years_forward)
    
    def survival(self, from_age: int, to_age: int) -> np.ndarray:
        """Survival curve between two ages.
        
        Args:
            from_age: Starting age
            to_age: Ending age (inclusive)
            
        Returns:
            Array of survival probabilities for each age
        """
        ages = np.arange(from_age, to_age + 1)
        survival = np.ones(len(ages))
        
        for i in range(1, len(ages)):
            years_forward = i - 1
            survival[i] = survival[i-1] * self.p(ages[i-1], years_forward)
            
        return survival
    
    def e(self, age: int, max_age: int = 120) -> float:
        """Life expectancy at given age.
        
        Args:
            age: Current age
            max_age: Maximum possible age
            
        Returns:
            Expected years of remaining life
        """
        survival = self.survival(age, max_age)
        # Trapezoidal integration for continuous approximation
        return np.trapz(survival, dx=1.0)
    
    def median_survival(self, age: int, max_age: int = 120) -> float:
        """Median survival age (50% probability).
        
        Args:
            age: Current age  
            max_age: Maximum possible age
            
        Returns:
            Age at which 50% probability of survival
        """
        survival = self.survival(age, max_age)
        ages = np.arange(age, max_age + 1)
        
        # Find where survival crosses 50%
        idx = np.searchsorted(-survival, -0.5)
        if idx >= len(ages):
            return max_age
            
        # Linear interpolation for fractional age
        if idx > 0:
            p1, p2 = survival[idx-1], survival[idx]
            a1, a2 = ages[idx-1], ages[idx]
            # Interpolate to find exact 50% point
            frac = (0.5 - p2) / (p1 - p2)
            return a2 - frac
        
        return ages[idx]
    
    def simulate(self, 
                age: int,
                n_sims: int = 1000,
                max_age: int = 120) -> np.ndarray:
        """Simulate death ages using Monte Carlo.
        
        Args:
            age: Starting age
            n_sims: Number of simulations
            max_age: Maximum possible age
            
        Returns:
            Array of simulated death ages
        """
        death_ages = np.full(n_sims, max_age, dtype=float)
        
        for i in range(n_sims):
            for current_age in range(age, max_age):
                years_forward = current_age - age
                if np.random.random() < self.q(current_age, years_forward):
                    death_ages[i] = current_age + np.random.random()  # Fractional
                    break
                    
        return death_ages
    
    def __repr__(self) -> str:
        """String representation."""
        factors_str = f", factors={self.factors}" if self.factors else ""
        return f"Mortality(gender='{self.gender}'{factors_str})"


# Convenience functions for quick calculations
def quick_life_expectancy(age: int, 
                          gender: str = "male",
                          health: str = "average") -> float:
    """Quick life expectancy calculation.
    
    Examples:
        >>> quick_life_expectancy(65)
        17.2
        >>> quick_life_expectancy(65, "female", "good")  
        21.5
    """
    mort = Mortality(
        gender=gender,
        factors=MortalityFactors(health=health, gender=gender)
    )
    return mort.e(age)