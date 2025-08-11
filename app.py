"""FinSim retirement planning simulator using modular package structure."""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import warnings
import logging
import os

# Suppress warnings
warnings.filterwarnings('ignore')
# Suppress PyTorch warnings specifically
os.environ['PYTORCH_DISABLE_WARNINGS'] = '1'
logging.getLogger('torch').setLevel(logging.ERROR)

# Import FinSim modules
from finsim.simulation import SimulationConfig, RetirementSimulation
from finsim.mortality import get_mortality_rates, calculate_survival_curve
from finsim.market import MarketDataFetcher
from finsim.tax import TaxCalculator
from finsim.portfolio_simulation import simulate_portfolio

# Configure page
st.set_page_config(
    page_title="FinSim by PolicyEngine",
    page_icon="💰",
    layout="wide"
)

st.title("💰 FinSim by PolicyEngine")
st.markdown("""
Financial simulator for retirement planning using Monte Carlo methods with real market data calibration.
All calculations are in **real (inflation-adjusted) terms** and performed **yearly**.
Tax calculations powered by PolicyEngine-US for accurate federal and state tax modeling.
""")

# Sidebar for inputs
# Add PolicyEngine logo at top of sidebar (centered)
col1, col2, col3 = st.sidebar.columns([1, 2, 1])
with col2:
    try:
        st.image("policyengine_logo.png", width=150)
    except:
        pass  # Logo file not found

st.sidebar.header("👤 Demographics")

col1, col2 = st.sidebar.columns(2)
with col1:
    current_age = st.number_input("Current Age", 18, 100, 65)
    retirement_age = st.number_input("Retirement Age", current_age, 100, max(current_age, 65))
with col2:
    max_age = st.number_input("Planning Horizon", current_age + 10, 120, 95)
    gender = st.selectbox("Gender (for mortality)", ["Male", "Female"])

# Spouse option
has_spouse = st.sidebar.checkbox(
    "Include Spouse",
    value=False,
    help="Model a married couple (files jointly for taxes)"
)

spouse_age = current_age
spouse_gender = "Female" if gender == "Male" else "Male"
spouse_employment_income = 0
spouse_employment_growth_rate = 0.0
spouse_social_security = 0
spouse_pension = 0
spouse_retirement_age = retirement_age

