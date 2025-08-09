# Interactive Examples

The documentation includes interactive Jupyter notebooks that demonstrate FinSim usage:

- **{doc}`basic_simulation`**: Introduction to Monte Carlo retirement simulation with mortality modeling

## Running Notebooks

### Prerequisites

```bash
pip install finsim[app]  # Installs all dependencies including Jupyter
```

### Options

1. **View online**: Browse notebooks directly in this documentation
2. **Download and run locally**: Get notebooks from the [GitHub repository](https://github.com/PolicyEngine/finsim/tree/main/docs/)
3. **Colab**: Click the Colab badge at the top of each notebook
4. **Binder**: Launch interactive environment without installation

## Data Requirements

Notebooks use real market data when possible:
- Cached data is used when available
- Falls back to sample/synthetic data if network fails
- Clear indicators show when real vs. synthetic data is used

## Additional Examples

For more comprehensive examples and tests that can serve as usage patterns, see the `tests/` directory in the repository.