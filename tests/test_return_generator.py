#!/usr/bin/env python3
"""Test suite for return generation module."""

import numpy as np

from finsim.return_generator import ReturnGenerator


class TestReturnGenerator:
    """Test the return generator functionality."""

    def test_matrix_shape(self):
        """Test that the return matrix has correct shape."""
        gen = ReturnGenerator(expected_return=0.07, volatility=0.15)
        returns = gen.generate_returns(n_simulations=100, n_years=30)

        assert returns.shape == (100, 30), f"Expected shape (100, 30), got {returns.shape}"

    def test_no_repeated_values(self):
        """Test that simulations don't get stuck with repeated values."""
        gen = ReturnGenerator(expected_return=0.07, volatility=0.15)
        returns = gen.generate_returns(n_simulations=100, n_years=30)

        # Check each simulation for repeated values
        for sim_idx in range(100):
            sim_returns = returns[sim_idx, :]
            unique_returns = np.unique(np.round(sim_returns, 6))

            # Should have at least 25 unique values out of 30 years
            # (allowing for some legitimate duplicates by chance)
            assert (
                len(unique_returns) >= 25
            ), f"Simulation {sim_idx} has only {len(unique_returns)} unique returns"

    def test_return_distribution(self):
        """Test that returns follow expected distribution."""
        gen = ReturnGenerator(expected_return=0.07, volatility=0.15)
        returns = gen.generate_returns(n_simulations=10000, n_years=1)

        # Flatten to get all returns
        all_returns = returns.flatten()

        # Convert to annual returns (from growth factors)
        annual_returns = all_returns - 1

        # Check mean is close to expected (within 2%)
        mean_return = np.mean(annual_returns)
        assert (
            abs(mean_return - 0.07) < 0.02
        ), f"Mean return {mean_return:.3f} too far from expected 0.07"

        # Check volatility is close to expected (within 3% - allows for fat tails)
        std_return = np.std(annual_returns)
        assert (
            abs(std_return - 0.15) < 0.03
        ), f"Volatility {std_return:.3f} too far from expected 0.15"

    def test_no_extreme_outliers(self):
        """Test that returns don't have unrealistic extremes."""
        gen = ReturnGenerator(expected_return=0.07, volatility=0.15)
        returns = gen.generate_returns(n_simulations=1000, n_years=30)

        # No single-year return should exceed 100% gain or 50% loss
        assert np.all(returns < 2.0), "Found returns exceeding 100% gain"
        assert np.all(returns > 0.5), "Found returns exceeding 50% loss"

        # Check compound growth over 30 years
        # Starting with $1, compound returns
        final_values = np.prod(returns, axis=1)

        # No portfolio should grow more than 100x over 30 years
        # (that would require ~16% annual returns consistently)
        assert np.all(
            final_values < 100
        ), f"Max final value {np.max(final_values):.0f}x is unrealistic"

    def test_independence_across_simulations(self):
        """Test that different simulations are independent."""
        gen = ReturnGenerator(expected_return=0.07, volatility=0.15, seed=42)
        returns = gen.generate_returns(n_simulations=100, n_years=30)

        # Check correlation between different simulations
        # With more years, correlations should be smaller
        correlations = []
        for i in range(min(10, 100)):
            for j in range(i + 1, min(10, 100)):
                corr = np.corrcoef(returns[i, :], returns[j, :])[0, 1]
                correlations.append(abs(corr))
        
        # Average correlation should be very low
        avg_corr = np.mean(correlations)
        assert avg_corr < 0.20, f"Average correlation {avg_corr:.3f} too high"
        
        # No individual correlation should be extreme
        max_corr = np.max(correlations)
        assert max_corr < 0.5, f"Max correlation {max_corr:.3f} too high"

    def test_independence_across_years(self):
        """Test that returns are independent across years."""
        gen = ReturnGenerator(expected_return=0.07, volatility=0.15)
        returns = gen.generate_returns(n_simulations=1000, n_years=10)

        # Check correlation between consecutive years
        # Should be near zero for each simulation
        for year in range(9):
            year_returns = returns[:, year]
            next_year_returns = returns[:, year + 1]
            corr = np.corrcoef(year_returns, next_year_returns)[0, 1]
            assert abs(corr) < 0.1, f"Years {year} and {year+1} have correlation {corr:.3f}"

    def test_reproducibility_with_seed(self):
        """Test that setting seed gives reproducible results."""
        gen1 = ReturnGenerator(expected_return=0.07, volatility=0.15, seed=42)
        returns1 = gen1.generate_returns(n_simulations=10, n_years=5)

        gen2 = ReturnGenerator(expected_return=0.07, volatility=0.15, seed=42)
        returns2 = gen2.generate_returns(n_simulations=10, n_years=5)

        assert np.allclose(returns1, returns2), "Same seed should give same results"

    def test_different_seeds_give_different_results(self):
        """Test that different seeds give different results."""
        gen1 = ReturnGenerator(expected_return=0.07, volatility=0.15, seed=42)
        returns1 = gen1.generate_returns(n_simulations=10, n_years=5)

        gen2 = ReturnGenerator(expected_return=0.07, volatility=0.15, seed=43)
        returns2 = gen2.generate_returns(n_simulations=10, n_years=5)

        assert not np.allclose(returns1, returns2), "Different seeds should give different results"

    def test_fat_tails_present(self):
        """Test that distribution has some fat tails (kurtosis > 3)."""
        gen = ReturnGenerator(expected_return=0.07, volatility=0.15)
        returns = gen.generate_returns(n_simulations=10000, n_years=1)

        # Calculate log returns
        log_returns = np.log(returns.flatten())

        # Check kurtosis is slightly above 3 (normal distribution)
        # But not too extreme
        from scipy import stats

        kurt = stats.kurtosis(log_returns)
        assert kurt > 0, f"Kurtosis {kurt:.2f} suggests no fat tails"
        assert kurt < 10, f"Kurtosis {kurt:.2f} suggests unrealistic fat tails"


