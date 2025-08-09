"""Core retirement simulation module."""

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any
import numpy as np
from pathlib import Path
import json


@dataclass
class SimulationConfig:
    """Configuration for retirement simulation."""
    
    # Required parameters (no defaults)
    current_age: int
    retirement_age: int
    max_age: int
    initial_portfolio: float
    annual_consumption: float
    social_security: float
    
    # Optional parameters (with defaults)
    gender: str = "Male"
    pension: float = 0
    
    # Annuity parameters
    annuity_annual: float = 0
    annuity_type: Optional[str] = None
    annuity_guarantee_years: int = 0
    
    # Market assumptions (all in real terms)
    expected_return: float = 5.0  # % per year
    return_volatility: float = 16.0  # % per year
    dividend_yield: float = 2.0  # % per year
    
    # Tax assumptions
    effective_tax_rate: float = 15.0  # % on withdrawals
    
    # Simulation settings
    n_simulations: int = 1000
    include_mortality: bool = True
    random_seed: Optional[int] = None
    
    @property
    def guaranteed_income(self) -> float:
        """Total guaranteed annual income."""
        return self.social_security + self.pension + self.annuity_annual
    
    @property
    def net_consumption_need(self) -> float:
        """Net amount needed from portfolio after guaranteed income."""
        return self.annual_consumption - self.guaranteed_income


@dataclass
class SimulationResult:
    """Results from a single simulation path."""
    
    portfolio_values: np.ndarray
    dividend_income: np.ndarray
    withdrawals: np.ndarray
    taxes_paid: np.ndarray
    annuity_income: np.ndarray
    failure_year: Optional[int] = None
    alive_mask: Optional[np.ndarray] = None


@dataclass 
class MonteCarloResults:
    """Results from Monte Carlo simulation."""
    
    n_simulations: int
    portfolio_paths: np.ndarray
    success_rate: float
    percentiles: Dict[int, np.ndarray]
    failure_years: np.ndarray
    alive_mask: np.ndarray
    dividend_income: np.ndarray
    withdrawals: np.ndarray
    taxes_paid: np.ndarray
    annuity_income: np.ndarray


