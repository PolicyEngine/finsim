"""Stacked simulation functionality for efficient multi-scenario analysis."""

from typing import Any

import numpy as np
import pandas as pd

from .cola import get_consumption_inflation_factors, get_ssa_cola_factors
from .mortality import get_mortality_rates
from .return_generator import ReturnGenerator
from .tax import TaxCalculator


def create_scenario_config(
    name: str,
    initial_portfolio: float,
    has_annuity: bool = False,
    annuity_type: str | None = None,
    annuity_annual: float = 0,
    annuity_guarantee_years: int = 0,
    **kwargs,
) -> dict[str, Any]:
    """
    Create a scenario configuration dictionary.

    Parameters
    ----------
    name : str
        Name of the scenario
    initial_portfolio : float
        Starting portfolio value
    has_annuity : bool
        Whether scenario includes an annuity
    annuity_type : str, optional
        Type of annuity ("Life Only", "Life Contingent with Guarantee", "Fixed Period")
    annuity_annual : float
        Annual annuity payment
    annuity_guarantee_years : int
        Years of guaranteed payments
    **kwargs
        Additional scenario parameters

    Returns
    -------
    dict
        Scenario configuration
    """
    config = {
        "name": name,
        "initial_portfolio": initial_portfolio,
        "has_annuity": has_annuity,
        "annuity_type": annuity_type,
        "annuity_annual": annuity_annual,
        "annuity_guarantee_years": annuity_guarantee_years,
    }
    config.update(kwargs)
    return config


def simulate_stacked_scenarios(
    scenarios: list[dict[str, Any]],
    spending_levels: list[float],
    n_simulations: int = 1000,
    n_years: int = 30,
    base_params: dict[str, Any] | None = None,
    track_tax_calls: bool = False,
    include_percentiles: bool = True,
    random_seed: int | None = 42,
) -> list[dict[str, Any]]:
    """
    Run stacked simulations for multiple scenarios and spending levels.

    This function runs all scenarios together for each spending level,
    using a single tax calculation per year instead of separate calculations
    for each simulation. This provides massive performance improvements.

    Parameters
    ----------
    scenarios : list of dict
        List of scenario configurations
    spending_levels : list of float
        Annual spending amounts to test (in today's dollars)
    n_simulations : int
        Number of Monte Carlo simulations per scenario
    n_years : int
        Number of years to simulate
    base_params : dict, optional
        Base parameters common to all scenarios
    track_tax_calls : bool
        Whether to track number of tax calculations
    include_percentiles : bool
        Whether to include percentile calculations
    random_seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    list of dict
        Results for each scenario and spending level combination
    """
    if base_params is None:
        base_params = {
            "current_age": 65,
            "gender": "Male",
            "social_security": 24_000,
            "pension": 0,
            "employment_income": 0,
            "retirement_age": 65,
            "expected_return": 7.0,
            "return_volatility": 18.0,
            "dividend_yield": 1.8,
            "state": "CA",
            "include_mortality": True,
        }

    all_results = []

    # Process each spending level
    for spending_level in spending_levels:
        results = _simulate_single_spending_level(
            scenarios=scenarios,
            spending_level=spending_level,
            n_simulations=n_simulations,
            n_years=n_years,
            base_params=base_params,
            track_tax_calls=track_tax_calls,
            include_percentiles=include_percentiles,
            random_seed=random_seed,
        )
        all_results.extend(results)

    return all_results


