"""Tests for stacked simulation functionality."""

import numpy as np

from finsim.stacked_simulation import (
    analyze_confidence_thresholds,
    create_scenario_config,
    simulate_stacked_scenarios,
)


class TestStackedSimulation:
    """Test suite for stacked simulation functionality."""

    def test_create_scenario_config(self):
        """Test creating scenario configuration."""
        config = create_scenario_config(
            name="Test Scenario", initial_portfolio=100_000, has_annuity=False
        )

        assert config["name"] == "Test Scenario"
        assert config["initial_portfolio"] == 100_000
        assert config["has_annuity"] is False

    def test_create_annuity_scenario(self):
        """Test creating scenario with annuity."""
        config = create_scenario_config(
            name="Annuity Test",
            initial_portfolio=50_000,
            has_annuity=True,
            annuity_type="Fixed Period",
            annuity_annual=10_000,
            annuity_guarantee_years=10,
        )

        assert config["has_annuity"] is True
        assert config["annuity_type"] == "Fixed Period"
        assert config["annuity_annual"] == 10_000
        assert config["annuity_guarantee_years"] == 10

    def test_simulate_single_spending_level(self):
        """Test simulating a single spending level across multiple scenarios."""
        scenarios = [
            create_scenario_config("Stocks", 100_000, has_annuity=False),
            create_scenario_config(
                "Annuity",
                50_000,
                has_annuity=True,
                annuity_type="Fixed Period",
                annuity_annual=5_000,
                annuity_guarantee_years=10,
            ),
        ]

        results = simulate_stacked_scenarios(
            scenarios=scenarios,
            spending_levels=[50_000],
            n_simulations=100,
            n_years=10,
            base_params={
                "current_age": 65,
                "gender": "Male",
                "social_security": 20_000,
                "state": "CA",
            },
        )

        # Should have results for each scenario
        assert len(results) == 2

        # Each result should have required fields
        for result in results:
            assert "scenario" in result
            assert "spending" in result
            assert "success_rate" in result
            assert 0 <= result["success_rate"] <= 1
            assert result["spending"] == 50_000

    def test_simulate_multiple_spending_levels(self):
        """Test simulating multiple spending levels."""
        scenarios = [create_scenario_config("Test", 100_000, has_annuity=False)]

        spending_levels = [30_000, 40_000, 50_000]

        results = simulate_stacked_scenarios(
            scenarios=scenarios,
            spending_levels=spending_levels,
            n_simulations=100,
            n_years=10,
            base_params={
                "current_age": 65,
                "gender": "Male",
                "social_security": 20_000,
                "state": "CA",
            },
        )

        # Should have results for each spending level
        assert len(results) == len(spending_levels)

        # Results should be in order
        for i, result in enumerate(results):
            assert result["spending"] == spending_levels[i]

        # Higher spending should generally have lower success rate
        assert results[0]["success_rate"] >= results[-1]["success_rate"]

    def test_stacking_efficiency(self):
        """Test that stacking uses fewer tax calculations."""
        scenarios = [create_scenario_config(f"Scenario{i}", 100_000) for i in range(4)]

        # With stacking, tax calculations should be O(n_years * n_spending)
        # not O(n_scenarios * n_simulations * n_years * n_spending)
        results = simulate_stacked_scenarios(
            scenarios=scenarios,
            spending_levels=[50_000],
            n_simulations=100,
            n_years=10,
            base_params={
                "current_age": 65,
                "gender": "Male",
                "social_security": 20_000,
                "state": "CA",
            },
            track_tax_calls=True,
        )

        # Should track tax calculation count
        assert "tax_calculations" in results[0]
        # Should be much less than n_scenarios * n_simulations * n_years
        expected_max = 10  # n_years for stacked approach
        assert results[0]["tax_calculations"] <= expected_max

    def test_analyze_confidence_thresholds(self):
        """Test analyzing confidence thresholds from results."""
        # Create mock results
        results = [
            {"scenario": "Test", "spending": 30_000, "success_rate": 0.95},
            {"scenario": "Test", "spending": 40_000, "success_rate": 0.85},
            {"scenario": "Test", "spending": 50_000, "success_rate": 0.70},
            {"scenario": "Test", "spending": 60_000, "success_rate": 0.50},
            {"scenario": "Test", "spending": 70_000, "success_rate": 0.30},
        ]

        thresholds = analyze_confidence_thresholds(
            results=results, scenario_name="Test", confidence_levels=[90, 75, 50, 25]
        )

        assert len(thresholds) == 4
        assert 90 in thresholds
        assert 75 in thresholds
        assert 50 in thresholds
        assert 25 in thresholds

        # Should interpolate between points
        assert 30_000 <= thresholds[90] <= 40_000  # ~90% is between 95% and 85%
        assert 40_000 <= thresholds[75] <= 50_000  # ~75% is between 85% and 70%
        assert thresholds[50] == 60_000  # Exact match
        assert thresholds[25] > 60_000  # Below 30% success

    def test_spending_axis_functionality(self):
        """Test that spending can be varied as an axis."""
        scenarios = [create_scenario_config("Stocks", 100_000)]

        # Define spending axis
        spending_axis = np.linspace(30_000, 70_000, 5)

        results = simulate_stacked_scenarios(
            scenarios=scenarios,
            spending_levels=spending_axis.tolist(),
            n_simulations=100,
            n_years=10,
            base_params={
                "current_age": 65,
                "gender": "Male",
                "social_security": 20_000,
                "state": "CA",
            },
        )

        # Should have result for each spending level
        assert len(results) == len(spending_axis)

        # Success rates should generally decrease with spending
        success_rates = [r["success_rate"] for r in results]
        assert success_rates[0] >= success_rates[-1]

    def test_multiple_scenarios_stacked(self):
        """Test that multiple scenarios are properly stacked."""
        scenarios = [
            create_scenario_config("A", 100_000),
            create_scenario_config("B", 150_000),
            create_scenario_config("C", 200_000),
        ]

        results = simulate_stacked_scenarios(
            scenarios=scenarios,
            spending_levels=[50_000],
            n_simulations=100,
            n_years=10,
            base_params={
                "current_age": 65,
                "gender": "Male",
                "social_security": 20_000,
                "state": "CA",
            },
        )

        # Should have result for each scenario
        assert len(results) == 3

        # Scenarios with more money should have higher success rates
        assert results[2]["success_rate"] >= results[0]["success_rate"]

    def test_mortality_handling(self):
        """Test that mortality is properly handled in stacked simulations."""
        scenarios = [create_scenario_config("Test", 100_000)]

        # Run with and without mortality
        results_with = simulate_stacked_scenarios(
            scenarios=scenarios,
            spending_levels=[50_000],
            n_simulations=1000,
            n_years=30,
            base_params={
                "current_age": 65,
                "gender": "Male",
                "social_security": 20_000,
                "state": "CA",
                "include_mortality": True,
            },
        )

        results_without = simulate_stacked_scenarios(
            scenarios=scenarios,
            spending_levels=[50_000],
            n_simulations=1000,
            n_years=30,
            base_params={
                "current_age": 65,
                "gender": "Male",
                "social_security": 20_000,
                "state": "CA",
                "include_mortality": False,
            },
        )

        # With mortality should have different (usually higher) success rate
        # because deaths with money count as success
        assert results_with[0]["success_rate"] != results_without[0]["success_rate"]

    def test_percentile_calculations(self):
        """Test that percentile calculations are included."""
        scenarios = [create_scenario_config("Test", 100_000)]

        results = simulate_stacked_scenarios(
            scenarios=scenarios,
            spending_levels=[50_000],
            n_simulations=1000,
            n_years=10,
            base_params={
                "current_age": 65,
                "gender": "Male",
                "social_security": 20_000,
                "state": "CA",
            },
            include_percentiles=True,
        )

        result = results[0]
        assert "median_final" in result
        assert "p10_final" in result
        assert "p25_final" in result
        assert "p75_final" in result
        assert "p90_final" in result

        # Percentiles should be ordered
        assert result["p10_final"] <= result["p25_final"]
        assert result["p25_final"] <= result["median_final"]
        assert result["median_final"] <= result["p75_final"]
        assert result["p75_final"] <= result["p90_final"]
