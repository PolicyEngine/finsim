"""Bayesian mortality projection - what StMoMo could have been.

This shows how a truly Bayesian approach to mortality projection would work,
using modern probabilistic programming. This is NOT how StMoMo works, but
illustrates the difference.

Requirements (if you wanted to run this):
- pip install pymc numpyro arviz
"""

import numpy as np
from typing import Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass 
class BayesianMortalityModel:
    """A Bayesian approach to mortality modeling.
    
    Key differences from StMoMo (frequentist):
    1. Priors on all parameters based on expert knowledge
    2. Full posterior distributions, not point estimates
    3. Natural uncertainty quantification
    4. Can incorporate external information
    """
    
    def conceptual_model(self):
        """Show what a Bayesian Lee-Carter model would look like.
        
        This is pseudocode - real implementation would use PyMC or NumPyro.
        """
        model_spec = """
        # Bayesian Lee-Carter Model
        # log(m_xt) = α_x + β_x * κ_t + ε_xt
        
        import pymc as pm
        
        with pm.Model() as mortality_model:
            
            # PRIORS (this is what makes it Bayesian!)
            
            # Age effect - smooth across ages
            α_x = pm.GaussianRandomWalk(
                'alpha', 
                sigma=0.01,  # Smooth changes between ages
                shape=n_ages
            )
            
            # Age-sensitivity to time trend
            β_x = pm.Normal(
                'beta',
                mu=0.01,  # Prior: ~1% improvement per year
                sigma=0.005,  # Fairly confident about this
                shape=n_ages
            )
            
            # Time trend - mortality improvements
            κ_t = pm.GaussianRandomWalk(
                'kappa',
                sigma=0.1,  # Year-to-year variation
                shape=n_years  
            )
            
            # Observation noise
            σ = pm.HalfNormal('sigma', 0.1)
            
            # LIKELIHOOD
            
            # Expected log mortality
            log_m = α_x[age_idx] + β_x[age_idx] * κ_t[year_idx]
            
            # Observed deaths ~ Poisson(exposure * exp(log_m))
            deaths = pm.Poisson(
                'deaths',
                mu=exposure * pm.math.exp(log_m),
                observed=observed_deaths
            )
            
            # INFERENCE
            
            # Modern Bayesian inference using NUTS sampler
            trace = pm.sample(
                draws=2000,
                tune=1000,
                chains=4,
                target_accept=0.95
            )
        
        return trace
        """
        return model_spec
    
    def advantages_over_frequentist(self):
        """Why you might want Bayesian mortality models."""
        
        advantages = {
            "Uncertainty Quantification": """
                Frequentist bootstrap: Resamples data, assumes model is correct
                Bayesian: Full posterior, includes model uncertainty
            """,
            
            "Small Data": """
                Frequentist: Needs lots of data for stable estimates
                Bayesian: Can work with less data using informative priors
            """,
            
            "External Information": """
                Frequentist: Can't easily incorporate expert opinion
                Bayesian: Priors naturally include external knowledge
            """,
            
            "Hierarchical Models": """
                Frequentist: Complex to fit multi-level models
                Bayesian: Natural framework for hierarchical structures
            """,
            
            "Prediction": """
                Frequentist: Confidence vs prediction intervals confusion
                Bayesian: Posterior predictive distribution is natural
            """
        }
        return advantages
    
    def why_stmomo_isnt_bayesian(self):
        """Reasons StMoMo uses frequentist methods."""
        
        reasons = {
            "Speed": """
                MLE + Bootstrap: Fast, seconds to fit
                Bayesian MCMC: Slow, minutes to hours
            """,
            
            "Tradition": """
                Actuarial science traditionally frequentist
                Lee-Carter (1992) was frequentist
                Industry expects these methods
            """,
            
            "Simplicity": """
                MLE: Standard optimization
                Bayesian: Requires choosing priors, checking convergence
            """,
            
            "Software": """
                2015 (when StMoMo released): PyMC3 just emerging
                Now (2024): PyMC, NumPyro, Stan make Bayesian easier
            """
        }
        return reasons


