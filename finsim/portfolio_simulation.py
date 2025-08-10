"""Portfolio simulation with next-year tax payment (more realistic)."""

import numpy as np

from .mortality import get_mortality_rates  # Keep local for now as fallback
from .tax import TaxCalculator

try:
    from mortality import MortalityTable  # Try to use the package

    USE_MORTALITY_PACKAGE = True
except ImportError:
    USE_MORTALITY_PACKAGE = False
    from .mortality_enhanced import EnhancedMortality
from .cola import get_consumption_inflation_factors, get_ssa_cola_factors
from .return_generator import ReturnGenerator


def validate_inputs(
    n_simulations: int,
    n_years: int,
    initial_portfolio: float,
    current_age: int,
    social_security: float,
    pension: float,
    employment_income: float,
    retirement_age: int,
    annuity_annual: float,
    annuity_guarantee_years: int,
    annual_consumption: float,
    expected_return: float,
    return_volatility: float,
    dividend_yield: float,
    state: str,
    gender: str,
    annuity_type: str = "Life Only",
    has_annuity: bool = False,
    spouse_age: int | None = None,
    spouse_gender: str | None = None,
    spouse_social_security: float | None = None,
    spouse_pension: float | None = None,
    spouse_employment_income: float | None = None,
    spouse_retirement_age: int | None = None,
    has_spouse: bool = False,
) -> None:
    """Validate all input parameters for portfolio simulation.

    Raises:
        ValueError: If any input parameter is invalid.
    """
    # Validate basic parameters
    if n_simulations <= 0:
        raise ValueError(f"n_simulations must be positive, got {n_simulations}")
    if n_simulations > 100000:
        raise ValueError(f"n_simulations too large ({n_simulations}), maximum is 100,000")

    if n_years <= 0:
        raise ValueError(f"n_years must be positive, got {n_years}")
    if n_years > 100:
        raise ValueError(f"n_years too large ({n_years}), maximum is 100")

    if initial_portfolio < 0:
        raise ValueError(f"initial_portfolio cannot be negative, got {initial_portfolio}")
    if initial_portfolio > 1e10:
        raise ValueError(
            f"initial_portfolio too large ({initial_portfolio:.0f}), maximum is $10 billion"
        )

    # Validate age parameters
    if current_age < 18:
        raise ValueError(f"current_age must be at least 18, got {current_age}")
    if current_age > 120:
        raise ValueError(f"current_age cannot exceed 120, got {current_age}")

    if retirement_age < current_age:
        raise ValueError(
            f"retirement_age ({retirement_age}) cannot be less than current_age ({current_age})"
        )
    if retirement_age > 100:
        raise ValueError(f"retirement_age cannot exceed 100, got {retirement_age}")

    # Validate income sources
    if social_security < 0:
        raise ValueError(f"social_security cannot be negative, got {social_security}")
    if social_security > 200000:
        raise ValueError(
            f"social_security seems unrealistic ({social_security}), maximum expected is $200,000"
        )

    if pension < 0:
        raise ValueError(f"pension cannot be negative, got {pension}")
    if pension > 1000000:
        raise ValueError(f"pension seems unrealistic ({pension}), maximum expected is $1,000,000")

    if employment_income < 0:
        raise ValueError(f"employment_income cannot be negative, got {employment_income}")
    if employment_income > 10000000:
        raise ValueError(
            f"employment_income seems unrealistic ({employment_income}), maximum expected is $10,000,000"
        )

    # Validate annuity parameters
    if annuity_annual < 0:
        raise ValueError(f"annuity_annual cannot be negative, got {annuity_annual}")
    if annuity_annual > 1000000:
        raise ValueError(
            f"annuity_annual seems unrealistic ({annuity_annual}), maximum expected is $1,000,000"
        )

    if annuity_guarantee_years < 0:
        raise ValueError(
            f"annuity_guarantee_years cannot be negative, got {annuity_guarantee_years}"
        )
    if annuity_guarantee_years > 50:
        raise ValueError(
            f"annuity_guarantee_years too large ({annuity_guarantee_years}), maximum is 50"
        )

    # Validate consumption
    if annual_consumption < 0:
        raise ValueError(f"annual_consumption cannot be negative, got {annual_consumption}")
    if annual_consumption > 10000000:
        raise ValueError(
            f"annual_consumption seems unrealistic ({annual_consumption}), maximum expected is $10,000,000"
        )

    # Validate market parameters
    if expected_return < -0.5:
        raise ValueError(f"expected_return too low ({expected_return}), minimum is -50%")
    if expected_return > 0.5:
        raise ValueError(f"expected_return too high ({expected_return}), maximum is 50%")

    if return_volatility < 0:
        raise ValueError(f"return_volatility cannot be negative, got {return_volatility}")
    if return_volatility > 1.0:
        raise ValueError(f"return_volatility too high ({return_volatility}), maximum is 100%")

    if dividend_yield < 0:
        raise ValueError(f"dividend_yield cannot be negative, got {dividend_yield}")
    if dividend_yield > 0.2:
        raise ValueError(f"dividend_yield too high ({dividend_yield}), maximum is 20%")

    # Validate state
    VALID_STATES = [
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    ]
    if state not in VALID_STATES:
        raise ValueError(f"Invalid state '{state}'. Must be one of: {', '.join(VALID_STATES)}")

    # Validate gender
    VALID_GENDERS = ["Male", "Female"]
    if gender not in VALID_GENDERS:
        raise ValueError(f"Invalid gender '{gender}'. Must be 'Male' or 'Female'")

    # Validate annuity type only if has_annuity is True
    if has_annuity:
        VALID_ANNUITY_TYPES = ["Life Only", "Life Contingent with Guarantee", "Fixed Period"]
        if annuity_type not in VALID_ANNUITY_TYPES:
            raise ValueError(
                f"Invalid annuity_type '{annuity_type}'. Must be one of: {', '.join(VALID_ANNUITY_TYPES)}"
            )

    # Validate spouse parameters if has_spouse
    if has_spouse:
        if spouse_age is None:
            raise ValueError("spouse_age is required when has_spouse=True")
        if spouse_age < 18:
            raise ValueError(f"spouse_age must be at least 18, got {spouse_age}")
        if spouse_age > 120:
            raise ValueError(f"spouse_age cannot exceed 120, got {spouse_age}")

        if spouse_gender is None:
            raise ValueError("spouse_gender is required when has_spouse=True")
        if spouse_gender not in VALID_GENDERS:
            raise ValueError(f"Invalid spouse_gender '{spouse_gender}'. Must be 'Male' or 'Female'")

        if spouse_social_security is not None:
            if spouse_social_security < 0:
                raise ValueError(
                    f"spouse_social_security cannot be negative, got {spouse_social_security}"
                )
            if spouse_social_security > 200000:
                raise ValueError(
                    f"spouse_social_security seems unrealistic ({spouse_social_security})"
                )

        if spouse_pension is not None:
            if spouse_pension < 0:
                raise ValueError(f"spouse_pension cannot be negative, got {spouse_pension}")
            if spouse_pension > 1000000:
                raise ValueError(f"spouse_pension seems unrealistic ({spouse_pension})")

        if spouse_employment_income is not None:
            if spouse_employment_income < 0:
                raise ValueError(
                    f"spouse_employment_income cannot be negative, got {spouse_employment_income}"
                )
            if spouse_employment_income > 10000000:
                raise ValueError(
                    f"spouse_employment_income seems unrealistic ({spouse_employment_income})"
                )

        if spouse_retirement_age is not None:
            if spouse_retirement_age < spouse_age:
                raise ValueError(
                    f"spouse_retirement_age ({spouse_retirement_age}) cannot be less than spouse_age ({spouse_age})"
                )
            if spouse_retirement_age > 100:
                raise ValueError(
                    f"spouse_retirement_age cannot exceed 100, got {spouse_retirement_age}"
                )


