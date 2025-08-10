"""Tests for input validation in portfolio simulation."""

import pytest

from finsim.portfolio_simulation import validate_inputs


class TestInputValidation:
    """Test input validation for portfolio simulation."""

    def get_valid_params(self):
        """Return a set of valid parameters for testing."""
        return {
            "n_simulations": 100,
            "n_years": 30,
            "initial_portfolio": 1_000_000,
            "current_age": 65,
            "social_security": 30_000,
            "pension": 10_000,
            "employment_income": 0,
            "retirement_age": 65,
            "annuity_annual": 0,
            "annuity_guarantee_years": 0,
            "annual_consumption": 60_000,
            "expected_return": 0.07,
            "return_volatility": 0.15,
            "dividend_yield": 0.02,
            "state": "CA",
            "gender": "Male",
            "annuity_type": "Life Only",
            "has_spouse": False,
        }

    def test_valid_inputs(self):
        """Test that valid inputs pass validation."""
        params = self.get_valid_params()
        # Should not raise any exception
        validate_inputs(**params)

    def test_negative_simulations(self):
        """Test that negative n_simulations raises ValueError."""
        params = self.get_valid_params()
        params["n_simulations"] = -1
        with pytest.raises(ValueError, match="n_simulations must be positive"):
            validate_inputs(**params)

    def test_excessive_simulations(self):
        """Test that too many simulations raises ValueError."""
        params = self.get_valid_params()
        params["n_simulations"] = 200_000
        with pytest.raises(ValueError, match="n_simulations too large"):
            validate_inputs(**params)

    def test_negative_years(self):
        """Test that negative n_years raises ValueError."""
        params = self.get_valid_params()
        params["n_years"] = -5
        with pytest.raises(ValueError, match="n_years must be positive"):
            validate_inputs(**params)

    def test_excessive_years(self):
        """Test that too many years raises ValueError."""
        params = self.get_valid_params()
        params["n_years"] = 150
        with pytest.raises(ValueError, match="n_years too large"):
            validate_inputs(**params)

    def test_negative_portfolio(self):
        """Test that negative initial_portfolio raises ValueError."""
        params = self.get_valid_params()
        params["initial_portfolio"] = -100_000
        with pytest.raises(ValueError, match="initial_portfolio cannot be negative"):
            validate_inputs(**params)

    def test_excessive_portfolio(self):
        """Test that excessive initial_portfolio raises ValueError."""
        params = self.get_valid_params()
        params["initial_portfolio"] = 100_000_000_000  # $100 billion
        with pytest.raises(ValueError, match="initial_portfolio too large"):
            validate_inputs(**params)

    def test_underage_person(self):
        """Test that age under 18 raises ValueError."""
        params = self.get_valid_params()
        params["current_age"] = 16
        with pytest.raises(ValueError, match="current_age must be at least 18"):
            validate_inputs(**params)

    def test_excessive_age(self):
        """Test that age over 120 raises ValueError."""
        params = self.get_valid_params()
        params["current_age"] = 125
        with pytest.raises(ValueError, match="current_age cannot exceed 120"):
            validate_inputs(**params)

    def test_retirement_before_current_age(self):
        """Test that retirement_age < current_age raises ValueError."""
        params = self.get_valid_params()
        params["current_age"] = 65
        params["retirement_age"] = 60
        with pytest.raises(ValueError, match="retirement_age .* cannot be less than current_age"):
            validate_inputs(**params)

    def test_negative_social_security(self):
        """Test that negative social_security raises ValueError."""
        params = self.get_valid_params()
        params["social_security"] = -1000
        with pytest.raises(ValueError, match="social_security cannot be negative"):
            validate_inputs(**params)

    def test_excessive_social_security(self):
        """Test that unrealistic social_security raises ValueError."""
        params = self.get_valid_params()
        params["social_security"] = 500_000
        with pytest.raises(ValueError, match="social_security seems unrealistic"):
            validate_inputs(**params)

    def test_negative_consumption(self):
        """Test that negative annual_consumption raises ValueError."""
        params = self.get_valid_params()
        params["annual_consumption"] = -5000
        with pytest.raises(ValueError, match="annual_consumption cannot be negative"):
            validate_inputs(**params)

    def test_excessive_return(self):
        """Test that excessive expected_return raises ValueError."""
        params = self.get_valid_params()
        params["expected_return"] = 0.75  # 75%
        with pytest.raises(ValueError, match="expected_return too high"):
            validate_inputs(**params)

    def test_very_negative_return(self):
        """Test that very negative expected_return raises ValueError."""
        params = self.get_valid_params()
        params["expected_return"] = -0.75  # -75%
        with pytest.raises(ValueError, match="expected_return too low"):
            validate_inputs(**params)

    def test_negative_volatility(self):
        """Test that negative return_volatility raises ValueError."""
        params = self.get_valid_params()
        params["return_volatility"] = -0.1
        with pytest.raises(ValueError, match="return_volatility cannot be negative"):
            validate_inputs(**params)

    def test_excessive_volatility(self):
        """Test that excessive return_volatility raises ValueError."""
        params = self.get_valid_params()
        params["return_volatility"] = 1.5  # 150%
        with pytest.raises(ValueError, match="return_volatility too high"):
            validate_inputs(**params)

    def test_invalid_state(self):
        """Test that invalid state code raises ValueError."""
        params = self.get_valid_params()
        params["state"] = "ZZ"
        with pytest.raises(ValueError, match="Invalid state"):
            validate_inputs(**params)

    def test_invalid_gender(self):
        """Test that invalid gender raises ValueError."""
        params = self.get_valid_params()
        params["gender"] = "Other"
        with pytest.raises(ValueError, match="Invalid gender"):
            validate_inputs(**params)

    def test_invalid_annuity_type(self):
        """Test that invalid annuity_type raises ValueError."""
        params = self.get_valid_params()
        params["annuity_type"] = "Unknown Type"
        with pytest.raises(ValueError, match="Invalid annuity_type"):
            validate_inputs(**params)

    def test_spouse_without_required_fields(self):
        """Test that has_spouse=True without spouse_age raises ValueError."""
        params = self.get_valid_params()
        params["has_spouse"] = True
        # Don't provide spouse_age
        with pytest.raises(ValueError, match="spouse_age is required"):
            validate_inputs(**params)

    def test_spouse_with_valid_fields(self):
        """Test that has_spouse=True with valid spouse fields passes."""
        params = self.get_valid_params()
        params["has_spouse"] = True
        params["spouse_age"] = 63
        params["spouse_gender"] = "Female"
        params["spouse_social_security"] = 20_000
        params["spouse_pension"] = 5_000
        params["spouse_employment_income"] = 0
        params["spouse_retirement_age"] = 65
        # Should not raise any exception
        validate_inputs(**params)

    def test_spouse_negative_income(self):
        """Test that negative spouse income raises ValueError."""
        params = self.get_valid_params()
        params["has_spouse"] = True
        params["spouse_age"] = 63
        params["spouse_gender"] = "Female"
        params["spouse_social_security"] = -5_000
        with pytest.raises(ValueError, match="spouse_social_security cannot be negative"):
            validate_inputs(**params)

    def test_spouse_retirement_before_age(self):
        """Test that spouse_retirement_age < spouse_age raises ValueError."""
        params = self.get_valid_params()
        params["has_spouse"] = True
        params["spouse_age"] = 65
        params["spouse_gender"] = "Female"
        params["spouse_retirement_age"] = 60
        with pytest.raises(
            ValueError, match="spouse_retirement_age .* cannot be less than spouse_age"
        ):
            validate_inputs(**params)

    def test_all_valid_states(self):
        """Test that all US states are accepted."""
        params = self.get_valid_params()
        states = [
            "AL",
            "AK",
            "AZ",
            "AR",
            "CA",
            "CO",
            "CT",
            "DE",
            "FL",
            "GA",
            "HI",
            "ID",
            "IL",
            "IN",
            "IA",
            "KS",
            "KY",
            "LA",
            "ME",
            "MD",
            "MA",
            "MI",
            "MN",
            "MS",
            "MO",
            "MT",
            "NE",
            "NV",
            "NH",
            "NJ",
            "NM",
            "NY",
            "NC",
            "ND",
            "OH",
            "OK",
            "OR",
            "PA",
            "RI",
            "SC",
            "SD",
            "TN",
            "TX",
            "UT",
            "VT",
            "VA",
            "WA",
            "WV",
            "WI",
            "WY",
            "DC",
        ]
        for state in states:
            params["state"] = state
            # Should not raise any exception
            validate_inputs(**params)

    def test_edge_case_values(self):
        """Test edge case values that should be valid."""
        params = self.get_valid_params()

        # Test minimum valid values
        params["n_simulations"] = 1
        params["n_years"] = 1
        params["initial_portfolio"] = 0
        params["current_age"] = 18
        params["social_security"] = 0
        params["annual_consumption"] = 0
        params["expected_return"] = -0.5
        params["return_volatility"] = 0
        params["dividend_yield"] = 0

        # Should not raise any exception
        validate_inputs(**params)

        # Test maximum valid values
        params["n_simulations"] = 100_000
        params["n_years"] = 100
        params["initial_portfolio"] = 9_999_999_999
        params["current_age"] = 60
        params["retirement_age"] = 100  # Max allowed retirement age
        params["expected_return"] = 0.5
        params["return_volatility"] = 1.0
        params["dividend_yield"] = 0.2

        # Should not raise any exception
        validate_inputs(**params)
