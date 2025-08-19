"""Modern mortality projection for practical applications.

A Python-first approach to mortality projection that balances sophistication
with usability. Instead of porting StMoMo's academic framework, this implements
what practitioners actually need.

Key Design Decisions:
1. Focus on simulation rather than statistical inference
2. Use pre-fitted models rather than fitting from raw data
3. Emphasize interpretable parameters over mathematical generality
4. Optimize for speed in Monte Carlo contexts

Author: Claude
License: MIT
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass
class MortalityAssumptions:
    """User-friendly mortality assumptions.

    Instead of abstract statistical parameters, use concepts that
    financial planners and individuals can understand.
    """

    # Health/lifestyle factors
    health_status: Literal["excellent", "good", "average", "below_average", "poor"] = (
        "average"
    )
    smoker: bool = False

    # Socioeconomic factors
    education: Literal["high_school", "some_college", "bachelors", "graduate"] = (
        "bachelors"
    )
    income_percentile: int = 50  # 1-99

    # Medical advances assumption
    medical_progress: Literal["pessimistic", "baseline", "optimistic"] = "baseline"

    def get_multiplier(self) -> float:
        """Convert assumptions to a mortality multiplier.

        Based on research from:
        - Chetty et al. (2016): Income gaps
        - Case & Deaton (2017): Education effects
        - Rogers et al. (2000): Smoking impact
        """
        multiplier = 1.0

        # Health status impact (±20%)
        health_multipliers = {
            "excellent": 0.8,
            "good": 0.9,
            "average": 1.0,
            "below_average": 1.15,
            "poor": 1.3,
        }
        multiplier *= health_multipliers[self.health_status]

        # Smoking roughly doubles mortality
        if self.smoker:
            multiplier *= 1.8

        # Education effect (college grads live ~3 years longer)
        education_multipliers = {
            "high_school": 1.1,
            "some_college": 1.05,
            "bachelors": 0.95,
            "graduate": 0.92,
        }
        multiplier *= education_multipliers[self.education]

        # Income effect (top 1% live ~15 years longer than bottom 1%)
        # Approximately linear in log income
        if self.income_percentile >= 90:
            multiplier *= 0.75
        elif self.income_percentile >= 75:
            multiplier *= 0.85
        elif self.income_percentile >= 25:
            multiplier *= 1.0
        else:
            multiplier *= 1.2

        return multiplier

    def get_improvement_rate(self) -> float:
        """Get annual mortality improvement rate."""
        rates = {
            "pessimistic": 0.005,  # 0.5% per year
            "baseline": 0.01,  # 1% per year (historical average)
            "optimistic": 0.02,  # 2% per year (recent decades)
        }
        return rates[self.medical_progress]


class PracticalMortalityModel:
    """Practical mortality model for financial planning.

    This is what I'd build instead of porting StMoMo:
    - Pre-calibrated to recent data
    - Fast simulation
    - Intuitive parameters
    - Good enough accuracy for planning
    """

    def __init__(
        self,
        gender: Literal["male", "female"],
        assumptions: MortalityAssumptions | None = None,
    ):
        """Initialize mortality model.

        Args:
            gender: Biological sex for base mortality
            assumptions: Personal factors affecting mortality
        """
        self.gender = gender
        self.assumptions = assumptions or MortalityAssumptions()
        self.base_rates = self._load_base_rates()

    def _load_base_rates(self) -> dict[int, float]:
        """Load base mortality rates.

        In production, these would come from:
        - Human Mortality Database for general population
        - SOA tables for insured populations
        - Social Security for US population
        """
        # Using SSA 2021 as baseline
        if self.gender == "male":
            return {
                30: 0.00187,
                35: 0.00241,
                40: 0.00322,
                45: 0.00446,
                50: 0.00533,
                55: 0.00803,
                60: 0.01158,
                65: 0.01604,
                70: 0.02476,
                75: 0.03843,
                80: 0.06069,
                85: 0.09764,
                90: 0.15829,
                95: 0.25457,
                100: 0.40032,
                105: 0.60868,
                110: 0.88489,
                115: 1.00000,
                120: 1.00000,
            }
        else:
            return {
                30: 0.00063,
                35: 0.00088,
                40: 0.00128,
                45: 0.00192,
                50: 0.00324,
                55: 0.00494,
                60: 0.00748,
                65: 0.01052,
                70: 0.01642,
                75: 0.02653,
                80: 0.04365,
                85: 0.07247,
                90: 0.11991,
                95: 0.19620,
                100: 0.31467,
                105: 0.48856,
                110: 0.72299,
                115: 1.00000,
                120: 1.00000,
            }

    def get_mortality_rate(self, age: int, years_from_now: int = 0) -> float:
        """Get mortality rate with improvements and adjustments.

        Args:
            age: Current age
            years_from_now: Years in future (for improvements)

        Returns:
            Adjusted mortality rate (qx)
        """
        # Interpolate base rate
        ages = sorted(self.base_rates.keys())
        rates = [self.base_rates[a] for a in ages]
        base_rate = np.interp(age, ages, rates)

        # Apply improvements
        improvement_rate = self.assumptions.get_improvement_rate()
        improvement_factor = (1 - improvement_rate) ** years_from_now

        # Apply personal multiplier
        personal_multiplier = self.assumptions.get_multiplier()

        # Combine adjustments
        adjusted_rate = base_rate * improvement_factor * personal_multiplier

        return np.clip(adjusted_rate, 0, 1)

    def simulate_lifetime(
        self, current_age: int, n_simulations: int = 1000, max_age: int = 120
    ) -> np.ndarray:
        """Simulate lifetimes using Monte Carlo.

        Args:
            current_age: Starting age
            n_simulations: Number of simulations
            max_age: Maximum possible age

        Returns:
            Array of death ages (max_age if survived to max)
        """
        death_ages = np.full(n_simulations, max_age)

        for sim in range(n_simulations):
            for age in range(current_age, max_age):
                years_from_now = age - current_age
                qx = self.get_mortality_rate(age, years_from_now)

                if np.random.random() < qx:
                    death_ages[sim] = age
                    break

        return death_ages

    def survival_curve(
        self, current_age: int, max_age: int = 120
    ) -> tuple[np.ndarray, np.ndarray]:
        """Get expected survival curve.

        Args:
            current_age: Starting age
            max_age: Maximum age to project

        Returns:
            Tuple of (ages, survival_probabilities)
        """
        ages = np.arange(current_age, max_age + 1)
        survival = np.ones(len(ages))

        for i, age in enumerate(ages[1:], 1):
            years_from_now = age - current_age - 1
            qx = self.get_mortality_rate(age - 1, years_from_now)
            survival[i] = survival[i - 1] * (1 - qx)

        return ages, survival

    def life_expectancy(self, current_age: int) -> float:
        """Calculate cohort life expectancy.

        Args:
            current_age: Current age

        Returns:
            Expected remaining years of life
        """
        ages, survival = self.survival_curve(current_age)
        # Trapezoidal integration
        return np.trapz(survival, ages) / survival[0]


def compare_to_stmomo():
    """Show how this compares to StMoMo approach.

    StMoMo fits statistical models to historical data:
    - log(m_xt) = α_x + β_x * κ_t + γ_t-x  (Lee-Carter with cohort)
    - Requires decades of death/exposure data
    - Estimates parameters via maximum likelihood
    - Projects κ_t using ARIMA models

    Our approach uses pre-calibrated rates with adjustments:
    - Start with recent official life tables
    - Apply research-based personal adjustments
    - Use scenario-based improvement assumptions
    - Optimize for simulation speed

    Trade-offs:
    - StMoMo: Rigorous but requires data and expertise
    - Ours: Practical and fast but less flexible
    """

    # Example usage
    model = PracticalMortalityModel(
        gender="male",
        assumptions=MortalityAssumptions(
            health_status="good",
            smoker=False,
            education="graduate",
            income_percentile=75,
            medical_progress="baseline",
        ),
    )

    # Quick results
    le = model.life_expectancy(65)
    print(f"Life expectancy at 65: {le:.1f} years")

    # Fast simulation
    import time

    start = time.time()
    lifetimes = model.simulate_lifetime(65, n_simulations=10000)
    elapsed = time.time() - start

    print(f"10,000 simulations in {elapsed:.2f} seconds")
    print(f"Median death age: {np.median(lifetimes):.1f}")
    print(f"10th percentile: {np.percentile(lifetimes, 10):.1f}")
    print(f"90th percentile: {np.percentile(lifetimes, 90):.1f}")


if __name__ == "__main__":
    compare_to_stmomo()