def simulate_portfolio(
    # Basic parameters
    n_simulations: int,
    n_years: int,
    initial_portfolio: float,
    # Age and mortality
    current_age: int,
    include_mortality: bool,
    # Income sources
    social_security: float,
    pension: float,
    employment_income: float,  # Wages and salaries (in today's dollars)
    retirement_age: int,  # Age when employment income stops
    # Consumption
    annual_consumption: float,  # Total consumption need (not net)
    # Market parameters
    expected_return: float,
    return_volatility: float,
    dividend_yield: float,
    # Tax parameters
    state: str,
    # Annuity parameters
    has_annuity: bool,
    annuity_type: str = "Life Only",  # Default to Life Only if not specified
    annuity_annual: float = 0,
    annuity_guarantee_years: int = 0,
    # Optional parameters with defaults
    employment_growth_rate: float = 0.0,  # Annual nominal wage growth percentage (e.g., 3.0 for 3%)
    # Spouse parameters (optional)
    has_spouse: bool = False,
    spouse_age: int = None,
    spouse_gender: str = None,
    spouse_social_security: float = 0,
    spouse_pension: float = 0,
    spouse_employment_income: float = 0,
    spouse_retirement_age: int = None,
    spouse_employment_growth_rate: float = 0.0,
    # Progress callback
    progress_callback=None,
    # Gender for primary person (optional, defaults to Male)
    gender: str = "Male",
    # Enhanced mortality parameters (optional)
    use_enhanced_mortality: bool = False,
    smoker: bool | None = None,
    income_percentile: int | None = None,
    health_status: str | None = None,
    spouse_smoker: bool | None = None,
    spouse_income_percentile: int | None = None,
    spouse_health_status: str | None = None,
) -> dict[str, np.ndarray]:
    """
    Run Monte Carlo simulation with next-year tax payment.

    Key difference: We withdraw exactly what we need for consumption each year,
    then pay taxes the following year from that year's withdrawal.
    This is more realistic and avoids circular dependency.
    """
    # Validate all inputs
    validate_inputs(
        n_simulations=n_simulations,
        n_years=n_years,
        initial_portfolio=initial_portfolio,
        current_age=current_age,
        social_security=social_security,
        pension=pension,
        employment_income=employment_income,
        retirement_age=retirement_age,
        annuity_annual=annuity_annual,
        annuity_guarantee_years=annuity_guarantee_years,
        annual_consumption=annual_consumption,
        expected_return=expected_return / 100.0,  # Convert from percentage
        return_volatility=return_volatility / 100.0,  # Convert from percentage
        dividend_yield=dividend_yield / 100.0,  # Convert from percentage
        state=state,
        gender=gender,
        annuity_type=annuity_type,
        has_annuity=has_annuity,
        spouse_age=spouse_age,
        spouse_gender=spouse_gender,
        spouse_social_security=spouse_social_security,
        spouse_pension=spouse_pension,
        spouse_employment_income=spouse_employment_income,
        spouse_retirement_age=spouse_retirement_age,
        has_spouse=has_spouse,
    )

    # Initialize tax calculator
    filing_status = "JOINT" if has_spouse else "SINGLE"
    tax_calc = TaxCalculator(state=state, year=2025)

    # Get inflation factors from PolicyEngine-US projections
    # These use actual SSA uprating (CPI-W) and C-CPI-U schedules
    START_YEAR = 2025  # TODO: Make this configurable
    cola_factors = get_ssa_cola_factors(START_YEAR, n_years)
    inflation_factors = get_consumption_inflation_factors(START_YEAR, n_years)

    # Get mortality rates if needed
    if USE_MORTALITY_PACKAGE and include_mortality:
        # Use the mortality package for clean SSA tables
        gender_lower = gender.lower() if gender else "male"
        table = MortalityTable(gender_lower)
        mortality_rates = {
            age: table.get_rate(age)
            for age in range(current_age, min(current_age + n_years + 1, 121))
        }

        if has_spouse:
            spouse_gender_lower = spouse_gender.lower() if spouse_gender else "female"
            spouse_table = MortalityTable(spouse_gender_lower)
            spouse_mortality_rates = {
                age: spouse_table.get_rate(age)
                for age in range(spouse_age, min(spouse_age + n_years + 1, 121))
            }
        else:
            spouse_mortality_rates = {}
    elif use_enhanced_mortality and include_mortality and not USE_MORTALITY_PACKAGE:
        # Use enhanced mortality with individual characteristics (fallback)
        mortality_calculator = EnhancedMortality(
            gender=gender,
            use_bayesian=True,
            smoker=smoker,
            income_percentile=income_percentile,
            health_status=health_status,
        )
        mortality_rates = {
            age: mortality_calculator.get_mortality_rate(age)
            for age in range(current_age, min(current_age + n_years + 1, 121))
        }

        if has_spouse:
            spouse_mortality_calculator = EnhancedMortality(
                gender=spouse_gender,
                use_bayesian=True,
                smoker=spouse_smoker,
                income_percentile=spouse_income_percentile,
                health_status=spouse_health_status,
            )
            spouse_mortality_rates = {
                age: spouse_mortality_calculator.get_mortality_rate(age)
                for age in range(spouse_age, min(spouse_age + n_years + 1, 121))
            }
        else:
            spouse_mortality_rates = {}
    else:
        # Use basic SSA tables (local fallback)
        mortality_rates = get_mortality_rates(gender) if include_mortality else {}
        spouse_mortality_rates = (
            get_mortality_rates(spouse_gender) if (include_mortality and has_spouse) else {}
        )

    # Generate all returns upfront using the return generator
    # This fixes the bug where returns were getting repeated
    return_gen = ReturnGenerator(
        expected_return=expected_return / 100, volatility=return_volatility / 100
    )
    growth_factors_matrix = return_gen.generate_returns(n_simulations, n_years)

    # Initialize arrays
    portfolio_paths = np.zeros((n_simulations, n_years + 1))
    portfolio_paths[:, 0] = initial_portfolio

    # Track cost basis for capital gains calculations
    cost_basis = np.full(n_simulations, initial_portfolio)

    # Track components for analysis
    dividend_income = np.zeros((n_simulations, n_years))
    capital_gains = np.zeros((n_simulations, n_years))
    gross_withdrawals = np.zeros((n_simulations, n_years))
    taxes_owed = np.zeros((n_simulations, n_years))  # Taxes calculated this year
    taxes_paid = np.zeros((n_simulations, n_years))  # Taxes actually paid this year
    net_withdrawals = np.zeros((n_simulations, n_years))

    failure_year = np.full(n_simulations, n_years + 1)
    alive_mask = np.ones((n_simulations, n_years + 1), dtype=bool)
    spouse_alive_mask = np.ones((n_simulations, n_years + 1), dtype=bool) if has_spouse else None

    # Track annuity income
    annuity_income = np.zeros((n_simulations, n_years))

    # Track prior year's tax liability (to be paid this year)
    prior_year_tax_liability = np.zeros(n_simulations)

    # Simulate each year
    for year in range(1, n_years + 1):
        age = current_age + year

        # Progress callback with partial results
        if progress_callback:
            progress_callback(year, n_years, age, {"portfolio_paths": portfolio_paths})

        # Calculate annuity income for this year
        if has_annuity:
            if annuity_type == "Fixed Period":
                gets_annuity = year <= annuity_guarantee_years
                annuity_income[:, year - 1] = annuity_annual if gets_annuity else 0
            elif annuity_type == "Life Only":
                annuity_income[:, year - 1] = np.where(alive_mask[:, year - 1], annuity_annual, 0)
            else:  # Life Contingent with Guarantee
                in_guarantee = year <= annuity_guarantee_years
                annuity_income[:, year - 1] = np.where(
                    alive_mask[:, year - 1] | in_guarantee, annuity_annual, 0
                )

        # Mortality
        if include_mortality and age > current_age:
            mort_rate = mortality_rates.get(age, 0)
            death_this_year = np.random.random(n_simulations) < mort_rate
            alive_mask[death_this_year, year:] = False

            # Spouse mortality
            if has_spouse:
                spouse_current_age = spouse_age + year
                spouse_mort_rate = spouse_mortality_rates.get(spouse_current_age, 0)
                spouse_death_this_year = np.random.random(n_simulations) < spouse_mort_rate
                spouse_alive_mask[spouse_death_this_year, year:] = False

        # Only simulate for those still alive and not failed
        active = alive_mask[:, year] & (portfolio_paths[:, year - 1] > 0)

        # Get pre-generated growth factors for this year
        growth_factor = growth_factors_matrix[:, year - 1]

        # Portfolio evolution (only for living people)
        current_portfolio = portfolio_paths[:, year - 1]
        portfolio_after_growth = np.where(
            alive_mask[:, year],
            current_portfolio * growth_factor,
            current_portfolio,  # Dead people's estates don't grow
        )

        # Dividends (only for living people's portfolios)
        dividends = np.where(alive_mask[:, year], current_portfolio * (dividend_yield / 100), 0)
        dividend_income[:, year - 1] = dividends

        # Calculate withdrawal needed for consumption AND last year's taxes
        # This is the KEY CHANGE - we pay last year's taxes from this year's withdrawal

        # Employment income (stops at retirement age) with growth
        # Apply compound growth for years worked
        if age <= retirement_age:
            years_of_growth = year - 1  # Years since start
            # employment_growth_rate is already in percentage form (e.g., 5.0 for 5%)
            growth_factor = (1 + employment_growth_rate / 100) ** years_of_growth
            wages = employment_income * growth_factor
        else:
            wages = 0

        # Spouse income if applicable
        spouse_wages = np.zeros(n_simulations)
        spouse_ss = np.zeros(n_simulations)
        spouse_pens = np.zeros(n_simulations)
        if has_spouse:
            spouse_current_age = spouse_age + year
            # Spouse employment income (only if alive and working) with growth
            if spouse_current_age <= spouse_retirement_age:
                years_of_growth = year - 1  # Years since start
                # spouse_employment_growth_rate is already in percentage form (e.g., 5.0 for 5%)
                growth_factor = (1 + spouse_employment_growth_rate / 100) ** years_of_growth
                grown_spouse_income = spouse_employment_income * growth_factor
                spouse_wages = np.where(spouse_alive_mask[:, year], grown_spouse_income, 0)
            # Spouse SS and pension (only if alive)
            spouse_ss = np.where(spouse_alive_mask[:, year], spouse_social_security, 0)
            spouse_pens = np.where(spouse_alive_mask[:, year], spouse_pension, 0)

        # Apply COLA to Social Security using actual SSA uprating schedule
        # Note: Pensions typically don't have COLA unless specified
        cola_factor = cola_factors[year - 1]  # Get pre-calculated factor

        # Apply COLA to Social Security (but not pensions, which typically don't have COLA)
        current_social_security = social_security * cola_factor
        current_spouse_ss = spouse_ss * cola_factor

        # Total household income
        total_employment = wages + spouse_wages
        total_ss_pension = current_social_security + pension + current_spouse_ss + spouse_pens

        guaranteed_income = total_ss_pension + annuity_income[:, year - 1] + total_employment
        total_income_available = guaranteed_income + dividends

        # Calculate inflation-adjusted consumption using actual C-CPI-U projections
        inflation_factor = inflation_factors[year - 1]  # Get pre-calculated factor
        current_consumption = annual_consumption * inflation_factor

        # What we need to withdraw = inflation-adjusted consumption + last year's taxes - available income
        withdrawal_need = np.zeros(n_simulations)
        withdrawal_need[active] = np.maximum(
            0,
            current_consumption + prior_year_tax_liability[active] - total_income_available[active],
        )

        # This is our actual gross withdrawal (no tax gross-up needed!)
        actual_gross_withdrawal = withdrawal_need
        gross_withdrawals[:, year - 1] = actual_gross_withdrawal

        # Calculate realized capital gains for tax purposes
        gain_fraction = np.where(
            current_portfolio > 0,
            np.maximum(0, (current_portfolio - cost_basis) / current_portfolio),
            0,
        )
        realized_gains = actual_gross_withdrawal * gain_fraction
        capital_gains[:, year - 1] = realized_gains

        # Update cost basis
        withdrawal_fraction = np.where(
            current_portfolio > 0, actual_gross_withdrawal / current_portfolio, 0
        )
        cost_basis = cost_basis * (1 - withdrawal_fraction)

        # Calculate taxes owed on THIS YEAR's income (to be paid NEXT year)
        if active.any():
            # Combine all SS and pension income for household
            total_ss_and_pension = total_ss_pension + annuity_income[:, year - 1]
            ages_array = np.full(n_simulations, age)

            # Employment income for tax calculation (household total)
            employment_income_array = np.full(n_simulations, total_employment)

            tax_results = tax_calc.calculate_batch_taxes(
                capital_gains_array=realized_gains,
                social_security_array=total_ss_and_pension,
                ages=ages_array,
                filing_status=filing_status,
                dividend_income_array=dividends,
                employment_income_array=employment_income_array,
            )

            # Store tax liability for next year
            taxes_owed[:, year - 1] = tax_results["total_tax"]
            prior_year_tax_liability = tax_results["total_tax"].copy()

        # Record taxes actually paid this year (from last year's liability)
        if year > 1:
            taxes_paid[:, year - 1] = taxes_owed[:, year - 2]

        # Net withdrawals (what's available for consumption after paying last year's taxes)
        net_withdrawals[:, year - 1] = actual_gross_withdrawal - taxes_paid[:, year - 1]

        # New portfolio value
        new_portfolio = portfolio_after_growth - actual_gross_withdrawal

        # Check for failures
        newly_failed = (current_portfolio > 0) & (new_portfolio < 0)
        failure_year[newly_failed & (failure_year > n_years)] = year

        # Update portfolio
        # Remove artificial cap - let the 4-sigma clipping handle extremes
        portfolio_paths[:, year] = np.maximum(0, new_portfolio)

    # Calculate estate values at death
    estate_at_death = np.full(n_simulations, np.nan)
    for i in range(n_simulations):
        death_years = np.where(~alive_mask[i, :])[0]
        if len(death_years) > 0:
            death_year = death_years[0]
            if death_year > 0:
                estate_at_death[i] = portfolio_paths[i, death_year - 1]

    return {
        "portfolio_paths": portfolio_paths,
        "failure_year": failure_year,
        "alive_mask": alive_mask,
        "estate_at_death": estate_at_death,
        "annuity_income": annuity_income,
        "dividend_income": dividend_income,
        "capital_gains": capital_gains,
        "gross_withdrawals": gross_withdrawals,
        "taxes_owed": taxes_owed,
        "taxes_paid": taxes_paid,
        "net_withdrawals": net_withdrawals,
        "cost_basis": cost_basis,
    }
