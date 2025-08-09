# FinSim Portfolio Simulation Flow

## Overview
FinSim performs Monte Carlo simulations of retirement portfolios, incorporating market returns, mortality risk, taxes, and various income sources. The simulation uses a "next-year tax payment" approach where taxes are calculated on the current year's income but paid from the following year's withdrawals.

## Complete Simulation Flow

### 1. **Initialization Phase**

#### A. Generate Return Matrix (Pre-computed)
```python
# Generate all returns upfront to ensure independence
return_gen = ReturnGenerator(expected_return, volatility)
growth_factors_matrix = return_gen.generate_returns(n_simulations, n_years)
```
- Generates a matrix of size (n_simulations × n_years)
- Each cell contains a growth factor (e.g., 1.07 for 7% return)
- Uses normal distribution with occasional fat tails (2% chance of 2.5-3.5σ moves)
- Capped at 4σ to prevent numerical overflow
- **This fixes the bug where simulations were getting repeated returns**

#### B. Load Mortality Tables
- Uses SSA mortality tables by age and gender
- Provides probability of death for each year of simulation

#### C. Initialize Arrays
- `portfolio_paths`: Track portfolio value over time
- `cost_basis`: For capital gains calculations
- `taxes_owed`: Tax liability calculated each year
- `taxes_paid`: Taxes actually paid (from prior year)
- Various income/expense tracking arrays

### 2. **Annual Simulation Loop** (for each year 1 to n_years)

For each year, the following steps occur in order:

#### Step 1: Update Age and Check Mortality
```python
age = current_age + year
if include_mortality:
    mort_rate = mortality_rates.get(age, 0)
    death_this_year = random() < mort_rate
    # Mark as dead for this and future years if died
```

#### Step 2: Get Pre-Generated Market Returns
```python
growth_factor = growth_factors_matrix[:, year-1]
```
- Uses the pre-computed return for this simulation and year
- Ensures no repeated values (the bug we fixed)

#### Step 3: Apply Market Growth to Portfolio
```python
current_portfolio = portfolio_paths[:, year-1]
portfolio_after_growth = current_portfolio * growth_factor
# Dead people's estates don't grow
```

#### Step 4: Calculate Dividend Income
```python
dividends = current_portfolio * (dividend_yield / 100)
```
- Dividends based on portfolio value at START of year (before growth)
- Currently assumes constant dividend yield

#### Step 5: Calculate Total Income Available
```python
# Employment income (stops at retirement)
wages = employment_income if age < retirement_age else 0

# Other guaranteed income
guaranteed_income = social_security + pension + annuity_income + wages

# Total income including dividends
total_income_available = guaranteed_income + dividends
```