class RetirementSimulation:
    """Run retirement Monte Carlo simulations."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize simulation with config."""
        self.config = config
        self.n_years = config.max_age - config.current_age
        self._load_mortality_data()
        
        if config.random_seed is not None:
            np.random.seed(config.random_seed)
    
    def _load_mortality_data(self):
        """Load SSA mortality tables."""
        data_path = Path(__file__).parent / "data" / "ssa_mortality.json"
        
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        # Convert string keys to integers
        if self.config.gender == "Male":
            self.mortality_rates = {int(k): v for k, v in data["male"].items()}
        else:
            self.mortality_rates = {int(k): v for k, v in data["female"].items()}
    
    def _get_mortality_rate(self, age: int) -> float:
        """Get mortality rate for a given age."""
        if not self.config.include_mortality:
            return 0.0
        
        # Interpolate if age not in table
        ages = sorted(self.mortality_rates.keys())
        if age < ages[0]:
            return 0.0
        if age > ages[-1]:
            return self.mortality_rates[ages[-1]]
        
        return np.interp(age, ages, [self.mortality_rates[a] for a in ages])
    
    def _calculate_annuity_income(self, year: int, alive: bool) -> float:
        """Calculate annuity income for a given year."""
        if self.config.annuity_annual == 0:
            return 0.0
        
        if self.config.annuity_type == "Fixed Period":
            # Pays for specified years regardless of mortality
            if year < self.config.annuity_guarantee_years:
                return self.config.annuity_annual
            return 0.0
        
        elif self.config.annuity_type == "Life Only":
            # Pays only while alive
            return self.config.annuity_annual if alive else 0.0
        
        elif self.config.annuity_type == "Life Contingent with Guarantee":
            # Pays while alive OR during guarantee period
            if year < self.config.annuity_guarantee_years or alive:
                return self.config.annuity_annual
            return 0.0
        
        return 0.0
    
    def run_single_simulation(self) -> SimulationResult:
        """Run a single simulation path."""
        # Initialize arrays
        portfolio_values = np.zeros(self.n_years + 1)
        portfolio_values[0] = self.config.initial_portfolio
        
        dividend_income = np.zeros(self.n_years)
        withdrawals = np.zeros(self.n_years)
        taxes_paid = np.zeros(self.n_years)
        annuity_income = np.zeros(self.n_years)
        alive_mask = np.ones(self.n_years + 1, dtype=bool)
        
        cost_basis = self.config.initial_portfolio
        failure_year = None
        
        for year in range(self.n_years):
            age = self.config.current_age + year + 1
            
            # Check mortality
            if self.config.include_mortality:
                mort_rate = self._get_mortality_rate(age)
                if np.random.random() < mort_rate:
                    alive_mask[year + 1:] = False
            
            # Skip if dead or portfolio depleted
            if not alive_mask[year] or portfolio_values[year] <= 0:
                if portfolio_values[year] <= 0 and failure_year is None:
                    failure_year = year
                continue
            
            # Calculate annuity income
            annuity_income[year] = self._calculate_annuity_income(year, alive_mask[year])
            
            # Investment returns (GBM) - PRICE appreciation only
            price_returns = np.random.normal(
                self.config.expected_return / 100,  # This is price return only
                self.config.return_volatility / 100
            )
            growth_factor = np.exp(price_returns)
            portfolio_after_growth = portfolio_values[year] * growth_factor
            
            # Dividends paid out as cash (separate from price appreciation)
            dividends = portfolio_values[year] * (self.config.dividend_yield / 100)
            dividend_income[year] = dividends
            
            # Calculate withdrawal needed
            # Dividends are cash we receive, reducing withdrawal needs
            guaranteed = self.config.social_security + self.config.pension + annuity_income[year]
            net_need = max(0, self.config.annual_consumption - guaranteed - dividends)
            gross_withdrawal = net_need / (1 - self.config.effective_tax_rate / 100)
            withdrawals[year] = gross_withdrawal
            
            # Calculate taxes (simplified)
            taxable_income = dividends + gross_withdrawal
            taxes_paid[year] = taxable_income * (self.config.effective_tax_rate / 100)
            
            # Update portfolio
            # Portfolio grows by price appreciation, we receive dividends as cash,
            # and we withdraw what we need
            new_portfolio = portfolio_after_growth - gross_withdrawal
            portfolio_values[year + 1] = max(0, new_portfolio)
            
            # Check for failure
            if portfolio_values[year + 1] <= 0 and failure_year is None:
                failure_year = year + 1
        
        return SimulationResult(
            portfolio_values=portfolio_values,
            dividend_income=dividend_income,
            withdrawals=withdrawals,
            taxes_paid=taxes_paid,
            annuity_income=annuity_income,
            failure_year=failure_year,
            alive_mask=alive_mask
        )
    
    def run_monte_carlo(self) -> MonteCarloResults:
        """Run Monte Carlo simulation."""
        n_sims = self.config.n_simulations
        
        # Initialize arrays
        portfolio_paths = np.zeros((n_sims, self.n_years + 1))
        failure_years = np.full(n_sims, self.n_years + 1)
        alive_mask = np.ones((n_sims, self.n_years + 1), dtype=bool)
        dividend_income = np.zeros((n_sims, self.n_years))
        withdrawals = np.zeros((n_sims, self.n_years))
        taxes_paid = np.zeros((n_sims, self.n_years))
        annuity_income = np.zeros((n_sims, self.n_years))
        
        # Run simulations
        for i in range(n_sims):
            result = self.run_single_simulation()
            portfolio_paths[i] = result.portfolio_values
            dividend_income[i] = result.dividend_income
            withdrawals[i] = result.withdrawals
            taxes_paid[i] = result.taxes_paid
            annuity_income[i] = result.annuity_income
            
            if result.failure_year is not None:
                failure_years[i] = result.failure_year
            
            if result.alive_mask is not None:
                alive_mask[i] = result.alive_mask
        
        # Calculate statistics
        success_mask = failure_years > self.n_years
        success_rate = success_mask.mean()
        
        # Calculate percentiles
        percentiles = {
            10: np.percentile(portfolio_paths, 10, axis=0),
            25: np.percentile(portfolio_paths, 25, axis=0),
            50: np.percentile(portfolio_paths, 50, axis=0),
            75: np.percentile(portfolio_paths, 75, axis=0),
            90: np.percentile(portfolio_paths, 90, axis=0)
        }
        
        return MonteCarloResults(
            n_simulations=n_sims,
            portfolio_paths=portfolio_paths,
            success_rate=success_rate,
            percentiles=percentiles,
            failure_years=failure_years,
            alive_mask=alive_mask,
            dividend_income=dividend_income,
            withdrawals=withdrawals,
            taxes_paid=taxes_paid,
            annuity_income=annuity_income
        )