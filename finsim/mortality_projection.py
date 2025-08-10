"""Advanced mortality projection module using cohort-based mortality improvements.

This module provides more accurate mortality projections by:
1. Starting with current period life tables
2. Applying cohort-based mortality improvements
3. Adjusting for socioeconomic factors (optional)

References:
-----------
1. Lee, R. D., & Carter, L. R. (1992). "Modeling and forecasting US mortality."
   Journal of the American Statistical Association, 87(419), 659-671.
   - Basis for age-period mortality projections with improvements

2. Society of Actuaries (2014). "Mortality Improvement Scale MP-2014."
   - Standard mortality improvement rates by age and gender
   - https://www.soa.org/resources/experience-studies/2014/mortality-improvement-scale-mp-2014/

3. Chetty, R., et al. (2016). "The association between income and life expectancy 
   in the United States, 2001-2014." JAMA, 315(16), 1750-1766.
   - Documents ~30% mortality difference between top and bottom income quartiles
   - Basis for socioeconomic adjustments

4. Social Security Administration (2024). "Period Life Table, 2021."
   - Source for base mortality rates
   - https://www.ssa.gov/oact/STATS/table4c6.html

Implementation Notes:
--------------------
- Uses simplified mortality improvement of 1% per year (MP-2014 uses 0.5-2% by age)
- Socioeconomic multipliers based on Chetty et al. findings
- Improvements taper after age 85 following actuarial practice
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class MortalityProjectionParams:
    """Parameters for mortality projection.

    Default values based on SOA Mortality Improvement Scale MP-2014 and
    subsequent research on mortality improvements.
    """
    base_year: int = 2021  # Year of SSA base mortality table
    mortality_improvement_rate: float = 0.01  # 1% annual (SOA MP-2014 average)
    max_improvement_age: int = 85  # SOA shows improvements tapering after 85
    socioeconomic_multiplier: float = 1.0  # Based on Chetty et al. 2016


class MortalityProjector:
    """Advanced mortality projector with cohort adjustments and improvements."""

    def __init__(self, params: MortalityProjectionParams | None = None):
        """Initialize mortality projector.

        Args:
            params: Projection parameters (uses defaults if None)
        """
        self.params = params or MortalityProjectionParams()
        self._base_mortality = self._load_base_mortality()

    def _load_base_mortality(self) -> dict[str, dict[int, float]]:
        """Load base mortality rates (2021 SSA Period Life Table).

        Returns:
            Dict with 'Male' and 'Female' mortality rates by age
        """
        # Using 2021 SSA Period Life Table as baseline
        # These are qx values (probability of death within one year)
        male = {
            18: 0.00082, 19: 0.00093, 20: 0.00104,
            21: 0.00115, 22: 0.00126, 23: 0.00135, 24: 0.00143, 25: 0.00150,
            26: 0.00157, 27: 0.00164, 28: 0.00171, 29: 0.00179, 30: 0.00187,
            31: 0.00196, 32: 0.00206, 33: 0.00217, 34: 0.00229, 35: 0.00241,
            36: 0.00255, 37: 0.00270, 38: 0.00286, 39: 0.00303, 40: 0.00322,
            41: 0.00342, 42: 0.00365, 43: 0.00389, 44: 0.00416, 45: 0.00446,
            46: 0.00478, 47: 0.00513, 48: 0.00552, 49: 0.00594, 50: 0.00533,
            51: 0.00581, 52: 0.00632, 53: 0.00686, 54: 0.00743, 55: 0.00803,
            56: 0.00867, 57: 0.00934, 58: 0.01005, 59: 0.01079, 60: 0.01158,
            61: 0.01241, 62: 0.01328, 63: 0.01421, 64: 0.01519, 65: 0.01604,
            66: 0.01753, 67: 0.01912, 68: 0.02084, 69: 0.02271, 70: 0.02476,
            71: 0.02700, 72: 0.02946, 73: 0.03217, 74: 0.03515, 75: 0.03843,
            76: 0.04204, 77: 0.04603, 78: 0.05043, 79: 0.05530, 80: 0.06069,
            81: 0.06665, 82: 0.07326, 83: 0.08058, 84: 0.08868, 85: 0.09764,
            86: 0.10753, 87: 0.11845, 88: 0.13048, 89: 0.14373, 90: 0.15829,
            91: 0.17427, 92: 0.19178, 93: 0.21093, 94: 0.23182, 95: 0.25457,
            96: 0.27930, 97: 0.30612, 98: 0.33515, 99: 0.36651, 100: 0.40032,
            101: 0.43672, 102: 0.47572, 103: 0.51737, 104: 0.56168, 105: 0.60868,
            106: 0.65839, 107: 0.71084, 108: 0.76606, 109: 0.82407, 110: 0.88489,
            111: 0.94855, 112: 1.00000, 113: 1.00000, 114: 1.00000, 115: 1.00000,
            116: 1.00000, 117: 1.00000, 118: 1.00000, 119: 1.00000, 120: 1.00000
        }

        female = {
            18: 0.00033, 19: 0.00034, 20: 0.00036,
            21: 0.00038, 22: 0.00040, 23: 0.00042, 24: 0.00044, 25: 0.00046,
            26: 0.00049, 27: 0.00052, 28: 0.00055, 29: 0.00059, 30: 0.00063,
            31: 0.00067, 32: 0.00072, 33: 0.00077, 34: 0.00082, 35: 0.00088,
            36: 0.00095, 37: 0.00102, 38: 0.00110, 39: 0.00119, 40: 0.00128,
            41: 0.00139, 42: 0.00150, 43: 0.00163, 44: 0.00177, 45: 0.00192,
            46: 0.00208, 47: 0.00226, 48: 0.00246, 49: 0.00267, 50: 0.00324,
            51: 0.00352, 52: 0.00383, 53: 0.00417, 54: 0.00454, 55: 0.00494,
            56: 0.00537, 57: 0.00584, 58: 0.00634, 59: 0.00689, 60: 0.00748,
            61: 0.00812, 62: 0.00881, 63: 0.00955, 64: 0.01035, 65: 0.01052,
            66: 0.01146, 67: 0.01251, 68: 0.01368, 69: 0.01498, 70: 0.01642,
            71: 0.01803, 72: 0.01983, 73: 0.02183, 74: 0.02406, 75: 0.02653,
            76: 0.02927, 77: 0.03232, 78: 0.03570, 79: 0.03947, 80: 0.04365,
            81: 0.04830, 82: 0.05345, 83: 0.05916, 84: 0.06548, 85: 0.07247,
            86: 0.08019, 87: 0.08872, 88: 0.09812, 89: 0.10849, 90: 0.11991,
            91: 0.13247, 92: 0.14627, 93: 0.16142, 94: 0.17802, 95: 0.19620,
            96: 0.21605, 97: 0.23770, 98: 0.26127, 99: 0.28689, 100: 0.31467,
            101: 0.34475, 102: 0.37715, 103: 0.41190, 104: 0.44903, 105: 0.48856,
            106: 0.53051, 107: 0.57491, 108: 0.62177, 109: 0.67113, 110: 0.72299,
            111: 0.77738, 112: 0.83432, 113: 0.89384, 114: 0.95595, 115: 1.00000,
            116: 1.00000, 117: 1.00000, 118: 1.00000, 119: 1.00000, 120: 1.00000
        }

        return {"Male": male, "Female": female}

    def get_projected_mortality_rate(self,
                                    current_age: int,
                                    gender: str,
                                    projection_year: int) -> float:
        """Get mortality rate with cohort-based projections.

        Args:
            current_age: Current age of person
            gender: "Male" or "Female"
            projection_year: Year for which to project mortality

        Returns:
            Projected mortality rate (qx)
        """
        # Get base mortality rate
        base_rates = self._base_mortality[gender]

        # Handle ages outside table
        if current_age < 18:
            return 0.0001  # Very low mortality for young ages
        if current_age > 120:
            return 1.0  # Certain death past 120

        # Interpolate if age not in table
        if current_age not in base_rates:
            ages = sorted(base_rates.keys())
            lower_age = max([a for a in ages if a < current_age], default=ages[0])
            upper_age = min([a for a in ages if a > current_age], default=ages[-1])

            if lower_age == upper_age:
                base_rate = base_rates[lower_age]
            else:
                # Linear interpolation
                weight = (current_age - lower_age) / (upper_age - lower_age)
                base_rate = (base_rates[lower_age] * (1 - weight) +
                           base_rates[upper_age] * weight)
        else:
            base_rate = base_rates[current_age]

        # Apply mortality improvements
        years_of_improvement = projection_year - self.params.base_year

        # Improvement rate decreases with age
        if current_age <= self.params.max_improvement_age:
            improvement_factor = self.params.mortality_improvement_rate
        else:
            # Linear taper from max_improvement_age to 120
            age_factor = max(0, (120 - current_age) / (120 - self.params.max_improvement_age))
            improvement_factor = self.params.mortality_improvement_rate * age_factor

        # Apply compound improvement
        improvement_multiplier = (1 - improvement_factor) ** years_of_improvement

        # Apply socioeconomic adjustment
        adjusted_rate = base_rate * improvement_multiplier * self.params.socioeconomic_multiplier

        # Ensure rate is in valid range
        return np.clip(adjusted_rate, 0.0, 1.0)

    def simulate_survival(self,
                         current_age: int,
                         gender: str,
                         n_years: int,
                         start_year: int = 2025,
                         n_simulations: int = 1000) -> np.ndarray:
        """Simulate survival paths using projected mortality.

        Args:
            current_age: Starting age
            gender: "Male" or "Female"
            n_years: Number of years to simulate
            start_year: Starting year for projection
            n_simulations: Number of Monte Carlo simulations

        Returns:
            Boolean array of shape (n_simulations, n_years + 1) indicating survival
        """
        alive = np.ones((n_simulations, n_years + 1), dtype=bool)

        for year in range(1, n_years + 1):
            age = current_age + year
            projection_year = start_year + year

            # Get projected mortality rate
            mortality_rate = self.get_projected_mortality_rate(
                age, gender, projection_year
            )

            # Simulate deaths
            random_draws = np.random.random(n_simulations)
            deaths = random_draws < mortality_rate

            # Update survival status
            # Once dead, stay dead
            currently_alive = alive[:, year - 1]
            alive[deaths & currently_alive, year:] = False

        return alive

    def get_life_expectancy(self,
                           current_age: int,
                           gender: str,
                           start_year: int = 2025,
                           max_age: int = 120) -> float:
        """Calculate cohort life expectancy with projections.

        Args:
            current_age: Current age
            gender: "Male" or "Female"
            start_year: Starting year for projection
            max_age: Maximum age to consider

        Returns:
            Expected remaining years of life
        """
        years = max_age - current_age
        survival_prob = 1.0
        life_expectancy = 0.0

        for year in range(years):
            age = current_age + year
            projection_year = start_year + year

            # Get mortality rate for this year
            mortality_rate = self.get_projected_mortality_rate(
                age, gender, projection_year
            )

            # Add fractional year survived
            life_expectancy += survival_prob * (1 - mortality_rate / 2)

            # Update survival probability
            survival_prob *= (1 - mortality_rate)

        return life_expectancy


def get_mortality_projector(wealth_level: str | None = "average") -> MortalityProjector:
    """Get a mortality projector configured for wealth level.

    Args:
        wealth_level: "low", "average", or "high"

    Returns:
        Configured mortality projector
    """
    # Research shows significant mortality differences by wealth
    # High wealth individuals have ~30% lower mortality
    # Low wealth individuals have ~20% higher mortality
    wealth_multipliers = {
        "low": 1.2,
        "average": 1.0,
        "high": 0.7
    }

    params = MortalityProjectionParams(
        socioeconomic_multiplier=wealth_multipliers.get(wealth_level, 1.0)
    )

    return MortalityProjector(params)
