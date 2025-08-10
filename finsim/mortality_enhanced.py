"""Enhanced mortality calculations with optional Bayesian adjustment.

This module provides an interface to use either simple SSA tables or
the advanced Bayesian mortality adjustments from the mortality package.
"""

from typing import Literal

import numpy as np

from .mortality import get_mortality_rates


class EnhancedMortality:
    """Enhanced mortality calculations with optional adjustments."""

    def __init__(
        self,
        gender: Literal["Male", "Female"] = "Male",
        use_bayesian: bool = False,
        smoker: bool | None = None,
        income_percentile: int | None = None,
        health_status: Literal["excellent", "good", "average", "poor"] | None = None,
    ):
        """Initialize enhanced mortality calculator.

        Args:
            gender: Gender for base rates
            use_bayesian: Whether to use Bayesian adjustments
            smoker: Smoking status (for Bayesian adjustment)
            income_percentile: Income percentile 1-100 (for Bayesian adjustment)
            health_status: Health status (for Bayesian adjustment)
        """
        self.gender = gender
        self.use_bayesian = use_bayesian
        self.smoker = smoker
        self.income_percentile = income_percentile
        self.health_status = health_status

        # Get base rates
        self.base_rates = get_mortality_rates(gender)

    def get_mortality_rate(self, age: int) -> float:
        """Get mortality rate for a specific age.

        Args:
            age: Age in years

        Returns:
            Annual mortality probability
        """
        # Get base rate
        if age in self.base_rates:
            base_rate = self.base_rates[age]
        else:
            # Interpolate
            ages = sorted(self.base_rates.keys())
            rates = [self.base_rates[a] for a in ages]
            base_rate = float(np.interp(age, ages, rates))

        if not self.use_bayesian:
            return base_rate

        # Apply Bayesian adjustment (simplified version)
        # This is a simplified implementation - the full version would
        # import from the mortality package
        log_odds = np.log(base_rate / (1 - base_rate + 1e-10))

        # Smoking adjustment
        if self.smoker is not None:
            smoking_prev = 0.15
            smoking_effect = 0.59  # log(1.8)
            population_effect = smoking_prev * smoking_effect
            log_odds -= population_effect
            if self.smoker:
                log_odds += smoking_effect

        # Income adjustment
        if self.income_percentile is not None:
            income_effect = -0.004 * (self.income_percentile - 50)
            log_odds += income_effect

        # Health adjustment
        if self.health_status is not None:
            health_effects = {"excellent": -0.35, "good": -0.16, "average": 0.0, "poor": 0.26}
            # Remove population average (assuming distribution)
            pop_avg = (
                0.2 * health_effects["excellent"]
                + 0.3 * health_effects["good"]
                + 0.3 * health_effects["average"]
                + 0.2 * health_effects["poor"]
            )
            log_odds -= pop_avg
            log_odds += health_effects[self.health_status]

        # Convert back to probability
        adjusted_rate = 1 / (1 + np.exp(-log_odds))
        return np.clip(adjusted_rate, 0, 1)

    def get_vectorized_rates(self, ages: np.ndarray, n_simulations: int) -> np.ndarray:
        """Get mortality rates for multiple ages (vectorized).

        Args:
            ages: Array of ages
            n_simulations: Number of simulations

        Returns:
            Array of mortality rates
        """
        rates = np.zeros((n_simulations, len(ages)))
        for i, age in enumerate(ages):
            rates[:, i] = self.get_mortality_rate(age)
        return rates

    def simulate_survival(
        self, starting_age: int, n_simulations: int, n_years: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Simulate survival paths.

        Args:
            starting_age: Starting age
            n_simulations: Number of Monte Carlo paths
            n_years: Number of years to simulate

        Returns:
            Tuple of (alive_mask, death_ages)
        """
        alive_mask = np.ones((n_simulations, n_years), dtype=bool)
        death_ages = np.full(n_simulations, starting_age + n_years)

        for year in range(1, n_years):
            age = starting_age + year - 1
            mort_rate = self.get_mortality_rate(age)

            # Only check mortality for those still alive
            still_alive = alive_mask[:, year - 1]
            if not np.any(still_alive):
                break

            death_this_year = np.zeros(n_simulations, dtype=bool)
            death_this_year[still_alive] = np.random.random(np.sum(still_alive)) < mort_rate

            # Update alive mask
            alive_mask[death_this_year, year:] = False

            # Record death ages
            death_ages[death_this_year & (death_ages == starting_age + n_years)] = (
                age + np.random.random()
            )

        return alive_mask, death_ages


def compare_mortality_approaches():
    """Compare basic vs enhanced mortality calculations."""

    # Setup
    age = 65
    n_sims = 10000
    n_years = 55  # To age 120

    print("Comparing Mortality Approaches")
    print("=" * 50)

    # Basic SSA tables
    basic = EnhancedMortality(gender="Male", use_bayesian=False)
    basic_alive, basic_deaths = basic.simulate_survival(age, n_sims, n_years)
    basic_life_exp = np.mean(basic_deaths - age)

    print("\nBasic SSA Tables:")
    print(f"  Life expectancy at {age}: {basic_life_exp:.1f} years")
    print(f"  10th percentile: {np.percentile(basic_deaths - age, 10):.1f} years")
    print(f"  90th percentile: {np.percentile(basic_deaths - age, 90):.1f} years")

    # Enhanced with good health, high income
    enhanced = EnhancedMortality(
        gender="Male", use_bayesian=True, smoker=False, income_percentile=80, health_status="good"
    )
    enhanced_alive, enhanced_deaths = enhanced.simulate_survival(age, n_sims, n_years)
    enhanced_life_exp = np.mean(enhanced_deaths - age)

    print("\nEnhanced (healthy, high-income non-smoker):")
    print(f"  Life expectancy at {age}: {enhanced_life_exp:.1f} years")
    print(f"  10th percentile: {np.percentile(enhanced_deaths - age, 10):.1f} years")
    print(f"  90th percentile: {np.percentile(enhanced_deaths - age, 90):.1f} years")
    print(f"  Difference from base: +{enhanced_life_exp - basic_life_exp:.1f} years")

    # Enhanced with poor health, smoker
    poor_health = EnhancedMortality(
        gender="Male", use_bayesian=True, smoker=True, income_percentile=25, health_status="poor"
    )
    poor_alive, poor_deaths = poor_health.simulate_survival(age, n_sims, n_years)
    poor_life_exp = np.mean(poor_deaths - age)

    print("\nEnhanced (poor health, low-income smoker):")
    print(f"  Life expectancy at {age}: {poor_life_exp:.1f} years")
    print(f"  10th percentile: {np.percentile(poor_deaths - age, 10):.1f} years")
    print(f"  90th percentile: {np.percentile(poor_deaths - age, 90):.1f} years")
    print(f"  Difference from base: {poor_life_exp - basic_life_exp:.1f} years")


if __name__ == "__main__":
    compare_mortality_approaches()
