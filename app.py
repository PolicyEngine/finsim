"""General retirement planning simulator with clear assumptions."""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from finsim.mortality import get_mortality_rates

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
""")

# Sidebar for inputs
st.sidebar.header("🎯 Your Situation")

col1, col2 = st.sidebar.columns(2)
with col1:
    current_age = st.number_input("Current Age", 50, 100, 65)
    retirement_age = st.number_input("Retirement Age", current_age, 100, max(current_age, 65))
with col2:
    max_age = st.number_input("Planning Horizon", current_age + 10, 120, 95)
    gender = st.selectbox("Gender (for mortality)", ["Male", "Female"])

st.sidebar.header("💰 Financial Position")
initial_portfolio = st.sidebar.number_input(
    "Current Portfolio Value ($)",
    min_value=0,
    value=500_000,
    step=10_000,
    format="%d",
    help="Current value of investable assets (stocks, bonds, etc.)"
)

st.sidebar.header("💸 Annual Spending & Income")
annual_consumption = st.sidebar.number_input(
    "Annual Real Consumption Need ($)",
    min_value=0,
    value=60_000,
    step=5_000,
    format="%d",
    help="How much you need to spend each year (in today's dollars)"
)

social_security = st.sidebar.number_input(
    "Annual Social Security ($)",
    min_value=0,
    value=24_000,
    step=1_000,
    format="%d",
    help="Annual Social Security benefits (in today's dollars)"
)

pension = st.sidebar.number_input(
    "Annual Pension/Other Income ($)",
    min_value=0,
    value=0,
    step=1_000,
    format="%d",
    help="Other guaranteed annual income (in today's dollars)"
)

# Annuity option
st.sidebar.subheader("🏦 Annuity Option")
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

st.sidebar.header("📈 Market Assumptions")
st.sidebar.markdown("*All returns are real (after inflation)*")

# Option to calibrate to specific funds
calibration_method = st.sidebar.radio(
    "Calibration Method",
    ["Manual", "Historical Fund Data"],
    help="Manual: Set your own assumptions\nHistorical: Calibrate to actual fund performance"
)

if calibration_method == "Historical Fund Data":
    fund_ticker = st.sidebar.text_input(
        "Fund Ticker",
        value="VT",
        help="Enter ticker symbol (e.g., VT, VOO, SPY, QQQ)"
    )
    
    lookback_years = st.sidebar.slider(
        "Years of History",
        3, 20, 10,
        help="How many years of historical data to use"
    )
    
    if st.sidebar.button("📊 Fetch & Calibrate"):
        with st.spinner(f"Fetching {fund_ticker} data..."):
            try:
                import yfinance as yf
                from datetime import datetime, timedelta
                
                # Fetch historical data
                ticker = yf.Ticker(fund_ticker)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365 * lookback_years)
                
                hist = ticker.history(start=start_date, end=end_date, interval="1d")
                
                if not hist.empty:
                    # Calculate returns
                    hist['Returns'] = hist['Close'].pct_change()
                    annual_returns = (1 + hist['Returns']).resample('Y').prod() - 1
                    
                    # Adjust for inflation (approximate using 2.5% average)
                    inflation_rate = 0.025
                    real_returns = annual_returns - inflation_rate
                    
                    # Calculate statistics
                    mean_return = real_returns.mean() * 100
                    volatility = real_returns.std() * 100
                    
                    # Get current dividend yield
                    info = ticker.info
                    current_div_yield = info.get('dividendYield', 0.02) * 100
                    
                    st.sidebar.success(f"""
                    ✅ **{fund_ticker} Historical Stats** ({lookback_years}Y)
                    - Real Return: {mean_return:.1f}%
                    - Volatility: {volatility:.1f}%
                    - Dividend Yield: {current_div_yield:.1f}%
                    """)
                    
                    # Store in session state
                    st.session_state['calibrated_return'] = mean_return
                    st.session_state['calibrated_volatility'] = volatility
                    st.session_state['calibrated_dividend'] = current_div_yield
                    
            except Exception as e:
                st.sidebar.error(f"Error fetching data: {str(e)}")
                st.sidebar.info("Using default values")
    
    # Use calibrated or default values
    expected_return = st.sidebar.slider(
        "Expected Real Return (%)",
        0.0, 10.0, 
        st.session_state.get('calibrated_return', 5.0),
        0.5,
        help="Calibrated from historical data"
    )
    
    return_volatility = st.sidebar.slider(
        "Return Volatility (%)",
        5.0, 30.0,
        st.session_state.get('calibrated_volatility', 16.0),
        1.0,
        help="Calibrated from historical data"
    )
    
    dividend_yield = st.sidebar.slider(
        "Dividend Yield (%)",
        0.0, 5.0,
        st.session_state.get('calibrated_dividend', 2.0),
        0.25,
        help="Current dividend yield"
    )
    
else:  # Manual
    st.sidebar.info("""
    **Typical Values:**
    - VT (Total World): 5% real, 16% vol
    - S&P 500: 7% real, 16% vol
    - Bonds: 2% real, 5% vol
    - 60/40 Portfolio: 5% real, 10% vol
    """)
    
    expected_return = st.sidebar.slider(
        "Expected Real Return (%)",
        0.0, 10.0, 5.0, 0.5,
        help="Historical equity premium suggests 5-7% real returns"
    )
    
    return_volatility = st.sidebar.slider(
        "Return Volatility (%)",
        5.0, 30.0, 16.0, 1.0,
        help="Historical volatility ~16% for diversified equity"
    )
    
    dividend_yield = st.sidebar.slider(
        "Dividend Yield (%)",
        0.0, 5.0, 2.0, 0.25,
        help="Current dividend yield"
    )

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

# Tax assumptions (simplified)
st.sidebar.header("📋 Tax Assumptions")
effective_tax_rate = st.sidebar.slider(
    "Effective Tax Rate on Withdrawals (%)",
    0.0, 40.0, 15.0, 1.0,
    help="Combined federal and state tax rate on portfolio withdrawals"
)

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
        st.markdown("**💵 Dividend Yield**")
        years_preview = np.arange(0, min(30, max_age - current_age + 1))
        # Show how dividend income changes with portfolio value
        sample_portfolio = initial_portfolio * np.exp(expected_return/100 * years_preview)
        dividend_preview = sample_portfolio * (dividend_yield / 100)
        
        fig_div_preview = go.Figure()
        fig_div_preview.add_trace(go.Scatter(
            x=current_age + years_preview, 
            y=dividend_preview,
            mode='lines',
            name='Expected Dividend Income',
            line=dict(color='green')
        ))
        fig_div_preview.update_layout(
            xaxis_title="Age",
            yaxis_title="Annual Dividends ($)",
            height=200,
            margin=dict(l=0, r=0, t=20, b=20)
        )
        st.plotly_chart(fig_div_preview, use_container_width=True)
        st.caption(f"At {dividend_yield:.1f}% yield on growing portfolio")
    
    with col3:
        st.markdown("**📈 Fund Value Projection**")
        # Show expected fund value with confidence bands
        years_preview = np.arange(0, min(30, max_age - current_age + 1))
        
        # Calculate expected value and confidence bands
        expected_value = initial_portfolio * np.exp(expected_return/100 * years_preview)
        
        # Standard deviation grows with sqrt(time)
        std_dev = initial_portfolio * np.exp(expected_return/100 * years_preview) * \
                  (np.exp(return_volatility/100 * np.sqrt(years_preview)) - 1)
        
        upper_band = expected_value + std_dev
        lower_band = np.maximum(0, expected_value - std_dev)
        
        fig_fund_preview = go.Figure()
        
        # Add confidence band
        fig_fund_preview.add_trace(go.Scatter(
            x=current_age + years_preview,
            y=upper_band,
            mode='lines',
            name='±1σ Band',
            line=dict(width=0),
            showlegend=False
        ))
        fig_fund_preview.add_trace(go.Scatter(
            x=current_age + years_preview,
            y=lower_band,
            mode='lines',
            name='±1σ Band',
            line=dict(width=0),
            fillcolor='rgba(68, 68, 68, 0.2)',
            fill='tonexty',
            showlegend=False
        ))
        
        # Add expected value
        fig_fund_preview.add_trace(go.Scatter(
            x=current_age + years_preview,
            y=expected_value,
            mode='lines',
            name='Expected Value',
            line=dict(color='blue', width=2)
        ))
        
        fig_fund_preview.update_layout(
            xaxis_title="Age",
            yaxis_title="Portfolio Value ($)",
            height=200,
            margin=dict(l=0, r=0, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_fund_preview, use_container_width=True)
        st.caption(f"{expected_return:.1f}% return, {return_volatility:.1f}% volatility")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎲 Portfolio Returns")
        
        st.write(f"""
        - **Model**: Geometric Brownian Motion (GBM)
        - **Mathematical Form**: dS/S = μdt + σdW
        - **Expected Return (μ)**: {expected_return:.1f}% real per year
        - **Volatility (σ)**: {return_volatility:.1f}% annual standard deviation
        - **Dividends**: {dividend_yield:.1f}% paid annually
        """)
        
        if calibration_method == "Historical Fund Data" and 'calibrated_return' in st.session_state:
            st.info(f"📊 Calibrated to {fund_ticker} using {lookback_years} years of data")
        
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
                name='Survival Probability'
            ))
            fig_mortality.update_layout(
                title="Survival Probability by Age",
                xaxis_title="Age",
                yaxis_title="Probability of Survival",
                height=300,
                yaxis_tickformat='.0%'
            )
            st.plotly_chart(fig_mortality, use_container_width=True)
        else:
            st.info("Mortality risk disabled - assuming survival to planning horizon")
    
    st.subheader("📊 Cash Flow Model")
    
    years_to_simulate = max_age - current_age
    guaranteed_income = social_security + pension + annuity_annual
    net_consumption_need = annual_consumption - guaranteed_income
    
    st.write(f"""
    **Annual Cash Flows (Real $)**
    - Consumption Need: ${annual_consumption:,}
    - Guaranteed Income: ${guaranteed_income:,}
    - **Net from Portfolio**: ${net_consumption_need:,}
    - Tax Rate on Withdrawals: {effective_tax_rate:.1f}%
    - **Gross Withdrawal Needed**: ${net_consumption_need / (1 - effective_tax_rate/100):,.0f}
    """)
    
    if net_consumption_need <= 0:
        st.success("✅ Your guaranteed income covers your consumption needs!")
    else:
        withdrawal_rate = (net_consumption_need / (1 - effective_tax_rate/100)) / initial_portfolio * 100
        st.info(f"📊 Initial withdrawal rate: {withdrawal_rate:.2f}%")

with tab2:
    st.header("Simulation Results")
    
    if st.button("🎲 Run Simulation", type="primary"):
        with st.spinner(f"Running {n_simulations:,} simulations..."):
            
            # Run Monte Carlo simulation
            n_years = max_age - current_age
            
            # Initialize arrays
            portfolio_paths = np.zeros((n_simulations, n_years + 1))
            portfolio_paths[:, 0] = initial_portfolio
            
            # Track cost basis for capital gains calculations
            cost_basis = np.full(n_simulations, initial_portfolio)  # Initial basis
            
            # Track components for analysis
            dividend_income = np.zeros((n_simulations, n_years))
            capital_gains = np.zeros((n_simulations, n_years))  # Now tracks REALIZED gains
            gross_withdrawals = np.zeros((n_simulations, n_years))
            taxes_paid = np.zeros((n_simulations, n_years))
            net_withdrawals = np.zeros((n_simulations, n_years))
            
            failure_year = np.full(n_simulations, n_years + 1)  # Year of failure
            alive_mask = np.ones((n_simulations, n_years + 1), dtype=bool)
            
            # Track annuity income for each simulation
            annuity_income = np.zeros((n_simulations, n_years))
            
            # Simulate each year
            for year in range(1, n_years + 1):
                age = current_age + year
                
                # Calculate annuity income for this year
                if has_annuity:
                    # Determine who gets annuity payments this year
                    if annuity_type == "Fixed Period":
                        # Fixed period: pays for specified years regardless of mortality
                        gets_annuity = year <= annuity_guarantee_years
                        annuity_income[:, year-1] = annuity_annual if gets_annuity else 0
                    elif annuity_type == "Life Only":
                        # Life only: pays while alive
                        annuity_income[:, year-1] = np.where(alive_mask[:, year-1], annuity_annual, 0)
                    else:  # Life Contingent with Guarantee
                        # Pays while alive OR during guarantee period
                        in_guarantee = year <= annuity_guarantee_years
                        annuity_income[:, year-1] = np.where(
                            alive_mask[:, year-1] | in_guarantee,
                            annuity_annual, 0
                        )
                
                # Mortality (if enabled)
                if include_mortality and age > current_age:
                    mort_rate = np.interp(age, 
                                         list(mortality_rates.keys()) if include_mortality else [age],
                                         list(mortality_rates.values()) if include_mortality else [0])
                    death_this_year = np.random.random(n_simulations) < mort_rate
                    alive_mask[death_this_year, year:] = False
                
                # Only simulate for those still alive and not failed
                active = alive_mask[:, year] & (portfolio_paths[:, year-1] > 0)
                
                if not active.any():
                    continue
                
                # Investment returns - Geometric Brownian Motion
                # This is the standard model in finance literature
                # dS/S = μdt + σdW where μ is drift, σ is volatility
                returns = np.random.normal(expected_return/100, return_volatility/100, n_simulations)
                growth_factor = np.exp(returns)  # Log-normal to ensure positive prices
                
                # Portfolio evolution for ALL scenarios (not just active)
                current_portfolio = portfolio_paths[:, year-1]
                
                # Growth (only for non-zero portfolios)
                portfolio_after_growth = np.zeros_like(current_portfolio)
                portfolio_after_growth[active] = current_portfolio[active] * growth_factor[active]
                
                # Dividends - calculated on current portfolio value for ALL scenarios
                # This WILL vary each year as portfolio values change
                dividends = current_portfolio * (dividend_yield / 100)
                dividend_income[:, year-1] = dividends  # Store for all scenarios
                
                # Calculate actual withdrawal needed (after considering dividends)
                # Net need is consumption minus guaranteed income minus dividends
                actual_net_need = np.maximum(0, net_consumption_need - dividends)
                
                # Only withdraw what we need (don't withdraw if dividends cover it)
                actual_gross_withdrawal = np.zeros(n_simulations)
                actual_gross_withdrawal[active] = actual_net_need[active] / (1 - effective_tax_rate/100)
                
                # Track withdrawals 
                gross_withdrawals[:, year-1] = actual_gross_withdrawal
                
                # Calculate REALIZED capital gains on withdrawals
                # Proportion of portfolio that is gains vs basis
                gain_fraction = np.where(current_portfolio > 0,
                                        np.maximum(0, (current_portfolio - cost_basis) / current_portfolio),
                                        0)
                
                # Realized capital gains from this withdrawal
                realized_gains = actual_gross_withdrawal * gain_fraction
                capital_gains[:, year-1] = realized_gains
                
                # Update cost basis (proportionally reduced by withdrawal)
                withdrawal_fraction = np.where(current_portfolio > 0,
                                              actual_gross_withdrawal / current_portfolio,
                                              0)
                cost_basis *= (1 - withdrawal_fraction)
                
                # Simplified tax calculation
                # In reality, capital gains have preferential rates
                # Dividends may be qualified (lower rate) or ordinary
                ordinary_income = dividends  # Assume dividends are ordinary (conservative)
                capital_gains_income = realized_gains
                
                # Apply different rates (simplified)
                ordinary_tax = ordinary_income * (effective_tax_rate/100)
                cap_gains_tax = capital_gains_income * (effective_tax_rate * 0.6 / 100)  # Cap gains ~60% of ordinary rate
                
                taxes_paid[:, year-1] = ordinary_tax + cap_gains_tax
                
                # Net withdrawals after tax
                net_withdrawals[:, year-1] = actual_gross_withdrawal * (1 - effective_tax_rate/100)
                
                # New portfolio value (dividends received, withdrawals taken)
                new_portfolio = portfolio_after_growth + dividends - actual_gross_withdrawal
                
                # Check for failures
                newly_failed = (current_portfolio > 0) & (new_portfolio < 0)
                failure_year[newly_failed & (failure_year > n_years)] = year
                
                # Update portfolio (floor at 0)
                portfolio_paths[:, year] = np.maximum(0, new_portfolio)
            
            # Calculate statistics
            success_mask = failure_year > n_years
            success_rate = success_mask.mean()
            
            # Percentiles over time
            percentiles = np.percentile(portfolio_paths, [10, 25, 50, 75, 90], axis=0)
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Success Rate", f"{success_rate:.1%}",
                         help="Probability of maintaining consumption through planning horizon")
            
            with col2:
                median_final = np.median(portfolio_paths[success_mask, -1]) if success_mask.any() else 0
                st.metric("Median Final Portfolio", f"${median_final:,.0f}",
                         help="Median portfolio value at end (successful scenarios only)")
            
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
            
            # Add percentile bands
            fig.add_trace(go.Scatter(
                x=years, y=percentiles[4],
                name='90th Percentile',
                line=dict(color='lightgreen', width=1),
                showlegend=True
            ))
            
            fig.add_trace(go.Scatter(
                x=years, y=percentiles[3],
                fill='tonexty',
                name='75th Percentile',
                line=dict(color='green', width=1),
                fillcolor='rgba(0,255,0,0.1)'
            ))
            
            fig.add_trace(go.Scatter(
                x=years, y=percentiles[2],
                name='Median',
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=years, y=percentiles[1],
                fill='tonexty',
                name='25th Percentile',
                line=dict(color='orange', width=1),
                fillcolor='rgba(255,165,0,0.1)'
            ))
            
            fig.add_trace(go.Scatter(
                x=years, y=percentiles[0],
                name='10th Percentile',
                line=dict(color='red', width=1)
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
                    trajectory_idx = np.random.randint(0, n_simulations)
                    st.rerun()
        
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
        current_withdrawal_rate = (net_consumption_need / (1 - effective_tax_rate/100)) / initial_portfolio * 100
        
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            spending_change = st.slider(
                "Adjust Annual Spending (%)",
                -30, 30, 0, 5
            )
            
            new_consumption = annual_consumption * (1 + spending_change/100)
            new_net = new_consumption - guaranteed_income
            new_withdrawal_rate = (new_net / (1 - effective_tax_rate/100)) / initial_portfolio * 100
            
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