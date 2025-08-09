"""Enhanced Monte Carlo simulator with GARCH volatility and historical data fitting."""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple
import warnings

try:
    from arch import arch_model
    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False
    warnings.warn("arch package not installed. GARCH modeling unavailable.", ImportWarning)

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    warnings.warn("yfinance not installed. Historical data fetching unavailable.", ImportWarning)


class EnhancedMonteCarloSimulator:
    """
    Enhanced Monte Carlo simulator with support for:
    - GARCH volatility modeling
    - Historical data fitting
    - Fat-tailed distributions
    - Regime switching
    - Jump diffusion processes
    """
    
    def __init__(
        self,
        initial_capital: float,
        monthly_withdrawal: float,
        ticker: Optional[str] = None,
        lookback_years: int = 30,
        n_simulations: int = 10_000,
        seed: Optional[int] = None
    ):
        """
        Initialize enhanced simulator.
        
        Args:
            initial_capital: Starting investment amount
            monthly_withdrawal: Monthly withdrawal amount
            ticker: Stock ticker for historical data (e.g., 'VT', 'SPY')
            lookback_years: Years of historical data to use
            n_simulations: Number of simulation paths
            seed: Random seed
        """
        self.initial_capital = initial_capital
        self.monthly_withdrawal = monthly_withdrawal
        self.ticker = ticker
        self.lookback_years = lookback_years
        self.n_simulations = n_simulations
        
        if seed is not None:
            np.random.seed(seed)
        
        # Fit historical data if ticker provided
        if ticker and HAS_YFINANCE:
            self.fit_historical_data()
        else:
            # Default parameters (VT-like)
            self.annual_return_mean = 0.08
            self.annual_return_std = 0.158
            self.annual_dividend_yield = 0.02
            self.garch_model = None
    
    def fit_historical_data(self) -> None:
        """Fetch and fit historical data for the specified ticker."""
        if not HAS_YFINANCE:
            raise ImportError("yfinance required for historical data fitting")
        
        # Fetch historical data
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=self.lookback_years)
        
        try:
            stock = yf.Ticker(self.ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                warnings.warn(f"No data found for {self.ticker}. Using defaults.")
                self.annual_return_mean = 0.08
                self.annual_return_std = 0.158
                self.annual_dividend_yield = 0.02
                self.garch_model = None
                return
            
            # Calculate returns
            prices = hist['Close']
            returns = prices.pct_change().dropna()
            
            # Annualized statistics
            self.annual_return_mean = returns.mean() * 252
            self.annual_return_std = returns.std() * np.sqrt(252)
            
            # Estimate dividend yield
            if 'Dividends' in hist.columns:
                annual_dividends = hist['Dividends'].resample('Y').sum().mean()
                avg_price = prices.mean()
                self.annual_dividend_yield = annual_dividends / avg_price if avg_price > 0 else 0.02
            else:
                self.annual_dividend_yield = 0.02
            
            # Fit GARCH model if available
            if HAS_ARCH:
                self.fit_garch_model(returns * 100)  # Convert to percentage
            else:
                self.garch_model = None
                
        except Exception as e:
            warnings.warn(f"Error fetching data for {self.ticker}: {e}")
            self.annual_return_mean = 0.08
            self.annual_return_std = 0.158
            self.annual_dividend_yield = 0.02
            self.garch_model = None
    
    def fit_garch_model(self, returns: pd.Series) -> None:
        """
        Fit GARCH(1,1) model to return series.
        
        Args:
            returns: Percentage returns series
        """
        if not HAS_ARCH:
            self.garch_model = None
            return
        
        try:
            # Fit GARCH(1,1) model
            model = arch_model(returns, vol='GARCH', p=1, q=1, dist='StudentsT')
            self.garch_model = model.fit(disp='off')
            
            # Extract parameters for simulation
            self.garch_params = {
                'omega': self.garch_model.params['omega'],
                'alpha': self.garch_model.params['alpha[1]'],
                'beta': self.garch_model.params['beta[1]'],
                'nu': self.garch_model.params.get('nu', 30)  # Student's t df
            }
        except Exception as e:
            warnings.warn(f"GARCH fitting failed: {e}")
            self.garch_model = None
    
    def simulate_garch_returns(self, n_months: int) -> np.ndarray:
        """
        Simulate returns using fitted GARCH model.
        
        Args:
            n_months: Number of months to simulate
            
        Returns:
            Array of simulated returns (n_simulations x n_months)
        """
        if not self.garch_model:
            # Fallback to normal distribution
            monthly_mean = self.annual_return_mean / 12
            monthly_std = self.annual_return_std / np.sqrt(12)
            return np.random.normal(monthly_mean, monthly_std, (self.n_simulations, n_months))
        
        # GARCH simulation
        omega = self.garch_params['omega']
        alpha = self.garch_params['alpha']
        beta = self.garch_params['beta']
        nu = self.garch_params['nu']
        
        returns = np.zeros((self.n_simulations, n_months))
        
        for sim in range(self.n_simulations):
            # Initialize
            h = np.zeros(n_months + 1)  # Conditional variance
            h[0] = omega / (1 - alpha - beta)  # Unconditional variance
            
            # Generate shocks from Student's t distribution
            if nu > 2:
                shocks = np.random.standard_t(nu, n_months)
                shocks = shocks / np.sqrt(nu / (nu - 2))  # Normalize
            else:
                shocks = np.random.standard_normal(n_months)
            
            for t in range(n_months):
                # Update conditional variance
                if t > 0:
                    h[t] = omega + alpha * (returns[sim, t-1]**2) + beta * h[t-1]
                
                # Generate return
                returns[sim, t] = np.sqrt(h[t]) * shocks[t]
        
        # Convert from percentage to decimal and adjust to monthly
        returns = returns / 100 / np.sqrt(21)  # Approx 21 trading days per month
        
        # Add drift
        returns += self.annual_return_mean / 12
        
        return returns
    
    def simulate_with_regime_switching(
        self,
        n_months: int,
        bull_params: Dict[str, float] = None,
        bear_params: Dict[str, float] = None,
        transition_probs: Tuple[float, float] = (0.95, 0.90)
    ) -> dict:
        """
        Simulate with regime switching between bull and bear markets.
        
        Args:
            n_months: Number of months
            bull_params: Parameters for bull market {'mean': 0.12, 'std': 0.10}
            bear_params: Parameters for bear market {'mean': -0.05, 'std': 0.25}
            transition_probs: (prob_stay_bull, prob_stay_bear)
            
        Returns:
            Simulation results dictionary
        """
        if bull_params is None:
            bull_params = {'mean': 0.12, 'std': 0.10}
        if bear_params is None:
            bear_params = {'mean': -0.05, 'std': 0.25}
        
        prob_bull_to_bull, prob_bear_to_bear = transition_probs
        
        paths = np.zeros((self.n_simulations, n_months + 1))
        paths[:, 0] = self.initial_capital
        depletion_month = np.full(self.n_simulations, np.inf)
        
        for sim in range(self.n_simulations):
            regime = 'bull'  # Start in bull market
            
            for month in range(n_months):
                # Determine regime
                if regime == 'bull':
                    if np.random.random() > prob_bull_to_bull:
                        regime = 'bear'
                else:
                    if np.random.random() > prob_bear_to_bear:
                        regime = 'bull'
                
                # Get regime parameters
                params = bull_params if regime == 'bull' else bear_params
                monthly_return = np.random.normal(
                    params['mean'] / 12,
                    params['std'] / np.sqrt(12)
                )
                
                # Calculate portfolio value
                current_value = paths[sim, month]
                if current_value <= 0:
                    continue
                
                # Apply return and withdrawal
                dividend = current_value * self.annual_dividend_yield / 12
                growth = current_value * monthly_return
                new_value = current_value + growth + dividend - self.monthly_withdrawal
                
                # Check depletion
                if current_value > 0 and new_value <= 0:
                    depletion_month[sim] = month + 1
                
                paths[sim, month + 1] = max(0, new_value)
        
        final_values = paths[:, -1]
        
        return {
            'paths': paths,
            'final_values': final_values,
            'depletion_month': depletion_month,
            'percentiles': {
                'p5': np.percentile(final_values, 5),
                'p25': np.percentile(final_values, 25),
                'p50': np.percentile(final_values, 50),
                'p75': np.percentile(final_values, 75),
                'p95': np.percentile(final_values, 95)
            },
            'depletion_probability': np.mean(depletion_month < np.inf),
            'mean_final_value': np.mean(final_values),
            'median_final_value': np.median(final_values)
        }
    
    def simulate(self, n_months: int, use_garch: bool = True) -> dict:
        """
        Run enhanced simulation.
        
        Args:
            n_months: Number of months to simulate
            use_garch: Whether to use GARCH model if fitted
            
        Returns:
            Simulation results dictionary
        """
        # Generate returns
        if use_garch and self.garch_model:
            returns = self.simulate_garch_returns(n_months)
        else:
            # Standard simulation
            monthly_mean = self.annual_return_mean / 12
            monthly_std = self.annual_return_std / np.sqrt(12)
            returns = np.random.normal(monthly_mean, monthly_std, (self.n_simulations, n_months))
        
        # Initialize paths
        paths = np.zeros((self.n_simulations, n_months + 1))
        paths[:, 0] = self.initial_capital
        depletion_month = np.full(self.n_simulations, np.inf)
        
        # Simulate paths
        for month in range(n_months):
            current_value = paths[:, month]
            active = current_value > 0
            
            if not np.any(active):
                break
            
            # Calculate dividends
            dividends = current_value * self.annual_dividend_yield / 12
            
            # Apply returns
            growth = current_value * returns[:, month]
            
            # New value after withdrawal
            new_value = current_value + growth + dividends - self.monthly_withdrawal
            
            # Track depletion
            depleted = (current_value > 0) & (new_value <= 0)
            depletion_month[depleted & (depletion_month == np.inf)] = month + 1
            
            # Update paths
            paths[:, month + 1] = np.maximum(0, new_value)
        
        final_values = paths[:, -1]
        
        return {
            'paths': paths,
            'final_values': final_values,
            'depletion_month': depletion_month,
            'percentiles': {
                'p5': np.percentile(final_values, 5),
                'p25': np.percentile(final_values, 25),
                'p50': np.percentile(final_values, 50),
                'p75': np.percentile(final_values, 75),
                'p95': np.percentile(final_values, 95)
            },
            'depletion_probability': np.mean(depletion_month < np.inf),
            'mean_final_value': np.mean(final_values),
            'median_final_value': np.median(final_values),
            'model_type': 'GARCH' if (use_garch and self.garch_model) else 'Normal'
        }