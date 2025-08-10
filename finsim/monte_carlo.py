"""Monte Carlo simulator with vectorized tax calculations."""

import warnings

import numpy as np
import pandas as pd

from .tax import TaxCalculator

# Optional imports for enhanced features
try:
    from arch import arch_model

    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False

try:
    import yfinance as yf

    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


class MonteCarloSimulator:
    """
    Monte Carlo simulator for retirement planning with tax-aware withdrawals.

    Features:
    - Vectorized tax calculations via PolicyEngine-US
    - Optional historical data calibration
    - Optional GARCH volatility modeling
    - Regime switching capability
    """

    def __init__(
        self,
        initial_capital: float,
        target_after_tax_monthly: float,
        social_security_monthly: float,
        age: int,
        state: str = "CA",
        filing_status: str = "SINGLE",
        n_simulations: int = 10_000,
        seed: int | None = None,
    ):
        """
        Initialize Monte Carlo simulator.

        Args:
            initial_capital: Starting investment amount
            target_after_tax_monthly: Desired monthly after-tax income
            social_security_monthly: Monthly Social Security benefits
            age: Current age
            state: Two-letter state code
            filing_status: Tax filing status
            n_simulations: Number of simulation paths
            seed: Random seed for reproducibility
        """
        self.initial_capital = initial_capital
        self.target_after_tax_monthly = target_after_tax_monthly
        self.target_after_tax_annual = target_after_tax_monthly * 12
        self.social_security_annual = social_security_monthly * 12
        self.age = age
        self.state = state
        self.filing_status = filing_status
        self.n_simulations = n_simulations

        if seed is not None:
            np.random.seed(seed)

        # Initialize tax calculator
        self.tax_calc = TaxCalculator(state=state)

        # Default market parameters (can be overridden with fit_historical)
        self.annual_return_mean = 0.08
        self.annual_return_std = 0.158
        self.annual_dividend_yield = 0.02
        self.garch_model = None

    def fit_historical(self, ticker: str = "VT", lookback_years: int = 30) -> None:
        """
        Fit parameters to historical data.

        Args:
            ticker: Stock ticker for calibration
            lookback_years: Years of history to use
        """
        if not HAS_YFINANCE:
            warnings.warn("yfinance not installed. Using default parameters.", stacklevel=2)
            return

        try:
            stock = yf.Ticker(ticker)
            end_date = pd.Timestamp.now()
            start_date = end_date - pd.DateOffset(years=lookback_years)
            hist = stock.history(start=start_date, end=end_date)

            if not hist.empty:
                returns = hist["Close"].pct_change().dropna()
                self.annual_return_mean = returns.mean() * 252
                self.annual_return_std = returns.std() * np.sqrt(252)

                # Fit GARCH if available
                if HAS_ARCH:
                    model = arch_model(returns * 100, vol="GARCH", p=1, q=1)
                    self.garch_model = model.fit(disp="off")

        except Exception as e:
            warnings.warn(f"Historical fitting failed: {e}. Using defaults.", stacklevel=2)

    def simulate(
        self,
        n_years: int = 30,
        initial_taxable_fraction: float = 0.2,
        taxable_fraction_increase: float = 0.03,
        cola_rate: float = 0.032,
    ) -> dict:
        """
        Run tax-aware Monte Carlo simulation.

        Args:
            n_years: Simulation horizon in years
            initial_taxable_fraction: Starting fraction of withdrawals that are gains
            taxable_fraction_increase: Annual increase in taxable fraction
            cola_rate: Social Security COLA adjustment rate

        Returns:
            Dictionary with simulation results
        """
        n_months = n_years * 12

        # Initialize arrays
        paths = np.zeros((self.n_simulations, n_months + 1))
        paths[:, 0] = self.initial_capital

        gross_withdrawals = np.zeros((self.n_simulations, n_months))
        taxes_paid = np.zeros((self.n_simulations, n_months))
        depletion_month = np.full(self.n_simulations, np.inf)

        # Generate returns (either normal or GARCH)
        returns = self._generate_returns(n_months)

        # Monthly parameters
        monthly_dividend_yield = self.annual_dividend_yield / 12

        # Process year by year for tax calculations
        for year in range(n_years):
            year_start_month = year * 12
            year_end_month = min((year + 1) * 12, n_months)

            if year_start_month >= n_months:
                break

            # Current year parameters
            current_age = self.age + year
            current_ss = self.social_security_annual * (1 + cola_rate) ** year
            taxable_fraction = min(0.8, initial_taxable_fraction + taxable_fraction_increase * year)

            # Find gross withdrawal needed for target after-tax income
            # Start with estimate
            gross_annual_withdrawal = self.target_after_tax_annual / (1 - 0.15 * taxable_fraction)

            # Iterate to find correct gross amount
            for _ in range(5):  # Usually converges in 2-3 iterations
                capital_gains = np.full(
                    self.n_simulations, gross_annual_withdrawal * taxable_fraction
                )
                ss_array = np.full(self.n_simulations, current_ss)
                age_array = np.full(self.n_simulations, current_age)

                tax_results = self.tax_calc.calculate_batch_taxes(
                    capital_gains_array=capital_gains,
                    social_security_array=ss_array,
                    ages=age_array,
                    filing_status=self.filing_status,
                )

                avg_tax = np.mean(tax_results["total_tax"])
                after_tax = gross_annual_withdrawal - avg_tax

                # Adjust gross withdrawal
                if abs(after_tax - self.target_after_tax_annual) < 100:  # Close enough
                    break
                gross_annual_withdrawal *= self.target_after_tax_annual / after_tax

            monthly_gross_withdrawal = gross_annual_withdrawal / 12

            # Simulate months in this year
            for month in range(year_start_month, year_end_month):
                current_value = paths[:, month]
                active = current_value > 0

                if not np.any(active):
                    continue

                # Portfolio dynamics
                dividends = current_value * monthly_dividend_yield
                growth = current_value * returns[:, month]
                new_value = current_value + growth + dividends - monthly_gross_withdrawal

                # Track depletion
                depleted = (current_value > 0) & (new_value <= 0)
                depletion_month[depleted & (depletion_month == np.inf)] = month + 1

                # Update
                paths[:, month + 1] = np.maximum(0, new_value)
                gross_withdrawals[:, month] = monthly_gross_withdrawal
                taxes_paid[:, month] = avg_tax / 12

        # Calculate results
        final_values = paths[:, -1]
        total_withdrawn = gross_withdrawals.sum(axis=1)
        total_taxes = taxes_paid.sum(axis=1)

        return {
            "paths": paths,
            "final_values": final_values,
            "depletion_month": depletion_month,
            "depletion_probability": np.mean(depletion_month < np.inf),
            "percentiles": {
                "p5": np.percentile(final_values, 5),
                "p25": np.percentile(final_values, 25),
                "p50": np.percentile(final_values, 50),
                "p75": np.percentile(final_values, 75),
                "p95": np.percentile(final_values, 95),
            },
            "gross_withdrawals": gross_withdrawals,
            "taxes_paid": taxes_paid,
            "total_withdrawn": total_withdrawn,
            "total_taxes": total_taxes,
            "mean_final_value": np.mean(final_values),
            "median_final_value": np.median(final_values),
        }

    def _generate_returns(self, n_months: int) -> np.ndarray:
        """Generate return matrix using normal or GARCH model."""
        if self.garch_model and HAS_ARCH:
            # GARCH simulation
            returns = np.zeros((self.n_simulations, n_months))
            params = self.garch_model.params
            omega = params["omega"]
            alpha = params["alpha[1]"]
            beta = params["beta[1]"]

            for sim in range(self.n_simulations):
                h = np.zeros(n_months + 1)
                h[0] = omega / (1 - alpha - beta)

                shocks = np.random.standard_normal(n_months)

                for t in range(n_months):
                    if t > 0:
                        h[t] = omega + alpha * (returns[sim, t - 1] ** 2) + beta * h[t - 1]
                    returns[sim, t] = np.sqrt(h[t]) * shocks[t]

            # Convert to monthly decimal returns
            returns = returns / 100 / np.sqrt(21) + self.annual_return_mean / 12
        else:
            # Standard normal returns
            monthly_mean = self.annual_return_mean / 12
            monthly_std = self.annual_return_std / np.sqrt(12)
            returns = np.random.normal(monthly_mean, monthly_std, (self.n_simulations, n_months))

        return returns

    def compare_to_annuity(
        self,
        annuity_monthly_payment: float,
        annuity_guarantee_years: int,
        simulation_results: dict | None = None,
    ) -> dict:
        """
        Compare Monte Carlo results to an annuity option.

        Args:
            annuity_monthly_payment: Monthly annuity payment
            annuity_guarantee_years: Guaranteed payment period
            simulation_results: Pre-computed simulation results

        Returns:
            Comparison metrics
        """
        if simulation_results is None:
            simulation_results = self.simulate(n_years=annuity_guarantee_years)

        # Annuity total payments (tax-free)
        annuity_total = annuity_monthly_payment * 12 * annuity_guarantee_years

        # Monte Carlo statistics
        mc_total_after_tax = (
            simulation_results["total_withdrawn"] - simulation_results["total_taxes"]
        )

        return {
            "annuity_total_guaranteed": annuity_total,
            "mc_median_total_after_tax": np.median(mc_total_after_tax),
            "mc_mean_total_after_tax": np.mean(mc_total_after_tax),
            "probability_mc_exceeds_annuity": np.mean(mc_total_after_tax > annuity_total),
            "mc_depletion_probability": simulation_results["depletion_probability"],
            "mc_median_final_value": simulation_results["median_final_value"],
        }
