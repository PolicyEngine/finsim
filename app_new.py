"""FinSim Streamlit application - refactored to use modular package structure."""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import FinSim modules
from finsim.simulation import SimulationConfig, RetirementSimulation
from finsim.mortality import get_mortality_rates, calculate_survival_curve
from finsim.market import MarketDataFetcher

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


def create_preview_charts(config: SimulationConfig):
    """Create preview charts for key inputs."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**💀 Mortality Risk**")
        if config.include_mortality:
            mortality_rates = get_mortality_rates(config.gender)
            
            ages = list(range(config.current_age, min(config.max_age + 1, 101)))
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
        st.markdown("**💵 Dividend Income**")
        years_preview = np.arange(0, min(30, config.max_age - config.current_age + 1))
        # Show how dividend income changes with portfolio value
        sample_portfolio = config.initial_portfolio * np.exp(config.expected_return/100 * years_preview)
        dividend_preview = sample_portfolio * (config.dividend_yield / 100)
        
        fig_div_preview = go.Figure()
        fig_div_preview.add_trace(go.Scatter(
            x=config.current_age + years_preview, 
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
        st.caption(f"At {config.dividend_yield:.1f}% yield on growing portfolio")
    
    with col3:
        st.markdown("**📈 Portfolio Projection**")
        years_preview = np.arange(0, min(30, config.max_age - config.current_age + 1))
        
        # Calculate expected value and confidence bands
        expected_value = config.initial_portfolio * np.exp(config.expected_return/100 * years_preview)
        
        # Standard deviation grows with sqrt(time)
        std_dev = config.initial_portfolio * np.exp(config.expected_return/100 * years_preview) * \
                  (np.exp(config.return_volatility/100 * np.sqrt(years_preview)) - 1)
        
        upper_band = expected_value + std_dev
        lower_band = np.maximum(0, expected_value - std_dev)
        
        fig_portfolio_preview = go.Figure()
        
        # Add confidence band
        fig_portfolio_preview.add_trace(go.Scatter(
            x=config.current_age + years_preview,
            y=upper_band,
            mode='lines',
            name='±1σ Band',
            line=dict(width=0),
            showlegend=False
        ))
        fig_portfolio_preview.add_trace(go.Scatter(
            x=config.current_age + years_preview,
            y=lower_band,
            mode='lines',
            name='±1σ Band',
            line=dict(width=0),
            fillcolor='rgba(68, 68, 68, 0.2)',
            fill='tonexty',
            showlegend=False
        ))
        
        # Add expected value
        fig_portfolio_preview.add_trace(go.Scatter(
            x=config.current_age + years_preview,
            y=expected_value,
            mode='lines',
            name='Expected Value',
            line=dict(color='blue', width=2)
        ))
        
        fig_portfolio_preview.update_layout(
            xaxis_title="Age",
            yaxis_title="Portfolio Value ($)",
            height=200,
            margin=dict(l=0, r=0, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_portfolio_preview, use_container_width=True)
        st.caption(f"{config.expected_return:.1f}% return, {config.return_volatility:.1f}% volatility")


def create_configuration_sidebar():
    """Create the configuration sidebar and return SimulationConfig."""
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

    # Market assumptions
    st.sidebar.header("📈 Market Assumptions")
    st.sidebar.markdown("*All returns are real (after inflation)*")

    # Option to calibrate to specific funds
    calibration_method = st.sidebar.radio(
        "Calibration Method",
        ["Manual", "Historical Fund Data"],
        help="Manual: Set your own assumptions\nHistorical: Calibrate to actual fund performance"
    )

    expected_return = 5.0
    return_volatility = 16.0
    dividend_yield = 2.0

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
                    fetcher = MarketDataFetcher()
                    fund_data = fetcher.fetch_fund_data(
                        ticker=fund_ticker,
                        years=lookback_years,
                        inflation_rate=2.5  # Default inflation assumption
                    )
                    
                    st.sidebar.success(f"""
                    ✅ **{fund_ticker} Data** ({lookback_years}Y, {fund_data.data_points} points)
                    - Real Return: {fund_data.annual_return:.1f}%
                    - Volatility: {fund_data.volatility:.1f}%
                    - Dividend Yield: {fund_data.dividend_yield:.1f}%
                    - Expense Ratio: {fund_data.expense_ratio:.2f}%
                    """)
                    
                    # Store in session state
                    st.session_state['calibrated_return'] = fund_data.annual_return
                    st.session_state['calibrated_volatility'] = fund_data.volatility
                    st.session_state['calibrated_dividend'] = fund_data.dividend_yield
                    
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

    # Simulation settings
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

    # Create configuration
    return SimulationConfig(
        current_age=current_age,
        retirement_age=retirement_age,
        max_age=max_age,
        gender=gender,
        initial_portfolio=initial_portfolio,
        annual_consumption=annual_consumption,
        social_security=social_security,
        pension=pension,
        annuity_annual=annuity_annual,
        annuity_type=annuity_type,
        annuity_guarantee_years=annuity_guarantee_years,
        expected_return=expected_return,
        return_volatility=return_volatility,
        dividend_yield=dividend_yield,
        effective_tax_rate=effective_tax_rate,
        n_simulations=n_simulations,
        include_mortality=include_mortality
    )


def display_assumptions_tab(config: SimulationConfig):
    """Display the assumptions tab with preview charts."""
    st.header("Key Assumptions & Methodology")
    
    # Preview charts
    st.subheader("📊 Key Input Trends")
    create_preview_charts(config)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎲 Portfolio Returns")
        
        st.write(f"""
        - **Model**: Geometric Brownian Motion (GBM)
        - **Mathematical Form**: dS/S = μdt + σdW
        - **Expected Return (μ)**: {config.expected_return:.1f}% real per year
        - **Volatility (σ)**: {config.return_volatility:.1f}% annual standard deviation
        - **Dividends**: {config.dividend_yield:.1f}% paid annually
        """)
        
        # Show return distribution
        x = np.linspace(-30, 50, 100)
        from scipy import stats
        y = stats.norm.pdf(x, config.expected_return, config.return_volatility)
        
        fig_returns = go.Figure()
        fig_returns.add_trace(go.Scatter(
            x=x, y=y,
            fill='tozeroy',
            name='Return Distribution'
        ))
        fig_returns.add_vline(x=config.expected_return, line_dash="dash", 
                             annotation_text=f"Expected: {config.expected_return:.1f}%")
        fig_returns.update_layout(
            title="Annual Return Distribution",
            xaxis_title="Real Return (%)",
            yaxis_title="Probability Density",
            height=300
        )
        st.plotly_chart(fig_returns, use_container_width=True)
    
    with col2:
        st.subheader("💀 Mortality Risk")
        if config.include_mortality:
            survival_probs = calculate_survival_curve(
                config.current_age, 
                config.max_age, 
                config.gender
            )
            ages = np.arange(config.current_age, config.max_age + 1)
            
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
    
    guaranteed_income = config.guaranteed_income
    net_consumption_need = config.net_consumption_need
    
    st.write(f"""
    **Annual Cash Flows (Real $)**
    - Consumption Need: ${config.annual_consumption:,}
    - Guaranteed Income: ${guaranteed_income:,}
    - **Net from Portfolio**: ${net_consumption_need:,}
    - Tax Rate on Withdrawals: {config.effective_tax_rate:.1f}%
    - **Gross Withdrawal Needed**: ${net_consumption_need / (1 - config.effective_tax_rate/100):,.0f}
    """)
    
    if net_consumption_need <= 0:
        st.success("✅ Your guaranteed income covers your consumption needs!")
    else:
        withdrawal_rate = (net_consumption_need / (1 - config.effective_tax_rate/100)) / config.initial_portfolio * 100
        st.info(f"📊 Initial withdrawal rate: {withdrawal_rate:.2f}%")


def main():
    """Main application function."""
    # Create configuration from sidebar
    config = create_configuration_sidebar()
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📖 Assumptions", "📊 Results", "📈 Detailed Analysis", "🎯 Strategy"])

    with tab1:
        display_assumptions_tab(config)

    with tab2:
        st.header("Simulation Results")
        
        if st.button("🎲 Run Simulation", type="primary"):
            with st.spinner(f"Running {config.n_simulations:,} simulations..."):
                
                # Run Monte Carlo simulation using the package
                sim = RetirementSimulation(config)
                results = sim.run_monte_carlo()
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Success Rate", f"{results.success_rate:.1%}",
                             help="Probability of maintaining consumption through planning horizon")
                
                with col2:
                    successful_mask = results.failure_years > (config.max_age - config.current_age)
                    if successful_mask.any():
                        median_final = np.median(results.portfolio_paths[successful_mask, -1])
                        st.metric("Median Final Portfolio", f"${median_final:,.0f}",
                                 help="Median portfolio value at end (successful scenarios only)")
                    else:
                        st.metric("Median Final Portfolio", "N/A")
                
                with col3:
                    failed_mask = ~successful_mask
                    if failed_mask.any():
                        median_failure_year = np.median(results.failure_years[failed_mask])
                        median_failure_age = config.current_age + median_failure_year
                        st.metric("Median Failure Age", f"{median_failure_age:.0f}",
                                 help="Median age at portfolio depletion (failed scenarios)")
                    else:
                        st.metric("Median Failure Age", "N/A", help="No failures")
                
                with col4:
                    prob_10_years = (results.failure_years <= 10).mean()
                    st.metric("10-Year Failure Risk", f"{prob_10_years:.1%}",
                             help="Probability of failure within 10 years")
                
                # Portfolio paths visualization
                st.subheader("Portfolio Value Over Time")
                
                ages = np.arange(config.current_age, config.max_age + 1)
                
                fig = go.Figure()
                
                # Add percentile bands
                percentiles = results.percentiles
                
                fig.add_trace(go.Scatter(
                    x=ages, y=percentiles[90],
                    name='90th Percentile',
                    line=dict(color='lightgreen', width=1),
                    showlegend=True
                ))
                
                fig.add_trace(go.Scatter(
                    x=ages, y=percentiles[75],
                    fill='tonexty',
                    name='75th Percentile',
                    line=dict(color='green', width=1),
                    fillcolor='rgba(0,255,0,0.1)'
                ))
                
                fig.add_trace(go.Scatter(
                    x=ages, y=percentiles[50],
                    name='Median',
                    line=dict(color='blue', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=ages, y=percentiles[25],
                    fill='tonexty',
                    name='25th Percentile',
                    line=dict(color='orange', width=1),
                    fillcolor='rgba(255,165,0,0.1)'
                ))
                
                fig.add_trace(go.Scatter(
                    x=ages, y=percentiles[10],
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
                
                # Store results in session state for other tabs
                st.session_state['simulation_results'] = results
                st.session_state['simulation_config'] = config

    with tab3:
        st.header("Detailed Analysis")
        
        if 'simulation_results' in st.session_state:
            st.info("Detailed analysis would show cash flow components, failure distributions, etc.")
            st.markdown("This tab will be implemented with the full refactor.")
        else:
            st.info("👈 Run simulation first to see detailed analysis")

    with tab4:
        st.header("Strategy Insights")
        
        if 'simulation_results' in st.session_state:
            results = st.session_state['simulation_results']
            
            if results.success_rate > 0.95:
                st.success(f"""
                ✅ **Strong Position**: {results.success_rate:.1%} success rate.
                Consider increasing spending or reducing portfolio risk.
                """)
            elif results.success_rate > 0.80:
                st.info(f"""
                ⚠️ **Moderate Risk**: {results.success_rate:.1%} success rate.
                Consider building cash reserves or planning spending flexibility.
                """)
            else:
                st.warning(f"""
                ⚠️ **High Risk**: {results.success_rate:.1%} success rate.
                Consider reducing spending, delaying retirement, or increasing guaranteed income.
                """)
        else:
            st.info("👈 Run simulation first to see strategy insights")

    # Footer
    st.markdown("---")
    st.markdown("""
    **Disclaimer**: This tool is for educational purposes only. 
    Consult with qualified financial professionals before making retirement decisions.
    All calculations are in real (inflation-adjusted) terms.
    """)


if __name__ == "__main__":
    main()