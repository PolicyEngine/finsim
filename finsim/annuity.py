"""Annuity calculations and comparisons."""

import numpy_financial as npf
import pandas as pd
from scipy import optimize


class AnnuityCalculator:
    """Calculate annuity values and compare with alternatives."""

    # CDC 2022 life table data for males
    # Source: https://www.cdc.gov/nchs/data/nvsr/nvsr73/nvsr73-05.pdf
    MALE_LIFE_TABLE = {
        65: 17.54,  # Life expectancy at 65
        66: 16.73,
        67: 15.93,
        68: 15.14,
        69: 14.37,
        70: 13.61,
        71: 12.87,
        72: 12.14,
        73: 11.43,
        74: 10.74,
        75: 10.07,
        76: 9.42,
        77: 8.79,
        78: 8.18,
        79: 7.60,
        80: 7.04,
        85: 4.98,
        90: 3.55,
        95: 2.65,
        100: 2.08,
    }

    def __init__(self, age: int = 65, gender: str = "male"):
        """
        Initialize annuity calculator.

        Args:
            age: Current age
            gender: Gender for mortality tables
        """
        self.age = age
        self.gender = gender

    def calculate_irr(
        self,
        premium: float,
        monthly_payment: float,
        guarantee_months: int,
        life_contingent: bool = False,
    ) -> float:
        """
        Calculate internal rate of return for an annuity.

        Args:
            premium: Upfront premium payment
            monthly_payment: Monthly benefit payment
            guarantee_months: Guaranteed payment period in months
            life_contingent: Whether payments continue for life after guarantee

        Returns:
            Annual internal rate of return
        """
        # Handle edge case of no guarantee period for non-life-contingent annuities
        if not life_contingent and guarantee_months == 0:
            return -1.0  # Complete loss if no payments

        if not life_contingent:
            # Simple case: fixed term annuity
            cash_flows = [-premium] + [monthly_payment] * guarantee_months

            # Use numpy_financial's IRR calculation
            try:
                monthly_irr = npf.irr(cash_flows)
                annual_irr = (1 + monthly_irr) ** 12 - 1
                return annual_irr
            except Exception:
                # If np.irr fails, use scipy optimize
                def npv(rate):
                    return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))

                try:
                    monthly_irr = optimize.brentq(npv, -0.99, 10, xtol=1e-6)
                    annual_irr = (1 + monthly_irr) ** 12 - 1
                    return annual_irr
                except Exception:
                    # If optimization fails, return approximation
                    total_payments = monthly_payment * guarantee_months
                    if premium == 0:
                        return 0.0
                    if guarantee_months > 0:
                        return (total_payments / premium) ** (12 / guarantee_months) - 1
                    return -1.0
        else:
            # Life contingent annuity - use survival probabilities
            return self._calculate_life_contingent_irr(
                premium, monthly_payment, guarantee_months
            )

    def _calculate_life_contingent_irr(
        self, premium: float, monthly_payment: float, guarantee_months: int
    ) -> float:
        """
        Calculate IRR for life-contingent annuity using mortality tables.

        Args:
            premium: Upfront premium
            monthly_payment: Monthly payment
            guarantee_months: Guaranteed period

        Returns:
            Expected IRR based on mortality
        """
        # Get life expectancy
        life_expectancy_years = self.MALE_LIFE_TABLE.get(self.age, 15)
        expected_months = int(life_expectancy_years * 12)

        # Create probability-weighted cash flows
        cash_flows = [-premium]

        # Guaranteed period - 100% probability
        for _ in range(min(guarantee_months, expected_months)):
            cash_flows.append(monthly_payment)

        # Post-guarantee period - declining probability
        if expected_months > guarantee_months:
            # Simple linear decline in survival probability
            for month in range(guarantee_months, expected_months):
                survival_prob = 1.0 - (month - guarantee_months) / (expected_months * 2)
                survival_prob = max(0, survival_prob)
                cash_flows.append(monthly_payment * survival_prob)

        # Calculate IRR
        try:
            monthly_irr = npf.irr(cash_flows)
            annual_irr = (1 + monthly_irr) ** 12 - 1
            return annual_irr
        except Exception:
            # Fallback calculation
            def npv(rate):
                return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))

            try:
                monthly_irr = optimize.brentq(npv, -0.99, 0.5, xtol=1e-6)
                annual_irr = (1 + monthly_irr) ** 12 - 1
                return annual_irr
            except Exception:
                # If optimization fails, return simple approximation
                total_expected = sum(cash_flows[1:])
                years = len(cash_flows) / 12
                return (total_expected / premium) ** (1 / years) - 1

    def compare_annuity_options(self, proposals: list) -> pd.DataFrame:
        """
        Compare multiple annuity proposals.

        Args:
            proposals: List of dictionaries with annuity details

        Returns:
            DataFrame with comparison metrics
        """
        results = []

        for proposal in proposals:
            irr = self.calculate_irr(
                premium=proposal["premium"],
                monthly_payment=proposal["monthly_payment"],
                guarantee_months=proposal.get("guarantee_months", 0),
                life_contingent=proposal.get("life_contingent", False),
            )

            total_guaranteed = proposal["monthly_payment"] * proposal.get(
                "guarantee_months", 0
            )

            results.append(
                {
                    "Name": proposal["name"],
                    "Premium": proposal["premium"],
                    "Monthly Payment": proposal["monthly_payment"],
                    "Annual Payment": proposal["monthly_payment"] * 12,
                    "Guarantee Period": proposal.get("guarantee_months", 0) / 12,
                    "Life Contingent": proposal.get("life_contingent", False),
                    "Total Guaranteed": total_guaranteed,
                    "IRR": irr,
                    "Taxable": proposal.get("taxable", False),
                }
            )

        return pd.DataFrame(results)

    def calculate_present_value(
        self, monthly_payment: float, months: int, discount_rate: float
    ) -> float:
        """
        Calculate present value of annuity payments.

        Args:
            monthly_payment: Monthly payment amount
            months: Number of months
            discount_rate: Annual discount rate

        Returns:
            Present value
        """
        monthly_rate = (1 + discount_rate) ** (1 / 12) - 1

        if monthly_rate == 0:
            return monthly_payment * months

        pv = monthly_payment * (1 - (1 + monthly_rate) ** -months) / monthly_rate
        return pv