def _simulate_single_spending_level(
    scenarios: list[dict[str, Any]],
    spending_level: float,
    n_simulations: int,
    n_years: int,
    base_params: dict[str, Any],
    track_tax_calls: bool,
    include_percentiles: bool,
    random_seed: int | None,
) -> list[dict[str, Any]]:
    """
    Simulate a single spending level across all scenarios.

    This is where the stacking magic happens - all scenarios run together
    with shared tax calculations.
    """
    n_scenarios = len(scenarios)
    total_sims = n_scenarios * n_simulations
    tax_calculation_count = 0

    # Set random seed if provided
    if random_seed is not None:
        np.random.seed(random_seed)

    # Initialize shared components
    tax_calc = TaxCalculator(state=base_params.get("state", "CA"), year=2025)

    # Get inflation factors once
    START_YEAR = 2025
    cola_factors = get_ssa_cola_factors(START_YEAR, n_years)
    inflation_factors = get_consumption_inflation_factors(START_YEAR, n_years)

    # Get mortality rates once
    include_mortality = base_params.get("include_mortality", True)
    if include_mortality:
        mortality_rates = get_mortality_rates(base_params.get("gender", "Male"))
    else:
        mortality_rates = {}

    # Generate ALL returns upfront (shared randomness)
    expected_return = base_params.get("expected_return", 7.0) / 100
    return_volatility = base_params.get("return_volatility", 18.0) / 100
    return_gen = ReturnGenerator(
        expected_return=expected_return, volatility=return_volatility
    )
    growth_factors_matrix = return_gen.generate_returns(total_sims, n_years)

    # Initialize arrays for ALL scenarios
    portfolio_paths = np.zeros((total_sims, n_years + 1))
    alive_mask = np.ones((total_sims, n_years + 1), dtype=bool)
    cost_basis = np.zeros(total_sims)
    prior_year_tax_liability = np.zeros(total_sims)

    # Track which simulation belongs to which scenario
    scenario_map = np.zeros(total_sims, dtype=int)

    # Initialize portfolios based on scenario
    idx = 0
    for s_idx, scenario in enumerate(scenarios):
        for _ in range(n_simulations):
            scenario_map[idx] = s_idx
            portfolio_paths[idx, 0] = scenario["initial_portfolio"]
            cost_basis[idx] = scenario["initial_portfolio"]
            idx += 1

    # Simulate each year
    for year in range(1, n_years + 1):
        current_age = base_params.get("current_age", 65)
        age = current_age + year

        # Apply mortality
        if include_mortality and age > current_age:
            mort_rate = mortality_rates.get(age, 0)
            death_this_year = np.random.random(total_sims) < mort_rate
            alive_mask[death_this_year, year:] = False

        # Get growth factors for this year
        growth_factor = growth_factors_matrix[:, year - 1]

        # Portfolio evolution
        current_portfolio = portfolio_paths[:, year - 1]
        portfolio_after_growth = np.where(
            alive_mask[:, year], current_portfolio * growth_factor, current_portfolio
        )

        # Dividends
        dividend_yield = base_params.get("dividend_yield", 1.8) / 100
        dividends = np.where(alive_mask[:, year], current_portfolio * dividend_yield, 0)

        # Calculate annuity income based on scenario
        annuity_income = np.zeros(total_sims)
        for idx in range(total_sims):
            scenario = scenarios[scenario_map[idx]]

            if scenario.get("has_annuity", False):
                annuity_type = scenario.get("annuity_type", "Life Only")
                annuity_annual = scenario.get("annuity_annual", 0)
                guarantee_years = scenario.get("annuity_guarantee_years", 0)

                if annuity_type == "Fixed Period":
                    if year <= guarantee_years:
                        annuity_income[idx] = annuity_annual
                elif annuity_type == "Life Only":
                    if alive_mask[idx, year - 1]:
                        annuity_income[idx] = annuity_annual
                else:  # Life Contingent with Guarantee
                    if alive_mask[idx, year - 1] or year <= guarantee_years:
                        annuity_income[idx] = annuity_annual

        # Apply COLA to Social Security
        cola_factor = cola_factors[year - 1]
        social_security = base_params.get("social_security", 0)
        current_social_security = social_security * cola_factor

        # Total guaranteed income
        pension = base_params.get("pension", 0)
        guaranteed_income = current_social_security + pension + annuity_income
        total_income_available = guaranteed_income + dividends

        # Calculate inflation-adjusted consumption
        inflation_factor = inflation_factors[year - 1]
        current_consumption = spending_level * inflation_factor

        # Calculate withdrawal needs
        active = alive_mask[:, year] & (portfolio_paths[:, year - 1] > 0)
        withdrawal_need = np.zeros(total_sims)
        withdrawal_need[active] = np.maximum(
            0,
            current_consumption
            + prior_year_tax_liability[active]
            - total_income_available[active],
        )

        # Actual withdrawal (capped at portfolio)
        actual_gross_withdrawal = np.minimum(withdrawal_need, current_portfolio)

        # Calculate realized capital gains
        gain_fraction = np.where(
            current_portfolio > 0,
            np.maximum(0, (current_portfolio - cost_basis) / current_portfolio),
            0,
        )
        realized_gains = actual_gross_withdrawal * gain_fraction

        # Update cost basis
        withdrawal_fraction = np.where(
            current_portfolio > 0, actual_gross_withdrawal / current_portfolio, 0
        )
        cost_basis = cost_basis * (1 - withdrawal_fraction)

        # SINGLE BATCH TAX CALCULATION for ALL scenarios!
        if active.any():
            total_ss_and_pension = current_social_security + pension + annuity_income
            ages_array = np.full(total_sims, age)
            employment_income_array = np.zeros(total_sims)

            # This is the key optimization - ONE tax call for ALL scenarios
            tax_results = tax_calc.calculate_batch_taxes(
                capital_gains_array=realized_gains,
                social_security_array=total_ss_and_pension,
                ages=ages_array,
                filing_status="SINGLE",
                dividend_income_array=dividends,
                employment_income_array=employment_income_array,
            )

            prior_year_tax_liability = tax_results["total_tax"].copy()

            if track_tax_calls:
                tax_calculation_count += 1

        # Update portfolio
        new_portfolio = portfolio_after_growth - actual_gross_withdrawal
        portfolio_paths[:, year] = np.maximum(0, new_portfolio)

    # Calculate results for each scenario
    results = []
    for s_idx, scenario in enumerate(scenarios):
        # Get indices for this scenario
        scenario_mask = scenario_map == s_idx

        # Success = alive with money OR died with money
        scenario_alive = alive_mask[scenario_mask, -1]
        scenario_portfolio = portfolio_paths[scenario_mask, -1]

        alive_with_money = scenario_alive & (scenario_portfolio > 0)
        died_with_money = (~scenario_alive) & (scenario_portfolio > 0)
        total_success = alive_with_money | died_with_money

        success_rate = np.mean(total_success)

        result = {
            "scenario": scenario["name"],
            "spending": spending_level,
            "success_rate": success_rate,
        }

        if track_tax_calls:
            result["tax_calculations"] = tax_calculation_count

        if include_percentiles:
            result["median_final"] = np.median(scenario_portfolio)
            result["p10_final"] = np.percentile(scenario_portfolio, 10)
            result["p25_final"] = np.percentile(scenario_portfolio, 25)
            result["p75_final"] = np.percentile(scenario_portfolio, 75)
            result["p90_final"] = np.percentile(scenario_portfolio, 90)

        results.append(result)

    return results


