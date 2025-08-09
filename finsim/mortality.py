"""SSA mortality tables and related functions."""

import json
from pathlib import Path
import numpy as np


def load_mortality_data():
    """Load SSA mortality data from JSON file."""
    data_path = Path(__file__).parent / "data" / "ssa_mortality.json"
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Convert string keys to integers
    male_mortality = {int(k): v for k, v in data["male"].items()}
    female_mortality = {int(k): v for k, v in data["female"].items()}
    
    return male_mortality, female_mortality


# Load data on import
SSA_MALE_MORTALITY, SSA_FEMALE_MORTALITY = load_mortality_data()


def get_mortality_rates(gender="Male"):
    """Get mortality rates for the specified gender.
    
    Args:
        gender: "Male" or "Female"
    
    Returns:
        Dictionary mapping age to annual mortality probability
    """
    if gender == "Male":
        return SSA_MALE_MORTALITY
    else:
        return SSA_FEMALE_MORTALITY


def get_mortality_rate(age: int, gender="Male") -> float:
    """Get mortality rate for a specific age.
    
    Args:
        age: Age in years
        gender: "Male" or "Female"
    
    Returns:
        Annual mortality probability
    """
    rates = get_mortality_rates(gender)
    
    # Interpolate if age not in table
    ages = sorted(rates.keys())
    if age < ages[0]:
        return 0.0
    if age > ages[-1]:
        return rates[ages[-1]]
    
    return np.interp(age, ages, [rates[a] for a in ages])


def calculate_survival_curve(start_age: int, end_age: int, gender="Male") -> np.ndarray:
    """Calculate survival probabilities from start_age to end_age.
    
    Args:
        start_age: Starting age
        end_age: Ending age (inclusive)
        gender: "Male" or "Female"
    
    Returns:
        Array of cumulative survival probabilities
    """
    ages = np.arange(start_age, end_age + 1)
    survival_probs = np.ones(len(ages))
    
    cumulative_survival = 1.0
    for i, age in enumerate(ages):
        if i > 0:  # First year is always 1.0
            mort_rate = get_mortality_rate(age - 1, gender)
            cumulative_survival *= (1 - mort_rate)
        survival_probs[i] = cumulative_survival
    
    return survival_probs


def calculate_life_expectancy(age: int, gender="Male", max_age=120) -> float:
    """Calculate remaining life expectancy for a given age.
    
    Args:
        age: Current age
        gender: "Male" or "Female"
        max_age: Maximum age to consider
    
    Returns:
        Expected remaining years of life
    """
    survival_probs = calculate_survival_curve(age, max_age, gender)
    
    # Life expectancy is the sum of survival probabilities
    # (discrete approximation of the integral)
    # We exclude the first year (current age) since that's probability 1.0
    life_expectancy = np.sum(survival_probs[1:])
    
    return life_expectancy