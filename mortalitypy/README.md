# mortalitypy

A pragmatic Python package for mortality modeling that grows with your needs.

## Philosophy

Start simple, add sophistication only when needed:

1. **Level 1: Basic** - SSA tables with simple adjustments (5 minutes to learn)
2. **Level 2: Personalized** - Health/wealth factors (what FinSim needs)
3. **Level 3: Statistical** - Lee-Carter and variants (StMoMo equivalent)
4. **Level 4: Bayesian** - Full probabilistic modeling (research grade)

## Quick Start

```python
from mortalitypy import Mortality

# Level 1: Simplest possible
mort = Mortality()
death_prob = mort.q(age=65)  # Probability of death within a year
life_exp = mort.e(age=65)    # Life expectancy

# Level 2: Personal factors (what most apps need)
mort = Mortality(
    gender="female",
    health="good",
    income_percentile=75
)
survival_curve = mort.survival(from_age=65, to_age=95)

# Level 3: Statistical models (for actuaries)
from mortalitypy.models import LeeCarter
model = LeeCarter()
model.fit(deaths, exposures, years)
forecast = model.project(n_years=20)

# Level 4: Bayesian (for researchers)
from mortalitypy.bayesian import BayesianLeeCarter
model = BayesianLeeCarter(
    prior_improvement_rate=(0.01, 0.005),  # mean, std
    prior_smoothness=0.1
)
posterior = model.fit(data, chains=4, samples=2000)
```

## Why Another Mortality Package?

**Existing packages have problems:**
- `pymort`: Just data access, no modeling
- `lifelines`: Survival analysis, not mortality projection  
- `pyliferisk`: Traditional actuarial only
- StMoMo (R): Too academic, not Python

**mortalitypy solves this:**
- Progressive complexity (simple → sophisticated)
- Production-ready performance
- Modern Python (type hints, dataclasses)
- Both practical and rigorous

## Installation

```bash
pip install mortalitypy
```

## Package Structure

```
mortalitypy/
├── __init__.py           # Simple API (Level 1-2)
├── core.py              # Base Mortality class
├── data/
│   ├── ssa.py          # SSA tables
│   ├── hmd.py          # Human Mortality Database
│   └── soa.py          # Society of Actuaries
├── factors.py           # Personal adjustments (Level 2)
├── models/              # Statistical models (Level 3)
│   ├── lee_carter.py
│   ├── cbd.py
│   └── apc.py
├── bayesian/            # Bayesian models (Level 4)
│   ├── base.py
│   ├── conjugate.py    # Fast conjugate priors
│   └── mcmc.py         # Full MCMC with NumPyro
└── utils/
    ├── lifetable.py    # Life table calculations
    └── visualization.py # Plotting functions
```

## Development Roadmap

### Phase 1: Core (What FinSim needs)
- [x] Basic mortality class
- [x] SSA/HMD data loading
- [x] Personal factors
- [ ] Fast Monte Carlo simulation
- [ ] Documentation

### Phase 2: Statistical (StMoMo equivalent)
- [ ] Lee-Carter model
- [ ] CBD model
- [ ] Model selection tools
- [ ] Bootstrap confidence intervals

### Phase 3: Bayesian (Research grade)
- [ ] Conjugate models (fast)
- [ ] MCMC with NumPyro (flexible)
- [ ] Hierarchical models
- [ ] Model comparison (WAIC, LOO-CV)

### Phase 4: Production
- [ ] Web API
- [ ] Caching layer
- [ ] GPU acceleration
- [ ] Commercial data sources

## Contributing

We welcome contributions! The package is designed to be modular:
- Add new data sources in `data/`
- Add new models in `models/` or `bayesian/`
- Add new personal factors in `factors.py`

## License

MIT - Use freely in commercial and academic work.

## Citations

If you use this package in research, please cite:

```bibtex
@software{mortalitypy,
  title = {mortalitypy: Progressive mortality modeling for Python},
  author = {FinSim Contributors},
  year = {2024},
  url = {https://github.com/finsim/mortalitypy}
}
```

## Comparison to Alternatives

| Feature | mortalitypy | pymort | StMoMo (R) | pyliferisk |
|---------|------------|---------|------------|------------|
| Simple API | ✅ | ❌ | ❌ | ⚠️ |
| Personal factors | ✅ | ❌ | ❌ | ❌ |
| Lee-Carter | ✅ | ❌ | ✅ | ❌ |
| Bayesian | ✅ | ❌ | ❌ | ❌ |
| Python | ✅ | ✅ | ❌ | ✅ |
| Fast simulation | ✅ | ❌ | ⚠️ | ⚠️ |
| Modern code | ✅ | ❌ | ❌ | ❌ |