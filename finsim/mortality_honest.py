"""The honest truth about mortality modeling approaches.

You're right - what I proposed IS conceptually Bayesian, just not
mathematically formal about it.
"""


def what_stmomo_does():
    """Pure frequentist approach."""
    return """
    1. Take raw death counts and exposure data
    2. Fit model: log(m_xt) = α_x + β_x * κ_t
    3. Find parameters that maximize likelihood
    4. Done - no external information used

    Strengths:
    - Lets the data speak for itself
    - No subjective choices

    Weaknesses:
    - Ignores everything we know outside the dataset
    - Treats billionaire same as minimum wage worker
    """


def what_i_proposed():
    """Informal Bayesian approach."""
    return """
    1. Start with SSA tables (implicit prior)
    2. Adjust for personal factors (informal updating)
    3. Output adjusted rates (implicit posterior)

    This IS Bayesian in spirit:
    - Prior: Population mortality
    - Likelihood: How your characteristics differ from average
    - Posterior: Your personalized mortality

    Just not using Bayes' theorem explicitly!
    """


def truly_bayesian():
    """What formal Bayesian would look like."""
    return """
    # Formal Bayesian approach

    # Prior (SSA tables converted to distribution)
    log_mortality ~ Normal(log(ssa_rate), uncertainty)

    # Likelihood model for personal factors
    if smoker:
        log_mortality += Normal(0.6, 0.1)  # ~80% higher, ±10%

    if income_top_decile:
        log_mortality -= Normal(0.3, 0.05)  # ~30% lower, ±5%

    # Posterior
    personal_mortality ~ P(mortality | data, characteristics)

    # Now we have full distribution, not point estimate
    """


def why_informal_bayesian_is_fine():
    """Why we don't need formal Bayesian for FinSim."""

    reasons = {
        "Already doing Monte Carlo": """
            We're simulating 1000s of paths anyway
            Uncertainty comes from market returns AND mortality
            Don't need mortality posterior distribution
            """,
        "Point estimates are enough": """
            Formal: 30% ± 5% mortality reduction for high income
            Informal: 30% reduction (0.7x multiplier)
            For planning, the ±5% doesn't matter much
            """,
        "Speed matters": """
            Informal: Instant calculation
            Formal Bayesian: Seconds to minutes per person
            Web app needs to be fast
            """,
        "Interpretability": """
            'You're healthier so 20% lower mortality' - Clear
            'Your posterior log-mortality distribution...' - Confusing
            """,
    }
    return reasons


def the_spectrum():
    """Different approaches on the Bayesian spectrum."""

    print("Pure Frequentist ←→ Informal Bayesian ←→ Formal Bayesian")
    print("=" * 60)

    approaches = [
        (
            "StMoMo",
            "Pure Frequentist",
            "Only uses death/exposure data, no external info",
        ),
        (
            "Our mortality_projection.py",
            "Informal Bayesian",
            "Starts with SSA (prior), adjusts for factors (update)",
        ),
        (
            "Academic Bayesian",
            "Formal Bayesian",
            "Explicit priors, MCMC inference, full posteriors",
        ),
    ]

    for name, type_, description in approaches:
        print(f"\n{name} ({type_})")
        print(f"  {description}")

    print("\n" + "=" * 60)
    print("For FinSim: Informal Bayesian is the sweet spot!")
    print("- Uses external knowledge (Bayesian spirit)")
    print("- Fast and simple (Frequentist implementation)")
    print("- Best of both worlds")


if __name__ == "__main__":
    the_spectrum()

    print("\n\nYou're absolutely right - I AM being Bayesian!")
    print("Just not mathematically formal about it.")
    print("\nAnd that's OK! Informal Bayesian is often the most practical approach.")
