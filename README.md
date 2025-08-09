# FinSim by PolicyEngine

A comprehensive financial simulation tool for comparing annuities with index fund investments, accounting for taxes, Social Security benefits, and mortality risk.

## Features

- **Annuity Analysis**: Compare multiple annuity proposals with IRR calculations
- **Monte Carlo Simulation**: Model index fund performance with customizable parameters
- **Tax Integration**: Uses PolicyEngine-US for accurate federal and state tax calculations
- **Social Security**: Includes COLA adjustments based on SSA uprating factors
- **Interactive Visualizations**: Portfolio paths, depletion probabilities, and tax impacts

## Installation

Using [uv](https://github.com/astral-sh/uv) (recommended):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/PolicyEngine/finsim
cd finsim

# Create virtual environment and install
uv venv
uv pip install -e ".[app]"
```

Or with pip:

```bash
pip install finsim
# For the Streamlit app:
pip install "finsim[app]"
```

## Usage

Run the Streamlit app:

```bash
uv run streamlit run app.py
# or
streamlit run app.py
```

## Components

### 1. Monte Carlo Simulator (`monte_carlo.py`)
- Simulates index fund performance (default: VT Total World Stock)
- Configurable returns, volatility, and dividend yields
- Calculates depletion probabilities and portfolio percentiles
- Supports dividend reinvestment strategies

### 2. Tax Calculator (`tax_calculator.py`)
- Integrates PolicyEngine-US for precise tax modeling
- Handles:
  - Long-term capital gains with basis tracking
  - Social Security benefit taxation
  - OBBBA senior deduction ($6,000 for 2025)
  - Federal and state taxes
- Projects SS benefits with COLA adjustments

### 3. Annuity Calculator (`annuity.py`)
- Calculates internal rate of return (IRR)
- Supports both fixed-term and life-contingent annuities
- Uses CDC mortality tables for survival weighting
- Handles taxable vs. tax-free (§104(a)(2)) annuities

### 4. Streamlit Interface (`app.py`)
- Input forms for:
  - Personal information (age, state, filing status)
  - Settlement amount
  - Social Security benefits
  - Multiple annuity proposals
- Interactive visualizations:
  - Monte Carlo simulation paths with percentile bands
  - Distribution of final portfolio values
  - Tax impact analysis
  - Capital gains inclusion ratio over time

## Key Assumptions

- **Default Index Fund**: VT (Vanguard Total World Stock)
  - Expected return: 8% annually
  - Volatility: 15.8% annually
  - Dividend yield: 2% annually
- **Tax Treatment**:
  - Personal injury settlements under IRC §104(a)(2) are tax-free
  - Index fund gains start at ~20% taxable fraction, increasing over time
  - California state tax applies; no tax on Social Security benefits
- **Social Security**:
  - Annual COLA adjustments based on CPI-W
  - Up to 85% taxable at federal level depending on income

## Example Scenarios

### Your Father's Case
- Age: 65
- Settlement: $527,530
- Social Security: $2,000/month
- State: California
- Three annuity proposals with varying terms and IRRs

The tool shows:
- Proposal A (life contingent): Lower monthly payment but longevity protection
- Proposal B (15-year certain): Higher IRR, fixed term
- Proposal C (10-year certain): Highest monthly payment, shortest term
- Index fund alternative: Higher expected return but ~20-35% depletion risk

## Limitations

- Mortality tables are simplified (CDC averages, not personalized)
- Tax calculations assume current law continues
- Market return assumptions based on historical data
- Does not model healthcare costs or long-term care needs
- State tax calculations limited to major states

## Contributing

Feel free to submit issues or pull requests to improve the tool.

## License

MIT