#### Step 6: Calculate Withdrawal Need
```python
# Need = consumption + last year's taxes - available income
withdrawal_need = max(0, 
    annual_consumption + prior_year_tax_liability - total_income_available)
```
- **Key insight**: We pay LAST YEAR's taxes from THIS YEAR's withdrawal
- This avoids circular dependency (don't need to estimate tax rate)

#### Step 7: Calculate Capital Gains from Withdrawal
```python
# What fraction of portfolio is gains?
gain_fraction = max(0, (current_portfolio - cost_basis) / current_portfolio)
realized_gains = withdrawal_need * gain_fraction

# Update cost basis (reduced proportionally)
cost_basis = cost_basis * (1 - withdrawal_fraction)
```

#### Step 8: Calculate Taxes for THIS Year (to be paid NEXT year)
Using PolicyEngine-US for accurate tax calculation:
```python
tax_results = tax_calc.calculate_batch_taxes(
    capital_gains_array=realized_gains,
    social_security_array=social_security + pension + annuity,
    employment_income_array=wages,
    dividend_income_array=dividends,
    ages=ages,
    filing_status="SINGLE"
)
taxes_owed[year] = tax_results['total_tax']
prior_year_tax_liability = taxes_owed[year]  # For next year's withdrawal
```

PolicyEngine calculates:
- Federal income tax
- State income tax
- Tax on Social Security benefits
- Capital gains tax (at preferential rates)
- Tax on dividends (qualified dividend rates)
- Tax on employment income
- Standard deduction and other deductions
- Age-based benefits (extra standard deduction at 65+)

#### Step 9: Update Portfolio Value
```python
new_portfolio = portfolio_after_growth - withdrawal_need
portfolio_paths[:, year] = max(0, new_portfolio)
```

#### Step 10: Check for Portfolio Failure
```python
if current_portfolio > 0 and new_portfolio <= 0:
    failure_year[sim] = year
```

### 3. **Key Insights and Design Decisions**

#### Next-Year Tax Payment
- **Problem**: Calculating taxes requires knowing withdrawals, but withdrawals depend on taxes (circular)
- **Solution**: Pay this year's taxes from next year's withdrawal
- **Reality check**: This mirrors real life where taxes are paid in arrears

#### Portfolio Growth Dynamics
When a portfolio grows large enough:
1. Dividends increase (2% of larger portfolio)
2. Eventually dividends + other income > consumption
3. Withdrawals drop to zero
4. Portfolio compounds freely (no drag from withdrawals)
5. This creates realistic "runaway wealth" scenarios for lucky simulations

#### Return Generation
- All returns generated upfront in a matrix
- Prevents the bug where simulations got stuck with repeated returns
- Uses normal distribution with realistic fat tails
- Independent across years and simulations

### 4. **Example Walkthrough**

**Year 1 for Simulation #0:**
```
Starting portfolio: $500,000
Age: 65
Employment income: $0 (retired)
Social Security: $24,000
Consumption need: $60,000

1. Market return: 7% (growth_factor = 1.07)
2. Portfolio after growth: $535,000
3. Dividends: $10,000 (2% of $500k)
4. Total income: $24,000 + $10,000 = $34,000
5. Withdrawal need: $60,000 - $34,000 = $26,000
6. Capital gains: $0 (no gains in year 1)
7. Taxes calculated: ~$3,000 (on SS + dividends)
8. New portfolio: $535,000 - $26,000 = $509,000
9. Next year will need to withdraw extra $3,000 for taxes
```

### 5. **Output Statistics**

The simulation produces:
- **Portfolio paths**: Value over time for each simulation
- **Success rate**: Percentage that don't run out of money
- **Percentiles**: 5th, 50th (median), 95th percentiles over time
- **Failure analysis**: When portfolios fail
- **Tax burden**: Total taxes paid over retirement
- **Estate values**: Portfolio value at death (if mortality included)

### 6. **Visualization**

The app displays:
- Portfolio percentiles over time (90% confidence interval)
- Success/failure rates
- Distribution of final portfolio values
- Cash flow components (withdrawals, taxes, dividends)
- Estate value distribution

## Configuration Parameters

### Required Inputs
- `initial_portfolio`: Starting portfolio value
- `current_age`: Age at start of simulation
- `annual_consumption`: Annual spending need
- `expected_return`: Expected annual return (%)
- `return_volatility`: Annual volatility (%)
- `dividend_yield`: Annual dividend yield (%)

### Optional Inputs
- `employment_income`: Annual wages (stops at retirement_age)
- `retirement_age`: When employment income stops
- `social_security`: Annual SS benefits
- `pension`: Other guaranteed income
- `include_mortality`: Whether to model death probability
- `state`: For state tax calculations

## Tax Calculation Details

PolicyEngine-US provides accurate tax modeling including:
- Progressive tax brackets
- Standard deduction ($14,600 for single filers in 2024)
- Extra standard deduction for 65+ ($1,950)
- Qualified dividend rates (0%, 15%, or 20%)
- Long-term capital gains rates (0%, 15%, or 20%)
- Net investment income tax (3.8% on high earners)
- State income taxes (varies by state)
- Taxable Social Security calculation (up to 85% taxable)

## Common Scenarios

### Early Retiree with Employment
- Ages 50-65 with employment income
- Employment income reduces withdrawal needs
- Higher taxes due to wages
- Portfolio can grow during working years

### Traditional Retiree
- Age 65+ with SS and portfolio
- No employment income
- Lower tax rates
- Focus on portfolio longevity

### High Net Worth
- Large initial portfolio
- Dividends may exceed spending needs
- Portfolio grows without withdrawals
- Significant estate value likely

## Validation and Testing

The simulation includes:
- Comprehensive test suite for return generation
- No repeated values across years
- Proper statistical distribution
- Independence verification
- Tax calculation validation against PolicyEngine

## Performance Considerations

- Pre-generating returns improves performance
- Batch tax calculations for all simulations
- Vectorized operations throughout
- Progress updates for user feedback
- Typical runtime: ~30 seconds for 1000 simulations × 30 years