def modern_bayesian_mortality():
    """If building mortality projection today, here's the Bayesian approach.
    
    Using NumPyro (JAX-based) for speed:
    """
    
    code = """
    import numpyro
    import numpyro.distributions as dist
    from numpyro.infer import MCMC, NUTS
    import jax.numpy as jnp
    import jax
    
    def mortality_model(ages, years, exposure, deaths=None):
        '''Modern Bayesian mortality model using NumPyro.
        
        This is 10-100x faster than PyMC and can run on GPU.
        '''
        
        n_ages = len(np.unique(ages))
        n_years = len(np.unique(years))
        
        # Priors based on demographic research
        with numpyro.plate("ages", n_ages):
            # Log base mortality by age
            log_a = numpyro.sample("log_a", dist.Normal(-5, 2))
            
            # Mortality improvement sensitivity  
            b = numpyro.sample("b", dist.HalfNormal(0.02))
        
        # Mortality improvement trend (with drift)
        drift = numpyro.sample("drift", dist.Normal(-0.01, 0.005))
        with numpyro.plate("years", n_years):
            if years > 0:
                k = numpyro.sample("k", dist.Normal(k_prev + drift, 0.1))
            else:
                k = numpyro.sample("k", dist.Normal(0, 1))
        
        # Expected deaths
        log_m = log_a[ages] + b[ages] * k[years]
        expected_deaths = exposure * jnp.exp(log_m)
        
        # Likelihood - negative binomial for overdispersion
        with numpyro.plate("observations", len(deaths)):
            numpyro.sample(
                "deaths",
                dist.NegativeBinomial2(expected_deaths, concentration=10),
                obs=deaths
            )
    
    # Fast inference with NUTS
    kernel = NUTS(mortality_model)
    mcmc = MCMC(kernel, num_warmup=1000, num_samples=2000, num_chains=4)
    mcmc.run(jax.random.PRNGKey(0), ages, years, exposure, deaths)
    
    # Get posterior samples
    posterior = mcmc.get_samples()
    
    # Posterior predictive for future years
    predictive = numpyro.infer.Predictive(
        mortality_model,
        posterior_samples=posterior
    )
    
    future_deaths = predictive(
        jax.random.PRNGKey(1),
        future_ages,
        future_years, 
        future_exposure
    )
    """
    
    return code


def simple_bayesian_life_expectancy():
    """Simplest Bayesian approach for practitioners.
    
    Instead of complex models, just be Bayesian about uncertainty:
    """
    
    # Use conjugate priors for closed-form solutions
    class SimpleeBayesian:
        def __init__(self, prior_mean_le=20, prior_confidence=10):
            """Initialize with prior beliefs about life expectancy.
            
            Args:
                prior_mean_le: Prior mean life expectancy at 65
                prior_confidence: How many 'observations' worth of confidence
            """
            # Beta distribution for survival probabilities
            self.alpha = prior_mean_le * prior_confidence
            self.beta = (85 - 65 - prior_mean_le) * prior_confidence
            
        def update(self, observed_deaths, exposure):
            """Update beliefs with observed data."""
            # Conjugate update for Beta-Binomial
            self.alpha += (exposure - observed_deaths)
            self.beta += observed_deaths
            
        def sample_life_expectancy(self, n_samples=1000):
            """Sample from posterior distribution."""
            # Sample survival probabilities
            annual_survival = np.random.beta(self.alpha, self.beta, n_samples)
            
            # Convert to life expectancy (simplified)
            life_expectancy = -1 / np.log(annual_survival)
            
            return life_expectancy
        
        def credible_interval(self, level=0.95):
            """Get Bayesian credible interval."""
            samples = self.sample_life_expectancy(10000)
            lower = (1 - level) / 2
            upper = 1 - lower
            return np.percentile(samples, [lower * 100, upper * 100])
    
    return SimpleeBayesian


if __name__ == "__main__":
    model = BayesianMortalityModel()
    
    print("=== Bayesian vs Frequentist Mortality Models ===\n")
    
    print("StMoMo (Frequentist):")
    print("- Maximum likelihood estimation")
    print("- Bootstrap for uncertainty")  
    print("- ARIMA for projections")
    print("- Fast, traditional, industry standard")
    
    print("\nBayesian Alternative:")
    print("- Prior distributions on parameters")
    print("- MCMC for posterior inference")
    print("- Natural uncertainty quantification")
    print("- Better for small data, worse for speed")
    
    print("\n" + "="*50)
    print("For FinSim: Frequentist is fine!")
    print("- We have lots of mortality data")
    print("- Speed matters for web apps")
    print("- Users understand scenarios better than priors")
    print("- Monte Carlo already captures uncertainty")