def analyze_confidence_thresholds(
    results: list[dict[str, Any]], scenario_name: str, confidence_levels: list[int]
) -> dict[int, float]:
    """
    Analyze results to find spending levels at various confidence thresholds.

    Parameters
    ----------
    results : list of dict
        Simulation results
    scenario_name : str
        Name of scenario to analyze
    confidence_levels : list of int
        Confidence levels to find (e.g., [90, 75, 50, 25])

    Returns
    -------
    dict
        Mapping of confidence level to spending amount
    """
    # Filter results for this scenario
    scenario_results = [r for r in results if r["scenario"] == scenario_name]

    if not scenario_results:
        raise ValueError(f"No results found for scenario: {scenario_name}")

    # Sort by spending level
    scenario_results.sort(key=lambda x: x["spending"])

    # Extract arrays for interpolation
    spending_levels = np.array([r["spending"] for r in scenario_results])
    success_rates = np.array([r["success_rate"] for r in scenario_results])

    thresholds = {}
    for confidence in confidence_levels:
        target_rate = confidence / 100.0

        # Handle edge cases
        if target_rate >= success_rates.max():
            thresholds[confidence] = spending_levels[success_rates.argmax()]
        elif target_rate <= success_rates.min():
            thresholds[confidence] = spending_levels[success_rates.argmin()]
        else:
            # Interpolate to find spending level
            # Note: success_rates generally decrease as spending increases
            # So we need to reverse for interpolation
            thresholds[confidence] = np.interp(
                target_rate,
                success_rates[::-1],  # Reverse so it's increasing
                spending_levels[::-1],  # Reverse spending too
            )

    return thresholds


def create_spending_analysis_dataframe(results: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Convert simulation results to a pandas DataFrame for analysis.

    Parameters
    ----------
    results : list of dict
        Simulation results

    Returns
    -------
    pd.DataFrame
        Results as a DataFrame
    """
    return pd.DataFrame(results)


def summarize_confidence_thresholds(
    results: list[dict[str, Any]],
    scenarios: list[str],
    confidence_levels: list[int] = [90, 75, 50, 25, 10],
) -> pd.DataFrame:
    """
    Create a summary table of confidence thresholds for all scenarios.

    Parameters
    ----------
    results : list of dict
        Simulation results
    scenarios : list of str
        Scenario names to include
    confidence_levels : list of int
        Confidence levels to analyze

    Returns
    -------
    pd.DataFrame
        Summary table with scenarios as rows and confidence levels as columns
    """
    summary_data = []

    for scenario_name in scenarios:
        thresholds = analyze_confidence_thresholds(
            results, scenario_name, confidence_levels
        )

        row = {"Scenario": scenario_name}
        for confidence in confidence_levels:
            row[f"{confidence}%"] = thresholds[confidence]

        summary_data.append(row)

    return pd.DataFrame(summary_data)
