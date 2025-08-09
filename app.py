"""Streamlit app for retirement decision analysis."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from finsim import MonteCarloSimulator, TaxCalculator, AnnuityCalculator


# Page config
st.set_page_config(
    page_title="Retirement Decision Tool",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Retirement Settlement Decision Tool")
st.markdown("""
Compare structured settlement annuities with index fund investments, 
accounting for taxes, Social Security benefits, and mortality risk.
""")

# Sidebar inputs
st.sidebar.header("📊 Basic Information")

age = st.sidebar.number_input("Current Age", min_value=50, max_value=100, value=65)
state = st.sidebar.selectbox("State", ["CA", "NY", "TX", "FL", "IL", "PA"], index=0)
filing_status = st.sidebar.selectbox("Filing Status", ["SINGLE", "JOINT"], index=0)

st.sidebar.header("💵 Settlement Details")
settlement_amount = st.sidebar.number_input(
    "Settlement Amount ($)", 
    min_value=0, 
    value=527_530, 
    step=10_000,
    format="%d"
)

st.sidebar.header("🏦 Social Security")
monthly_ss_benefit = st.sidebar.number_input(
    "Monthly SS Benefit ($)", 
    min_value=0, 
    value=2_000, 
    step=100,
    format="%d"
)
annual_ss_benefit = monthly_ss_benefit * 12

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Annuity Options", "📈 Analysis", "🎲 Monte Carlo", "📊 Tax Details"])

# Tab 1: Annuity Options
with tab1:
    st.header("Enter Annuity Proposals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Proposal A")
        a_monthly = st.number_input("Monthly Payment A ($)", value=3_516, step=100, key="a_monthly")
        a_guarantee = st.number_input("Guarantee Period A (years)", value=15, step=1, key="a_guarantee")
        a_life = st.checkbox("Life Contingent", value=True, key="a_life")
        a_taxable = st.checkbox("Taxable", value=False, key="a_taxable")
    
    with col2:
        st.subheader("Proposal B")
        b_monthly = st.number_input("Monthly Payment B ($)", value=4_058, step=100, key="b_monthly")
        b_guarantee = st.number_input("Guarantee Period B (years)", value=15, step=1, key="b_guarantee")
        b_life = st.checkbox("Life Contingent", value=False, key="b_life")
        b_taxable = st.checkbox("Taxable", value=False, key="b_taxable")
    
    st.subheader("Proposal C")
    col3, col4 = st.columns(2)
    with col3:
        c_monthly = st.number_input("Monthly Payment C ($)", value=5_397, step=100, key="c_monthly")
        c_guarantee = st.number_input("Guarantee Period C (years)", value=10, step=1, key="c_guarantee")
    with col4:
        c_life = st.checkbox("Life Contingent", value=False, key="c_life")
        c_taxable = st.checkbox("Taxable", value=False, key="c_taxable")

# Tab 2: Analysis
with tab2:
    st.header("Comparative Analysis")
    
    # Create annuity proposals
    proposals = [
        {
            'name': 'Proposal A',
            'premium': settlement_amount,
            'monthly_payment': a_monthly,
            'guarantee_months': int(a_guarantee * 12),
            'life_contingent': a_life,
            'taxable': a_taxable
        },
        {
            'name': 'Proposal B',
            'premium': settlement_amount,
            'monthly_payment': b_monthly,
            'guarantee_months': int(b_guarantee * 12),
            'life_contingent': b_life,
            'taxable': b_taxable
        },
        {
            'name': 'Proposal C',
            'premium': settlement_amount,
            'monthly_payment': c_monthly,
            'guarantee_months': int(c_guarantee * 12),
            'life_contingent': c_life,
            'taxable': c_taxable
        }
    ]
    
    # Calculate annuity metrics
    annuity_calc = AnnuityCalculator(age=age)
    annuity_df = annuity_calc.compare_annuity_options(proposals)
    
    # Display annuity comparison
    st.subheader("Annuity Comparison")
    st.dataframe(annuity_df.style.format({
        'Premium': '${:,.0f}',
        'Monthly Payment': '${:,.0f}',
        'Annual Payment': '${:,.0f}',
        'Total Guaranteed': '${:,.0f}',
        'IRR': '{:.1%}',
        'Guarantee Period': '{:.0f} years'
    }))
    
    # Index fund alternatives
    st.subheader("Index Fund Alternative (VT)")
    
    col1, col2 = st.columns(2)
    with col1:
        expected_return = st.slider("Expected Annual Return", 0.0, 0.15, 0.08, 0.01, format="%.1%")
        volatility = st.slider("Annual Volatility", 0.0, 0.30, 0.158, 0.01, format="%.1%")
    with col2:
        dividend_yield = st.slider("Dividend Yield", 0.0, 0.05, 0.02, 0.005, format="%.1%")
        n_simulations = st.selectbox("Number of Simulations", [1000, 5000, 10000, 50000], index=2)
    
    # Tax calculations
    st.subheader("Tax-Adjusted Comparison")
    
    tax_calc = TaxCalculator(state=state, year=2025)
    
    # Calculate required gross withdrawals for each annuity level
    tax_results = {}
    for proposal in proposals:
        if proposal['taxable']:
            # If annuity is taxable, need to calculate after-tax amount
            target = proposal['monthly_payment'] * 12
        else:
            # If annuity is tax-free, this is the target after-tax income
            target = proposal['monthly_payment'] * 12
        
        # Calculate gross withdrawal needed from index fund
        gross_withdrawal, taxes = tax_calc.calculate_withdrawal_to_match_after_tax(
            target_after_tax=target,
            social_security_benefits=annual_ss_benefit,
            age=age,
            taxable_fraction=0.2  # Assume 20% capital gains initially
        )
        
        tax_results[proposal['name']] = {
            'target_after_tax': target,
            'gross_withdrawal': gross_withdrawal,
            'monthly_gross': gross_withdrawal / 12,
            'total_tax': taxes['total_tax'],
            'effective_rate': taxes['effective_tax_rate']
        }
    
    # Display tax comparison
    tax_df = pd.DataFrame(tax_results).T
    st.dataframe(tax_df.style.format({
        'target_after_tax': '${:,.0f}',
        'gross_withdrawal': '${:,.0f}',
        'monthly_gross': '${:,.0f}',
        'total_tax': '${:,.0f}',
        'effective_rate': '{:.1%}'
    }))

# Tab 3: Monte Carlo Simulation
with tab3:
    st.header("Monte Carlo Simulation Results")
    
    # Run simulations for each proposal
    selected_proposal = st.selectbox(
        "Select Proposal to Simulate",
        ['Proposal A', 'Proposal B', 'Proposal C']
    )
    
    simulation_years = st.slider("Simulation Period (Years)", 5, 30, 15, 1)
    simulation_months = simulation_years * 12
    
    # Get the withdrawal amount for selected proposal
    selected_idx = ['Proposal A', 'Proposal B', 'Proposal C'].index(selected_proposal)
    monthly_withdrawal = tax_results[selected_proposal]['monthly_gross']
    
    # Run Monte Carlo
    mc_simulator = MonteCarloSimulator(
        initial_capital=settlement_amount,
        monthly_withdrawal=monthly_withdrawal,
        annual_return_mean=expected_return,
        annual_return_std=volatility,
        annual_dividend_yield=dividend_yield,
        n_simulations=n_simulations
    )
    
    results = mc_simulator.simulate(simulation_months)
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Depletion Risk", f"{results['depletion_probability']:.1%}")
    with col2:
        st.metric("Median Final Value", f"${results['median_final_value']:,.0f}")
    with col3:
        st.metric("5th Percentile", f"${results['percentiles']['p5']:,.0f}")
    with col4:
        st.metric("95th Percentile", f"${results['percentiles']['p95']:,.0f}")
    
    # Plot simulation paths
    st.subheader("Portfolio Value Over Time")
    
    # Sample paths for visualization
    n_display = min(100, n_simulations)
    sample_indices = np.random.choice(n_simulations, n_display, replace=False)
    
    fig = go.Figure()
    
    # Add individual paths
    for i in sample_indices:
        fig.add_trace(go.Scatter(
            x=list(range(simulation_months + 1)),
            y=results['paths'][i],
            mode='lines',
            line=dict(width=0.5, color='lightblue'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Add percentile bands
    percentiles_over_time = np.percentile(results['paths'], [5, 25, 50, 75, 95], axis=0)
    
    fig.add_trace(go.Scatter(
        x=list(range(simulation_months + 1)),
        y=percentiles_over_time[2],  # Median
        mode='lines',
        name='Median',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=list(range(simulation_months + 1)),
        y=percentiles_over_time[0],  # 5th percentile
        mode='lines',
        name='5th Percentile',
        line=dict(color='red', width=1, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=list(range(simulation_months + 1)),
        y=percentiles_over_time[4],  # 95th percentile
        mode='lines',
        name='95th Percentile',
        line=dict(color='green', width=1, dash='dash')
    ))
    
    fig.update_layout(
        title=f"Monte Carlo Simulation - {selected_proposal}",
        xaxis_title="Months",
        yaxis_title="Portfolio Value ($)",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Distribution of final values
    st.subheader("Distribution of Final Values")
    
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=results['final_values'],
        nbinsx=50,
        name='Final Values',
        marker_color='blue',
        opacity=0.7
    ))
    
    fig2.add_vline(
        x=0, 
        line_dash="dash", 
        line_color="red",
        annotation_text="Depleted"
    )
    
    fig2.add_vline(
        x=settlement_amount, 
        line_dash="dash", 
        line_color="green",
        annotation_text="Initial Capital"
    )
    
    fig2.update_layout(
        title="Distribution of Final Portfolio Values",
        xaxis_title="Portfolio Value ($)",
        yaxis_title="Frequency",
        height=400
    )
    
    st.plotly_chart(fig2, use_container_width=True)

# Tab 4: Tax Details
with tab4:
    st.header("Tax Calculation Details")
    
    # Taxable fraction over time
    st.subheader("Capital Gains Inclusion Ratio")
    
    years = np.arange(1, 21)
    taxable_fractions = np.minimum(0.8, 0.2 + 0.05 * (years - 1))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years,
        y=taxable_fractions,
        mode='lines+markers',
        name='Taxable Fraction',
        line=dict(color='purple', width=2)
    ))
    
    fig.update_layout(
        title="Proportion of Withdrawal Subject to Capital Gains Tax",
        xaxis_title="Year",
        yaxis_title="Taxable Fraction",
        yaxis_tickformat='.0%',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tax breakdown for different withdrawal levels
    st.subheader("Tax Analysis by Withdrawal Amount")
    
    withdrawal_amounts = np.linspace(30_000, 100_000, 20)
    tax_data = []
    
    for withdrawal in withdrawal_amounts:
        capital_gains = withdrawal * 0.2  # Assume 20% taxable
        taxes = tax_calc.calculate_taxes(
            capital_gains=capital_gains,
            social_security_benefits=annual_ss_benefit,
            age=age
        )
        tax_data.append({
            'Withdrawal': withdrawal,
            'Federal Tax': taxes['federal_income_tax'],
            'State Tax': taxes['state_income_tax'],
            'Total Tax': taxes['total_tax'],
            'After-Tax': withdrawal - taxes['total_tax']
        })
    
    tax_analysis_df = pd.DataFrame(tax_data)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=tax_analysis_df['Withdrawal'],
        y=tax_analysis_df['After-Tax'],
        mode='lines',
        name='After-Tax Income',
        line=dict(color='green', width=2)
    ))
    
    fig2.add_trace(go.Scatter(
        x=tax_analysis_df['Withdrawal'],
        y=tax_analysis_df['Total Tax'],
        mode='lines',
        name='Total Tax',
        line=dict(color='red', width=2)
    ))
    
    fig2.update_layout(
        title="Tax Impact on Index Fund Withdrawals",
        xaxis_title="Gross Withdrawal ($)",
        yaxis_title="Amount ($)",
        height=400
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Social Security taxation
    st.subheader("Social Security Benefit Taxation")
    st.info(f"""
    With ${annual_ss_benefit:,.0f} in annual Social Security benefits:
    - Benefits become taxable when combined income exceeds thresholds
    - Up to 85% of benefits can be subject to federal tax
    - California does not tax Social Security benefits
    - The OBBBA senior deduction helps shield income from federal tax
    """)

# Footer
st.markdown("---")
st.markdown("""
**Disclaimer:** This tool is for educational purposes only. 
Consult with qualified financial and tax professionals before making decisions.
""")