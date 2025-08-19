"""Advanced market models for improved Monte Carlo forecasting."""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import yfinance as yf
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import minimize
import warnings

@dataclass
class MarketParameters:
    """Market parameters with uncertainty quantification."""
    expected_return: float
    volatility: float
    dividend_yield: float
    # Parameter uncertainty (standard errors)
    return_stderr: float
    volatility_stderr: float
    # Distributional parameters
    skewness: float = 0.0
    excess_kurtosis: float = 0.0
    # Regime parameters
    regime_probs: Optional[List[float]] = None
    regime_returns: Optional[List[float]] = None
    regime_vols: Optional[List[float]] = None


class MarketCalibrator:
    """Advanced market calibration with best practices."""
    
    def __init__(self):
        # Common market factor loadings for major indices
        self.factor_priors = {
            'SPY': {'market_beta': 1.0, 'vol_of_vol': 0.25},
            'VOO': {'market_beta': 1.0, 'vol_of_vol': 0.25},
            'VT': {'market_beta': 0.95, 'vol_of_vol': 0.22},
            'VTI': {'market_beta': 1.0, 'vol_of_vol': 0.24},
            'QQQ': {'market_beta': 1.2, 'vol_of_vol': 0.35},
            'IWM': {'market_beta': 1.1, 'vol_of_vol': 0.30},
        }
        
        # Historical long-term equity risk premium (over risk-free rate)
        self.equity_risk_premium = 0.055  # 5.5% historical average
        self.risk_free_rate = 0.04  # Current approximate 10Y treasury
        
    def fetch_multi_asset_data(
        self, 
        tickers: List[str], 
        lookback_years: int = 10
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple assets."""
        data = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * lookback_years)
        
        for ticker in tickers:
            try:
                ticker_obj = yf.Ticker(ticker)
                hist = ticker_obj.history(start=start_date, end=end_date, interval="1d")
                if not hist.empty:
                    data[ticker] = hist
            except Exception as e:
                warnings.warn(f"Failed to fetch {ticker}: {e}")
                
        return data
    
    def calculate_shrinkage_estimator(
        self,
        returns: pd.Series,
        prior_mean: float,
        prior_vol: float,
        shrinkage_factor: float = 0.3
    ) -> Tuple[float, float]:
        """
        Apply Bayesian shrinkage to parameter estimates.
        Shrinks sample estimates toward informative priors.
        """
        sample_mean = returns.mean() * 252
        sample_vol = returns.std() * np.sqrt(252)
        
        # Shrink toward priors
        shrunk_mean = shrinkage_factor * prior_mean + (1 - shrinkage_factor) * sample_mean
        shrunk_vol = shrinkage_factor * prior_vol + (1 - shrinkage_factor) * sample_vol
        
        return shrunk_mean, shrunk_vol
    
    def detect_regimes(self, returns: pd.Series, n_regimes: int = 2) -> Dict:
        """
        Detect market regimes using Hidden Markov Model approach.
        Simplified version using volatility clustering.
        """
        # Calculate rolling volatility
        rolling_vol = returns.rolling(window=21).std() * np.sqrt(252)
        
        # Use k-means clustering on volatility to identify regimes
        from sklearn.cluster import KMeans
        
        vol_data = rolling_vol.dropna().values.reshape(-1, 1)
        kmeans = KMeans(n_clusters=n_regimes, random_state=42)
        regimes = kmeans.fit_predict(vol_data)
        
        # Calculate statistics for each regime
        regime_stats = []
        for i in range(n_regimes):
            regime_returns = returns.iloc[len(returns) - len(regimes):][regimes == i]
            if len(regime_returns) > 0:
                regime_stats.append({
                    'mean': regime_returns.mean() * 252,
                    'vol': regime_returns.std() * np.sqrt(252),
                    'prob': len(regime_returns) / len(regimes)
                })
        
        return regime_stats
    
    def estimate_tail_risk(self, returns: pd.Series) -> Dict[str, float]:
        """Estimate tail risk metrics."""
        # Calculate VaR and CVaR
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean()
        
        # Fit Student's t distribution for fat tails
        params = stats.t.fit(returns)
        df = params[0]  # degrees of freedom
        
        # Calculate skewness and excess kurtosis
        skewness = stats.skew(returns)
        excess_kurtosis = stats.kurtosis(returns)
        
        return {
            'var_95': var_95 * np.sqrt(252),
            'cvar_95': cvar_95 * np.sqrt(252),
            'tail_index': df,
            'skewness': skewness,
            'excess_kurtosis': excess_kurtosis
        }
    
    def calibrate_with_cross_sectional_info(
        self,
        primary_ticker: str,
        related_tickers: List[str] = None,
        lookback_years: int = 10,
        use_factor_model: bool = True,
        use_regime_switching: bool = True,
        use_parameter_uncertainty: bool = True
    ) -> MarketParameters:
        """
        Calibrate market parameters using best practices:
        1. Cross-sectional information from related assets
        2. Factor model with shrinkage
        3. Regime detection
        4. Parameter uncertainty quantification
        """
        
        # Default related tickers for borrowing information
        if related_tickers is None:
            if primary_ticker in ['SPY', 'VOO']:
                related_tickers = ['SPY', 'VOO', 'IVV']  # S&P 500 funds
            elif primary_ticker == 'VT':
                related_tickers = ['VT', 'ACWI', 'URTH']  # Global funds
            elif primary_ticker == 'QQQ':
                related_tickers = ['QQQ', 'ONEQ', 'QQQM']  # Nasdaq funds
            else:
                related_tickers = ['VTI', 'SPY', 'VT']  # Broad market
        
        # Fetch data for all tickers
        all_tickers = list(set([primary_ticker] + related_tickers))
        data = self.fetch_multi_asset_data(all_tickers, lookback_years)
        
        if primary_ticker not in data or data[primary_ticker].empty:
            # Return sensible defaults
            return MarketParameters(
                expected_return=7.0,
                volatility=18.0,
                dividend_yield=2.0,
                return_stderr=2.0,
                volatility_stderr=3.0
            )
        
        # Calculate returns
        primary_data = data[primary_ticker]
        primary_returns = primary_data['Close'].pct_change().dropna()
        
        # 1. Basic statistics
        basic_return = primary_returns.mean() * 252 * 100
        basic_vol = primary_returns.std() * np.sqrt(252) * 100
        
        # Get dividend yield
        ticker_obj = yf.Ticker(primary_ticker)
        info = ticker_obj.info
        div_yield = info.get('dividendYield', 0.02) * 100
        
        # 2. Cross-sectional pooling
        if len(data) > 1 and use_factor_model:
            # Calculate average statistics across related assets
            all_returns = []
            all_vols = []
            
            for ticker, hist in data.items():
                if not hist.empty:
                    ret = hist['Close'].pct_change().dropna()
                    all_returns.append(ret.mean() * 252)
                    all_vols.append(ret.std() * np.sqrt(252))
            
            # Use cross-sectional average as prior
            prior_return = np.mean(all_returns) * 100
            prior_vol = np.mean(all_vols) * 100
            
            # Apply shrinkage
            shrinkage = 0.3 if primary_ticker in self.factor_priors else 0.2
            final_return, final_vol = self.calculate_shrinkage_estimator(
                primary_returns, 
                prior_return / 100, 
                prior_vol / 100,
                shrinkage
            )
            final_return *= 100
            final_vol *= 100
        else:
            final_return = basic_return
            final_vol = basic_vol
        
        # 3. Regime detection
        regime_stats = None
        if use_regime_switching and len(primary_returns) > 252:
            regime_stats = self.detect_regimes(primary_returns)
        
        # 4. Parameter uncertainty
        if use_parameter_uncertainty:
            # Standard error of mean return
            n_years = len(primary_returns) / 252
            return_stderr = final_vol / np.sqrt(n_years)
            
            # Standard error of volatility (approximation)
            vol_stderr = final_vol / np.sqrt(2 * n_years)
        else:
            return_stderr = 0
            vol_stderr = 0
        
        # 5. Tail risk metrics
        tail_metrics = self.estimate_tail_risk(primary_returns)
        
        # Build final parameters
        params = MarketParameters(
            expected_return=round(final_return, 1),
            volatility=round(final_vol, 1),
            dividend_yield=round(min(div_yield, 5.0), 2),
            return_stderr=round(return_stderr, 2),
            volatility_stderr=round(vol_stderr, 2),
            skewness=round(tail_metrics['skewness'], 3),
            excess_kurtosis=round(tail_metrics['excess_kurtosis'], 3)
        )
        
        # Add regime parameters if detected
        if regime_stats:
            params.regime_probs = [r['prob'] for r in regime_stats]
            params.regime_returns = [r['mean'] * 100 for r in regime_stats]
            params.regime_vols = [r['vol'] * 100 for r in regime_stats]
        
        return params


class MonteCarloEngine:
    """Enhanced Monte Carlo engine with advanced features."""
    
    def __init__(self, params: MarketParameters):
        self.params = params
        
    def generate_returns(
        self,
        n_years: int,
        n_simulations: int,
        use_parameter_uncertainty: bool = True,
        use_regime_switching: bool = False,
        use_fat_tails: bool = True
    ) -> np.ndarray:
        """
        Generate return paths with advanced features.
        
        Returns:
            Array of shape (n_simulations, n_years) with annual returns
        """
        annual_returns = np.zeros((n_simulations, n_years))
        
        for sim in range(n_simulations):
            # Sample parameter uncertainty
            if use_parameter_uncertainty:
                # Draw from parameter distribution
                mean = np.random.normal(
                    self.params.expected_return / 100,
                    self.params.return_stderr / 100
                )
                vol = np.random.normal(
                    self.params.volatility / 100,
                    self.params.volatility_stderr / 100
                )
                vol = max(vol, 0.05)  # Floor at 5% volatility
            else:
                mean = self.params.expected_return / 100
                vol = self.params.volatility / 100
            
            # Generate returns for this simulation
            if use_regime_switching and self.params.regime_probs:
                # Regime-switching model
                annual_returns[sim] = self._generate_regime_switching_returns(
                    n_years, mean, vol
                )
            elif use_fat_tails and self.params.excess_kurtosis > 0:
                # Student's t distribution for fat tails
                df = 10 / (1 + self.params.excess_kurtosis)  # Approximate mapping
                annual_returns[sim] = stats.t.rvs(
                    df, loc=mean, scale=vol, size=n_years
                )
            else:
                # Standard normal returns
                annual_returns[sim] = np.random.normal(mean, vol, n_years)
        
        return annual_returns
    
    def _generate_regime_switching_returns(
        self,
        n_years: int,
        base_mean: float,
        base_vol: float
    ) -> np.ndarray:
        """Generate returns with regime switching."""
        returns = np.zeros(n_years)
        
        # Start in random regime based on steady-state probabilities
        current_regime = np.random.choice(
            len(self.params.regime_probs),
            p=self.params.regime_probs
        )
        
        # Simplified transition matrix (symmetric)
        transition_prob = 0.1  # Probability of switching regimes each year
        
        for year in range(n_years):
            # Get current regime parameters
            regime_return = self.params.regime_returns[current_regime] / 100
            regime_vol = self.params.regime_vols[current_regime] / 100
            
            # Generate return for this year
            returns[year] = np.random.normal(regime_return, regime_vol)
            
            # Potentially switch regimes
            if np.random.random() < transition_prob:
                # Switch to different regime
                other_regimes = [i for i in range(len(self.params.regime_probs)) 
                                if i != current_regime]
                if other_regimes:
                    current_regime = np.random.choice(other_regimes)
        
        return returns
    
    def calculate_forecast_metrics(
        self,
        returns: np.ndarray,
        confidence_levels: List[float] = [5, 25, 50, 75, 95]
    ) -> Dict:
        """Calculate forecast metrics including prediction intervals."""
        
        # Calculate cumulative returns
        cumulative_returns = np.cumprod(1 + returns, axis=1) - 1
        
        # Calculate percentiles for each year
        percentiles = {}
        for level in confidence_levels:
            percentiles[f'p{level}'] = np.percentile(
                cumulative_returns, level, axis=0
            )
        
        # Calculate probability of negative returns
        prob_negative = np.mean(cumulative_returns < 0, axis=0)
        
        # Calculate expected shortfall (CVaR)
        var_5 = np.percentile(cumulative_returns, 5, axis=0)
        cvar_5 = np.mean(
            np.where(cumulative_returns <= var_5[:, np.newaxis].T, 
                    cumulative_returns, np.nan),
            axis=0
        )
        
        return {
            'percentiles': percentiles,
            'prob_negative': prob_negative,
            'expected_shortfall': cvar_5,
            'mean': np.mean(cumulative_returns, axis=0),
            'std': np.std(cumulative_returns, axis=0)
        }