if __name__ == "__main__":
    # Run tests
    test = TestReturnGenerator()

    print("Running return generator tests...")
    print("=" * 60)

    try:
        test.test_matrix_shape()
        print("✓ Matrix shape test passed")
    except AssertionError as e:
        print(f"✗ Matrix shape test failed: {e}")

    try:
        test.test_no_repeated_values()
        print("✓ No repeated values test passed")
    except AssertionError as e:
        print(f"✗ No repeated values test failed: {e}")

    try:
        test.test_return_distribution()
        print("✓ Return distribution test passed")
    except AssertionError as e:
        print(f"✗ Return distribution test failed: {e}")

    try:
        test.test_no_extreme_outliers()
        print("✓ No extreme outliers test passed")
    except AssertionError as e:
        print(f"✗ No extreme outliers test failed: {e}")

    try:
        test.test_independence_across_simulations()
        print("✓ Independence across simulations test passed")
    except AssertionError as e:
        print(f"✗ Independence across simulations test failed: {e}")

    try:
        test.test_independence_across_years()
        print("✓ Independence across years test passed")
    except AssertionError as e:
        print(f"✗ Independence across years test failed: {e}")

    try:
        test.test_reproducibility_with_seed()
        print("✓ Reproducibility test passed")
    except AssertionError as e:
        print(f"✗ Reproducibility test failed: {e}")

    try:
        test.test_different_seeds_give_different_results()
        print("✓ Different seeds test passed")
    except AssertionError as e:
        print(f"✗ Different seeds test failed: {e}")

    try:
        test.test_fat_tails_present()
        print("✓ Fat tails test passed")
    except AssertionError as e:
        print(f"✗ Fat tails test failed: {e}")

    print("=" * 60)
    print("All tests completed!")
