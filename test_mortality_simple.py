"""Simple test of enhanced mortality features without tax calculation."""

from finsim.mortality_enhanced import EnhancedMortality
from finsim.mortality import get_mortality_rates
import numpy as np


def test_mortality_comparison():
    """Compare mortality rates and life expectancy across different profiles."""
    
    age = 65
    
    print("Mortality Rate Comparison at Age 65")
    print("=" * 50)
    
    # Basic SSA rate
    basic_rates = get_mortality_rates("Male")
    basic_rate = basic_rates[age] if age in basic_rates else 0.016
    print(f"Basic SSA rate: {basic_rate:.4f} ({basic_rate*100:.2f}%)")
    
    # Enhanced - healthy profile
    healthy = EnhancedMortality(
        gender="Male",
        use_bayesian=True,
        smoker=False,
        income_percentile=80,
        health_status="good"
    )
    healthy_rate = healthy.get_mortality_rate(age)
    print(f"Healthy non-smoker (80th percentile income): {healthy_rate:.4f} ({healthy_rate*100:.2f}%)")
    print(f"  Relative to SSA: {healthy_rate/basic_rate:.2f}x")
    
    # Enhanced - poor health profile
    poor = EnhancedMortality(
        gender="Male",
        use_bayesian=True,
        smoker=True,
        income_percentile=25,
        health_status="poor"
    )
    poor_rate = poor.get_mortality_rate(age)
    print(f"Smoker with poor health (25th percentile income): {poor_rate:.4f} ({poor_rate*100:.2f}%)")
    print(f"  Relative to SSA: {poor_rate/basic_rate:.2f}x")
    
    # Life expectancy simulation
    print("\nLife Expectancy Simulation (10,000 paths)")
    print("-" * 50)
    
    n_sims = 10000
    n_years = 55  # To age 120
    
    # Basic SSA
    basic_mortality = EnhancedMortality(gender="Male", use_bayesian=False)
    basic_alive, basic_deaths = basic_mortality.simulate_survival(age, n_sims, n_years)
    basic_life_exp = np.mean(basic_deaths - age)
    
    print(f"Basic SSA life expectancy: {basic_life_exp:.1f} years")
    print(f"  10th percentile: {np.percentile(basic_deaths - age, 10):.1f} years")
    print(f"  90th percentile: {np.percentile(basic_deaths - age, 90):.1f} years")
    
    # Healthy
    healthy_alive, healthy_deaths = healthy.simulate_survival(age, n_sims, n_years)
    healthy_life_exp = np.mean(healthy_deaths - age)
    
    print(f"\nHealthy non-smoker life expectancy: {healthy_life_exp:.1f} years")
    print(f"  10th percentile: {np.percentile(healthy_deaths - age, 10):.1f} years")
    print(f"  90th percentile: {np.percentile(healthy_deaths - age, 90):.1f} years")
    print(f"  Additional years vs SSA: +{healthy_life_exp - basic_life_exp:.1f}")
    
    # Poor health
    poor_alive, poor_deaths = poor.simulate_survival(age, n_sims, n_years)
    poor_life_exp = np.mean(poor_deaths - age)
    
    print(f"\nPoor health smoker life expectancy: {poor_life_exp:.1f} years")
    print(f"  10th percentile: {np.percentile(poor_deaths - age, 10):.1f} years")
    print(f"  90th percentile: {np.percentile(poor_deaths - age, 90):.1f} years")
    print(f"  Fewer years vs SSA: {poor_life_exp - basic_life_exp:.1f}")
    
    # Survival probabilities
    print("\nSurvival Probabilities")
    print("-" * 50)
    
    years_ahead = [5, 10, 15, 20, 25]
    for years in years_ahead:
        if years < n_years:
            basic_surv = np.mean(basic_alive[:, years])
            healthy_surv = np.mean(healthy_alive[:, years])
            poor_surv = np.mean(poor_alive[:, years])
            
            print(f"Probability of surviving {years} years (to age {age + years}):")
            print(f"  Basic SSA: {basic_surv:.1%}")
            print(f"  Healthy: {healthy_surv:.1%}")
            print(f"  Poor health: {poor_surv:.1%}")
            print()
    
    # Population calibration check
    print("Population Calibration Check")
    print("-" * 50)
    print("Creating population with characteristics matching SSA average...")
    
    # Create a population that should average to SSA
    pop_size = 10000
    np.random.seed(42)
    
    # 15% smokers
    smokers = np.random.random(pop_size) < 0.15
    
    # Income distribution (normal around 50th percentile)
    incomes = np.clip(np.random.normal(50, 20, pop_size), 1, 99)
    
    # Health distribution (20% excellent, 30% good, 30% average, 20% poor)
    health_probs = np.random.random(pop_size)
    healths = np.where(health_probs < 0.2, "excellent",
                       np.where(health_probs < 0.5, "good",
                               np.where(health_probs < 0.8, "average", "poor")))
    
    # Calculate average mortality rate
    avg_rate = 0
    for i in range(min(100, pop_size)):  # Sample for speed
        person = EnhancedMortality(
            gender="Male",
            use_bayesian=True,
            smoker=bool(smokers[i]),
            income_percentile=int(incomes[i]),
            health_status=healths[i]
        )
        avg_rate += person.get_mortality_rate(age)
    avg_rate /= min(100, pop_size)
    
    print(f"Average mortality rate for diverse population: {avg_rate:.4f}")
    print(f"SSA baseline rate: {basic_rate:.4f}")
    print(f"Ratio (should be ~1.0): {avg_rate/basic_rate:.2f}")
    
    if abs(avg_rate/basic_rate - 1.0) < 0.1:
        print("✓ Bayesian adjustment correctly calibrated to population average")
    else:
        print("⚠ Calibration may need adjustment")


if __name__ == "__main__":
    test_mortality_comparison()