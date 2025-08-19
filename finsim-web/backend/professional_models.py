"""Professional market models using established packages."""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import warnings
from datetime import datetime, timedelta
import yfinance as yf


class ProfessionalMarketCalibrator:
    """Market calibration using professional packages."""
    
    def calibrate_with_arch(
        self,
        ticker: str,
        lookback_years: int = 10
    ) -> Dict:
        """
        Use ARCH package for GARCH volatility modeling.
        Provides better volatility forecasts and fat-tail modeling.
        """
        try:
            from arch import arch_model
            
            # Fetch data
            ticker_obj = yf.Ticker(ticker)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * lookback_years)
            hist = ticker_obj.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No data for {ticker}")
            
            # Calculate returns (percentage)
            returns = hist['Close'].pct_change().dropna() * 100
            
            # Fit GARCH(1,1) model with Student's t distribution for fat tails
            model = arch_model(
                returns,
                vol='Garch',
                p=1,
                q=1,
                dist='StudentsT'  # Fat-tailed distribution
            )
            
            res = model.fit(disp='off')
            
            # Extract parameters
            mean_return = res.params['mu']
            
            # Forecast volatility (1-year ahead)
            forecasts = res.forecast(horizon=252)
            volatility_forecast = np.sqrt(forecasts.variance.iloc[-1].mean())
            
            # Get distribution parameters
            nu = res.params.get('nu', 30)  # Degrees of freedom for Student's t
            tail_index = nu
            
            # Calculate VaR and CVaR
            from scipy import stats
            var_95 = stats.t.ppf(0.05, nu, loc=mean_return, scale=volatility_forecast)
            
            # Get conditional volatility series for regime detection
            conditional_vol = res.conditional_volatility
            
            # Simple regime detection based on volatility percentiles
            high_vol_threshold = conditional_vol.quantile(0.75)
            low_vol_threshold = conditional_vol.quantile(0.25)
            
            high_vol_returns = returns[conditional_vol > high_vol_threshold]
            low_vol_returns = returns[conditional_vol < low_vol_threshold]
            
            return {
                'expected_return': float(mean_return * 252 / 100),  # Annualized
                'volatility': float(volatility_forecast * np.sqrt(252) / 100),
                'tail_index': float(tail_index),
                'var_95_daily': float(var_95),
                'model_type': 'GARCH-t',
                'high_vol_regime': {
                    'prob': len(high_vol_returns) / len(returns),
                    'mean_return': float(high_vol_returns.mean() * 252 / 100),
                    'volatility': float(high_vol_returns.std() * np.sqrt(252) / 100)
                },
                'low_vol_regime': {
                    'prob': len(low_vol_returns) / len(returns),
                    'mean_return': float(low_vol_returns.mean() * 252 / 100),
                    'volatility': float(low_vol_returns.std() * np.sqrt(252) / 100)
                }
            }
            
        except ImportError:
            warnings.warn("arch package not installed, using fallback")
            return None
        except Exception as e:
            warnings.warn(f"ARCH model failed: {e}")
            return None
    
    def calibrate_with_prophet(
        self,
        ticker: str,
        lookback_years: int = 10,
        forecast_years: int = 1
    ) -> Dict:
        """
        Use Prophet for time series forecasting with uncertainty.
        Good for capturing trends and seasonality.
        """
        try:
            from prophet import Prophet
            from prophet.diagnostics import cross_validation, performance_metrics
            
            # Fetch data
            ticker_obj = yf.Ticker(ticker)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * lookback_years)
            hist = ticker_obj.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No data for {ticker}")
            
            # Prepare data for Prophet (log prices for multiplicative model)
            df = pd.DataFrame({
                'ds': hist.index,
                'y': np.log(hist['Close'])  # Log transform for returns
            })
            
            # Initialize and fit Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,  # Regularization
                interval_width=0.95  # 95% prediction interval
            )
            
            model.fit(df)
            
            # Make future predictions
            future = model.make_future_dataframe(periods=252 * forecast_years, freq='D')
            forecast = model.predict(future)
            
            # Calculate annualized return from trend
            initial_trend = forecast['trend'].iloc[0]
            final_trend = forecast['trend'].iloc[-1]
            years = (forecast['ds'].iloc[-1] - forecast['ds'].iloc[0]).days / 365.25
            annualized_return = (np.exp(final_trend - initial_trend) - 1) / years
            
            # Estimate volatility from prediction intervals
            # Width of 95% interval ≈ 4 * sigma for normal distribution
            recent_forecast = forecast.iloc[-252:]  # Last year
            interval_width = recent_forecast['yhat_upper'] - recent_forecast['yhat_lower']
            daily_vol = interval_width.mean() / 4
            annualized_vol = daily_vol * np.sqrt(252)
            
            # Cross-validation for model accuracy
            try:
                df_cv = cross_validation(
                    model,
                    initial='730 days',
                    period='180 days',
                    horizon='365 days'
                )
                df_p = performance_metrics(df_cv)
                mape = df_p['mape'].mean()
                
                # Use MAPE as uncertainty measure
                uncertainty_factor = mape
            except:
                uncertainty_factor = 0.15  # Default 15% uncertainty
            
            return {
                'expected_return': float(annualized_return),
                'volatility': float(annualized_vol),
                'return_stderr': float(annualized_vol * uncertainty_factor),
                'model_type': 'Prophet',
                'trend_changepoints': len(model.changepoints),
                'yearly_seasonality': float(model.params['yearly_seasonality_prior_scale']),
                'forecast_lower': float(recent_forecast['yhat_lower'].mean()),
                'forecast_upper': float(recent_forecast['yhat_upper'].mean())
            }
            
        except ImportError:
            warnings.warn("prophet package not installed, using fallback")
            return None
        except Exception as e:
            warnings.warn(f"Prophet model failed: {e}")
            return None
    
    def calibrate_with_statsmodels(
        self,
        ticker: str,
        lookback_years: int = 10
    ) -> Dict:
        """
        Use statsmodels for ARIMA and state space models.
        Good for traditional time series analysis.
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tsa.stattools import adfuller
            from statsmodels.stats.diagnostic import acorr_ljungbox
            
            # Fetch data
            ticker_obj = yf.Ticker(ticker)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * lookback_years)
            hist = ticker_obj.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No data for {ticker}")
            
            # Calculate log returns
            log_returns = np.log(hist['Close'] / hist['Close'].shift(1)).dropna()
            
            # Test for stationarity
            adf_result = adfuller(log_returns)
            is_stationary = adf_result[1] < 0.05
            
            # Fit ARIMA model (simple AR(1) with drift for returns)
            model = ARIMA(log_returns, order=(1, 0, 1))
            res = model.fit()
            
            # Get parameters
            drift = res.params.get('const', 0)
            ar_coef = res.params.get('ar.L1', 0)
            ma_coef = res.params.get('ma.L1', 0)
            
            # Forecast
            forecast = res.forecast(steps=252)
            forecast_mean = forecast.mean() * 252  # Annualized
            
            # Get prediction intervals
            forecast_result = res.get_forecast(steps=252)
            pred_summary = forecast_result.summary_frame(alpha=0.05)
            
            # Calculate volatility from residuals
            residual_vol = res.resid.std() * np.sqrt(252)
            
            # Ljung-Box test for autocorrelation in residuals
            lb_test = acorr_ljungbox(res.resid, lags=10, return_df=True)
            no_autocorr = (lb_test['lb_pvalue'] > 0.05).all()
            
            return {
                'expected_return': float(forecast_mean),
                'volatility': float(residual_vol),
                'model_type': 'ARIMA(1,0,1)',
                'is_stationary': bool(is_stationary),
                'ar_coefficient': float(ar_coef),
                'ma_coefficient': float(ma_coef),
                'drift': float(drift * 252),
                'residuals_clean': bool(no_autocorr),
                'aic': float(res.aic),
                'bic': float(res.bic)
            }
            
        except ImportError:
            warnings.warn("statsmodels package not installed, using fallback")
            return None
        except Exception as e:
            warnings.warn(f"Statsmodels ARIMA failed: {e}")
            return None
    
    def ensemble_calibration(
        self,
        ticker: str,
        lookback_years: int = 10
    ) -> Dict:
        """
        Ensemble approach using multiple models.
        Combines GARCH, Prophet, and ARIMA for robust estimates.
        """
        results = []
        weights = []
        
        # Try GARCH model (best for volatility)
        garch_result = self.calibrate_with_arch(ticker, lookback_years)
        if garch_result:
            results.append(garch_result)
            weights.append(0.4)  # Higher weight for volatility expertise
        
        # Try Prophet (best for trends)
        prophet_result = self.calibrate_with_prophet(ticker, lookback_years)
        if prophet_result:
            results.append(prophet_result)
            weights.append(0.3)
        
        # Try ARIMA (traditional approach)
        arima_result = self.calibrate_with_statsmodels(ticker, lookback_years)
        if arima_result:
            results.append(arima_result)
            weights.append(0.3)
        
        if not results:
            # Fallback to simple historical statistics
            return self._simple_historical_calibration(ticker, lookback_years)
        
        # Normalize weights
        weights = np.array(weights) / sum(weights)
        
        # Weighted average of estimates
        ensemble_return = sum(
            w * r['expected_return'] 
            for w, r in zip(weights, results)
        )
        ensemble_vol = sum(
            w * r['volatility'] 
            for w, r in zip(weights, results)
        )
        
        # Disagreement as uncertainty measure
        return_std = np.std([r['expected_return'] for r in results])
        vol_std = np.std([r['volatility'] for r in results])
        
        return {
            'expected_return': float(ensemble_return),
            'volatility': float(ensemble_vol),
            'return_stderr': float(return_std),
            'volatility_stderr': float(vol_std),
            'model_type': 'Ensemble',
            'models_used': [r['model_type'] for r in results],
            'model_weights': weights.tolist(),
            'model_agreement': float(1 - return_std / abs(ensemble_return))
            if ensemble_return != 0 else 0
        }
    
    def _simple_historical_calibration(
        self,
        ticker: str,
        lookback_years: int
    ) -> Dict:
        """Fallback to simple historical statistics."""
        try:
            ticker_obj = yf.Ticker(ticker)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * lookback_years)
            hist = ticker_obj.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No data for {ticker}")
            
            # Calculate returns
            returns = hist['Close'].pct_change().dropna()
            
            # Simple statistics
            mean_return = returns.mean() * 252
            volatility = returns.std() * np.sqrt(252)
            
            return {
                'expected_return': float(mean_return),
                'volatility': float(volatility),
                'model_type': 'Historical',
                'return_stderr': float(volatility / np.sqrt(len(returns) / 252)),
                'volatility_stderr': float(volatility / np.sqrt(2 * len(returns) / 252))
            }
        except:
            # Ultimate fallback
            return {
                'expected_return': 0.07,
                'volatility': 0.18,
                'model_type': 'Default',
                'return_stderr': 0.02,
                'volatility_stderr': 0.03
            }