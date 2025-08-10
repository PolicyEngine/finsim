"""Tests for portfolio simulation module."""

import numpy as np
import pytest

from finsim.portfolio_simulation import simulate_portfolio


class TestPortfolioSimulation:
    @pytest.fixture
    def basic_params(self):
        """Basic parameters for testing."""
        return {
            'n_simulations': 100,
            'n_years': 10,
            'initial_portfolio': 500_000,
            'current_age': 65,
            'include_mortality': False,
            'social_security': 24_000,
            'pension': 10_000,
            'employment_income': 0,
            'retirement_age': 65,
            'has_annuity': False,
            'annuity_type': 'Fixed Period',
            'annuity_annual': 0,
            'annuity_guarantee_years': 0,
            'annual_consumption': 60_000,
            'expected_return': 7.0,
            'return_volatility': 15.0,
            'dividend_yield': 2.0,
            'state': 'CA',
        }

    def test_basic_simulation(self, basic_params):
        """Test basic simulation runs without errors."""
        results = simulate_portfolio(**basic_params)

        # Check all expected keys are present
        expected_keys = [
            'portfolio_paths', 'failure_year', 'alive_mask',
            'estate_at_death', 'annuity_income', 'dividend_income',
            'capital_gains', 'gross_withdrawals', 'taxes_owed',
            'taxes_paid', 'net_withdrawals', 'cost_basis'
        ]
        for key in expected_keys:
            assert key in results

        # Check shapes
        n_sims = basic_params['n_simulations']
        n_years = basic_params['n_years']
        assert results['portfolio_paths'].shape == (n_sims, n_years + 1)
        assert results['failure_year'].shape == (n_sims,)
        assert results['dividend_income'].shape == (n_sims, n_years)

    def test_portfolio_paths_start_value(self, basic_params):
        """Test that portfolios start at the initial value."""
        results = simulate_portfolio(**basic_params)

        # All portfolios should start at initial value
        initial_values = results['portfolio_paths'][:, 0]
        assert np.all(initial_values == basic_params['initial_portfolio'])

    def test_portfolio_growth_reasonable(self, basic_params):
        """Test that portfolio growth is reasonable."""
        results = simulate_portfolio(**basic_params)

        # Get final values for successful portfolios
        final_values = results['portfolio_paths'][:, -1]
        successful = final_values > 0

        if np.any(successful):
            # Some should grow, some should shrink
            median_final = np.median(final_values[successful])
            _initial = basic_params['initial_portfolio']

            # With 7% returns, 60k consumption, 34k income
            # Net withdrawal ~26k/year from 500k
            # Should be sustainable but declining
            assert 100_000 < median_final < 800_000

    def test_failure_tracking(self, basic_params):
        """Test that failures are tracked correctly."""
        # Set high consumption to force failures
        params = basic_params.copy()
        params['annual_consumption'] = 150_000
        params['social_security'] = 0
        params['pension'] = 0

        results = simulate_portfolio(**params)

        # Most should fail with such high consumption
        failures = results['failure_year'] <= params['n_years']
        assert np.sum(failures) > params['n_simulations'] * 0.8

        # Failure years should be reasonable
        failure_years = results['failure_year'][failures]
        assert np.all(failure_years >= 1)
        assert np.all(failure_years <= params['n_years'])

    def test_employment_income(self, basic_params):
        """Test that employment income is handled correctly."""
        params = basic_params.copy()
        params['employment_income'] = 100_000
        params['current_age'] = 55
        params['retirement_age'] = 65

        results = simulate_portfolio(**params)

        # With high employment income, portfolios should grow initially
        # Check that portfolios generally increase in early years
        early_growth = (\
            results['portfolio_paths'][:, 5] > results['portfolio_paths'][:, 0]
        )
        assert np.mean(early_growth) > 0.7  # Most should grow

    def test_dividend_income_calculation(self, basic_params):
        """Test dividend income calculation."""
        results = simulate_portfolio(**basic_params)

        # First year dividends should be 2% of initial portfolio
        expected_first_dividend = basic_params['initial_portfolio'] * 0.02
        first_year_dividends = results['dividend_income'][:, 0]

        # Should be close (some variation due to mortality/failures)
        assert np.allclose(
            first_year_dividends[first_year_dividends > 0],
            expected_first_dividend,
            rtol=0.01
        )

    def test_tax_calculation(self, basic_params):
        """Test that taxes are calculated and positive."""
        results = simulate_portfolio(**basic_params)

        # Taxes should be calculated
        taxes_owed = results['taxes_owed']

        # Should have some positive taxes
        assert np.any(taxes_owed > 0)

        # Taxes should be reasonable (not extreme)
        max_tax = np.max(taxes_owed)
        assert max_tax < 100_000  # Reasonable upper bound

    def test_withdrawal_calculation(self, basic_params):
        """Test withdrawal calculations."""
        results = simulate_portfolio(**basic_params)

        gross_withdrawals = results['gross_withdrawals']

        # Withdrawals should be positive for most simulations
        assert np.any(gross_withdrawals > 0)

        # Net withdrawals should be less than gross (due to taxes)
        net_withdrawals = results['net_withdrawals']

        # In year 2+, net should be less than gross due to taxes
        year_2_gross = gross_withdrawals[:, 1]
        year_2_net = net_withdrawals[:, 1]
        positive_withdrawals = year_2_gross > 0

        if np.any(positive_withdrawals):
            # Net should be less than or equal to gross
            assert np.all(
                year_2_net[positive_withdrawals] <= year_2_gross[positive_withdrawals]
            )

    def test_cost_basis_tracking(self, basic_params):
        """Test that cost basis is tracked correctly."""
        results = simulate_portfolio(**basic_params)

        # Cost basis should start at initial portfolio value
        initial_cost_basis = basic_params['initial_portfolio']

        # Cost basis should decrease with withdrawals
        # (It's tracked as final cost basis after all withdrawals)
        final_cost_basis = results['cost_basis']

        # Should be non-negative
        assert np.all(final_cost_basis >= 0)

        # Should be less than or equal to initial for those with withdrawals
        assert np.all(final_cost_basis <= initial_cost_basis)

    def test_annuity_fixed_period(self, basic_params):
        """Test fixed period annuity."""
        params = basic_params.copy()
        params['has_annuity'] = True
        params['annuity_type'] = 'Fixed Period'
        params['annuity_annual'] = 20_000
        params['annuity_guarantee_years'] = 5

        results = simulate_portfolio(**params)

        annuity_income = results['annuity_income']

        # Should have annuity for first 5 years
        assert np.all(annuity_income[:, :5] == 20_000)

        # Should have no annuity after 5 years
        assert np.all(annuity_income[:, 5:] == 0)

    def test_annuity_life_only(self, basic_params):
        """Test life-only annuity with mortality."""
        params = basic_params.copy()
        params['has_annuity'] = True
        params['annuity_type'] = 'Life Only'
        params['annuity_annual'] = 20_000
        params['include_mortality'] = True

        results = simulate_portfolio(**params)

        annuity_income = results['annuity_income']
        alive_mask = results['alive_mask']

        # Annuity should match alive status
        for i in range(params['n_simulations']):
            for j in range(params['n_years']):
                if alive_mask[i, j]:
                    assert annuity_income[i, j] == 20_000
                else:
                    assert annuity_income[i, j] == 0

    def test_extreme_volatility(self, basic_params):
        """Test simulation with extreme volatility."""
        params = basic_params.copy()
        params['return_volatility'] = 50.0  # Very high volatility

        results = simulate_portfolio(**params)

        # Should have wide range of outcomes
        final_values = results['portfolio_paths'][:, -1]
        successful = final_values > 0

        if np.sum(successful) > 10:
            # Check for wide dispersion
            percentile_95 = np.percentile(final_values[successful], 95)
            percentile_5 = np.percentile(final_values[successful], 5)

            # High volatility should create large spread
            assert percentile_95 / (percentile_5 + 1) > 5

    def test_zero_portfolio_start(self):
        """Test starting with zero portfolio."""
        params = {
            'n_simulations': 10,
            'n_years': 5,
            'initial_portfolio': 0,
            'current_age': 65,
            'include_mortality': False,
            'social_security': 24_000,
            'pension': 10_000,
            'employment_income': 0,
            'retirement_age': 65,
            'has_annuity': False,
            'annuity_type': 'Fixed Period',
            'annuity_annual': 0,
            'annuity_guarantee_years': 0,
            'annual_consumption': 30_000,  # Less than income
            'expected_return': 7.0,
            'return_volatility': 15.0,
            'dividend_yield': 2.0,
            'state': 'CA',
        }

        results = simulate_portfolio(**params)

        # Should handle zero portfolio gracefully
        assert results['portfolio_paths'].shape == (10, 6)

        # With income > consumption, might accumulate
        final_values = results['portfolio_paths'][:, -1]
        assert np.all(final_values >= 0)