if has_spouse:
    st.sidebar.markdown("**Spouse Details**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        spouse_age = st.number_input("Spouse Age", 18, 100, current_age)
    with col2:
        spouse_gender = st.selectbox("Spouse Gender", ["Male", "Female"], 
                                    index=1 if gender == "Male" else 0)

# State for tax calculations
state = st.sidebar.selectbox(
    "State (for taxes)",
    ["CA", "NY", "TX", "FL", "WA", "IL", "PA", "OH", "GA", "NC", "MI", "NJ", "VA", "MA", "AZ", "IN", "TN", "MO", "MD", "WI", "MN", "CO", "AL", "SC", "LA", "KY", "OR", "OK", "CT", "UT", "IA", "NV", "AR", "MS", "KS", "NM", "NE", "WV", "ID", "HI", "NH", "ME", "RI", "MT", "DE", "SD", "ND", "AK", "DC", "VT", "WY"],
    index=0,  # Default to CA
    help="State of residence for tax calculations"
)

st.sidebar.header("💸 Annual Consumption")
annual_consumption = st.sidebar.number_input(
    "Annual Spending Need ($)",
    min_value=0,
    value=60_000,
    step=5_000,
    format="%d",
    help="How much you need to spend each year (in today's dollars, real terms)"
)

st.sidebar.header("💰 Assets & Market")
initial_portfolio = st.sidebar.number_input(
    "Current Portfolio Value ($)",
    min_value=0,
    value=500_000,
    step=10_000,
    format="%d",
    help="Current value of investable assets (stocks, bonds, etc.)"
)

# Fund ticker in the same section as portfolio
fund_ticker = st.sidebar.text_input(
    "Index Fund Ticker",
    value="VT",
    help="Common funds: VT (2008+), VOO (2010+), SPY (1993+), QQQ (1999+), VTI (2001+)"
)

st.sidebar.header("🏦 Income Sources")

# Primary person's income
if has_spouse:
    st.sidebar.markdown("**Your Income**")

employment_income = st.sidebar.number_input(
    "Annual Employment Income ($)" if not has_spouse else "Your Employment Income ($)",
    min_value=0,
    value=0,
    step=5_000,
    format="%d",
    help="Annual wages and salaries (in today's dollars, stops at retirement age)"
)

if employment_income > 0:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        retirement_age = st.number_input(
            "Retirement Age" if not has_spouse else "Your Retirement Age",
            min_value=current_age,
            max_value=75,
            value=max(current_age, 65),
            help="Age when employment income stops"
        )
    with col2:
        employment_growth_rate = st.number_input(
            "Income Growth (%)",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.5,
            format="%.1f",
            help="Annual nominal wage growth (includes inflation)"
        )
else:
    retirement_age = current_age  # No retirement if no employment income
    employment_growth_rate = 0.0

social_security = st.sidebar.number_input(
    "Annual Social Security ($)" if not has_spouse else "Your Social Security ($)",
    min_value=0,
    value=0,  # Default to 0 to avoid confusion
    step=1_000,
    format="%d",
    help="Annual Social Security benefits (in today's dollars, with automatic COLA adjustments)"
)

pension = st.sidebar.number_input(
    "Annual Pension/Other Income ($)" if not has_spouse else "Your Pension ($)",
    min_value=0,
    value=0,
    step=1_000,
    format="%d",
    help="Other guaranteed annual income (in today's dollars)"
)

# Spouse's income
if has_spouse:
    st.sidebar.markdown("**Spouse's Income**")
    
    spouse_employment_income = st.sidebar.number_input(
        "Spouse Employment Income ($)",
        min_value=0,
        value=0,
        step=5_000,
        format="%d",
        help="Spouse's annual wages and salaries"
    )
    
    if spouse_employment_income > 0:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            spouse_retirement_age = st.number_input(
                "Spouse Retirement Age",
                min_value=spouse_age,
                max_value=75,
                value=max(spouse_age, 65),
                help="Age when spouse's employment income stops"
            )
        with col2:
            spouse_employment_growth_rate = st.number_input(
                "Spouse Income Growth (%)",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                format="%.1f",
                help="Annual nominal wage growth for spouse"
            )
    else:
        spouse_retirement_age = spouse_age
        spouse_employment_growth_rate = 0.0
    
    spouse_social_security = st.sidebar.number_input(
        "Spouse Social Security ($)",
        min_value=0,
        value=0,
        step=1_000,
        format="%d",
        help="Spouse's annual Social Security benefits"
    )
    
    spouse_pension = st.sidebar.number_input(
        "Spouse Pension ($)",
        min_value=0,
        value=0,
        step=1_000,
        format="%d",
        help="Spouse's other guaranteed annual income"
    )

# Annuity option
has_annuity = st.sidebar.checkbox(
    "Include Annuity Income",
    value=False,
    help="Add a structured settlement annuity as guaranteed income"
)

annuity_annual = 0
annuity_type = None
annuity_guarantee_years = 0

if has_annuity:
    annuity_type = st.sidebar.radio(
        "Annuity Type",
        ["Life Contingent with Guarantee", "Fixed Period", "Life Only"],
        help="Type of annuity payment structure"
    )
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        annuity_monthly = st.number_input(
            "Monthly Payment ($)",
            min_value=0,
            value=3_500,
            step=100,
            format="%d"
        )
        annuity_annual = annuity_monthly * 12
    
    with col2:
        if annuity_type == "Life Contingent with Guarantee":
            annuity_guarantee_years = st.number_input(
                "Guarantee Period (years)",
                min_value=0,
                max_value=30,
                value=15,
                help="Payments guaranteed for this period even if death occurs"
            )
        elif annuity_type == "Fixed Period":
            annuity_guarantee_years = st.number_input(
                "Payment Period (years)",
                min_value=1,
                max_value=30,
                value=15,
                help="Total years of payments"
            )
        else:  # Life Only
            annuity_guarantee_years = 0
            st.info("Payments for life only")
    
    st.sidebar.info(f"Annual annuity income: ${annuity_annual:,}")

# Market calibration section
st.sidebar.header("📊 Market Calibration")

# Market calibration options
st.sidebar.markdown("*All returns are real (after inflation)*")

use_all_data = st.sidebar.checkbox(
    "Use all available data",
    value=True,
    help="Use all available historical data for the selected fund"
)

if not use_all_data:
    lookback_years = st.sidebar.slider(
        "Years of History",
        3, 50, 10,
        help="How many years of historical data to use"
    )
else:
    lookback_years = 50  # Maximum lookback for "all available"

# Auto-fetch on load or when ticker/years change
cache_key = f"market_data_{fund_ticker}_{'all' if use_all_data else lookback_years}"
if cache_key not in st.session_state:
    with st.spinner(f"Fetching {fund_ticker} data..."):
        try:
            import yfinance as yf
            from datetime import datetime, timedelta
            
            # Fetch historical data
            ticker = yf.Ticker(fund_ticker)
            end_date = datetime.now()
            # If using all data, try to get maximum history
            if use_all_data:
                start_date = end_date - timedelta(days=365 * 50)  # Try 50 years back
            else:
                start_date = end_date - timedelta(days=365 * lookback_years)
            
            hist = ticker.history(start=start_date, end=end_date, interval="1d")
            
            if not hist.empty:
                # Check actual data availability
                actual_years = (hist.index[-1] - hist.index[0]).days / 365.25
                
                # Calculate PRICE returns only (not including dividends)
                hist['Price_Return'] = hist['Close'].pct_change()
                
                # Annual price returns
                annual_price_returns = (1 + hist['Price_Return']).resample('Y').prod() - 1
                
                # Adjust for inflation (approximate using 2.5% average)
                inflation_rate = 0.025
                real_price_returns = annual_price_returns - inflation_rate
                
                # Calculate statistics for price appreciation only
                mean_price_return = real_price_returns.mean() * 100
                volatility = real_price_returns.std() * 100
                
                # Get current dividend yield (fix the scaling issue)
                info = ticker.info
                div_yield_raw = info.get('dividendYield', 0.02)
                # dividendYield is already in decimal form (e.g., 0.0175 for 1.75%)
                current_div_yield = div_yield_raw * 100 if div_yield_raw < 1 else div_yield_raw
                
                # Store in session state with cache key
                st.session_state[cache_key] = {
                    'return': mean_price_return,  # Price appreciation only
                    'volatility': volatility,
                    'dividend': current_div_yield
                }
                
                # Total return for display
                total_return = mean_price_return + current_div_yield
                
                years_display = f"{actual_years:.1f}"
                
                st.sidebar.success(f"""
                ✅ **{fund_ticker} Historical Stats** ({years_display}Y available)
                - Price Return: {mean_price_return:.1f}%
                - Dividend Yield: {current_div_yield:.1f}%
                - Total Return: {total_return:.1f}%
                - Volatility: {volatility:.1f}%
                """)
                
        except Exception as e:
            st.sidebar.error(f"Error fetching data: {str(e)}")
            # Use sensible defaults
            st.session_state[cache_key] = {
                'return': 5.0,
                'volatility': 16.0,
                'dividend': 2.0
            }

# Get cached values
cached_data = st.session_state.get(cache_key, {'return': 5.0, 'volatility': 16.0, 'dividend': 2.0})

# Manual override option
manual_override = st.sidebar.checkbox("Manual Override", value=False, help="Override with custom values")

if manual_override:
    expected_return = st.sidebar.slider(
        "Expected Real Return (%)",
        0.0, 10.0, 
        cached_data['return'],  # Default to calibrated value
        0.5,
        help="Override the calibrated return"
    )
    
    return_volatility = st.sidebar.slider(
        "Return Volatility (%)",
        5.0, 30.0, 
        cached_data['volatility'],  # Default to calibrated value
        1.0,
        help="Override the calibrated volatility"
    )
    
    dividend_yield = st.sidebar.slider(
        "Dividend Yield (%)",
        0.0, 5.0, 
        min(cached_data['dividend'], 5.0),  # Cap at 5% to avoid display issues
        0.25,
        help="Override the calibrated dividend yield"
    )
else:
    # Use auto-calibrated values
    expected_return = cached_data['return']
    return_volatility = cached_data['volatility']
    dividend_yield = min(cached_data['dividend'], 5.0)  # Cap at reasonable value

st.sidebar.header("🎲 Simulation Settings")
n_simulations = st.sidebar.selectbox(
    "Number of Simulations",
    [100, 500, 1000, 5000, 10000],
    index=2
)

include_mortality = st.sidebar.checkbox(
    "Include Mortality Risk",
    value=True,
    help="Account for probability of death each year"
)

# PolicyEngine will calculate accurate taxes based on state

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📖 Assumptions", "📊 Results", "📈 Detailed Analysis", "🎯 Strategy"])

with tab1:
    st.header("Key Assumptions & Methodology")
    
    # Add three columns for the key preview charts
    st.subheader("📊 Key Input Trends")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**💀 Mortality Risk**")
        mortality_rates = get_mortality_rates(gender)
        
        if include_mortality:
            ages = list(range(current_age, min(max_age + 1, 101)))
            annual_mortality = []
            for age in ages:
                mort_rate = np.interp(age, list(mortality_rates.keys()), 
                                     list(mortality_rates.values()))
                annual_mortality.append(mort_rate)
            
            fig_mort_preview = go.Figure()
            fig_mort_preview.add_trace(go.Scatter(
                x=ages, y=annual_mortality,
                mode='lines',
                name='Annual Mortality Rate',
                line=dict(color='red')
            ))
            fig_mort_preview.update_layout(
                xaxis_title="Age",
                yaxis_title="Annual Mortality Rate",
                height=200,
                yaxis_tickformat='.1%',
                margin=dict(l=0, r=0, t=20, b=20)
            )
            st.plotly_chart(fig_mort_preview, use_container_width=True)
            st.caption("SSA Period Life Table 2021")
        else:
            st.info("Mortality risk disabled")
    
    with col2:
        st.markdown(f"**📊 {fund_ticker} Historical Data**")
        
        # Try to show actual historical performance
        try:
            import yfinance as yf
            from datetime import datetime, timedelta
            
            # Get 5 years of data for display
            ticker = yf.Ticker(fund_ticker)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * 5)
            hist_display = ticker.history(start=start_date, end=end_date, interval="1mo")
            
            if not hist_display.empty:
                # Normalize to $100 starting value
                normalized_price = 100 * hist_display['Close'] / hist_display['Close'].iloc[0]
                
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Scatter(
                    x=hist_display.index,
                    y=normalized_price,
                    mode='lines',
                    name=f'{fund_ticker} Price',
                    line=dict(color='green', width=2)
                ))
                fig_hist.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Value of $100",
                    height=200,
                    margin=dict(l=0, r=0, t=20, b=20),
                    showlegend=False
                )
                st.plotly_chart(fig_hist, use_container_width=True)
                st.caption(f"Total return: {expected_return:.1f}% (includes dividends)")
            else:
                st.info(f"No historical data for {fund_ticker}")
        except:
            st.info(f"Unable to fetch {fund_ticker} history")
    
    with col3:
        st.markdown("**📈 Return Distribution**")
        
        # Show return distribution (not projections)
        x = np.linspace(-30, 30, 200)
        y = stats.norm.pdf(x, expected_return, return_volatility)
        
        fig_return_dist = go.Figure()
        fig_return_dist.add_trace(go.Scatter(
            x=x, y=y,
            fill='tozeroy',
            name='Return Distribution',
            line=dict(color='blue')
        ))
        fig_return_dist.add_vline(
            x=expected_return, 
            line_dash="dash", 
            line_color="darkblue",
            annotation_text=f"Expected: {expected_return:.1f}%"
        )
        fig_return_dist.update_layout(
            xaxis_title="Annual Return (%)",
            yaxis_title="Probability Density",
            height=200,
            margin=dict(l=0, r=0, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_return_dist, use_container_width=True)
        st.caption(f"μ={expected_return:.1f}%, σ={return_volatility:.1f}%, div={dividend_yield:.1f}%")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎲 Portfolio Returns")
        
        st.write(f"""
        - **Model**: Geometric Brownian Motion (GBM) for price
        - **Price dynamics**: dS/S = μdt + σdW
        - **Price Return (μ)**: {expected_return:.1f}% real per year
        - **Volatility (σ)**: {return_volatility:.1f}% annual standard deviation
        - **Dividend Yield**: {dividend_yield:.1f}% paid as cash
        
        The fund price follows GBM. Dividends are paid separately as cash.
        Total return = Price appreciation + Dividend yield
        """)
        
        if not manual_override:
            years_msg = f"{actual_years:.1f}" if 'actual_years' in locals() else "all available"
            st.info(f"📊 Calibrated to {fund_ticker} using {years_msg} years of data")
        
        # Show return distribution
        x = np.linspace(-30, 50, 100)
        y = stats.norm.pdf(x, expected_return, return_volatility)
        
        fig_returns = go.Figure()
        fig_returns.add_trace(go.Scatter(
            x=x, y=y,
            fill='tozeroy',
            name='Return Distribution'
        ))
        fig_returns.add_vline(x=expected_return, line_dash="dash", 
                             annotation_text=f"Expected: {expected_return:.1f}%")
        fig_returns.update_layout(
            title="Annual Return Distribution",
            xaxis_title="Real Return (%)",
            yaxis_title="Probability Density",
            height=300
        )
        st.plotly_chart(fig_returns, use_container_width=True)
    
    with col2:
        st.subheader("💀 Mortality Risk")
        if include_mortality:
            # Get mortality rates from the mortality module
            mortality_rates = get_mortality_rates(gender)
            
            ages = list(range(current_age, min(max_age + 1, 101)))
            survival_probs = []
            cumulative_survival = 1.0
            
            for age in ages:
                # Interpolate mortality rate
                mort_rate = np.interp(age, list(mortality_rates.keys()), 
                                     list(mortality_rates.values()))
                cumulative_survival *= (1 - mort_rate)
                survival_probs.append(cumulative_survival)
            
            fig_mortality = go.Figure()
            fig_mortality.add_trace(go.Scatter(
                x=ages, y=survival_probs,
                mode='lines',
                name=f'Your Survival ({gender})',
                line=dict(color='blue')
            ))
            
            # Add spouse survival if applicable
            if has_spouse:
                spouse_mortality_rates = get_mortality_rates(spouse_gender)
                spouse_ages = list(range(spouse_age, min(max_age + 1, 101)))
                spouse_survival_probs = []
                spouse_cumulative_survival = 1.0
                
                for age in spouse_ages:
                    mort_rate = np.interp(age, list(spouse_mortality_rates.keys()), 
                                        list(spouse_mortality_rates.values()))
                    spouse_cumulative_survival *= (1 - mort_rate)
                    spouse_survival_probs.append(spouse_cumulative_survival)
                
                # Align to same x-axis (years from now)
                years_from_now = list(range(len(spouse_ages)))
                fig_mortality.add_trace(go.Scatter(
                    x=spouse_ages, y=spouse_survival_probs,
                    mode='lines',
                    name=f'Spouse Survival ({spouse_gender})',
                    line=dict(color='red', dash='dash')
                ))
                
                # Add joint survival (both alive)
                # Need to align the ages properly
                joint_survival = []
                for i, age in enumerate(ages):
                    # Your survival at this age
                    your_surv = survival_probs[i] if i < len(survival_probs) else 0
                    
                    # Spouse survival at their age
                    spouse_age_at_time = spouse_age + i
                    if spouse_age_at_time >= spouse_age and spouse_age_at_time <= 100:
                        # Find spouse survival for their age
                        spouse_idx = spouse_age_at_time - spouse_age
                        if spouse_idx < len(spouse_survival_probs):
                            spouse_surv = spouse_survival_probs[spouse_idx]
                        else:
                            spouse_surv = 0
                    else:
                        spouse_surv = 0
                    
                    joint_survival.append(your_surv * spouse_surv)
                
                if joint_survival:
                    fig_mortality.add_trace(go.Scatter(
                        x=ages[:len(joint_survival)], y=joint_survival,
                        mode='lines',
                        name='Both Survive',
                        line=dict(color='green', dash='dot')
                    ))
            
            fig_mortality.update_layout(
                title="Survival Probability by Age",
                xaxis_title="Age",
                yaxis_title="Probability of Survival",
                height=300,
                yaxis_tickformat='.0%',
                showlegend=has_spouse
            )
            st.plotly_chart(fig_mortality, use_container_width=True)
        else:
            st.info("Mortality risk disabled - assuming survival to planning horizon")
    
    st.subheader("📊 Cash Flow Model")
    
    years_to_simulate = max_age - current_age
    
    # Calculate household income
    your_income = social_security + pension
    household_guaranteed = your_income + annuity_annual
    if has_spouse:
        spouse_income = spouse_social_security + spouse_pension
        household_guaranteed += spouse_income
    
    net_consumption_need = annual_consumption - household_guaranteed
    
    # Display household information
    if has_spouse:
        col1, col2 = st.columns(2)
        with col1:
            employment_desc = f"${employment_income:,}"
            if employment_income > 0 and employment_growth_rate > 0:
                employment_desc += f" (growing {employment_growth_rate:.1f}%/yr)"
            st.write(f"""
            **Your Income (Annual)**
            - Employment: {employment_desc} until age {retirement_age}
            - Social Security: ${social_security:,}
            - Pension: ${pension:,}
            - **Your Total**: ${your_income + employment_income:,}
            """)
        with col2:
            spouse_employment_desc = f"${spouse_employment_income:,}"
            if spouse_employment_income > 0 and spouse_employment_growth_rate > 0:
                spouse_employment_desc += f" (growing {spouse_employment_growth_rate:.1f}%/yr)"
            st.write(f"""
            **Spouse Income (Annual)**
            - Employment: {spouse_employment_desc} until age {spouse_retirement_age}
            - Social Security: ${spouse_social_security:,}
            - Pension: ${spouse_pension:,}
            - **Spouse Total**: ${spouse_income + spouse_employment_income:,}
            """)
    
    st.write(f"""
    **Household Cash Flows (Real $)**
    - Consumption Need: ${annual_consumption:,}
    - Household Guaranteed Income: ${household_guaranteed:,}
    - **Net from Portfolio**: ${net_consumption_need:,}
    - Tax Filing Status: {"Married Filing Jointly" if has_spouse else "Single"}
    - Tax Calculation: PolicyEngine-US (federal + {state} state)
    - **Estimated Gross Withdrawal**: ~${max(0, net_consumption_need * 1.25):,.0f} (before taxes)
    """)
    
    # Show note about income growth if applicable
    if (employment_income > 0 and employment_growth_rate > 0) or (has_spouse and spouse_employment_income > 0 and spouse_employment_growth_rate > 0):
        st.info("📈 Note: Income growth rates are nominal (includes inflation). For example, 3% growth = ~0% real growth if inflation is 3%.")
    
    if net_consumption_need <= 0:
        st.success("✅ Your guaranteed income covers your consumption needs!")
    else:
        withdrawal_rate = (net_consumption_need * 1.25) / initial_portfolio * 100  # Rough estimate before tax calc
        st.info(f"📊 Initial withdrawal rate: {withdrawal_rate:.2f}%")
    
    # Add simulation button in tab1
    st.markdown("---")
    # Create a hash of current parameters to detect changes
    import hashlib
    param_string = f"{n_simulations}{max_age}{initial_portfolio}{current_age}{social_security}{pension}{employment_income}{retirement_age}{annual_consumption}{expected_return}{return_volatility}{dividend_yield}{state}{has_annuity}{annuity_annual}{has_spouse}"
    param_hash = hashlib.md5(param_string.encode()).hexdigest()
    
    # Check if parameters have changed
    if 'last_param_hash' in st.session_state and st.session_state.last_param_hash != param_hash:
        st.session_state.simulation_run = False  # Invalidate old results
        st.warning("⚠️ Parameters have changed. Please run a new simulation.")
    
    st.info("💡 Click 'Run Simulation' to generate results, then check the **Results** tab")
    if st.button("🎲 Run Simulation", type="primary", key="run_sim"):
        st.session_state.simulation_run = True
        st.session_state.last_param_hash = param_hash
        st.rerun()  # Force rerun to update tab2

with tab2:
    st.header("Simulation Results")
    
    if 'simulation_run' not in st.session_state or not st.session_state.simulation_run:
        st.info("👈 Please run a simulation from the Assumptions tab first")
    else:
        # Create progress containers
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Run Monte Carlo simulation
        n_years = max_age - current_age
        
        with st.container():
            # Create a placeholder for live results
            live_chart_placeholder = st.empty()
            
            # Progress callback function
            def update_progress(year, total_years, age, partial_results=None):
                progress = year / total_years
                progress_bar.progress(progress)
                status_text.text(f"Simulating year {year}/{total_years} (Age {age}) - Calculating taxes with PolicyEngine...")
                
                # Update live chart every 5 years
                if (year % 5 == 0 or year == total_years) and partial_results:
                    if 'portfolio_paths' in partial_results:
                        portfolio_paths_partial = partial_results['portfolio_paths']
                        # Only use the portion that has been calculated
                        # Year 0 is initial, year 1 is after first simulation, etc.
                        # So when year=5, we have calculated through index 5 (6 values total)
                        valid_indices = year + 1  # Include initial value + calculated years
                        portfolio_slice = portfolio_paths_partial[:, :valid_indices]
                        
                        # Calculate percentiles only for valid data
                        current_percentiles = np.percentile(portfolio_slice, [5, 50, 95], axis=0)
                        years_so_far = np.arange(current_age, current_age + valid_indices)
                        
                        fig_live = go.Figure()
                        # 90% CI
                        fig_live.add_trace(go.Scatter(
                            x=years_so_far, y=current_percentiles[2],  # 95th percentile
                            mode='lines', name='95th percentile',
                            line=dict(width=0), showlegend=False
                        ))
                        fig_live.add_trace(go.Scatter(
                            x=years_so_far, y=current_percentiles[0],  # 5th percentile
                            mode='lines', name='5th percentile',
                            line=dict(width=0), fill='tonexty',
                            fillcolor='rgba(0,100,200,0.2)', showlegend=False
                        ))
                        # Median
                        fig_live.add_trace(go.Scatter(
                            x=years_so_far, y=current_percentiles[1],
                            mode='lines', name='Median',
                            line=dict(color='blue', width=2)
                        ))
                        fig_live.update_layout(
                            title=f"Portfolio Projections (Progress: {year}/{total_years} years)",
                            xaxis_title="Age", yaxis_title="Portfolio Value ($)",
                            yaxis_tickformat='$,.0f', height=400
                        )
                        live_chart_placeholder.plotly_chart(fig_live, use_container_width=True)
            
            # Run simulation using modularized function
            simulation_results = simulate_portfolio(
                n_simulations=n_simulations,
                n_years=n_years,
                initial_portfolio=initial_portfolio,
                current_age=current_age,
                include_mortality=include_mortality,
                social_security=social_security,
                pension=pension,
                employment_income=employment_income,
                retirement_age=retirement_age,
                has_annuity=has_annuity,
                annuity_type=annuity_type,
                annuity_annual=annuity_annual,
                annuity_guarantee_years=annuity_guarantee_years,
                annual_consumption=annual_consumption,  # Now using total consumption
                expected_return=expected_return,
                return_volatility=return_volatility,
                dividend_yield=dividend_yield,
                state=state,
                employment_growth_rate=employment_growth_rate,  # Now after required params
                gender=gender,
                has_spouse=has_spouse,
                spouse_age=spouse_age,
                spouse_gender=spouse_gender,
                spouse_social_security=spouse_social_security,
                spouse_pension=spouse_pension,
                spouse_employment_income=spouse_employment_income,
                spouse_retirement_age=spouse_retirement_age,
                spouse_employment_growth_rate=spouse_employment_growth_rate if has_spouse else 0.0,
                progress_callback=update_progress
            )
            
            # Extract results
            portfolio_paths = simulation_results['portfolio_paths']
            failure_year = simulation_results['failure_year']
            alive_mask = simulation_results['alive_mask']
            annuity_income = simulation_results['annuity_income']
            dividend_income = simulation_results['dividend_income']
            capital_gains = simulation_results['capital_gains']
            gross_withdrawals = simulation_results['gross_withdrawals']
            taxes_paid = simulation_results['taxes_paid']
            net_withdrawals = simulation_results['net_withdrawals']
            cost_basis = simulation_results['cost_basis']
            
            # Calculate statistics
            # Use the correct success mask from simulation (alive at end with money)
            if "success_mask" in simulation_results:
                success_mask = simulation_results["success_mask"]
            else:
                # Fallback for backward compatibility
                success_mask = failure_year > n_years
            success_rate = success_mask.mean()
            
            # Percentiles over time (5th, 50th, 95th for 90% CI)
            percentiles = np.percentile(portfolio_paths, [5, 50, 95], axis=0)
            
            # Display income summary for transparency
            st.info(f"""
            **📊 Simulation Parameters**
            - Annual Spending: ${annual_consumption:,}
            - Social Security: ${social_security:,}/year (with COLA)
            - Pension: ${pension:,}/year
            - Employment: ${employment_income:,}/year until age {retirement_age if employment_income > 0 else 'N/A'}
            - Annuity: ${annuity_annual if has_annuity else 0:,}/year
            - **Initial Portfolio Withdrawal: ${max(0, annual_consumption - social_security - pension - (employment_income if current_age < retirement_age else 0) - (annuity_annual if has_annuity else 0)):,}/year**
            """)
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Success Rate", f"{success_rate:.1%}",
                         help="Probability of maintaining consumption through planning horizon")
            
            with col2:
                # Calculate median of ALL scenarios (including failures)
                median_final_all = np.median(portfolio_paths[:, -1])
                st.metric("Median Final Portfolio", f"${median_final_all:,.0f}",
                         help="Median portfolio value at end (all scenarios)")
            
            with col3:
                if (~success_mask).any():
                    median_failure_year = np.median(failure_year[~success_mask])
                    median_failure_age = current_age + median_failure_year
                    st.metric("Median Failure Age", f"{median_failure_age:.0f}",
                             help="Median age at portfolio depletion (failed scenarios)")
                else:
                    st.metric("Median Failure Age", "N/A", help="No failures")
            
            with col4:
                prob_10_years = (failure_year <= 10).mean()
                st.metric("10-Year Failure Risk", f"{prob_10_years:.1%}",
                         help="Probability of failure within 10 years")
            
            # Portfolio paths visualization
            st.subheader("Portfolio Value Over Time")
            
            years = np.arange(current_age, max_age + 1)
            
            fig = go.Figure()
            
            # Add 90% confidence interval (5th to 95th percentile)
            fig.add_trace(go.Scatter(
                x=years, y=percentiles[2],  # 95th percentile
                name='90% Confidence Interval',
                line=dict(color='rgba(0,100,200,0.3)', width=1),
                showlegend=True,
                legendgroup='ci'
            ))
            
            fig.add_trace(go.Scatter(
                x=years, y=percentiles[0],  # 5th percentile
                name='5th Percentile',
                fill='tonexty',
                fillcolor='rgba(0,100,200,0.2)',
                line=dict(color='rgba(0,100,200,0.3)', width=1),
                showlegend=False,
                legendgroup='ci'
            ))
            
            # Add median line
            fig.add_trace(go.Scatter(
                x=years, y=percentiles[1],  # Median (50th percentile)
                name='Median',
                line=dict(color='blue', width=3)
            ))
            
            # Add horizontal line at 0
            fig.add_hline(y=0, line_dash="dash", line_color="red",
                         annotation_text="Depletion")
            
            fig.update_layout(
                title="Portfolio Value Projection (Real $)",
                xaxis_title="Age",
                yaxis_title="Portfolio Value ($)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Store results in session state
            st.session_state['simulation_results'] = {
                'portfolio_paths': portfolio_paths,
                'failure_year': failure_year,
                'success_rate': success_rate,
                'percentiles': percentiles,
                'years': years,
                'dividend_income': dividend_income,
                'capital_gains': capital_gains,
                'gross_withdrawals': gross_withdrawals,
                'taxes_paid': taxes_paid,
                'net_withdrawals': net_withdrawals,
                'cost_basis': cost_basis  # Track basis for debugging
            }
            
            # Save raw simulation data to CSV for analysis
            import pandas as pd
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create DataFrame with all simulation paths
            # Each row is a simulation-year combination
            data_rows = []
            for sim_idx in range(n_simulations):
                for year_idx in range(n_years + 1):
                    row = {
                        'simulation_id': sim_idx,
                        'year': year_idx,
                        'age': current_age + year_idx,
                        'portfolio_value': portfolio_paths[sim_idx, year_idx],
                        'dividend_income': dividend_income[sim_idx, year_idx] if year_idx < n_years else 0,
                        'capital_gains': capital_gains[sim_idx, year_idx] if year_idx < n_years else 0,
                        'gross_withdrawal': gross_withdrawals[sim_idx, year_idx] if year_idx < n_years else 0,
                        'taxes_paid': taxes_paid[sim_idx, year_idx] if year_idx < n_years else 0,
                        'net_withdrawal': net_withdrawals[sim_idx, year_idx] if year_idx < n_years else 0,
                        'alive': alive_mask[sim_idx, year_idx] if include_mortality else True,
                        'failed': year_idx >= failure_year[sim_idx]
                    }
                    data_rows.append(row)
            
            df = pd.DataFrame(data_rows)
            
            # Add VT index value (hypothetical growth at expected return without volatility)
            # This represents what $1 invested in VT would be worth
            vt_index_values = np.exp((expected_return / 100 - 0.5 * (return_volatility / 100)**2) * np.arange(n_years + 1))
            df['vt_index_value'] = df['year'].apply(lambda y: vt_index_values[y])
            
            # Save to CSV
            csv_filename = f"simulation_raw_data_{timestamp}.csv"
            df.to_csv(csv_filename, index=False)
            
            # Also save a summary CSV with just the key metrics per simulation
            summary_data = []
            for sim_idx in range(n_simulations):
                summary_data.append({
                    'simulation_id': sim_idx,
                    'initial_portfolio': initial_portfolio,
                    'final_portfolio': portfolio_paths[sim_idx, -1],
                    'total_return': (portfolio_paths[sim_idx, -1] / initial_portfolio - 1) * 100,
                    'failed': failure_year[sim_idx] <= n_years,
                    'failure_year': failure_year[sim_idx] if failure_year[sim_idx] <= n_years else None,
                    'max_portfolio': np.max(portfolio_paths[sim_idx, :]),
                    'min_portfolio': np.min(portfolio_paths[sim_idx, :]),
                    'total_dividends': np.sum(dividend_income[sim_idx, :]),
                    'total_withdrawals': np.sum(gross_withdrawals[sim_idx, :]),
                    'total_taxes': np.sum(taxes_paid[sim_idx, :])
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_csv_filename = f"simulation_summary_{timestamp}.csv"
            summary_df.to_csv(summary_csv_filename, index=False)
            
            # Display summary statistics
            st.success(f"✅ Raw data saved to {csv_filename} ({len(df):,} rows)")
            st.info(f"📊 Summary saved to {summary_csv_filename} ({len(summary_df):,} simulations)")
            
            # Show quick stats
            extreme_sims = summary_df[summary_df['final_portfolio'] > 1e9]
            if len(extreme_sims) > 0:
                st.warning(f"⚠️ Found {len(extreme_sims)} simulations with final portfolio > $1B")
                st.dataframe(extreme_sims[['simulation_id', 'final_portfolio', 'max_portfolio', 'total_return']].head(10))
            
            # Debug: Show that dividends do vary
            st.info(f"""
            📊 **Dividend Income Verification** (Median across simulations):
            - Year 1: ${np.median(dividend_income[:, 0]):,.0f}
            - Year 5: ${np.median(dividend_income[:, 4] if n_years > 4 else dividend_income[:, -1]):,.0f}
            - Year 10: ${np.median(dividend_income[:, 9] if n_years > 9 else dividend_income[:, -1]):,.0f}
            - Last Year: ${np.median(dividend_income[:, -1]):,.0f}
            
            Portfolio values should drive dividend changes.
            """)

with tab3:
    st.header("Detailed Analysis")
    
    if 'simulation_results' in st.session_state:
        results = st.session_state['simulation_results']
        
        # Component Analysis with Dropdown
        st.subheader("📊 Annual Cash Flow Components")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            component_to_plot = st.selectbox(
                "Select Component to Visualize",
                [
                    "Taxes Paid",
                    "Dividend Income", 
                    "Capital Gains (Realized)",
                    "Gross Withdrawals", 
                    "Net Withdrawals",
                    "Total Income (After Tax)",
                    "Gross Income",
                    "Effective Tax Rate"
                ]
            )
        
        with col2:
            view_mode = st.radio(
                "View Mode",
                ["Percentiles", "Single Trajectory"],
                horizontal=True
            )
        
        with col3:
            if view_mode == "Single Trajectory":
                trajectory_idx = st.number_input(
                    "Trajectory #",
                    1, n_simulations, 1
                ) - 1
                if st.button("🔀 Shuffle"):
                    st.session_state.shuffled_trajectory = np.random.randint(0, n_simulations)
                    st.rerun()
                
                # Use shuffled trajectory if available
                if 'shuffled_trajectory' in st.session_state:
                    trajectory_idx = st.session_state.shuffled_trajectory
        
        # Prepare data based on selection
        years_plot = np.arange(current_age + 1, max_age + 1)
        
        if component_to_plot == "Taxes Paid":
            data = results['taxes_paid']
        elif component_to_plot == "Dividend Income":
            data = results['dividend_income']
        elif component_to_plot == "Capital Gains (Realized)":
            # Capital gains are realized when we withdraw from the portfolio
            # Simplified: assume a fixed % of withdrawals are capital gains vs return of basis
            # This percentage increases over time as the cost basis shrinks
            data = results['capital_gains']  # Note: this needs proper basis tracking
        elif component_to_plot == "Gross Withdrawals":
            data = results['gross_withdrawals']
        elif component_to_plot == "Net Withdrawals":
            data = results['net_withdrawals']
        elif component_to_plot == "Total Income (After Tax)":
            data = results['dividend_income'] + results['net_withdrawals'] - results['taxes_paid']
        elif component_to_plot == "Gross Income":
            # Total gross income before any taxes
            data = results['dividend_income'] + results['gross_withdrawals']
        elif component_to_plot == "Effective Tax Rate":
            taxable_income = results['dividend_income'] + results['gross_withdrawals']
            data = np.where(taxable_income > 0,
                          results['taxes_paid'] / taxable_income * 100,
                          0)
        
        # Create plot
        fig_component = go.Figure()
        
        if view_mode == "Percentiles":
            # Calculate percentiles
            component_percentiles = np.percentile(data, [10, 25, 50, 75, 90], axis=0)
            
            # Add traces
            fig_component.add_trace(go.Scatter(
                x=years_plot, y=component_percentiles[4],
                name='90th Percentile',
                line=dict(color='lightgreen', width=1)
            ))
            
            fig_component.add_trace(go.Scatter(
                x=years_plot, y=component_percentiles[3],
                fill='tonexty',
                name='75th Percentile',
                line=dict(color='green', width=1),
                fillcolor='rgba(0,255,0,0.1)'
            ))
            
            fig_component.add_trace(go.Scatter(
                x=years_plot, y=component_percentiles[2],
                name='Median',
                line=dict(color='blue', width=2)
            ))
            
            fig_component.add_trace(go.Scatter(
                x=years_plot, y=component_percentiles[1],
                fill='tonexty',
                name='25th Percentile',
                line=dict(color='orange', width=1),
                fillcolor='rgba(255,165,0,0.1)'
            ))
            
            fig_component.add_trace(go.Scatter(
                x=years_plot, y=component_percentiles[0],
                name='10th Percentile',
                line=dict(color='red', width=1)
            ))
            
        else:  # Single Trajectory
            # Show the single trajectory
            fig_component.add_trace(go.Scatter(
                x=years_plot, y=data[trajectory_idx],
                name=f'Trajectory #{trajectory_idx + 1}',
                line=dict(color='blue', width=2),
                mode='lines+markers'
            ))
            
            # Add failure indicator if applicable
            n_years = max_age - current_age
            if results['failure_year'][trajectory_idx] <= n_years:
                failure_age = current_age + results['failure_year'][trajectory_idx]
                fig_component.add_vline(
                    x=failure_age,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Portfolio Depleted"
                )
        
        # Update layout
        y_title = component_to_plot
        if "Rate" in component_to_plot:
            y_title += " (%)"
        else:
            y_title += " ($)"
            
        fig_component.update_layout(
            title=f"{component_to_plot} Over Time",
            xaxis_title="Age",
            yaxis_title=y_title,
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_component, use_container_width=True)
        
        # Statistics for selected component
        if view_mode == "Percentiles":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Median Annual", f"${np.median(data):,.0f}")
            with col2:
                st.metric("Mean Annual", f"${np.mean(data):,.0f}")
            with col3:
                st.metric("Total (Median)", f"${np.median(np.sum(data, axis=1)):,.0f}")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Annual", f"${np.mean(data[trajectory_idx]):,.0f}")
            with col2:
                st.metric("Total", f"${np.sum(data[trajectory_idx]):,.0f}")
            with col3:
                n_years = max_age - current_age
                status = "✅ Success" if results['failure_year'][trajectory_idx] > n_years else "❌ Failed"
                st.metric("Outcome", status)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Failure Time Distribution")
            
            failures = results['failure_year'][results['failure_year'] <= n_years]
            if len(failures) > 0:
                fig_failure = go.Figure()
                fig_failure.add_trace(go.Histogram(
                    x=current_age + failures,
                    nbinsx=20,
                    name='Failure Age'
                ))
                fig_failure.update_layout(
                    xaxis_title="Age at Portfolio Depletion",
                    yaxis_title="Number of Scenarios",
                    height=400
                )
                st.plotly_chart(fig_failure, use_container_width=True)
            else:
                st.success("No failures in simulation!")
        
        with col2:
            st.subheader("Final Portfolio Distribution")
            
            final_values = results['portfolio_paths'][:, -1]
            successful_finals = final_values[final_values > 0]
            
            if len(successful_finals) > 0:
                fig_final = go.Figure()
                fig_final.add_trace(go.Histogram(
                    x=successful_finals,
                    nbinsx=30,
                    name='Final Portfolio Value'
                ))
                fig_final.update_layout(
                    xaxis_title="Final Portfolio Value ($)",
                    yaxis_title="Number of Scenarios",
                    height=400
                )
                st.plotly_chart(fig_final, use_container_width=True)
        
        # Survival analysis
        st.subheader("Portfolio Survival Analysis")
        
        survival_by_year = np.mean(results['portfolio_paths'] > 0, axis=0)
        
        fig_survival = go.Figure()
        fig_survival.add_trace(go.Scatter(
            x=results['years'],
            y=survival_by_year,
            mode='lines',
            name='Portfolio Survival Rate'
        ))
        
        fig_survival.update_layout(
            title="Probability of Portfolio Survival by Age",
            xaxis_title="Age",
            yaxis_title="Survival Probability",
            yaxis_tickformat='.0%',
            height=400
        )
        
        st.plotly_chart(fig_survival, use_container_width=True)
        
        # Summary statistics table
        st.subheader("Summary Statistics")
        
        summary_df = pd.DataFrame({
            'Metric': [
                'Success Rate',
                'Median Final Value (All)',
                'Median Final Value (Success Only)',
                '25th Percentile Final',
                '75th Percentile Final',
                'Probability of 50% Loss',
                'Probability of Doubling'
            ],
            'Value': [
                f"{results['success_rate']:.1%}",
                f"${np.median(final_values):,.0f}",
                f"${np.median(successful_finals):,.0f}" if len(successful_finals) > 0 else "N/A",
                f"${np.percentile(final_values, 25):,.0f}",
                f"${np.percentile(final_values, 75):,.0f}",
                f"{np.mean(final_values < initial_portfolio * 0.5):.1%}",
                f"{np.mean(final_values > initial_portfolio * 2):.1%}"
            ]
        })
        
        st.table(summary_df)
    else:
        st.info("👈 Run simulation first to see detailed analysis")

with tab4:
    st.header("Strategy Insights")
    
    if 'simulation_results' in st.session_state:
        results = st.session_state['simulation_results']
        
        st.subheader("📊 Key Findings")
        
        # Safe withdrawal rate analysis
        # Calculate actual withdrawal rate from simulation results
        avg_gross_withdrawal = np.mean(results['gross_withdrawals'][:, 0])  # First year average
        current_withdrawal_rate = (avg_gross_withdrawal / initial_portfolio) * 100
        
        if results['success_rate'] > 0.95:
            st.success(f"""
            ✅ **Strong Position**: Your {current_withdrawal_rate:.2f}% withdrawal rate has a {results['success_rate']:.1%} success rate.
            Consider:
            - Increasing spending if desired
            - Reducing portfolio risk
            - Planning for legacy/charity
            """)
        elif results['success_rate'] > 0.80:
            st.info(f"""
            ⚠️ **Moderate Risk**: Your {current_withdrawal_rate:.2f}% withdrawal rate has a {results['success_rate']:.1%} success rate.
            Consider:
            - Building cash reserves
            - Planning spending flexibility
            - Part-time work as backup
            """)
        else:
            st.warning(f"""
            ⚠️ **High Risk**: Your {current_withdrawal_rate:.2f}% withdrawal rate has a {results['success_rate']:.1%} success rate.
            Consider:
            - Reducing spending
            - Delaying retirement
            - Increasing guaranteed income (annuities)
            - Working part-time
            """)
        
        # Sensitivity analysis
        st.subheader("🎯 What-If Scenarios")
        
        # Calculate guaranteed income for what-if scenarios
        guaranteed_income = social_security + pension + (annuity_annual if has_annuity else 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            spending_change = st.slider(
                "Adjust Annual Spending (%)",
                -30, 30, 0, 5
            )
            
            new_consumption = annual_consumption * (1 + spending_change/100)
            new_net = new_consumption - guaranteed_income
            new_withdrawal_rate = (new_net * 1.25) / initial_portfolio * 100  # Rough estimate
            
            st.write(f"""
            **Adjusted Scenario:**
            - New Consumption: ${new_consumption:,.0f}
            - New Withdrawal Rate: {new_withdrawal_rate:.2f}%
            """)
        
        with col2:
            return_change = st.slider(
                "Adjust Expected Return (pp)",
                -3.0, 3.0, 0.0, 0.5,
                help="Percentage points change in return"
            )
            
            new_return = expected_return + return_change
            
            st.write(f"""
            **Adjusted Market:**
            - New Expected Return: {new_return:.1f}%
            - Original Return: {expected_return:.1f}%
            """)
        
        if spending_change != 0 or return_change != 0:
            st.info("👆 Re-run simulation with adjusted parameters to see impact")
    else:
        st.info("👈 Run simulation first to see strategy insights")

# Footer
st.markdown("---")
st.markdown("""
**Disclaimer**: This tool is for educational purposes only. 
Consult with qualified financial professionals before making retirement decisions.
All calculations are in real (inflation-adjusted) terms.
""")